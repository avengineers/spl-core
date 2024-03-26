import argparse
import json
import os
import re
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Any, Generator, List, Optional

import kconfiglib

from spl_core.common.path import existing_path, non_existing_path


class GeneratedFile:
    def __init__(self, path: Path, content: str = "", skip_writing_if_unchanged: bool = False) -> None:
        self.path = path

        self.content = content

        self.skip_writing_if_unchanged = skip_writing_if_unchanged

    def to_string(self) -> str:
        return self.content

    def to_file(self) -> None:
        """
        Only write to file if the content has changed.

        The directory of the file is created if it does not exist.
        """
        content = self.to_string()

        if not self.path.exists() or not self.skip_writing_if_unchanged or self.path.read_text() != content:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(content)


class TriState(Enum):
    Y = auto()
    M = auto()
    N = auto()


class ConfigElementType(Enum):
    UNKNOWN = auto()
    BOOL = auto()
    TRISTATE = auto()
    STRING = auto()
    INT = auto()
    HEX = auto()


@dataclass
class ConfigElement:
    type: ConfigElementType
    name: str
    value: Any
    #: Is determined when the value is calculated. This is a hidden function call due to property magic.
    _write_to_conf: bool = True


@dataclass
class ConfigurationData:
    """
    - holds the variant configuration data
    - requires no variable substitution (this should have been already done)
    """

    elements: List[ConfigElement]


class FileWriter(ABC):
    """- writes the ConfigurationData to a file"""

    def __init__(self, output_file: Path):
        self.output_file = output_file

    def write(self, configuration_data: ConfigurationData) -> None:
        """
        - writes the ConfigurationData to a file
        The file shall not be modified if the content is the same as the existing one
        """
        content = self.generate_content(configuration_data)
        GeneratedFile(self.output_file, content, skip_writing_if_unchanged=True).to_file()

    @abstractmethod
    def generate_content(self, configuration_data: ConfigurationData) -> str:
        """- generates the content of the file from the ConfigurationData"""


class HeaderWriter(FileWriter):
    """Writes the ConfigurationData as pre-processor defines in a C Header file"""

    config_prefix = "CONFIG_"  # Prefix for all configuration defines

    def generate_content(self, configuration_data: ConfigurationData) -> str:
        """
        This method does exactly what the kconfiglib.write_autoconf() method does.
        We had to implemented here because we refactor the file writers to use the ConfigurationData
        instead of the KConfig configuration. ConfigurationData has variable substitution already done.
        """
        result: List[str] = [
            "/** @file */",
            "#ifndef __autoconf_h__",
            "#define __autoconf_h__",
            "",
        ]

        def add_define(define_decl: str, description: str) -> None:
            result.append(f"/** {description} */")
            result.append(define_decl)

        for element in configuration_data.elements:
            val = element.value
            if not element._write_to_conf:
                continue

            if element.type in [ConfigElementType.BOOL, ConfigElementType.TRISTATE]:
                if val == TriState.Y:
                    add_define(f"#define {self.config_prefix}{element.name} 1", element.name)
                elif val == TriState.M:
                    add_define(
                        f"#define {self.config_prefix}{element.name}_MODULE 1",
                        element.name,
                    )

            elif element.type is ConfigElementType.STRING:
                add_define(
                    f'#define {self.config_prefix}{element.name} "{kconfiglib.escape(val)}"',
                    element.name,
                )

            else:  # element.type in [INT, HEX]:
                if element.type is ConfigElementType.HEX:
                    val = hex(val)
                add_define(f"#define {self.config_prefix}{element.name} {val}", element.name)
        result.extend(["", "#endif /* __autoconf_h__ */", ""])
        return "\n".join(result)


class JsonWriter(FileWriter):
    """Writes the ConfigurationData in json format"""

    def generate_content(self, configuration_data: ConfigurationData) -> str:
        result = {}
        for element in configuration_data.elements:
            if element.type is ConfigElementType.BOOL:
                result[element.name] = True if element.value == TriState.Y else False
            else:
                result[element.name] = element.value
        return json.dumps({"features": result}, indent=4)


class CMakeWriter(FileWriter):
    """Writes the ConfigurationData as CMake variables"""

    def generate_content(self, configuration_data: ConfigurationData) -> str:
        result: List[str] = []
        add = result.append
        for element in configuration_data.elements:
            val = element.value
            if element.type is ConfigElementType.BOOL:
                val = True if element.value == TriState.Y else False
            if not element._write_to_conf:
                continue
            add(f'set({element.name} "{val}")')

        return "\n".join(result)


@contextmanager
def working_directory(some_directory: Path) -> Generator[Any, Any, Any]:
    current_directory = Path().absolute()
    try:
        os.chdir(some_directory)
        yield
    finally:
        os.chdir(current_directory)


class KConfig:
    def __init__(
        self,
        k_config_model_file: Path,
        k_config_file: Optional[Path] = None,
        k_config_root_directory: Optional[Path] = None,
    ):
        """
        :param k_config_model_file: Feature model definition (KConfig format)
        :param k_config_file: User feature selection configuration file
        :param k_config_root_directory: all paths for the included configuration paths shall be relative to this folder
        """
        if not k_config_model_file.exists():
            raise FileNotFoundError(f"File {k_config_model_file} does not exist.")
        with working_directory(k_config_root_directory or k_config_model_file.parent):
            self._config = kconfiglib.Kconfig(k_config_model_file.absolute().as_posix())
        if k_config_file:
            if not k_config_file.exists():
                raise FileNotFoundError(f"File {k_config_file} does not exist.")
            self._config.load_config(k_config_file, replace=False)
        self.config = self.create_config_data(self._config)

    def create_config_data(self, config: kconfiglib.Kconfig) -> ConfigurationData:
        """- creates the ConfigurationData from the KConfig configuration"""
        elements = []
        elements_dict = {}

        def process_node(node: Any) -> None:
            sym = node.item
            if not isinstance(sym, kconfiglib.Symbol):
                return

            if sym.config_string:
                val = sym.str_value
                type = ConfigElementType.STRING
                if sym.type in [kconfiglib.BOOL, kconfiglib.TRISTATE]:
                    val = getattr(TriState, str(val).upper())
                    type = ConfigElementType.BOOL if sym.type == kconfiglib.BOOL else ConfigElementType.TRISTATE
                elif sym.type == kconfiglib.HEX:
                    val = int(str(val), 16)
                    type = ConfigElementType.HEX
                elif sym.type == kconfiglib.INT:
                    val = int(val)
                    type = ConfigElementType.INT
                new_element = ConfigElement(type, sym.name, val, sym._write_to_conf)
                elements.append(new_element)
                elements_dict[sym.name] = new_element

        for n in config.node_iter(False):
            process_node(n)

        # replace text in KConfig with referenced variables (string type only)
        # KConfig variables get replaced like: ${VARIABLE_NAME}, e.g. ${CONFIG_FOO}
        for element in elements:
            if element.type == ConfigElementType.STRING:
                element.value = re.sub(
                    r"\$\{([A-Za-z0-9_]+)\}",
                    lambda m: str(elements_dict[m.group(1)].value),
                    element.value,
                )
                element.value = re.sub(
                    r"\$\{ENV:([A-Za-z0-9_]+)\}",
                    lambda m: str(os.environ.get(m.group(1), "")),
                    element.value,
                )

        return ConfigurationData(elements)


def main() -> None:
    parser = argparse.ArgumentParser(description="KConfig generation")
    parser.add_argument("--kconfig_model_file", required=True, type=existing_path)
    parser.add_argument("--kconfig_config_file", required=False, type=existing_path)
    parser.add_argument("--out_header_file", required=True, type=non_existing_path)
    parser.add_argument("--out_json_file", required=False, type=non_existing_path)
    parser.add_argument("--out_cmake_file", required=False, type=non_existing_path)
    arguments = parser.parse_args()
    config = KConfig(arguments.kconfig_model_file, arguments.kconfig_config_file).config

    HeaderWriter(arguments.out_header_file).write(config)
    if arguments.out_json_file:
        JsonWriter(arguments.out_json_file).write(config)
    if arguments.out_cmake_file:
        CMakeWriter(arguments.out_cmake_file).write(config)


if __name__ == "__main__":
    main()
