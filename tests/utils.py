import dataclasses
import os
import random
import shutil
import string
import subprocess
from contextlib import ContextDecorator
from pathlib import Path
from time import perf_counter
from typing import Collection, Dict, Optional

from spl_core.common.cmake import CMake
from spl_core.project_creator.creator import Creator
from spl_core.project_creator.variant import Variant
from spl_core.project_creator.workspace_artifacts import WorkspaceArtifacts


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


class TestUtils:
    __test__ = False
    DEFAULT_TEST_DIR = "tmp_test"

    @staticmethod
    def create_clean_test_dir(name: Optional[str] = None) -> TestDir:
        out_dir = TestUtils.this_repository_root_dir().joinpath("out")
        test_dir = out_dir.joinpath(name if name else TestUtils.DEFAULT_TEST_DIR).absolute()
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

    @staticmethod
    def this_repository_root_dir() -> Path:
        return Path(__file__).parent.parent.absolute()

    @staticmethod
    def force_spl_core_usage_to_this_repo():
        os.environ["SPLCORE_PATH"] = TestUtils.this_repository_root_dir().as_posix()


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


class TestWorkspace:
    __test__ = False
    DEFAULT_VARIANT = Variant("Flv1", "Sys1")

    def __init__(self, out_dir_name: str):
        self.workspace_dir = self.create_default(out_dir_name)
        self.workspace_artifacts = WorkspaceArtifacts(self.workspace_dir)
        self.directory_tracker = DirectoryTracker(self.workspace_dir)
        self.use_local_spl_core = True

    @staticmethod
    def create_default(out_dir_name: str) -> Path:
        out_dir = TestUtils.create_clean_test_dir(out_dir_name)
        project_name = "MyProject"
        variants = [TestWorkspace.DEFAULT_VARIANT, Variant("Flv1", "Sys2")]
        return TestWorkspace.create(out_dir, project_name, variants)

    @staticmethod
    def create(out_dir, project_name, variants):
        creator = Creator(project_name, out_dir.path)
        return creator.materialize(variants)

    def install_mandatory(self):
        pass

    def link(self, variant: Variant = DEFAULT_VARIANT) -> subprocess.CompletedProcess[bytes]:
        return self.execute_command(f"{self.workspace_artifacts.build_script}" f" -target link -variants {variant}")

    def selftests(self) -> subprocess.CompletedProcess[bytes]:
        return self.execute_command(f"{self.workspace_artifacts.build_script}" f" -target selftests")

    def run_cmake_configure(self, build_kit: str = "prod", variant: Variant = DEFAULT_VARIANT) -> subprocess.CompletedProcess[bytes]:
        if self.use_local_spl_core:
            TestUtils.force_spl_core_usage_to_this_repo()
        return CMake(self.workspace_artifacts).configure(variant=variant, build_kit=build_kit)

    def run_cmake_build(
        self,
        target: str = "all",
        build_kit: str = "prod",
        variant: Variant = DEFAULT_VARIANT,
    ) -> subprocess.CompletedProcess[bytes]:
        if self.use_local_spl_core:
            TestUtils.force_spl_core_usage_to_this_repo()
        return CMake(self.workspace_artifacts).build(variant=variant, target=target, build_kit=build_kit)

    def execute_command(self, command: str) -> subprocess.CompletedProcess[bytes]:
        if self.use_local_spl_core:
            TestUtils.force_spl_core_usage_to_this_repo()
        return subprocess.run(command.split())

    def get_component_file(self, component_name: str, component_file: str) -> Path:
        return self.workspace_artifacts.get_component_path(component_name).joinpath(component_file)

    def take_files_snapshot(self):
        self.directory_tracker.reset_status()

    def get_workspace_files_status(self) -> DirectoryStatus:
        return self.directory_tracker.get_status()
