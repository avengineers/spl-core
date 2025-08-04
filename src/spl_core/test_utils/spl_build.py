import json
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, ClassVar, List, Optional

from py_app_dev.core.logging import time_it

from spl_core.common.command_line_executor import CommandLineExecutor


@dataclass
class ArchiveArtifact:
    """Obsolete class for storing archive artifacts."""

    archive_path: Path
    absolute_path: Path


class ArtifactsCollection:
    """Obsolete class for collecting artifacts to be archived."""

    def __init__(self, artifacts: List[Path], build_dir: Path):
        self.archive_artifacts: List[ArchiveArtifact] = []
        for artifact in artifacts:
            if artifact.is_absolute():
                artifact_path = artifact
            else:
                artifact_path = Path.joinpath(build_dir.absolute(), artifact)
            if artifact_path.is_dir():
                for artifact in artifact_path.glob("**/*"):
                    if artifact.is_file():
                        if artifact_path.is_relative_to(build_dir.absolute()):
                            self.archive_artifacts.append(ArchiveArtifact(archive_path=artifact.relative_to(build_dir.absolute()), absolute_path=artifact.absolute()))
                        else:
                            self.archive_artifacts.append(ArchiveArtifact(archive_path=Path(artifact.name), absolute_path=artifact.absolute()))
            else:
                if artifact_path.is_relative_to(build_dir.absolute()):
                    self.archive_artifacts.append(ArchiveArtifact(archive_path=artifact_path.relative_to(build_dir.absolute()), absolute_path=artifact_path.absolute()))
                else:
                    self.archive_artifacts.append(ArchiveArtifact(archive_path=Path(artifact_path.name), absolute_path=artifact_path.absolute()))


class SplBuild:
    """
    Class for building an SPL repository.

    Relies on build.bat in the root of the SPL repository.
    """

    @dataclass
    class BuildArtifacts:
        artifacts: list[str]
        # callable to resolve the path to the component artifacts specific to the build target
        path_resolver: Callable[[Path, str], Path]

    TARGET_VARIANT_BUILD_ARTIFACTS: ClassVar[dict[str, list[str]]] = {"prod/all": ["compile_commands.json"]}

    TARGET_COMPONENT_BUILD_ARTIFACTS: ClassVar[dict[str, "SplBuild.BuildArtifacts"]] = {
        "test/unittests": BuildArtifacts(
            [
                "coverage.json",
                "junit.xml",
                "reports/coverage/index.html",
            ],
            lambda build_dir, component_name: build_dir / component_name,
        ),
        "test/reports": BuildArtifacts(
            [
                "coverage.html",
                "coverage/index.html",
                "doxygen/html/index.html",
                "unit_test_results.html",
                "unit_test_spec.html",
            ],
            lambda build_dir, component_name: build_dir / "reports" / "html" / build_dir / component_name / "reports",
        ),
    }

    def __init__(self, variant: str, build_kit: str, build_type: Optional[str] = None, target: Optional[str] = None) -> None:
        self.variant = variant
        self.build_kit = build_kit
        self.build_type = build_type
        self.target = target

    @property
    def build_dir(self) -> Path:
        """
        Output directory of all build artifacts.
        """
        if self.build_type:
            return Path(f"build/{self.variant}/{self.build_kit}/{self.build_type}")
        return Path(f"build/{self.variant}/{self.build_kit}")

    @time_it()
    def execute(self, target: Optional[str] = None, additional_args: Optional[List[str]] = None) -> int:
        """
        Execute an SPL build (of a given target).

        Args:
            target: The target to build, optional, defaults to value given in the constructor.
            additional_args: Additional arguments to pass to the build command.

        Returns:
            int: 0 in case of success.

        """
        if target is None:
            target = self.target if self.target else "all"
        return_code = -1
        while True:
            cmd = [
                "build.bat",
                "-build",
                "-buildKit",
                self.build_kit,
                "-variants",
                self.variant,
                "-target",
                target,
                "-reconfigure",
            ]
            if self.build_type:
                cmd.extend(["-buildType", self.build_type])
            if additional_args:
                cmd.extend(additional_args)
            result = CommandLineExecutor().execute(cmd)
            return_code = result.returncode
            if result.returncode:
                if result.stdout:
                    if any(error in str(result.stdout) for error in ["No valid floating license", "No valid license", "GHS_LMHOST = N/A"]):
                        print("Probably a license issue, retrying ...")
                        time.sleep(10)
                    else:
                        break
                else:
                    break
            else:
                break
        return return_code

    def get_component_artifacts(self, component_name: str) -> list[Path]:
        if not self.target:
            return []
        target_data = self.TARGET_COMPONENT_BUILD_ARTIFACTS.get(self.build_kit + "/" + self.target)
        if not target_data:
            return []

        return [target_data.path_resolver(self.build_dir, component_name) / artifact for artifact in target_data.artifacts]

    def get_components_artifacts(self, component_names: list[str]) -> list[Path]:
        artifacts = []
        for component_name in component_names:
            artifacts.extend(self.get_component_artifacts(component_name))
        return artifacts

    def get_variant_artifacts(self) -> list[Path]:
        if not self.target:
            return []
        target_data = self.TARGET_VARIANT_BUILD_ARTIFACTS.get(self.build_kit + "/" + self.target)
        if not target_data:
            return []
        return [self.build_dir / artifact for artifact in target_data]

    def create_artifacts_archive(self, expected_artifacts: List[Path]) -> Path:
        """
        Obsolete method for creating an archive of artifacts.

        Args:
            expected_artifacts: List of Path of artifacts which should be archived

        Returns:
            Path: The path to the created zip file.

        Raises:
            Exception: If there is an error creating the zip file.

        """
        zip_path = self.build_dir / "artifacts.zip"

        # Delete the file if it already exists
        if zip_path.exists():
            zip_path.unlink()

        try:
            with zipfile.ZipFile(zip_path, "w") as zip_file:
                artifacts_collection = ArtifactsCollection(artifacts=expected_artifacts, build_dir=self.build_dir)
                for artifact in artifacts_collection.archive_artifacts:
                    zip_file.write(artifact.absolute_path, arcname=artifact.archive_path)
            print(f"Zip file created at: {zip_path}")
            return zip_path
        except Exception as e:
            print(f"Error creating artifacts zip file: {e}")
            raise e

    def create_artifacts_json(self, expected_artifacts: List[Path]) -> Path:
        """
        Obsolete method to create a JSON file listing the collected artifacts.

        Returns:
            Path: The path to the created JSON file.

        Raises:
            Exception: If there is an error creating the JSON file.

        """
        artifacts_collection = ArtifactsCollection(artifacts=expected_artifacts, build_dir=self.build_dir)
        json_content = {
            "variant": self.variant,
            "build_kit": self.build_kit,
            "artifacts": [str(artifact.archive_path.as_posix()) for artifact in artifacts_collection.archive_artifacts],
        }
        if self.build_type:
            json_content["build_type"] = self.build_type
        json_path = self.build_dir / "artifacts.json"

        json_path.write_text(json.dumps(json_content, indent=4))

        return json_path
