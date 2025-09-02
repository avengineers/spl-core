import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import py7zr


class ArtifactsArchive:
    """
    This class represents a single archive containing artifacts.
    It collects artifacts to be packed and archived.

    Currently supports 7z and Artifactory.
    """

    @dataclass
    class ArchiveArtifact:
        """
        Represents a single artifact to be archived.
        This class holds the archive path (relative to the output directory of the 7z archive)
        and the absolute path of the artifact.
        It is used to ensure that artifacts are correctly archived with their intended paths.
        """

        archive_path: Path
        absolute_path: Path

    def __init__(self, out_dir: Path, archive_name: str) -> None:
        self.out_dir: Path = out_dir
        self.archive_name: str = archive_name
        self.archive_artifacts: List[ArtifactsArchive.ArchiveArtifact] = []

    def register(self, artifacts: List[Path]) -> None:
        """
        Register artifacts for archiving.
        Args:
            artifacts: List of paths to artifacts (files or directories) to be archived.
        """
        for artifact in artifacts:
            self._add_artifact(artifact)

    def _add_artifact(self, artifact_path: Path) -> None:
        """
        Add an artifact (file or directory) to the archive list.
        Args:
            artifact_path: path to the artifact to be archived.
        """
        # Convert to absolute path first
        absolute_path = artifact_path.resolve() if not artifact_path.is_absolute() else artifact_path

        # Calculate the relative path from out_dir for the archive
        if absolute_path.is_relative_to(self.out_dir.absolute()):
            archive_path = absolute_path.relative_to(self.out_dir.absolute())
        else:
            # If not relative to out_dir, just use the name
            archive_path = Path(absolute_path.name)

        self.archive_artifacts.append(
            self.ArchiveArtifact(
                archive_path=archive_path,
                absolute_path=absolute_path,
            )
        )

    def create_archive(self) -> Path:
        """
        Create a 7z file containing the collected artifacts.
        Returns:
            Path: The path to the created 7z file.
        Raises:
            Exception: If there is an error creating the 7z file.
        """
        # Construct the full archive path
        archive_path = self.out_dir / self.archive_name

        # Create output directory if it doesn't exist
        archive_path.parent.mkdir(parents=True, exist_ok=True)

        # Delete the file if it already exists
        if archive_path.exists():
            archive_path.unlink()

        if not self.archive_artifacts:
            print("Warning: No artifacts registered for archiving")
            # Create empty 7z file
            with py7zr.SevenZipFile(archive_path, "w") as archive:
                pass
            return archive_path

        try:
            with py7zr.SevenZipFile(archive_path, "w") as archive:
                for artifact in self.archive_artifacts:
                    if not artifact.absolute_path.exists():
                        print(f"Warning: Artifact {artifact.absolute_path} does not exist, skipping")
                        continue

                    try:
                        if artifact.absolute_path.is_file():
                            archive.write(artifact.absolute_path, arcname=str(artifact.archive_path))
                        elif artifact.absolute_path.is_dir():
                            # py7zr can handle directories directly
                            archive.writeall(artifact.absolute_path, arcname=str(artifact.archive_path))
                    except Exception as file_error:
                        print(f"Warning: Failed to add {artifact.absolute_path} to archive: {file_error}")
                        continue

            print(f"7z file created at: {archive_path}")
            return archive_path
        except Exception as e:
            print(f"Error creating artifacts 7z file: {e}")
            raise e


class ArtifactsArchiver:
    """
    This class manages multiple ArtifactsArchive instances.
    It provides a unified interface for registering artifacts to different archives.
    """

    def __init__(self) -> None:
        self.archives: Dict[str, ArtifactsArchive] = {}
        self._target_repos: Dict[str, str] = {}

    def add_archive(self, out_dir: Path, archive_filename: str, target_repo: Optional[str] = None, archive_name: str = "default") -> ArtifactsArchive:
        """
        Add a new archive to the archiver.

        Args:
            out_dir: Output directory for the archive
            archive_filename: Filename for the archive
            target_repo: Target repository path for Artifactory upload (optional)
            archive_name: Name identifier for the archive (defaults to "default")

        Returns:
            The created ArtifactsArchive instance
        """
        archive = ArtifactsArchive(out_dir, archive_filename)
        self.archives[archive_name] = archive
        # Store the target repo information for this archive only if provided
        if target_repo is not None:
            self._target_repos[archive_name] = target_repo
        return archive

    def register(self, artifacts: List[Path], archive_name: str = "default") -> None:
        """
        Register artifacts for archiving to a specific archive.

        Args:
            artifacts: List of paths to artifacts (files or directories) to be archived.
            archive_name: Name of the archive to register artifacts to (defaults to "default")

        Raises:
            KeyError: If the specified archive_name doesn't exist
        """
        if archive_name not in self.archives:
            raise KeyError(f"Archive '{archive_name}' not found. Available archives: {list(self.archives.keys())}")

        self.archives[archive_name].register(artifacts)

    def get_archive(self, archive_name: str) -> ArtifactsArchive:
        """
        Get a specific archive by name.

        Args:
            archive_name: Name of the archive to retrieve

        Returns:
            The ArtifactsArchive instance

        Raises:
            KeyError: If the specified archive_name doesn't exist
        """
        if archive_name not in self.archives:
            raise KeyError(f"Archive '{archive_name}' not found. Available archives: {list(self.archives.keys())}")

        return self.archives[archive_name]

    def create_all_archives(self) -> Dict[str, Path]:
        """
        Create all registered archives.

        Returns:
            Dictionary mapping archive names to their created file paths
        """
        created_archives = {}
        for archive_name, archive in self.archives.items():
            created_archives[archive_name] = archive.create_archive()
        return created_archives

    def create_rt_upload_json(self, out_dir: Path) -> Path:
        """
        Create a single rt-upload.json file containing all archives.

        This function replicates the logic from the Jenkinsfile for determining the RT_TARGET
        and creating the upload specification file. It uses Jenkins environment variables
        when available, otherwise falls back to default values.

        Args:
            output_dir: Directory where the rt-upload.json file will be created

        Returns:
            Path to the created rt-upload.json file
        """
        # Set local defaults first
        change_id = None
        branch_name = "local_branch"
        build_number = "local_build"

        # Adapt values when Jenkins environment is detected
        # TODO: check if an existing library can be used for CI context detection
        if os.environ.get("JENKINS_URL"):
            change_id = os.environ.get("CHANGE_ID")
            jenkins_branch_name = os.environ.get("BRANCH_NAME")
            jenkins_build_number = os.environ.get("BUILD_NUMBER")
            tag_name = os.environ.get("TAG_NAME")

            if change_id:
                # Pull request case
                branch_name = f"PR-{change_id}"
            elif tag_name:
                # Tag build case
                branch_name = tag_name
            elif jenkins_branch_name:
                # Regular branch case
                branch_name = jenkins_branch_name

            if jenkins_build_number:
                build_number = jenkins_build_number

        # Create the files array for Artifactory upload format
        files_array = []

        for archive_name, archive in self.archives.items():
            if archive_name in self._target_repos:
                target_repo = self._target_repos[archive_name]

                # Construct the RT target path
                rt_target = f"{target_repo}/{branch_name}/{build_number}/"

                # Add this archive to the files array
                files_array.append(
                    {
                        "pattern": archive.archive_name,
                        "target": rt_target,
                        "recursive": "false",
                        "flat": "false",
                        "regexp": "false",
                    }
                )

        # Create the single rt-upload.json file
        json_path = out_dir / "rt-upload.json"

        spec = {"files": files_array}

        with open(json_path, "w") as f:
            json.dump(spec, f, indent=4)

        return json_path

    def list_archives(self) -> List[str]:
        """
        Get a list of all archive names.

        Returns:
            List of archive names
        """
        return list(self.archives.keys())

    def create_archive(self, archive_name: str = "default") -> Path:
        """
        Create a specific archive (convenience method for single-archive use case).

        Args:
            archive_name: Name of the archive to create (defaults to "default")

        Returns:
            Path to the created archive file

        Raises:
            KeyError: If the specified archive_name doesn't exist
        """
        if archive_name not in self.archives:
            raise KeyError(f"Archive '{archive_name}' not found. Available archives: {list(self.archives.keys())}")

        return self.archives[archive_name].create_archive()


# Example usage:
#
# ## Simple single-archive use case with target repo:
# archiver = ArtifactsArchiver()
# archiver.add_archive(Path("./build/output"), "results.7z", "my-repo/results")  # uses "default" name
# archiver.register([Path("./build/test_report.xml"), Path("./build/coverage.html")])  # registers to "default"
# archive_path = archiver.create_archive()  # creates the "default" archive
# upload_json = archiver.create_rt_upload_json(Path("./build/output"))
#
# ## Simple single-archive use case without target repo (archive only):
# archiver = ArtifactsArchiver()
# archiver.add_archive(Path("./build/output"), "results.7z")  # no target repo, uses "default" name
# archiver.register([Path("./build/test_report.xml"), Path("./build/coverage.html")])
# archive_path = archiver.create_archive()  # creates the "default" archive
# # upload_json = archiver.create_rt_upload_json(Path("./build/output"))  # would create empty JSON
#
# ## Multi-archive use case:
# archiver = ArtifactsArchiver()
# archiver.add_archive(Path("./build/output"), "test_results.7z", "my-repo/test-results", "test_results")
# archiver.add_archive(Path("./build/output"), "coverage.7z", "my-repo/coverage", "coverage_reports")
# archiver.add_archive(Path("./build/output"), "docs.7z", None, "documentation")  # no target repo for docs
#
# archiver.register([Path("./build/test_report.xml")], "test_results")
# archiver.register([Path("./build/coverage.html")], "coverage_reports")
# archiver.register([Path("./build/docs/")], "documentation")
#
# created_files = archiver.create_all_archives()
# upload_json = archiver.create_rt_upload_json(Path("./build/output"))  # only includes archives with target repos
