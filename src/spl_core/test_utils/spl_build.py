import json
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from py_app_dev.core.logging import time_it

from spl_core.common.command_line_executor import CommandLineExecutor


@dataclass
class ArchiveArtifact:
    archive_path: Path
    absolute_path: Path


class ArtifactsCollection:
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
    """Class for building an SPL repository."""

    def __init__(self, variant: str, build_kit: str, build_type: Optional[str] = None) -> None:
        """
        Initialize a SplBuild instance.

        Args:
            variant (str): The build variant.
            build_kit (str): The build kit.
            build_type (str, optional): The build type. Defaults to None.

        """
        self.variant = variant
        self.build_kit = build_kit
        self.build_type = build_type

    @property
    def build_dir(self) -> Path:
        """
        Get the build directory.

        Returns:
            Path: The build directory path.

        """
        if self.build_type:
            return Path(f"build/{self.variant}/{self.build_kit}/{self.build_type}")
        return Path(f"build/{self.variant}/{self.build_kit}")

    @time_it()
    def execute(self, target: str, additional_args: Optional[List[str]] = None) -> int:
        """
        Build the target

        Args:
            target (str): The build target.
            additional_args (List[str], optional): Additional arguments for building. Defaults to ["-build"].

        Returns:
            int: 0 in case of success.

        """
        if additional_args is None:
            additional_args = ["-build"]
        return_code = -1
        while True:
            cmd = [
                "build.bat",
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

    def create_artifacts_archive(self, expected_artifacts: List[Path]) -> Path:
        """
        Create a zip file containing the collected artifacts.

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
        Create a JSON file listing the collected artifacts.

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
