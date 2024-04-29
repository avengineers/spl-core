import shutil
from pathlib import Path
from typing import List, Optional, Union

from py_app_dev.core.exceptions import UserNotificationException
from py_app_dev.core.logging import logger


class ProjectBuilder:
    def __init__(self, project_dir: Path, input_dir: Optional[Path] = None) -> None:
        self.project_dir = project_dir
        self.input_dir = input_dir if input_dir else Path(__file__).parent.joinpath("templates")

        self.dirs: List[Path] = []
        self.check_target_directory_flag = True

    def with_disable_target_directory_check(self) -> "ProjectBuilder":
        self.check_target_directory_flag = False
        return self

    def with_dir(self, dir: Union[Path, str]) -> "ProjectBuilder":
        self.dirs.append(self.resolve_file_path(dir))
        return self

    def resolve_file_paths(self, files: List[Path | str]) -> List[Path]:
        return [self.resolve_file_path(file) for file in files]

    def resolve_file_path(self, file: Union[Path, str]) -> Path:
        return self.input_dir.joinpath(file) if isinstance(file, str) else file

    @staticmethod
    def _check_target_directory(project_dir: Path) -> None:
        if project_dir.is_dir() and any(project_dir.iterdir()):
            raise UserNotificationException(f"Project directory '{project_dir}' is not empty. Use --force to override.")

    def build(self) -> None:
        if self.check_target_directory_flag:
            self._check_target_directory(self.project_dir)
        for dir in self.dirs:
            shutil.copytree(dir, self.project_dir, dirs_exist_ok=True)


class KickstartProject:
    """Kickstart a new project in the given directory.

    Args:
        project_dir (Path): The directory where the project should be created.
        force (bool, optional): If True, the project directory will be overridden if it is not empty. Defaults to False.
        no_application (bool, optional): If True, the project will not contain variants and components.
    """

    def __init__(self, project_dir: Path, force: bool = False, no_application: bool = False) -> None:
        self.logger = logger.bind()
        self.project_dir = project_dir
        self.force = force
        self.no_application = no_application

    def run(self) -> None:
        self.logger.info(f"Kickstart new project in '{self.project_dir.absolute().as_posix()}'")
        project_builder = ProjectBuilder(self.project_dir)
        if self.force:
            project_builder.with_disable_target_directory_check()
        project_builder.with_dir("project")
        if not self.no_application:
            project_builder.with_dir("application")
        project_builder.build()
