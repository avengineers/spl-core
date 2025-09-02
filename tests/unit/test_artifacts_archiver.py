import json
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import pytest

from spl_core.test_utils.artifacts_archiver import ArtifactsArchiver


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
    ],
)
def test_multiple_archives_with_target_repos(test_dir, test_files, monkeypatch, jenkins_url, change_id, branch_name, tag_name, build_number, expected_branch, expected_build):
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
            },
            {
                "pattern": "configuration.7z",
                "target": f"config-repo/{expected_branch}/{expected_build}/",
                "recursive": "false",
                "flat": "false",
                "regexp": "false",
            },
        ]
    }

    # Compare the actual JSON with expected JSON
    assert rt_upload_data == expected_json, f"rt-upload.json content mismatch. Expected: {expected_json}, Got: {rt_upload_data}"
