import os
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest
from utils import create_clean_test_dir

from spl_core.kconfig.kconfig import (
    CMakeWriter,
    ConfigElement,
    ConfigElementType,
    ConfigurationData,
    HeaderWriter,
    JsonWriter,
    KConfig,
    TriState,
    main,
)


@pytest.fixture
def configuration_data():
    return ConfigurationData(
        [
            ConfigElement(ConfigElementType.STRING, "NAME", "John Smith"),
            ConfigElement(ConfigElementType.BOOL, "STATUS_SET", TriState.Y),
            ConfigElement(ConfigElementType.BOOL, "STATUS_NOT_SET", TriState.N),
            ConfigElement(ConfigElementType.INT, "MY_INT", 13),
            ConfigElement(ConfigElementType.HEX, "MY_HEX", 0x10),
        ]
    )


def test_create_configuration_data(tmp_path: Path) -> None:
    feature_model_file = tmp_path / "my_file.txt"
    feature_model_file.write_text(
        """
    config NAME
        string "Description"
        default "John Smith"
    config STATUS
        bool "Description"
        default y
    config NOT_SET
        bool "Description"
        default n
    """
    )
    iut = KConfig(feature_model_file)
    assert iut.config.elements[0].type == ConfigElementType.STRING
    assert iut.config.elements[0].value == "John Smith"
    assert iut.config.elements[1].type == ConfigElementType.BOOL
    assert iut.config.elements[1].name == "STATUS"
    assert iut.config.elements[1].value == TriState.Y
    assert iut.config.elements[2].type == ConfigElementType.BOOL
    assert iut.config.elements[2].name == "NOT_SET"
    assert iut.config.elements[2].value == TriState.N


def test_create_configuration_data_with_variables(tmp_path: Path) -> None:
    feature_model_file = tmp_path / "my_file.txt"
    feature_model_file.write_text(
        """
    config NAME
        string "Description"
        default "John Smith"
    config REFERENCING
        string "Reference another KConfig value here"
        default "Variable: ${NAME}, environment variable: ${ENV:MY_ENV_VAR}"
    """
    )
    # define MY_ENV_VAR environment variable
    os.environ["MY_ENV_VAR"] = "MY_ENV_VAR_VALUE"
    iut = KConfig(feature_model_file)
    assert iut.config.elements[0].value == "John Smith"
    assert iut.config.elements[1].type == ConfigElementType.STRING
    assert iut.config.elements[1].value == "Variable: John Smith, environment variable: MY_ENV_VAR_VALUE"


def test_header_writer(tmp_path: Path, configuration_data: ConfigurationData) -> None:
    header_file = tmp_path / "my_file.h"
    writer = HeaderWriter(header_file)
    writer.write(configuration_data)
    assert header_file.read_text() == textwrap.dedent(
        """\
    /** @file */
    #ifndef __autoconf_h__
    #define __autoconf_h__

    /** NAME */
    #define CONFIG_NAME "John Smith"
    /** STATUS_SET */
    #define CONFIG_STATUS_SET 1
    /** MY_INT */
    #define CONFIG_MY_INT 13
    /** MY_HEX */
    #define CONFIG_MY_HEX 0x10

    #endif /* __autoconf_h__ */
    """
    )


def test_header_file_written_when_changed(tmp_path: Path) -> None:
    os.environ["HowDoYouLikeThis"] = "ThisIsCool"
    feature_model_file = tmp_path / "kconfig.txt"
    feature_model_file.write_text(
        """
        menu "First menu"
            config FIRST_BOOL
                bool "You can select FIRST_BOOL"
        endmenu
        """
    )

    user_config = tmp_path / "user.config"
    user_config.write_text(
        textwrap.dedent(
            """\
            CONFIG_FIRST_BOOL=y
        """
        )
    )
    header_file = tmp_path / "my_file.h"
    config = KConfig(feature_model_file, user_config).config

    writer = HeaderWriter(header_file)
    writer.write(config)

    assert header_file.exists()
    timestamp = header_file.stat().st_mtime
    writer.write(config)
    assert header_file.stat().st_mtime == timestamp, "the file shall not be written if content is not changed"
    header_file.write_text("Modified content")
    writer.write(config)
    assert header_file.read_text() != "Modified content", "the file should have been updated because the content changed"


def test_json_writer(configuration_data: ConfigurationData) -> None:
    writer = JsonWriter(Path("my_file.json"))
    assert writer.generate_content(configuration_data) == textwrap.dedent(
        """\
    {
        "features": {
            "NAME": "John Smith",
            "STATUS_SET": true,
            "STATUS_NOT_SET": false,
            "MY_INT": 13,
            "MY_HEX": 16
        }
    }"""
    )


def test_cmake_writer(configuration_data: ConfigurationData) -> None:
    writer = CMakeWriter(Path("my_file.cmake"))
    assert writer.generate_content(configuration_data) == textwrap.dedent(
        """\
        set(NAME "John Smith")
        set(STATUS_SET "True")
        set(STATUS_NOT_SET "False")
        set(MY_INT "13")
        set(MY_HEX "16")"""
    )


def test_boolean_without_description():
    """
    A configuration without description can not be selected by the user
    """
    out_dir = create_clean_test_dir()
    feature_model_file = out_dir.write_file(
        "kconfig.txt",
        """
    mainmenu "This is the main menu"
        menu "First menu"
            config FIRST_BOOL
                bool
            config FIRST_NAME
                string "You can select this"
            config SECOND_NAME
                string
        endmenu
    """,
    )
    user_config = out_dir.write_file(
        "user.config",
        textwrap.dedent(
            """
    CONFIG_FIRST_BOOL=y
    CONFIG_FIRST_NAME="Dude"
    CONFIG_SECOND_NAME="King"
    """
        ),
    )

    iut = KConfig(feature_model_file, user_config)
    assert iut.config.elements == [ConfigElement(ConfigElementType.STRING, "FIRST_NAME", "Dude")]


def test_boolean_with_description():
    """
    A configuration with description can be selected by the user
    """
    out_dir = create_clean_test_dir()
    feature_model_file = out_dir.write_file(
        "kconfig.txt",
        """
    mainmenu "This is the main menu"
        menu "First menu"
            config FIRST_BOOL
                bool "You can select this"
            config FIRST_NAME
                string "You can select this also"
        endmenu
    """,
    )
    user_config = out_dir.write_file(
        "user.config",
        textwrap.dedent(
            """
    CONFIG_FIRST_BOOL=y
    CONFIG_FIRST_NAME="Dude"
    """
        ),
    )

    iut = KConfig(feature_model_file, user_config)
    assert iut.config.elements == [
        ConfigElement(ConfigElementType.BOOL, "FIRST_BOOL", TriState.Y),
        ConfigElement(ConfigElementType.STRING, "FIRST_NAME", "Dude"),
    ]


def test_hex():
    """
    A configuration with description can be selected by the user
    """
    out_dir = create_clean_test_dir()
    feature_model_file = out_dir.write_file(
        "kconfig.txt",
        """
        menu "First menu"
            config MY_HEX
                hex
                default 0x00FF
                help
                    my hex value
        endmenu
    """,
    )

    iut = KConfig(feature_model_file)
    assert iut.config.elements == [ConfigElement(ConfigElementType.HEX, "MY_HEX", 0xFF)]


def test_define_boolean_choices():
    """
    Using a boolean choice will define a boolean for every value.
    Only the choices with a 'prompt' are selectable.
    There is a warning generated for choices without a 'prompt'.
    """
    out_dir = create_clean_test_dir()
    feature_model_file = out_dir.write_file(
        "kconfig.txt",
        """
    choice APP_VERSION
        prompt "application version"
        default APP_VERSION_1
        help
            Currently there are several application version supported.
            Select the one that matches your needs.

        config APP_VERSION_1
            bool
            prompt "app v1"
        config APP_VERSION_2
            bool
            prompt "app v2"
        # This is not selectable because it has no prompt
        config APP_VERSION_3
            bool
    endchoice
    """,
    )
    user_config = out_dir.write_file(
        "user.config",
        textwrap.dedent(
            """
    CONFIG_APP_VERSION="APP_VERSION_1"
    """
        ),
    )

    iut = KConfig(feature_model_file, user_config)
    assert iut.config.elements == [
        ConfigElement(ConfigElementType.BOOL, "APP_VERSION_1", TriState.Y),
        ConfigElement(ConfigElementType.BOOL, "APP_VERSION_2", TriState.N),
    ]


def test_define_string_choices():
    """
    A choice can only be of type bool or tristate.
    One can use string but a warning will be issued.
    """
    out_dir = create_clean_test_dir()
    feature_model_file = out_dir.write_file(
        "kconfig.txt",
        """
    choice APP_VERSION
        prompt "application version"
        default APP_VERSION_1
        help
            Currently there are several application version supported.
            Select the one that matches your needs.

        config APP_VERSION_1
            string
            prompt "app v1"
        config APP_VERSION_2
            string
            prompt "app v2"
    endchoice
    """,
    )
    user_config = out_dir.write_file(
        "user.config",
        textwrap.dedent(
            """
    CONFIG_APP_VERSION="APP_VERSION_1"
    CONFIG_APP_VERSION_1="VERSION_NEW"
    """
        ),
    )

    iut = KConfig(feature_model_file, user_config)
    assert iut.config.elements == [
        ConfigElement(ConfigElementType.STRING, "APP_VERSION_1", "VERSION_NEW"),
        ConfigElement(ConfigElementType.STRING, "APP_VERSION_2", ""),
    ]


def test_define_tristate_choices():
    """
    For KConfig, `bool` and `tristate` types are represented as JSON Booleans,
    the third `tristate` state is not supported.
    """
    out_dir = create_clean_test_dir()
    feature_model_file = out_dir.write_file(
        "kconfig.txt",
        """
    choice APP_VERSION
        prompt "application version"
        default APP_VERSION_1
        help
            Currently there are several application version supported.
            Select the one that matches your needs.

        config APP_VERSION_1
            tristate
            prompt "app v1"
        config APP_VERSION_2
            tristate
            prompt "app v2"
    endchoice
    """,
    )
    user_config = out_dir.write_file(
        "user.config",
        textwrap.dedent(
            """
    CONFIG_APP_VERSION="APP_VERSION_1"
    """
        ),
    )

    iut = KConfig(feature_model_file, user_config)
    assert iut.config.elements == [
        ConfigElement(ConfigElementType.BOOL, "APP_VERSION_1", TriState.Y),
        ConfigElement(ConfigElementType.BOOL, "APP_VERSION_2", TriState.N),
    ]


def test_config_including_other_config():
    """
    Including other configuration files with 'source' works only as relative paths to the main file folder :(
    See how 'common.txt' must include 'new.txt' with its relative path to the main file.
    One can also use:
        * 'rsource' - for paths relative to the current file
        * 'osource' - for files that might not exist
    """
    out_dir = create_clean_test_dir()
    feature_model_file = out_dir.write_file(
        "kconfig.txt",
        """
    menu "First menu"
        config FIRST_BOOL
            bool "You can select FIRST_BOOL"
        config FIRST_NAME
            string "You can select FIRST_NAME"
    endmenu
    source "common/common.txt"
    """,
    )
    out_dir.write_file(
        "common/common.txt",
        """
    config COMMON_BOOL
        bool "You can select COMMON_BOOL"
        default n
    source "new/new.txt"
    """,
    )
    out_dir.write_file(
        "new/new.txt",
        """
    config NEW_BOOL
        bool "You can select NEW_BOOL"
        default n
    """,
    )
    user_config = out_dir.write_file(
        "user.config",
        textwrap.dedent(
            """
    CONFIG_FIRST_BOOL=y
    CONFIG_FIRST_NAME="Dude"
    CONFIG_COMMON_BOOL=y
    CONFIG_NEW_BOOL=y
    """
        ),
    )
    iut = KConfig(feature_model_file, user_config)
    assert iut.config.elements == [
        ConfigElement(ConfigElementType.BOOL, "FIRST_BOOL", TriState.Y),
        ConfigElement(ConfigElementType.STRING, "FIRST_NAME", "Dude"),
        ConfigElement(ConfigElementType.BOOL, "COMMON_BOOL", TriState.Y),
        ConfigElement(ConfigElementType.BOOL, "NEW_BOOL", TriState.Y),
    ]


def test_config_including_other_configs_based_on_env_vars():
    """
    One can refer to environment variables when including other files
    """
    out_dir = create_clean_test_dir()
    feature_model_file = out_dir.write_file(
        "kconfig.txt",
        """
    menu "First menu"
        config FIRST_BOOL
            bool "You can select FIRST_BOOL"
        config FIRST_NAME
            string "You can select FIRST_NAME"
    endmenu
    source "$(COMMON_PATH)/common.txt"
    """,
    )
    out_dir.write_file(
        "common/common.txt",
        """
    config COMMON_BOOL
        bool "You can select COMMON_BOOL"
        default n
    """,
    )
    user_config = out_dir.write_file(
        "user.config",
        textwrap.dedent(
            """
    CONFIG_FIRST_BOOL=y
    CONFIG_FIRST_NAME="Dude"
    CONFIG_COMMON_BOOL=y
    """
        ),
    )
    os.environ["COMMON_PATH"] = "common"
    iut = KConfig(feature_model_file, user_config)
    assert iut.config.elements == [
        ConfigElement(ConfigElementType.BOOL, "FIRST_BOOL", TriState.Y),
        ConfigElement(ConfigElementType.STRING, "FIRST_NAME", "Dude"),
        ConfigElement(ConfigElementType.BOOL, "COMMON_BOOL", TriState.Y),
    ]


def test_main():
    """
    KConfigLib can generate the configuration as C-header file (like autoconf.h)
    """
    out_dir = create_clean_test_dir()
    feature_model_file = out_dir.write_file(
        "kconfig.txt",
        """
            menu "First menu"
                config FIRST_BOOL
                    bool "You can select FIRST_BOOL"
                config FIRST_NAME
                    string "You can select FIRST_NAME"
            endmenu
            """,
    )

    user_config = out_dir.write_file(
        "user.config",
        textwrap.dedent(
            """
                CONFIG_FIRST_BOOL=y
                CONFIG_FIRST_NAME="Dude"
                """
        ),
    )
    header_file = out_dir.joinpath("gen/header.h")
    json_file = out_dir.joinpath("gen/features.json")
    cmake_file = out_dir.joinpath("gen/features.cmake")

    with patch(
        "sys.argv",
        [
            "kconfig",
            "--kconfig_model_file",
            f"{feature_model_file}",
            "--kconfig_config_file",
            f"{user_config}",
            "--out_header_file",
            f"{header_file}",
            "--out_json_file",
            f"{json_file}",
            "--out_cmake_file",
            f"{cmake_file}",
        ],
    ):
        main()
    assert json_file.exists()
    assert cmake_file.exists()
    assert header_file.exists()
