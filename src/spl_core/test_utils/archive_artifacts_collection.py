import json
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


class ArchiveArtifactsCollection:
    """
    Collection of artifacts to be archived.
    This class collects artifacts from a list of paths, handling both individual files and directories.
    It supports absolute paths and ensures that the paths are relative to the build directory when archived.
    """

    @dataclass
    class ArchiveArtifact:
        """
        Represents a single artifact to be archived.
        This class holds the archive path (relative to the build directory) and the absolute path of the artifact.
        It is used to ensure that artifacts are correctly archived with their intended paths.
        """

        archive_path: Path
        absolute_path: Path

    def __init__(self, artifacts: List[Path], build_dir: Path):
        self.build_dir = build_dir
        self.archive_artifacts: List[ArchiveArtifactsCollection.ArchiveArtifact] = []
        for artifact in artifacts:
            # Convert all artifacts to absolute paths first
            artifact_path = artifact.resolve() if not artifact.is_absolute() else artifact

            # Handle directories by recursively adding all files within them
            if artifact_path.is_dir():
                for file_artifact in artifact_path.glob("**/*"):
                    if file_artifact.is_file():
                        # Calculate the relative path from build_dir for the archive
                        if file_artifact.is_relative_to(build_dir.absolute()):
                            archive_path = file_artifact.relative_to(build_dir.absolute())
                        else:
                            # If not relative to build_dir, just use the filename
                            archive_path = Path(file_artifact.name)

                        self.archive_artifacts.append(self.ArchiveArtifact(archive_path=archive_path, absolute_path=file_artifact))
            else:
                # Handle individual files
                # Calculate the relative path from build_dir for the archive
                if artifact_path.is_relative_to(build_dir.absolute()):
                    archive_path = artifact_path.relative_to(build_dir.absolute())
                else:
                    # If not relative to build_dir, just use the filename
                    archive_path = Path(artifact_path.name)

                self.archive_artifacts.append(self.ArchiveArtifact(archive_path=archive_path, absolute_path=artifact_path))

    def create_archive(self, zip_filename: Optional[str] = None) -> Path:
        """
        Create a zip file containing the collected artifacts.
        Args:
            zip_filename: Optional custom name for the zip file (without extension).
                         If None, defaults to "artifacts.zip"
        Returns:
            Path: The path to the created zip file.
        Raises:
            Exception: If there is an error creating the zip file.
        """
        if zip_filename is None:
            zip_path = self.build_dir / "artifacts.zip"
        else:
            # Ensure the filename has .zip extension
            if not zip_filename.endswith(".zip"):
                zip_filename += ".zip"
            zip_path = self.build_dir / zip_filename

        # Delete the file if it already exists
        if zip_path.exists():
            zip_path.unlink()

        try:
            with zipfile.ZipFile(zip_path, "w") as zip_file:
                for artifact in self.archive_artifacts:
                    zip_file.write(artifact.absolute_path, arcname=artifact.archive_path)
            print(f"Zip file created at: {zip_path}")
            return zip_path
        except Exception as e:
            print(f"Error creating artifacts zip file: {e}")
            raise e

    def create_json(self, json_filename: Optional[str] = None) -> Path:
        """
        Create a JSON file containing the collected artifacts.
        Args:
            json_filename: Optional custom name for the JSON file (without extension).
                           If None, defaults to "artifacts.json"
        Returns:
            Path: The path to the created JSON file.
        Raises:
            Exception: If there is an error creating the JSON file.
        """
        if json_filename is None:
            json_path = self.build_dir / "artifacts.json"
        else:
            # Ensure the filename has .json extension
            if not json_filename.endswith(".json"):
                json_filename += ".json"
            json_path = self.build_dir / json_filename

        # Delete the file if it already exists
        if json_path.exists():
            json_path.unlink()

        try:
            json_content = {
                "artifacts": [str(artifact.archive_path.as_posix()) for artifact in self.archive_artifacts],
            }
            json_path.write_text(json.dumps(json_content, indent=4))
            return json_path
        except Exception as e:
            print(f"Error creating artifacts JSON file: {e}")
            raise e
