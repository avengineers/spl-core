import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import py7zr
from py_app_dev.core.logging import logger
from py_app_dev.core.subprocess import SubprocessExecutor


@dataclass
class BuildMetadata:
    """
    Contains build metadata extracted from environment variables.

    Attributes:
        branch_name: The branch name, PR identifier (e.g., "PR-123"), or tag name
        build_number: The build number or "local_build"
        is_tag: Whether this is a tag build
        pr_number: The PR number (without "PR-" prefix) for pull request builds, None otherwise
    """

    branch_name: str
    build_number: str
    is_tag: bool
    pr_number: Optional[str]


@dataclass
class GitMetadata:
    """
    Contains git metadata extracted from environment variables or git commands.

    Attributes:
        commit_id: The git commit SHA (full hash)
        commit_message: The git commit message subject line (first line only)
        repository_url: The git repository URL (from remote.origin.url)
    """

    commit_id: Optional[str]
    commit_message: Optional[str]
    repository_url: Optional[str]


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
            logger.warning("No artifacts registered for archiving")
            # Create empty 7z file
            with py7zr.SevenZipFile(archive_path, "w") as archive:
                pass
            return archive_path

        try:
            with py7zr.SevenZipFile(archive_path, "w") as archive:
                for artifact in self.archive_artifacts:
                    if not artifact.absolute_path.exists():
                        logger.warning(f"Artifact {artifact.absolute_path} does not exist, skipping")
                        continue

                    try:
                        if artifact.absolute_path.is_file():
                            archive.write(artifact.absolute_path, arcname=str(artifact.archive_path))
                        elif artifact.absolute_path.is_dir():
                            # py7zr can handle directories directly
                            archive.writeall(artifact.absolute_path, arcname=str(artifact.archive_path))
                    except Exception as file_error:
                        logger.warning(f"Failed to add {artifact.absolute_path} to archive: {file_error}")
                        continue

            logger.info(f"7z file created at: {archive_path}")
            return archive_path
        except Exception as e:
            logger.error(f"Error creating artifacts 7z file: {e}")
            raise e


class ArtifactsArchiver:
    """
    This class manages multiple ArtifactsArchive instances.
    It provides a unified interface for registering artifacts to different archives.
    """

    def __init__(self, artifactory_base_url: Optional[str] = None) -> None:
        self.archives: Dict[str, ArtifactsArchive] = {}
        self._target_repos: Dict[str, str] = {}
        self.artifactory_base_url = artifactory_base_url

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

    def get_archive_url(self, archive_name: str = "default") -> Optional[str]:
        """
        Get the Artifactory URL for a specific archive.

        Args:
            archive_name: Name of the archive (defaults to "default")

        Returns:
            The full Artifactory URL for the archive, or None if no target repo configured

        Example:
            "https://artifactory.example.com/artifactory/my-repo/results/develop/123/result.7z"
        """
        if archive_name not in self.archives:
            return None

        if archive_name not in self._target_repos:
            return None

        if self.artifactory_base_url is None:
            return None

        archive = self.archives[archive_name]
        target_repo = self._target_repos[archive_name]
        metadata = self._get_build_metadata()

        # Construct the URL following the same pattern as create_rt_upload_json
        archive_url = f"{self.artifactory_base_url}/{target_repo}/{metadata.branch_name}/{metadata.build_number}/{archive.archive_name}"

        return archive_url

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

    @staticmethod
    def calculate_retention_period(branch_name: str, is_tag: bool) -> int:
        """
        Calculate the retention period in days based on branch name or tag.

        Args:
            branch_name: The name of the branch
            is_tag: Whether this is a tag build

        Returns:
            Retention period in days:
            - 84 days for "develop" branch
            - -1 (infinite) for release branches (release/*)
            - -1 (infinite) for tags
            - 28 days for everything else (PRs, feature branches, etc.)
        """
        if is_tag:
            return -1  # Infinite retention for tags
        elif branch_name == "develop":
            return 84  # Length of a PI (Program Increment)
        elif branch_name.startswith("release/"):
            return -1  # Infinite retention for release branches
        else:
            return 28  # 4 weeks for PRs, feature branches, and other branches

    @staticmethod
    def _get_build_metadata() -> BuildMetadata:
        """
        Get build metadata from environment variables or defaults.

        Detects Jenkins environment variables when available, otherwise falls back
        to local development defaults.

        Returns:
            BuildMetadata instance containing:
            - branch_name: The branch name, PR identifier (e.g., "PR-123"), or tag name
            - build_number: The build number or "local_build"
            - is_tag: Whether this is a tag build
            - pr_number: The PR number (without "PR-" prefix) for pull requests, None otherwise
        """
        branch_name = "local_branch"
        build_number = "local_build"
        is_tag = False
        pr_number = None

        if os.environ.get("JENKINS_URL"):
            change_id = os.environ.get("CHANGE_ID")
            jenkins_branch_name = os.environ.get("BRANCH_NAME")
            jenkins_build_number = os.environ.get("BUILD_NUMBER")
            tag_name = os.environ.get("TAG_NAME")

            if change_id:
                # Pull request case
                branch_name = f"PR-{change_id}"
                pr_number = change_id
            elif tag_name:
                # Tag build case
                branch_name = tag_name
                is_tag = True
            elif jenkins_branch_name:
                # Regular branch case
                branch_name = jenkins_branch_name

            if jenkins_build_number:
                build_number = jenkins_build_number

        return BuildMetadata(
            branch_name=branch_name,
            build_number=build_number,
            is_tag=is_tag,
            pr_number=pr_number,
        )

    @staticmethod
    def _get_git_metadata() -> GitMetadata:
        """
        Get git metadata from environment variables or git commands.

        Attempts to retrieve git information in the following order:
        1. Environment variables (GIT_COMMIT, GIT_URL) - typically set by Jenkins Git plugin
        2. Git commands as fallback - executed locally using git CLI

        The commit message captured is only the subject line (first line), not the full message.

        Returns:
            GitMetadata instance containing:
            - commit_id: The git commit SHA, or None if unavailable
            - commit_message: The commit subject line (first line only), or None if unavailable
            - repository_url: The git repository URL, or None if unavailable
        """
        commit_id = None
        commit_message = None
        repository_url = None

        # Try environment variables first (Jenkins Git plugin)
        env_commit = os.environ.get("GIT_COMMIT")
        env_url = os.environ.get("GIT_URL")

        if env_commit:
            commit_id = env_commit if env_commit.strip() else None
        if env_url:
            repository_url = env_url if env_url.strip() else None

        # Fallback to git commands if environment variables not available
        # Get commit ID
        if not commit_id:
            try:
                result = SubprocessExecutor(["git", "rev-parse", "HEAD"]).execute(handle_errors=False)
                if result and result.returncode == 0:
                    value = result.stdout.strip()
                    commit_id = value if value else None
            except Exception as e:
                logger.warning(f"Failed to get commit ID from git: {e}")

        # Get commit message (subject line only)
        if not commit_message:
            try:
                result = SubprocessExecutor(["git", "log", "-1", "--format=%s"]).execute(handle_errors=False)
                if result and result.returncode == 0:
                    value = result.stdout.strip()
                    commit_message = value if value else None
            except Exception as e:
                logger.warning(f"Failed to get commit message from git: {e}")

        # Get repository URL
        if not repository_url:
            try:
                result = SubprocessExecutor(["git", "config", "--get", "remote.origin.url"]).execute(handle_errors=False)
                if result and result.returncode == 0:
                    value = result.stdout.strip()
                    repository_url = value if value else None
            except Exception as e:
                logger.warning(f"Failed to get repository URL from git: {e}")

        return GitMetadata(
            commit_id=commit_id,
            commit_message=commit_message,
            repository_url=repository_url,
        )

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
        # Get build metadata from environment or defaults
        metadata = self._get_build_metadata()

        # Calculate retention period based on branch/tag
        retention_period = self.calculate_retention_period(metadata.branch_name, metadata.is_tag)

        # Create the files array for Artifactory upload format
        files_array = []

        for archive_name, archive in self.archives.items():
            if archive_name in self._target_repos:
                target_repo = self._target_repos[archive_name]

                # Construct the RT target path
                rt_target = f"{target_repo}/{metadata.branch_name}/{metadata.build_number}/"

                # Add this archive to the files array with retention_period property
                files_array.append(
                    {
                        "pattern": archive.archive_name,
                        "target": rt_target,
                        "recursive": "false",
                        "flat": "false",
                        "regexp": "false",
                        "props": f"retention_period={retention_period}",
                    }
                )

        # Create the single rt-upload.json file
        json_path = out_dir / "rt-upload.json"

        spec = {"files": files_array}

        with open(json_path, "w") as f:
            json.dump(spec, f, indent=4)

        return json_path

    def create_artifacts_json(self, variant: str, out_dir: Path) -> Path:
        """
        Create an initial artifacts.json file with build metadata structure.

        This function creates a fresh artifacts.json file with build metadata
        but no artifacts. Use update_artifacts_json() to add artifact categories.
        It uses Jenkins environment variables when available, otherwise falls back to default values.

        The JSON file includes conditional keys based on the build type:
        - For pull requests: includes "pull_request" key with the PR number (e.g., "117")
        - For tag builds: includes "tag" key with the tag name (e.g., "v1.2.3")
        - For regular branch builds: includes "branch" key with the branch name (e.g., "develop")

        Optional fields (included only if available):
        - build_url: Jenkins build URL from BUILD_URL environment variable
        - commit_id: Git commit SHA from GIT_COMMIT env var or git rev-parse HEAD
        - commit_message: Git commit subject line from git log (first line only)
        - repository_url: Git repository URL from GIT_URL env var or git config

        Args:
            variant: The variant name (e.g., "Disco")
            out_dir: Directory where the artifacts.json file will be created

        Returns:
            Path to the created artifacts.json file

        Raises:
            ValueError: If variant is empty or None
        """
        # Input validation
        if not variant or not variant.strip():
            raise ValueError("Variant name cannot be empty or None")

        # Get metadata from environment or defaults
        build_metadata = self._get_build_metadata()
        git_metadata = self._get_git_metadata()

        # Create the initial artifacts.json structure with base metadata
        artifacts_data: Dict[str, Any] = {
            "variant": variant,
            "build_timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds") + "Z",
            "build_number": build_metadata.build_number,
        }

        # Add build_url if available
        build_url = os.environ.get("BUILD_URL")
        if build_url:
            artifacts_data["build_url"] = build_url

        # Add conditional keys based on build type
        if build_metadata.pr_number:
            # Pull request build
            artifacts_data["pull_request"] = build_metadata.pr_number
        elif build_metadata.is_tag:
            # Tag build
            artifacts_data["tag"] = build_metadata.branch_name
        else:
            # Regular branch build (or local build)
            artifacts_data["branch"] = build_metadata.branch_name

        # Add git metadata if available
        if git_metadata.commit_id:
            artifacts_data["commit_id"] = git_metadata.commit_id
        if git_metadata.commit_message:
            artifacts_data["commit_message"] = git_metadata.commit_message
        if git_metadata.repository_url:
            artifacts_data["repository_url"] = git_metadata.repository_url

        # Add empty artifacts dictionary
        artifacts_data["artifacts"] = {}

        # Create the artifacts.json file
        json_path = out_dir / "artifacts.json"
        json_path.parent.mkdir(parents=True, exist_ok=True)

        with open(json_path, "w") as f:
            json.dump(artifacts_data, f, indent=2)

        return json_path

    def update_artifacts_json(self, category: str, artifacts: Dict[str, str], artifacts_json_path: Path) -> Path:
        """
        Add or update artifacts in a specific category for the artifacts.json file.

        Args:
            category: The artifact category (e.g., "test_reports", "sca_reports", "build_binaries")
            artifacts: Dictionary mapping artifact names to their URLs/paths
            artifacts_json_path: Path to the artifacts.json file to be updated

        Returns:
            Path to the updated artifacts.json file

        Raises:
            ValueError: If category is empty, artifacts dictionary is empty, or JSON structure is invalid
            FileNotFoundError: If artifacts.json file does not exist
        """
        # Input validation
        if not category or not category.strip():
            raise ValueError("Category name cannot be empty or None")
        if not artifacts:
            raise ValueError("Artifacts dictionary cannot be empty")

        # Check if artifacts.json file exists
        if not artifacts_json_path.exists():
            raise FileNotFoundError(f"artifacts.json file does not exist at {artifacts_json_path}. Please create it first using create_artifacts_json().")

        # Read existing artifacts.json file
        try:
            with open(artifacts_json_path) as f:
                artifacts_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Could not parse artifacts.json: {e}") from e
        except OSError as e:
            raise ValueError(f"Could not read artifacts.json: {e}") from e

        # Validate that the file has the expected structure
        if not artifacts_data or "artifacts" not in artifacts_data:
            raise ValueError("artifacts.json file has invalid structure. Expected 'artifacts' section not found.")

        # Update the specific category with new artifacts
        if category in artifacts_data["artifacts"]:
            artifacts_data["artifacts"][category].update(artifacts)
        else:
            artifacts_data["artifacts"][category] = artifacts.copy()

        # Write the updated data back to the file
        with open(artifacts_json_path, "w") as f:
            json.dump(artifacts_data, f, indent=2)

        return artifacts_json_path

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
#
# ## Artifacts.json use case (variant-specific metadata):
# archiver = ArtifactsArchiver()
# variant = "Disco"
# out_dir = Path("./build/output")
#
# # Create initial artifacts.json file first, then add categories
# # The resulting JSON will contain conditional keys based on build type:
# # - For PRs: {"variant": "Disco", "build_timestamp": "...", "build_number": "123", "pull_request": "117", "artifacts": {}}
# # - For tags: {"variant": "Disco", "build_timestamp": "...", "build_number": "123", "tag": "v1.2.3", "artifacts": {}}
# # - For branches: {"variant": "Disco", "build_timestamp": "...", "build_number": "123", "branch": "develop", "artifacts": {}}
# artifacts_json_path = archiver.create_artifacts_json(variant, out_dir)
# archiver.update_artifacts_json("test_reports", test_reports, artifacts_json_path)
# archiver.update_artifacts_json("sca_reports", sca_reports, artifacts_json_path)
# archiver.update_artifacts_json("build_binaries", build_binaries, artifacts_json_path)
