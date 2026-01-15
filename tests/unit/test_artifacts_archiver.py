import json
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

from spl_core.test_utils.artifacts_archiver import ArtifactsArchiver

# Artifactory base URL constant for tests
ARTIFACTORY_BASE_URL = "https://artifactory.example.com/artifactory"


@pytest.fixture
def test_dir():
    """Create a temporary directory for test outputs."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    # Cleanup after test
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def test_files(test_dir):
    """Create 5 different test files in different subdirectories to be archived."""
    # Create subdirectories
    (test_dir / "logs").mkdir()
    (test_dir / "config").mkdir()
    (test_dir / "data" / "input").mkdir(parents=True)
    (test_dir / "reports" / "coverage").mkdir(parents=True)
    (test_dir / "build" / "artifacts").mkdir(parents=True)

    # Create test files in different locations
    files = []

    # File 1: Root level
    file1 = test_dir / "readme.txt"
    file1.write_text("This is the main readme file.")
    files.append(file1)

    # File 2: Logs directory
    file2 = test_dir / "logs" / "application.log"
    file2.write_text("2025-09-02 INFO: Application started\n2025-09-02 DEBUG: Processing data")
    files.append(file2)

    # File 3: Config directory
    file3 = test_dir / "config" / "settings.json"
    file3.write_text('{"debug": true, "timeout": 30}')
    files.append(file3)

    # File 4: Nested data directory
    file4 = test_dir / "data" / "input" / "dataset.csv"
    file4.write_text("name,value\ntest1,100\ntest2,200")
    files.append(file4)

    # File 5: Deep nested directory
    file5 = test_dir / "build" / "artifacts" / "output.bin"
    file5.write_bytes(b"\x00\x01\x02\x03\x04\x05")  # Binary content
    files.append(file5)

    return files


@pytest.fixture
def sample_artifacts_dict():
    """Provide sample artifact dictionaries for testing."""
    return {
        "test_reports": {
            "unit_test_report.html": "https://example.com/reports/unit_tests.html",
            "integration_test_report.xml": "https://example.com/reports/integration_tests.xml",
        },
        "sca_reports": {
            "coverage_report.html": "https://example.com/sca/coverage.html",
            "linting_report.json": "https://example.com/sca/linting.json",
        },
        "build_binaries": {
            "application.elf": "https://example.com/binaries/app.elf",
            "bootloader.hex": "https://example.com/binaries/bootloader.hex",
        },
    }


@pytest.fixture
def sample_artifacts_json(test_dir, monkeypatch):
    """Create a pre-populated artifacts.json file for testing updates."""
    # Clear Jenkins environment to use local defaults
    for env_var in ["JENKINS_URL", "CHANGE_ID", "BRANCH_NAME", "TAG_NAME", "BUILD_NUMBER"]:
        monkeypatch.delenv(env_var, raising=False)

    archiver = ArtifactsArchiver()
    artifacts_json_path = archiver.create_artifacts_json("TestVariant", test_dir)

    # Add an initial category
    initial_artifacts = {"initial_report.html": "https://example.com/initial.html"}
    archiver.update_artifacts_json("initial_category", initial_artifacts, artifacts_json_path)

    return artifacts_json_path


def test_simple_archive_creation(test_dir, test_files):
    """Test the simplest use case: add multiple artifacts and create archive."""
    # Arrange
    archiver = ArtifactsArchiver()
    output_dir = test_dir / "output"
    archive_filename = "test_archive.7z"

    # Act
    archiver.add_archive(output_dir, archive_filename)
    archiver.register(test_files)
    archive_path = archiver.create_archive()

    # Assert
    assert archive_path.exists(), "Archive file should be created"
    assert archive_path.name == archive_filename, "Archive should have the correct filename"
    assert archive_path.parent == output_dir, "Archive should be in the correct output directory"
    assert archive_path.stat().st_size > 0, "Archive file should not be empty"
    assert len(test_files) == 5, "Should have 5 test files"


@pytest.mark.parametrize(
    "jenkins_url,change_id,branch_name,tag_name,build_number,expected_branch,expected_build,expected_retention",
    [
        # Local build case (no Jenkins environment) - 28 days for other branches
        (None, None, None, None, None, "local_branch", "local_build", 28),
        # Jenkins regular branch build - 28 days for feature branches
        ("http://jenkins.example.com", None, "feature/test-branch", None, "123", "feature/test-branch", "123", 28),
        # Jenkins pull request build - 28 days for PRs
        ("http://jenkins.example.com", "456", "PR-456", None, "124", "PR-456", "124", 28),
        # Jenkins tag build - -1 (infinite) for tags
        ("http://jenkins.example.com", None, "v1.2.3", "v1.2.3", "125", "v1.2.3", "125", -1),
        # Jenkins develop branch build - 84 days for develop
        ("http://jenkins.example.com", None, "develop", None, "126", "develop", "126", 84),
        # Jenkins release branch build - -1 (infinite) for release branches
        ("http://jenkins.example.com", None, "release/1.0.0", None, "127", "release/1.0.0", "127", -1),
    ],
)
def test_multiple_archives_with_target_repos(test_dir, test_files, monkeypatch, jenkins_url, change_id, branch_name, tag_name, build_number, expected_branch, expected_build, expected_retention):
    """Test creating 3 archives with random file combinations, target repos, and rt-upload JSON."""
    # Arrange - Set up environment variables
    # Clear all Jenkins-related env vars first
    for env_var in ["JENKINS_URL", "CHANGE_ID", "BRANCH_NAME", "TAG_NAME", "BUILD_NUMBER"]:
        monkeypatch.delenv(env_var, raising=False)

    # Set the specific environment variables for this test case
    if jenkins_url:
        monkeypatch.setenv("JENKINS_URL", jenkins_url)
    if change_id:
        monkeypatch.setenv("CHANGE_ID", change_id)
    if branch_name:
        monkeypatch.setenv("BRANCH_NAME", branch_name)
    if tag_name:
        monkeypatch.setenv("TAG_NAME", tag_name)
    if build_number:
        monkeypatch.setenv("BUILD_NUMBER", build_number)

    archiver = ArtifactsArchiver()
    output_dir = test_dir / "output"

    # Create 3 archives with different configurations
    archives_config: List[Dict[str, Any]] = [
        {
            "name": "logs_archive",
            "filename": "logs.7z",
            "target_repo": "logging-repo",
            "files": [test_files[0], test_files[1]],  # readme.txt and application.log
        },
        {
            "name": "config_archive",
            "filename": "configuration.7z",
            "target_repo": "config-repo",
            "files": [test_files[1], test_files[2], test_files[3]],  # application.log, settings.json, dataset.csv
        },
        {
            "name": "data_archive",
            "filename": "data.7z",
            "target_repo": None,  # No target repo for this one
            "files": [test_files[3], test_files[4]],  # dataset.csv and output.bin
        },
    ]

    # Act
    for config in archives_config:
        archiver.add_archive(output_dir, config["filename"], archive_name=config["name"], target_repo=config["target_repo"])
        archiver.register(config["files"], archive_name=config["name"])
    archive_paths_dict = archiver.create_all_archives()
    rt_upload_path = archiver.create_rt_upload_json(output_dir)

    # Assert
    assert len(archive_paths_dict) == 3, "Should have created 3 archives"

    for config in archives_config:
        archive_name = config["name"]
        archive_path = archive_paths_dict[archive_name]
        assert archive_path.exists(), f"Archive {config['filename']} should be created"
        assert archive_path.name == config["filename"], f"Archive should have correct filename {config['filename']}"
        assert archive_path.parent == output_dir, f"Archive {config['filename']} should be in output directory"
        assert archive_path.stat().st_size > 0, f"Archive {config['filename']} should not be empty"

    # Verify rt-upload JSON was created and has correct content
    assert rt_upload_path.exists(), "rt-upload.json should be created"

    with open(rt_upload_path) as f:
        rt_upload_data = json.load(f)

    assert "files" in rt_upload_data, "rt-upload.json should have 'files' key"
    files_list = rt_upload_data["files"]

    # Should have exactly 2 entries (only archives with target repos)
    assert len(files_list) == 2, "rt-upload.json should contain exactly 2 files"

    # Expected JSON structure with the expected target paths from test parameters
    expected_json = {
        "files": [
            {
                "pattern": "logs.7z",
                "target": f"logging-repo/{expected_branch}/{expected_build}/",
                "recursive": "false",
                "flat": "false",
                "regexp": "false",
                "props": f"retention_period={expected_retention}",
            },
            {
                "pattern": "configuration.7z",
                "target": f"config-repo/{expected_branch}/{expected_build}/",
                "recursive": "false",
                "flat": "false",
                "regexp": "false",
                "props": f"retention_period={expected_retention}",
            },
        ]
    }

    # Compare the actual JSON with expected JSON
    assert rt_upload_data == expected_json, f"rt-upload.json content mismatch. Expected: {expected_json}, Got: {rt_upload_data}"


@pytest.mark.parametrize(
    "branch_name,is_tag,expected_retention",
    [
        ("develop", False, 84),  # develop branch -> 84 days (PI length)
        ("release/1.0.0", False, -1),  # release branch -> infinite
        ("release/2.5.3", False, -1),  # another release branch -> infinite
        ("main", False, 28),  # main branch -> 28 days
        ("feature/new-feature", False, 28),  # feature branch -> 28 days
        ("bugfix/fix-123", False, 28),  # bugfix branch -> 28 days
        ("PR-123", False, 28),  # pull request -> 28 days
        ("local_branch", False, 28),  # local branch -> 28 days
        ("v1.0.0", True, -1),  # tag -> infinite
        ("v2.5.3", True, -1),  # another tag -> infinite
    ],
)
def testcalculate_retention_period(branch_name, is_tag, expected_retention):
    """Test the retention period calculation logic for different branch names and tags."""
    # Act
    retention_period = ArtifactsArchiver.calculate_retention_period(branch_name, is_tag)

    # Assert
    assert retention_period == expected_retention, f"Retention period for {branch_name} (is_tag={is_tag}) should be {expected_retention}, got {retention_period}"


# =============================================================================
# Tests for get_archive_url
# =============================================================================


def test_get_archive_url_default_archive_with_target_repo(test_dir, monkeypatch):
    """Test get_archive_url for default archive with target repo."""
    # Arrange
    for env_var in ["JENKINS_URL", "CHANGE_ID", "BRANCH_NAME", "TAG_NAME", "BUILD_NUMBER"]:
        monkeypatch.delenv(env_var, raising=False)

    monkeypatch.setenv("JENKINS_URL", "http://jenkins.example.com")
    monkeypatch.setenv("BRANCH_NAME", "develop")
    monkeypatch.setenv("BUILD_NUMBER", "123")

    archiver = ArtifactsArchiver(artifactory_base_url=ARTIFACTORY_BASE_URL)
    archiver.add_archive(test_dir, "results.7z", target_repo="my-repo/results")

    # Act
    url = archiver.get_archive_url()

    # Assert
    expected_url = f"{ARTIFACTORY_BASE_URL}/my-repo/results/develop/123/results.7z"
    assert url == expected_url, f"Expected {expected_url}, got {url}"


def test_get_archive_url_named_archive_with_target_repo(test_dir, monkeypatch):
    """Test get_archive_url for a named archive with target repo."""
    # Arrange
    for env_var in ["JENKINS_URL", "CHANGE_ID", "BRANCH_NAME", "TAG_NAME", "BUILD_NUMBER"]:
        monkeypatch.delenv(env_var, raising=False)

    monkeypatch.setenv("JENKINS_URL", "http://jenkins.example.com")
    monkeypatch.setenv("BRANCH_NAME", "feature/new-feature")
    monkeypatch.setenv("BUILD_NUMBER", "456")

    archiver = ArtifactsArchiver(artifactory_base_url=ARTIFACTORY_BASE_URL)
    archiver.add_archive(test_dir, "coverage.7z", target_repo="my_project-generic-snapshot-blocksberg", archive_name="coverage_reports")

    # Act
    url = archiver.get_archive_url("coverage_reports")

    # Assert
    expected_url = f"{ARTIFACTORY_BASE_URL}/my_project-generic-snapshot-blocksberg/feature/new-feature/456/coverage.7z"
    assert url == expected_url, f"Expected {expected_url}, got {url}"


def test_get_archive_url_without_target_repo(test_dir, monkeypatch):
    """Test get_archive_url returns None when archive has no target repo."""
    # Arrange
    for env_var in ["JENKINS_URL", "CHANGE_ID", "BRANCH_NAME", "TAG_NAME", "BUILD_NUMBER"]:
        monkeypatch.delenv(env_var, raising=False)

    archiver = ArtifactsArchiver()
    archiver.add_archive(test_dir, "docs.7z")  # No target repo

    # Act
    url = archiver.get_archive_url()

    # Assert
    assert url is None, "Should return None when no target repo is configured"


def test_get_archive_url_nonexistent_archive(test_dir):
    """Test get_archive_url returns None for non-existent archive."""
    # Arrange
    archiver = ArtifactsArchiver()
    archiver.add_archive(test_dir, "results.7z", target_repo="my-repo/results")

    # Act
    url = archiver.get_archive_url("nonexistent_archive")

    # Assert
    assert url is None, "Should return None for non-existent archive"


@pytest.mark.parametrize(
    "jenkins_url,change_id,branch_name,tag_name,build_number,expected_branch,expected_build",
    [
        # Local build case (no Jenkins environment)
        (None, None, None, None, None, "local_branch", "local_build"),
        # Jenkins regular branch build
        ("http://jenkins.example.com", None, "feature/test-branch", None, "123", "feature/test-branch", "123"),
        # Jenkins pull request build
        ("http://jenkins.example.com", "456", "PR-456", None, "124", "PR-456", "124"),
        # Jenkins tag build
        ("http://jenkins.example.com", None, "v1.2.3", "v1.2.3", "125", "v1.2.3", "125"),
        # Jenkins develop branch build
        ("http://jenkins.example.com", None, "develop", None, "126", "develop", "126"),
        # Jenkins release branch build
        ("http://jenkins.example.com", None, "release/1.0.0", None, "127", "release/1.0.0", "127"),
    ],
)
def test_get_archive_url_environment_detection(test_dir, monkeypatch, jenkins_url, change_id, branch_name, tag_name, build_number, expected_branch, expected_build):
    """Test that get_archive_url correctly uses environment variables for URL construction."""
    # Arrange - Set up environment variables
    for env_var in ["JENKINS_URL", "CHANGE_ID", "BRANCH_NAME", "TAG_NAME", "BUILD_NUMBER"]:
        monkeypatch.delenv(env_var, raising=False)

    if jenkins_url:
        monkeypatch.setenv("JENKINS_URL", jenkins_url)
    if change_id:
        monkeypatch.setenv("CHANGE_ID", change_id)
    if branch_name:
        monkeypatch.setenv("BRANCH_NAME", branch_name)
    if tag_name:
        monkeypatch.setenv("TAG_NAME", tag_name)
    if build_number:
        monkeypatch.setenv("BUILD_NUMBER", build_number)

    archiver = ArtifactsArchiver(artifactory_base_url=ARTIFACTORY_BASE_URL)
    target_repo = "test-repo/artifacts"
    archive_filename = "test.7z"
    archiver.add_archive(test_dir, archive_filename, target_repo=target_repo)

    # Act
    url = archiver.get_archive_url()

    # Assert
    expected_url = f"{ARTIFACTORY_BASE_URL}/{target_repo}/{expected_branch}/{expected_build}/{archive_filename}"
    assert url == expected_url, f"Expected {expected_url}, got {url}"


def test_get_archive_url_multiple_archives(test_dir, monkeypatch):
    """Test get_archive_url with multiple archives returns correct URLs for each."""
    # Arrange
    for env_var in ["JENKINS_URL", "CHANGE_ID", "BRANCH_NAME", "TAG_NAME", "BUILD_NUMBER"]:
        monkeypatch.delenv(env_var, raising=False)

    monkeypatch.setenv("JENKINS_URL", "http://jenkins.example.com")
    monkeypatch.setenv("BRANCH_NAME", "develop")
    monkeypatch.setenv("BUILD_NUMBER", "100")

    archiver = ArtifactsArchiver(artifactory_base_url=ARTIFACTORY_BASE_URL)
    archiver.add_archive(test_dir, "tests.7z", target_repo="repo1/tests", archive_name="test_archive")
    archiver.add_archive(test_dir, "coverage.7z", target_repo="repo2/coverage", archive_name="coverage_archive")
    archiver.add_archive(test_dir, "docs.7z", archive_name="docs_archive")  # No target repo

    # Act
    test_url = archiver.get_archive_url("test_archive")
    coverage_url = archiver.get_archive_url("coverage_archive")
    docs_url = archiver.get_archive_url("docs_archive")

    # Assert
    assert test_url == f"{ARTIFACTORY_BASE_URL}/repo1/tests/develop/100/tests.7z"
    assert coverage_url == f"{ARTIFACTORY_BASE_URL}/repo2/coverage/develop/100/coverage.7z"
    assert docs_url is None, "Archive without target repo should return None"


def test_get_archive_url_special_characters_in_branch(test_dir, monkeypatch):
    """Test get_archive_url handles special characters in branch names correctly."""
    # Arrange
    for env_var in ["JENKINS_URL", "CHANGE_ID", "BRANCH_NAME", "TAG_NAME", "BUILD_NUMBER"]:
        monkeypatch.delenv(env_var, raising=False)

    monkeypatch.setenv("JENKINS_URL", "http://jenkins.example.com")
    monkeypatch.setenv("BRANCH_NAME", "feature/JIRA-123-special_fix")
    monkeypatch.setenv("BUILD_NUMBER", "999")

    archiver = ArtifactsArchiver(artifactory_base_url=ARTIFACTORY_BASE_URL)
    archiver.add_archive(test_dir, "result.7z", target_repo="my-repo/results")

    # Act
    url = archiver.get_archive_url()

    # Assert
    expected_url = f"{ARTIFACTORY_BASE_URL}/my-repo/results/feature/JIRA-123-special_fix/999/result.7z"
    assert url == expected_url, f"Expected {expected_url}, got {url}"


def test_get_archive_url_without_artifactory_base_url(test_dir, monkeypatch):
    """Test get_archive_url returns None when archiver is initialized without artifactory_base_url."""
    # Arrange
    for env_var in ["JENKINS_URL", "CHANGE_ID", "BRANCH_NAME", "TAG_NAME", "BUILD_NUMBER"]:
        monkeypatch.delenv(env_var, raising=False)

    monkeypatch.setenv("JENKINS_URL", "http://jenkins.example.com")
    monkeypatch.setenv("BRANCH_NAME", "develop")
    monkeypatch.setenv("BUILD_NUMBER", "123")

    archiver = ArtifactsArchiver()  # No artifactory_base_url provided
    archiver.add_archive(test_dir, "results.7z", target_repo="my-repo/results")  # Has target repo

    # Act
    url = archiver.get_archive_url()

    # Assert
    assert url is None, "Should return None when artifactory_base_url is not configured"


def test_get_archive_url_custom_artifactory_base_url(test_dir, monkeypatch):
    """Test get_archive_url with custom Artifactory base URL."""
    # Arrange
    for env_var in ["JENKINS_URL", "CHANGE_ID", "BRANCH_NAME", "TAG_NAME", "BUILD_NUMBER"]:
        monkeypatch.delenv(env_var, raising=False)

    monkeypatch.setenv("JENKINS_URL", "http://jenkins.example.com")
    monkeypatch.setenv("BRANCH_NAME", "develop")
    monkeypatch.setenv("BUILD_NUMBER", "42")

    # Create archiver with custom Artifactory URL (your company's URL)
    custom_base_url = "https://artifactory.fancy_company.de/artifactory"
    archiver = ArtifactsArchiver(artifactory_base_url=custom_base_url)
    archiver.add_archive(test_dir, "custom.7z", target_repo="my-repo/artifacts")

    # Act
    url = archiver.get_archive_url()

    # Assert
    expected_url = "https://artifactory.fancy_company.de/artifactory/my-repo/artifacts/develop/42/custom.7z"
    assert url == expected_url, f"Expected {expected_url}, got {url}"


# =============================================================================
# Tests for create_artifacts_json
# =============================================================================


@pytest.mark.parametrize(
    "variant,expected_error",
    [
        ("", "Variant name cannot be empty or None"),
        (None, "Variant name cannot be empty or None"),
        ("   ", "Variant name cannot be empty or None"),  # whitespace only
    ],
)
def test_create_artifacts_json_invalid_variant(test_dir, variant, expected_error):
    """Test that create_artifacts_json raises ValueError for invalid variant inputs."""
    # Arrange
    archiver = ArtifactsArchiver()

    # Act & Assert
    with pytest.raises(ValueError, match=expected_error):
        archiver.create_artifacts_json(variant, test_dir)


@pytest.mark.parametrize(
    "jenkins_url,change_id,branch_name,tag_name,build_number,expected_branch,expected_build",
    [
        # Local build case (no Jenkins environment)
        (None, None, None, None, None, "local_branch", "local_build"),
        # Jenkins regular branch build
        ("http://jenkins.example.com", None, "feature/test-branch", None, "123", "feature/test-branch", "123"),
        # Jenkins pull request build
        ("http://jenkins.example.com", "456", "PR-456", None, "124", "PR-456", "124"),
        # Jenkins tag build
        ("http://jenkins.example.com", None, "v1.2.3", "v1.2.3", "125", "v1.2.3", "125"),
        # Jenkins develop branch build
        ("http://jenkins.example.com", None, "develop", None, "126", "develop", "126"),
        # Jenkins release branch build
        ("http://jenkins.example.com", None, "release/1.0.0", None, "127", "release/1.0.0", "127"),
    ],
)
def test_create_artifacts_json_environment_detection(test_dir, monkeypatch, jenkins_url, change_id, branch_name, tag_name, build_number, expected_branch, expected_build):
    """Test that create_artifacts_json correctly detects and uses environment variables."""
    # Arrange - Set up environment variables
    for env_var in ["JENKINS_URL", "CHANGE_ID", "BRANCH_NAME", "TAG_NAME", "BUILD_NUMBER"]:
        monkeypatch.delenv(env_var, raising=False)

    if jenkins_url:
        monkeypatch.setenv("JENKINS_URL", jenkins_url)
    if change_id:
        monkeypatch.setenv("CHANGE_ID", change_id)
    if branch_name:
        monkeypatch.setenv("BRANCH_NAME", branch_name)
    if tag_name:
        monkeypatch.setenv("TAG_NAME", tag_name)
    if build_number:
        monkeypatch.setenv("BUILD_NUMBER", build_number)

    archiver = ArtifactsArchiver()

    # Act
    artifacts_json_path = archiver.create_artifacts_json("TestVariant", test_dir)

    # Assert
    assert artifacts_json_path.exists(), "artifacts.json should be created"

    with open(artifacts_json_path) as f:
        data = json.load(f)

    # Verify build_number is always present
    assert data["build_number"] == expected_build, f"Build number should be {expected_build}"

    # Verify conditional keys based on build type
    if change_id:
        # Pull request case - should have "pull_request" key
        assert "pull_request" in data, "JSON should contain 'pull_request' key for PR builds"
        assert data["pull_request"] == change_id, f"Pull request number should be {change_id}"
        assert "branch" not in data, "JSON should not contain 'branch' key for PR builds"
        assert "tag" not in data, "JSON should not contain 'tag' key for PR builds"
    elif tag_name:
        # Tag case - should have "tag" key
        assert "tag" in data, "JSON should contain 'tag' key for tag builds"
        assert data["tag"] == tag_name, f"Tag should be {tag_name}"
        assert "branch" not in data, "JSON should not contain 'branch' key for tag builds"
        assert "pull_request" not in data, "JSON should not contain 'pull_request' key for tag builds"
    else:
        # Regular branch case (or local) - should have "branch" key
        assert "branch" in data, "JSON should contain 'branch' key for regular branch builds"
        assert data["branch"] == expected_branch, f"Branch should be {expected_branch}"
        assert "pull_request" not in data, "JSON should not contain 'pull_request' key for branch builds"
        assert "tag" not in data, "JSON should not contain 'tag' key for branch builds"


def test_create_artifacts_json_structure(test_dir, monkeypatch):
    """Test that create_artifacts_json creates a file with correct JSON structure."""
    # Arrange
    for env_var in ["JENKINS_URL", "CHANGE_ID", "BRANCH_NAME", "TAG_NAME", "BUILD_NUMBER", "BUILD_URL", "GIT_COMMIT", "GIT_URL"]:
        monkeypatch.delenv(env_var, raising=False)

    archiver = ArtifactsArchiver()
    variant_name = "MyVariant"

    # Act
    artifacts_json_path = archiver.create_artifacts_json(variant_name, test_dir)

    # Assert
    assert artifacts_json_path.exists(), "artifacts.json should be created"
    assert artifacts_json_path.name == "artifacts.json", "File should be named artifacts.json"
    assert artifacts_json_path.parent == test_dir, "File should be in test_dir"

    with open(artifacts_json_path) as f:
        data = json.load(f)

    # Verify required keys are present
    assert "variant" in data, "JSON should contain 'variant' key"
    assert "build_timestamp" in data, "JSON should contain 'build_timestamp' key"
    assert "build_number" in data, "JSON should contain 'build_number' key"
    assert "artifacts" in data, "JSON should contain 'artifacts' key"

    # Verify conditional key is present (for local build, should be 'branch')
    assert "branch" in data, "JSON should contain 'branch' key for local builds"

    # Verify values
    assert data["variant"] == variant_name, f"Variant should be {variant_name}"
    assert data["build_number"] == "local_build", "Build number should be 'local_build' for local builds"
    assert data["branch"] == "local_branch", "Branch should be 'local_branch' for local builds"
    assert data["artifacts"] == {}, "Artifacts dictionary should be empty initially"

    # Optional fields - may or may not be present depending on git availability
    # Just verify they're valid if present
    if "build_url" in data:
        assert isinstance(data["build_url"], str)
    if "commit_id" in data:
        assert isinstance(data["commit_id"], str)
    if "commit_message" in data:
        assert isinstance(data["commit_message"], str)
    if "repository_url" in data:
        assert isinstance(data["repository_url"], str)

    # Verify timestamp format
    timestamp = data["build_timestamp"]
    assert timestamp.endswith("Z"), "Timestamp should end with 'Z' (Zulu time indicator)"
    # Verify it's a valid ISO 8601 timestamp by parsing it (remove Z and parse)
    datetime.fromisoformat(timestamp[:-1])


def test_create_artifacts_json_creates_directories(test_dir, monkeypatch):
    """Test that create_artifacts_json creates parent directories if they don't exist."""
    # Arrange
    for env_var in ["JENKINS_URL", "CHANGE_ID", "BRANCH_NAME", "TAG_NAME", "BUILD_NUMBER", "BUILD_URL", "GIT_COMMIT", "GIT_URL"]:
        monkeypatch.delenv(env_var, raising=False)

    archiver = ArtifactsArchiver()
    nested_dir = test_dir / "nested" / "deep" / "path"

    # Act
    artifacts_json_path = archiver.create_artifacts_json("TestVariant", nested_dir)

    # Assert
    assert artifacts_json_path.exists(), "artifacts.json should be created"
    assert nested_dir.exists(), "Parent directories should be created"
    assert artifacts_json_path.parent == nested_dir, "File should be in nested directory"


# =============================================================================
# Tests for update_artifacts_json
# =============================================================================


@pytest.mark.parametrize(
    "category,artifacts,expected_error",
    [
        ("", {"test.html": "url"}, "Category name cannot be empty or None"),
        (None, {"test.html": "url"}, "Category name cannot be empty or None"),
        ("   ", {"test.html": "url"}, "Category name cannot be empty or None"),  # whitespace only
        ("valid_category", {}, "Artifacts dictionary cannot be empty"),
    ],
)
def test_update_artifacts_json_invalid_inputs(sample_artifacts_json, category, artifacts, expected_error):
    """Test that update_artifacts_json raises ValueError for invalid inputs."""
    # Arrange
    archiver = ArtifactsArchiver()

    # Act & Assert
    with pytest.raises(ValueError, match=expected_error):
        archiver.update_artifacts_json(category, artifacts, sample_artifacts_json)


def test_update_artifacts_json_file_not_exists(test_dir):
    """Test that update_artifacts_json raises FileNotFoundError for non-existent file."""
    # Arrange
    archiver = ArtifactsArchiver()
    non_existent_path = test_dir / "non_existent.json"
    artifacts = {"test.html": "https://example.com/test.html"}

    # Act & Assert
    with pytest.raises(FileNotFoundError, match="artifacts.json file does not exist"):
        archiver.update_artifacts_json("test_category", artifacts, non_existent_path)


def test_update_artifacts_json_corrupted_json(test_dir):
    """Test that update_artifacts_json raises ValueError for corrupted JSON."""
    # Arrange
    archiver = ArtifactsArchiver()
    corrupted_json_path = test_dir / "corrupted.json"
    corrupted_json_path.write_text("{invalid json content")
    artifacts = {"test.html": "https://example.com/test.html"}

    # Act & Assert
    with pytest.raises(ValueError, match="Could not parse artifacts.json"):
        archiver.update_artifacts_json("test_category", artifacts, corrupted_json_path)


def test_update_artifacts_json_invalid_structure(test_dir):
    """Test that update_artifacts_json raises ValueError for invalid JSON structure."""
    # Arrange
    archiver = ArtifactsArchiver()
    invalid_structure_path = test_dir / "invalid_structure.json"
    invalid_structure_path.write_text(json.dumps({"variant": "Test", "no_artifacts_key": {}}))
    artifacts = {"test.html": "https://example.com/test.html"}

    # Act & Assert
    with pytest.raises(ValueError, match="invalid structure.*artifacts.*not found"):
        archiver.update_artifacts_json("test_category", artifacts, invalid_structure_path)


def test_update_artifacts_json_new_category(sample_artifacts_json):
    """Test that update_artifacts_json creates a new category when it doesn't exist."""
    # Arrange
    archiver = ArtifactsArchiver()
    new_artifacts = {
        "new_report.html": "https://example.com/new_report.html",
        "new_data.json": "https://example.com/new_data.json",
    }

    # Act
    result_path = archiver.update_artifacts_json("new_category", new_artifacts, sample_artifacts_json)

    # Assert
    assert result_path == sample_artifacts_json, "Should return the input path"

    with open(sample_artifacts_json) as f:
        data = json.load(f)

    assert "new_category" in data["artifacts"], "New category should be created"
    assert data["artifacts"]["new_category"] == new_artifacts, "New category should contain the provided artifacts"
    # Verify existing category is preserved
    assert "initial_category" in data["artifacts"], "Existing category should be preserved"


def test_update_artifacts_json_update_existing_category(sample_artifacts_json):
    """Test that update_artifacts_json merges artifacts into an existing category."""
    # Arrange
    archiver = ArtifactsArchiver()
    additional_artifacts = {
        "additional_report.html": "https://example.com/additional.html",
        "initial_report.html": "https://example.com/updated.html",  # Overlapping key
    }

    # Read initial state
    with open(sample_artifacts_json) as f:
        initial_data = json.load(f)
    initial_artifacts = initial_data["artifacts"]["initial_category"].copy()

    # Act
    result_path = archiver.update_artifacts_json("initial_category", additional_artifacts, sample_artifacts_json)

    # Assert
    assert result_path == sample_artifacts_json, "Should return the input path"

    with open(sample_artifacts_json) as f:
        data = json.load(f)

    updated_category = data["artifacts"]["initial_category"]

    # Should have merged artifacts (2 total: 1 updated + 1 new)
    assert len(updated_category) == 2, "Should have 2 artifacts after merge"
    assert "additional_report.html" in updated_category, "New artifact should be added"
    assert updated_category["initial_report.html"] == "https://example.com/updated.html", "Existing artifact should be updated"
    assert initial_artifacts.get("initial_report.html") != updated_category["initial_report.html"], "Initial artifact URL should be changed"


def test_update_artifacts_json_multiple_sequential_updates(sample_artifacts_json, sample_artifacts_dict):
    """Test multiple sequential updates to different categories."""
    # Arrange
    archiver = ArtifactsArchiver()

    # Act - Add multiple categories sequentially
    for category, artifacts in sample_artifacts_dict.items():
        archiver.update_artifacts_json(category, artifacts, sample_artifacts_json)

    # Assert
    with open(sample_artifacts_json) as f:
        data = json.load(f)

    # Should have initial_category + 3 new categories = 4 total
    assert len(data["artifacts"]) == 4, "Should have 4 categories total"

    for category, expected_artifacts in sample_artifacts_dict.items():
        assert category in data["artifacts"], f"Category '{category}' should exist"
        assert data["artifacts"][category] == expected_artifacts, f"Category '{category}' should have correct artifacts"

    # Initial category should still exist
    assert "initial_category" in data["artifacts"], "Initial category should still exist"


# =============================================================================
# Edge case tests
# =============================================================================


@pytest.mark.parametrize(
    "variant_name",
    [
        "Variant-With-Dashes",
        "Variant_With_Underscores",
        "Variant.With.Dots",
        "Variant With Spaces",
        "Variant/With/Slashes",
        "Вариант",  # Unicode (Cyrillic)
        "変種",  # Unicode (Japanese)
    ],
)
def test_create_artifacts_json_special_characters_in_variant(test_dir, monkeypatch, variant_name):
    """Test that create_artifacts_json handles special characters and Unicode in variant names."""
    # Arrange
    for env_var in ["JENKINS_URL", "CHANGE_ID", "BRANCH_NAME", "TAG_NAME", "BUILD_NUMBER"]:
        monkeypatch.delenv(env_var, raising=False)

    archiver = ArtifactsArchiver()

    # Act
    artifacts_json_path = archiver.create_artifacts_json(variant_name, test_dir)

    # Assert
    assert artifacts_json_path.exists(), "artifacts.json should be created"

    with open(artifacts_json_path, encoding="utf-8") as f:
        data = json.load(f)

    assert data["variant"] == variant_name, f"Variant should preserve special characters: {variant_name}"


def test_update_artifacts_json_artifact_key_overlap(sample_artifacts_json):
    """Test that overlapping artifact keys are properly updated (last write wins)."""
    # Arrange
    archiver = ArtifactsArchiver()

    first_artifacts = {
        "report.html": "https://example.com/first/report.html",
        "data.json": "https://example.com/first/data.json",
    }

    second_artifacts = {
        "report.html": "https://example.com/second/report.html",  # Overlapping key
        "new_file.txt": "https://example.com/second/new_file.txt",
    }

    # Act
    archiver.update_artifacts_json("test_category", first_artifacts, sample_artifacts_json)
    archiver.update_artifacts_json("test_category", second_artifacts, sample_artifacts_json)

    # Assert
    with open(sample_artifacts_json) as f:
        data = json.load(f)

    category = data["artifacts"]["test_category"]

    # Should have 3 total artifacts (report.html updated, data.json from first, new_file.txt from second)
    assert len(category) == 3, "Should have 3 artifacts after overlap merge"
    assert category["report.html"] == "https://example.com/second/report.html", "Overlapping key should use latest value"
    assert category["data.json"] == "https://example.com/first/data.json", "Non-overlapping artifact from first update should be preserved"
    assert category["new_file.txt"] == "https://example.com/second/new_file.txt", "New artifact from second update should be added"


# =============================================================================
# Tests for _get_git_metadata
# =============================================================================


@patch("spl_core.test_utils.artifacts_archiver.SubprocessExecutor")
def test_get_git_metadata_from_environment(mock_subprocess, monkeypatch):
    """Test _get_git_metadata returns metadata from environment variables."""
    # Arrange
    monkeypatch.setenv("GIT_COMMIT", "abc123def456")
    monkeypatch.setenv("GIT_URL", "https://git.example.de/scm/sple/my_project.git")

    # Mock git command (for commit_message fallback)
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "Test commit message"

    mock_subprocess_instance = MagicMock()
    mock_subprocess_instance.execute.return_value = mock_result
    mock_subprocess.return_value = mock_subprocess_instance

    # Act
    metadata = ArtifactsArchiver._get_git_metadata()

    # Assert
    assert metadata.commit_id == "abc123def456"
    assert metadata.commit_message == "Test commit message"  # From git command (no env var)
    assert metadata.repository_url == "https://git.example.de/scm/sple/my_project.git"

    # Git command should only be called for commit_message
    assert mock_subprocess.call_count == 1
    mock_subprocess.assert_called_with(["git", "log", "-1", "--format=%s"])


@patch("spl_core.test_utils.artifacts_archiver.SubprocessExecutor")
def test_get_git_metadata_from_git_commands(mock_subprocess, monkeypatch):
    """Test _get_git_metadata returns metadata from git commands when env vars not available."""
    # Arrange - Clear environment variables
    for env_var in ["GIT_COMMIT", "GIT_URL"]:
        monkeypatch.delenv(env_var, raising=False)

    # Mock git command results
    def create_mock_result(stdout_value, returncode=0):
        mock_result = MagicMock()
        mock_result.returncode = returncode
        mock_result.stdout = stdout_value
        return mock_result

    # Set up mock to return different values for different git commands
    mock_subprocess_instance = MagicMock()
    call_count = 0

    def mock_execute(handle_errors=True):
        nonlocal call_count
        call_count += 1
        if call_count == 1:  # git rev-parse HEAD
            return create_mock_result("abc123def456789")
        elif call_count == 2:  # git log -1 --format=%s
            return create_mock_result("Fix: resolve critical bug")
        elif call_count == 3:  # git config --get remote.origin.url
            return create_mock_result("git@git.example.de:sple/my_project.git")
        return create_mock_result("", 1)

    mock_subprocess_instance.execute = mock_execute
    mock_subprocess.return_value = mock_subprocess_instance

    # Act
    metadata = ArtifactsArchiver._get_git_metadata()

    # Assert
    assert metadata.commit_id == "abc123def456789"
    assert metadata.commit_message == "Fix: resolve critical bug"
    assert metadata.repository_url == "git@git.example.de:sple/my_project.git"
    assert mock_subprocess.call_count == 3
    mock_subprocess.assert_any_call(["git", "rev-parse", "HEAD"])
    mock_subprocess.assert_any_call(["git", "log", "-1", "--format=%s"])
    mock_subprocess.assert_any_call(["git", "config", "--get", "remote.origin.url"])


@patch("spl_core.test_utils.artifacts_archiver.SubprocessExecutor")
def test_get_git_metadata_all_unavailable(mock_subprocess, monkeypatch):
    """Test _get_git_metadata returns all None when env vars and git commands fail."""
    # Arrange - Clear environment variables
    for env_var in ["GIT_COMMIT", "GIT_URL"]:
        monkeypatch.delenv(env_var, raising=False)

    # Mock git commands to fail
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = "fatal: not a git repository"

    mock_subprocess_instance = MagicMock()
    mock_subprocess_instance.execute.return_value = mock_result
    mock_subprocess.return_value = mock_subprocess_instance

    # Act
    metadata = ArtifactsArchiver._get_git_metadata()

    # Assert
    assert metadata.commit_id is None
    assert metadata.commit_message is None
    assert metadata.repository_url is None


@patch("spl_core.test_utils.artifacts_archiver.SubprocessExecutor")
def test_get_git_metadata_environment_priority(mock_subprocess, monkeypatch):
    """Test _get_git_metadata prioritizes environment variables over git commands."""
    # Arrange - Set environment variables
    monkeypatch.setenv("GIT_COMMIT", "env_commit_123")
    monkeypatch.setenv("GIT_URL", "https://env.example.com/repo.git")

    # Mock git commands (should not be called for commit and URL)
    mock_subprocess_instance = MagicMock()
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "git_message_from_command"
    mock_subprocess_instance.execute.return_value = mock_result
    mock_subprocess.return_value = mock_subprocess_instance

    # Act
    metadata = ArtifactsArchiver._get_git_metadata()

    # Assert
    assert metadata.commit_id == "env_commit_123"  # From environment
    assert metadata.commit_message == "git_message_from_command"  # From git command (no env var)
    assert metadata.repository_url == "https://env.example.com/repo.git"  # From environment

    # Git commands should only be called for commit_message
    assert mock_subprocess.call_count == 1
    mock_subprocess.assert_called_with(["git", "log", "-1", "--format=%s"])


@patch("spl_core.test_utils.artifacts_archiver.SubprocessExecutor")
def test_get_git_metadata_empty_string_conversion(mock_subprocess, monkeypatch):
    """Test _get_git_metadata converts empty strings to None."""
    # Arrange - Set empty environment variables
    monkeypatch.setenv("GIT_COMMIT", "   ")
    monkeypatch.setenv("GIT_URL", "")

    # Mock git commands to return empty strings
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "   \n  "

    mock_subprocess_instance = MagicMock()
    mock_subprocess_instance.execute.return_value = mock_result
    mock_subprocess.return_value = mock_subprocess_instance

    # Act
    metadata = ArtifactsArchiver._get_git_metadata()

    # Assert
    assert metadata.commit_id is None
    assert metadata.commit_message is None
    assert metadata.repository_url is None


@patch("spl_core.test_utils.artifacts_archiver.SubprocessExecutor")
def test_get_git_metadata_exception_handling(mock_subprocess, monkeypatch):
    """Test _get_git_metadata handles exceptions gracefully and logs warnings."""
    # Arrange - Clear environment variables
    for env_var in ["GIT_COMMIT", "GIT_URL"]:
        monkeypatch.delenv(env_var, raising=False)

    # Mock git commands to raise exceptions
    mock_subprocess_instance = MagicMock()
    mock_subprocess_instance.execute.side_effect = Exception("Git command failed")
    mock_subprocess.return_value = mock_subprocess_instance

    # Act
    metadata = ArtifactsArchiver._get_git_metadata()

    # Assert
    assert metadata.commit_id is None
    assert metadata.commit_message is None
    assert metadata.repository_url is None
    assert mock_subprocess.call_count == 3


def test_create_artifacts_json_with_full_metadata(test_dir, monkeypatch):
    """Test create_artifacts_json includes all metadata when BUILD_URL and git metadata available."""
    # Arrange - Clear Jenkins env vars
    for env_var in ["JENKINS_URL", "CHANGE_ID", "BRANCH_NAME", "TAG_NAME", "BUILD_NUMBER"]:
        monkeypatch.delenv(env_var, raising=False)

    # Set Jenkins and git environment variables
    monkeypatch.setenv("JENKINS_URL", "http://jenkins.example.com")
    monkeypatch.setenv("BRANCH_NAME", "develop")
    monkeypatch.setenv("BUILD_NUMBER", "42")
    monkeypatch.setenv("BUILD_URL", "https://jenkins.example.de/job/SPLE/42/")
    monkeypatch.setenv("GIT_COMMIT", "abc123def456789")
    monkeypatch.setenv("GIT_URL", "https://git.example.de/scm/sple/my_project.git")

    archiver = ArtifactsArchiver()

    # Act
    artifacts_json_path = archiver.create_artifacts_json("TestVariant", test_dir)

    # Assert
    assert artifacts_json_path.exists()

    with open(artifacts_json_path) as f:
        data = json.load(f)

    # Verify all fields are present
    assert data["variant"] == "TestVariant"
    assert data["build_number"] == "42"
    assert data["build_url"] == "https://jenkins.example.de/job/SPLE/42/"
    assert data["branch"] == "develop"
    assert data["commit_id"] == "abc123def456789"
    assert data["repository_url"] == "https://git.example.de/scm/sple/my_project.git"
    assert "build_timestamp" in data
    assert data["artifacts"] == {}


@patch("spl_core.test_utils.artifacts_archiver.SubprocessExecutor")
def test_create_artifacts_json_with_git_from_commands(mock_subprocess, test_dir, monkeypatch):
    """Test create_artifacts_json includes git metadata from git commands when env vars not available."""
    # Arrange - Clear all env vars
    for env_var in ["JENKINS_URL", "CHANGE_ID", "BRANCH_NAME", "TAG_NAME", "BUILD_NUMBER", "BUILD_URL", "GIT_COMMIT", "GIT_URL"]:
        monkeypatch.delenv(env_var, raising=False)

    # Mock git command results
    def create_mock_result(stdout_value):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = stdout_value
        return mock_result

    mock_subprocess_instance = MagicMock()
    call_count = 0

    def mock_execute(handle_errors=True):
        nonlocal call_count
        call_count += 1
        if call_count == 1:  # git rev-parse HEAD
            return create_mock_result("git_commit_sha")
        elif call_count == 2:  # git log -1 --format=%s
            return create_mock_result("Add new feature")
        elif call_count == 3:  # git config --get remote.origin.url
            return create_mock_result("git@github.com:user/repo.git")
        # Return failed result for any additional calls
        failed_result = MagicMock()
        failed_result.returncode = 1
        failed_result.stdout = ""
        return failed_result

    mock_subprocess_instance.execute = mock_execute
    mock_subprocess.return_value = mock_subprocess_instance

    archiver = ArtifactsArchiver()

    # Act
    artifacts_json_path = archiver.create_artifacts_json("LocalVariant", test_dir)

    # Assert
    with open(artifacts_json_path) as f:
        data = json.load(f)

    # Verify git metadata from commands
    assert data["commit_id"] == "git_commit_sha"
    assert data["commit_message"] == "Add new feature"
    assert data["repository_url"] == "git@github.com:user/repo.git"
    # Verify no BUILD_URL (not in environment)
    assert "build_url" not in data
    # Verify local defaults
    assert data["branch"] == "local_branch"
    assert data["build_number"] == "local_build"
