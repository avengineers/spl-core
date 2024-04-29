import dataclasses
import os
import random
import shutil
import string
import subprocess
from contextlib import ContextDecorator
from pathlib import Path
from time import perf_counter
from typing import Collection, Dict, List, Optional

from spl_core.common.command_line_executor import CommandLineExecutor
from spl_core.kickstart.create import KickstartProject
from spl_core.project_creator.creator import Creator
from spl_core.project_creator.variant import Variant
from spl_core.project_creator.workspace_artifacts import WorkspaceArtifacts


def this_repository_root_dir() -> Path:
    return Path(__file__).parent.parent.absolute()


class ExecutionTime(ContextDecorator):
    def __init__(self, message: Optional[str] = None):
        self.name = message

    def __enter__(self):
        self.time = perf_counter()
        print(f"[START] {self.name}")
        return self

    def __exit__(self, type, value, traceback):
        self.time = perf_counter() - self.time
        print(f"[END] {self.name} execution took {self.time:.3f}s")


@dataclasses.dataclass
class TestDir:
    __test__ = False
    path: Path

    def write_file(self, name: str, content: Optional[str] = None) -> Path:
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


def create_cli_for_spl_project(project_dir: Path) -> CommandLineExecutor:
    """Creates a CommandLineExecutor for the given SPL project directory.

    The SPL-Core repository is used as a Python dependency and forces the usage of the project directory virtual environment.
    """
    env = os.environ.copy()
    env["SPLCORE_PATH"] = this_repository_root_dir().as_posix()
    # Force the usage of the project directory virtual environment
    env["PIPENV_IGNORE_VIRTUALENVS"] = "1"
    # Make sure the project directory virtual environment is used
    env["PATH"] = f"{project_dir.joinpath('.venv/Scripts').as_posix()}{os.pathsep}{env['PATH']}"
    return CommandLineExecutor(cwd=project_dir, env=env)


def setup_new_spl_project(project_dir: Path) -> Path:
    """Creates a new SPL project in the given directory and returns the path to the project.
    The current SPL-Core repository is installed as a Python dependency."""
    KickstartProject(project_dir).run()

    # Replace the SPL-Core dependency in the Pipfile
    pipfile = project_dir.joinpath("pipfile")
    new_dependency = f'spl-core = {{path = "{this_repository_root_dir().as_posix()}"}}'
    pipfile.write_text(pipfile.read_text().replace('spl-core = "*"', new_dependency))

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

    def _collect_files_status(self) -> Dict[Path, int]:
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

    DEFAULT_VARIANT = Variant("Variant1")

    def __init__(self, out_dir_name: str, use_example_project: bool = False):
        if use_example_project:
            self.workspace_dir = setup_new_spl_project(create_clean_test_dir(out_dir_name).path)
        else:
            self.workspace_dir = self.create_default(out_dir_name)
        self.workspace_artifacts = WorkspaceArtifacts(self.workspace_dir)
        self.directory_tracker = DirectoryTracker(self.workspace_dir)
        self.cli = create_cli_for_spl_project(self.workspace_dir)

    @staticmethod
    def create_default(out_dir_name: str) -> Path:
        out_dir = create_clean_test_dir(out_dir_name)
        project_name = "MyProject"
        variants = [IntegrationTestsSplProject.DEFAULT_VARIANT, Variant("Variant1")]
        return IntegrationTestsSplProject.create(out_dir, project_name, variants)

    @staticmethod
    def create(out_dir, project_name, variants):
        creator = Creator(project_name, out_dir.path)
        return creator.materialize(variants)

    def bootstrap(self):
        return self.cli.execute(f"{self.workspace_artifacts.build_script}" f" -install")

    def link(self, variant: Variant = DEFAULT_VARIANT) -> subprocess.CompletedProcess[str]:
        return self.cli.execute(f"{self.workspace_artifacts.build_script}" f" -build -target link -variants {variant}")

    def selftests(self) -> subprocess.CompletedProcess[str]:
        return self.cli.execute(f"{self.workspace_artifacts.build_script}" f" -build -target selftests")

    def get_component_file(self, component_name: str, component_file: str) -> Path:
        return self.workspace_artifacts.get_component_path(component_name).joinpath(component_file)

    def take_files_snapshot(self):
        self.directory_tracker.reset_status()

    def get_workspace_files_status(self) -> DirectoryStatus:
        return self.directory_tracker.get_status()


class SplKickstartProjectIntegrationTestBase:
    project_dir: Path
    cli: CommandLineExecutor
    component_paths: List[str]

    @classmethod
    def setup_class(cls):
        # create new project
        cls.project_dir = setup_new_spl_project(create_clean_test_dir(cls.__name__).path)
        cls.component_paths = ["src/main", "src/greeter"]
        cls.cli = create_cli_for_spl_project(cls.project_dir)
        # Bootstrap the project
        result = cls.cli.execute(["build.bat", "-install"])
        assert result.returncode == 0, "Execution shall not fail."
