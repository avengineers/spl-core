import dataclasses
import os
import random
import re
import shutil
import string
import subprocess
from collections.abc import Collection
from contextlib import ContextDecorator
from pathlib import Path
from time import perf_counter
from typing import Any

from py_app_dev.core.subprocess import SubprocessExecutor

from spl_core.kickstart.create import KickstartProject, ProjectBuilder


def this_repository_root_dir() -> Path:
    return Path(__file__).parent.parent.absolute()


class ExecutionTime(ContextDecorator):
    def __init__(self, message: str | None = None):
        self.name = message

    def __enter__(self):
        self.time = perf_counter()
        print(f"[START] {self.name}")
        return self

    def __exit__(self, type, value, traceback):
        self.time = perf_counter() - self.time
        print(f"[END] {self.name} execution took {self.time:.3f}s")


@dataclasses.dataclass
class Variant:
    name: str

    @classmethod
    def from_string(cls, variant: str) -> "Variant":
        return cls(variant)

    def __str__(self) -> str:
        return self.to_string()

    def to_string(self) -> str:
        return self.name

    def __lt__(self, other: "Variant") -> bool:
        return f"{self}" < f"{other}"

    def __hash__(self) -> int:
        return hash(f"{self}")


class WorkspaceArtifacts:
    def __init__(self, project_root_dir: Path):
        self.project_root_dir = project_root_dir
        self.variants_dir = self.project_root_dir.joinpath("variants")
        self.src_dir = self.project_root_dir.joinpath("src")
        self.test_dir = self.project_root_dir.joinpath("test")

    @property
    def build_script(self) -> Path:
        return self.project_root_dir.joinpath("build.bat")

    @property
    def kconfig_model_file(self) -> Path:
        return self.project_root_dir.joinpath("KConfig")

    def get_build_dir(self, variant: Variant | str, build_kit: str, build_type: str | None = "Debug") -> Path:
        if build_type:
            return self.project_root_dir.joinpath(f"build/{variant}/{build_kit}/{build_type}")
        return self.project_root_dir.joinpath(f"build/{variant}/{build_kit}")

    def get_variant_dir(self, variant: Variant | str) -> Path:
        return self.variants_dir.joinpath(f"{variant}")

    def get_kconfig_config_file(self, variant: Variant | str) -> Path:
        return self.get_variant_dir(variant).joinpath("config.txt")


@dataclasses.dataclass
class TestDir:
    __test__ = False
    path: Path

    def write_file(self, name: str, content: str | None = None) -> Path:
        file = self.path.joinpath(name)
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content if content else self.gen_random_text(10))
        return file

    def delete_file(self, name: str) -> None:
        self.path.joinpath(name).unlink()

    @staticmethod
    def gen_random_text(size: int) -> str:
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=size))  # noqa: S311

    def joinpath(self, path: str) -> Path:
        return self.path.joinpath(path)

    def __str__(self):
        return f"{self.path}"


def create_clean_test_dir(name: str = "tmp_test") -> TestDir:
    out_dir = this_repository_root_dir().joinpath("out")
    test_dir = out_dir.joinpath(name).absolute()
    if test_dir.exists():
        # rmtree throws an exception if any of the files to be deleted is read-only
        if os.name == "nt":
            rm_dir_cmd = f"cmd /c rmdir /S /Q {test_dir}"
            print(f"Execute: {rm_dir_cmd}")
            subprocess.call(rm_dir_cmd)
        else:
            shutil.rmtree(test_dir)
    test_dir.mkdir(parents=True, exist_ok=True)
    print(f"New clean test directory created: {test_dir}")
    return TestDir(test_dir)


def setup_new_spl_project(project_dir: Path, no_application: bool = False) -> Path:
    """Creates a new SPL project in the given directory and returns the path to the project.
    The current SPL-Core repository is installed as a Python dependency."""
    # force=True: on Windows, locked .venv files may prevent full directory deletion in
    # create_clean_test_dir, leaving stale content. force=True skips the non-empty check
    # and overwrites with copytree, so the kickstart always succeeds.
    KickstartProject(project_dir=project_dir, force=True, no_application=no_application).run()

    # Replace the SPL-Core dependency in the pyproject.toml
    pyproject_toml = project_dir.joinpath("pyproject.toml")
    # "spl-core @ file:///C:/D/git/_oss_/spl-core",
    new_dependency = f"spl-core @ file:///{this_repository_root_dir().as_posix()}"
    original_content = pyproject_toml.read_text()
    # Match "spl-core" followed by any version specifier, with or without parentheses.
    # Examples: "spl-core (>=7,<8)", "spl-core>=8,<9", "spl-core ^8.0"
    updated_content = re.sub(r"spl-core\s*\(?[><=!~^,.\d\s]+\)?", new_dependency, original_content)
    assert original_content != updated_content, f"Failed to replace spl-core dependency in {pyproject_toml}. Check if the dependency format has changed."
    pyproject_toml.write_text(updated_content)

    return project_dir


@dataclasses.dataclass
class DirectoryStatus:
    changed_files: Collection[Path]
    deleted_files: Collection[Path]
    new_files: Collection[Path]
    unchanged_files: Collection[Path]

    @property
    def changed_files_names(self) -> Collection[str]:
        return [file.name for file in self.changed_files]


class DirectoryTracker:
    def __init__(self, target_dir: Path):
        self.target_dir = target_dir
        self.start_status = self._collect_files_status()

    def reset_status(self):
        self.start_status = self._collect_files_status()

    def _collect_files_status(self) -> dict[Path, int]:
        """
        Store a set with all files and their timestamps
        """
        status = {}
        for file in self.target_dir.glob("**/*"):
            if file.is_file():
                status[file] = os.stat(file).st_mtime_ns
        return status

    def get_status(self) -> DirectoryStatus:
        current_status = self._collect_files_status()
        common_files = current_status.keys() & self.start_status.keys()
        deleted_files = self.start_status.keys() - current_status.keys()
        new_files = current_status.keys() - self.start_status.keys()
        changed_files = []
        unchanged_files = []
        for file in common_files:
            if current_status[file] != self.start_status[file]:
                changed_files.append(file)
            else:
                unchanged_files.append(file)
        status = DirectoryStatus(changed_files, deleted_files, new_files, unchanged_files)
        return status


class IntegrationTestsSplProject:
    """
    Creates a new SPL project and provides methods to interact with it.

    The workspace is created in a new directory and the SPL-Core repository is used as a Python dependency.
    One can either create a new project or use an example project.
    """

    def __init__(self, project_dir: Path, components: list[str]):
        self.project_dir = project_dir
        self.components = components
        self.artifacts = WorkspaceArtifacts(self.project_dir)
        self.directory_tracker = DirectoryTracker(self.project_dir)
        self.env = os.environ.copy()
        self.env["SPLCORE_PATH"] = this_repository_root_dir().joinpath("src/spl_core").as_posix()
        # Force the usage of the project directory virtual environment
        self.env["PIPENV_IGNORE_VIRTUALENVS"] = "1"
        # Prevent Poetry from detecting and reusing the parent project's venv
        self.env.pop("VIRTUAL_ENV", None)
        # Make sure the project directory virtual environment is used
        self.env["PATH"] = f"{project_dir.joinpath('.venv/Scripts').as_posix()}{os.pathsep}{self.env['PATH']}"

    def bootstrap(self) -> subprocess.CompletedProcess[Any] | None:
        return SubprocessExecutor(command=f"{self.artifacts.build_script} -install", env=self.env, cwd=self.project_dir).execute(handle_errors=False)

    def build(self, variant: str | Variant, target: str) -> subprocess.CompletedProcess[Any] | None:
        return SubprocessExecutor(command=f"{self.artifacts.build_script} -build -target {target} -variants {variant}", env=self.env, cwd=self.project_dir).execute(handle_errors=False)

    def selftests(self) -> subprocess.CompletedProcess[Any] | None:
        return SubprocessExecutor(command=f"{self.artifacts.build_script} -build -target selftests", env=self.env, cwd=self.project_dir).execute(handle_errors=False)

    def take_files_snapshot(self):
        self.directory_tracker.reset_status()

    def get_workspace_files_status(self) -> DirectoryStatus:
        return self.directory_tracker.get_status()


class SplProjectIntegrationTestBase:
    """Creates a new SPL project."""

    spl_project: IntegrationTestsSplProject

    @classmethod
    def setup_class(cls):
        cls.spl_project = cls.create_new_spl_project(cls.__name__)
        result = cls.spl_project.bootstrap()
        assert result is not None and result.returncode == 0, "Bootstrap the project shall not fail."

    @staticmethod
    def create_new_spl_project(out_dir_name: str) -> IntegrationTestsSplProject:
        project_dir = setup_new_spl_project(create_clean_test_dir(out_dir_name).path, no_application=True)
        ProjectBuilder(project_dir).with_disable_target_directory_check().with_dir(this_repository_root_dir().joinpath("tests/data/application")).build()
        return IntegrationTestsSplProject(project_dir, ["src/main", "src/greeter"])


class SplKickstartProjectIntegrationTestBase(SplProjectIntegrationTestBase):
    """Creates a new SPL project based on the Kickstart example project."""

    @staticmethod
    def create_new_spl_project(out_dir_name: str) -> IntegrationTestsSplProject:
        return IntegrationTestsSplProject(setup_new_spl_project(create_clean_test_dir(out_dir_name).path), ["src/main", "src/greeter"])
