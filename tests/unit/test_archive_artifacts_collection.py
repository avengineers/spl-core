import json
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

from spl_core.test_utils.archive_artifacts_collection import ArchiveArtifactsCollection


class TestArchiveArtifactsCollection:
    """Test suite for ArchiveArtifactsCollection class."""

    def test_init_with_single_file(self, tmp_path):
        """Test initialization with a single file artifact."""
        # Arrange
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        test_file = build_dir / "test.txt"
        test_file.write_text("test content")

        # Act
        collection = ArchiveArtifactsCollection([test_file], build_dir)

        # Assert
        assert len(collection.archive_artifacts) == 1
        artifact = collection.archive_artifacts[0]
        assert artifact.archive_path == Path("test.txt")
        assert artifact.absolute_path == test_file.absolute()

    def test_init_with_multiple_files(self, tmp_path):
        """Test initialization with multiple file artifacts."""
        # Arrange
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        test_file1 = build_dir / "test1.txt"
        test_file1.write_text("test content 1")
        test_file2 = build_dir / "test2.txt"
        test_file2.write_text("test content 2")

        # Act
        collection = ArchiveArtifactsCollection([test_file1, test_file2], build_dir)

        # Assert
        assert len(collection.archive_artifacts) == 2
        paths = [artifact.archive_path for artifact in collection.archive_artifacts]
        assert Path("test1.txt") in paths
        assert Path("test2.txt") in paths

    def test_init_with_directory(self, tmp_path):
        """Test initialization with a directory containing multiple files."""
        # Arrange
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        test_dir = build_dir / "test_dir"
        test_dir.mkdir()

        file1 = test_dir / "file1.txt"
        file1.write_text("content 1")
        file2 = test_dir / "file2.txt"
        file2.write_text("content 2")

        subdir = test_dir / "subdir"
        subdir.mkdir()
        file3 = subdir / "file3.txt"
        file3.write_text("content 3")

        # Act
        collection = ArchiveArtifactsCollection([test_dir], build_dir)

        # Assert
        assert len(collection.archive_artifacts) == 3
        archive_paths = [artifact.archive_path for artifact in collection.archive_artifacts]
        expected_paths = [Path("test_dir/file1.txt"), Path("test_dir/file2.txt"), Path("test_dir/subdir/file3.txt")]
        for expected_path in expected_paths:
            assert expected_path in archive_paths

    def test_init_with_file_outside_build_dir(self, tmp_path):
        """Test initialization with a file outside the build directory."""
        # Arrange
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        external_file = tmp_path / "external.txt"
        external_file.write_text("external content")

        # Act
        collection = ArchiveArtifactsCollection([external_file], build_dir)

        # Assert
        assert len(collection.archive_artifacts) == 1
        artifact = collection.archive_artifacts[0]
        assert artifact.archive_path == Path("external.txt")  # Just the filename
        assert artifact.absolute_path == external_file.absolute()

    def test_init_with_relative_paths(self, tmp_path):
        """Test initialization with relative paths."""
        # Arrange
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        test_file = build_dir / "test.txt"
        test_file.write_text("test content")

        # Change to build_dir to make relative path work
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(build_dir)
            relative_path = Path("test.txt")

            # Act
            collection = ArchiveArtifactsCollection([relative_path], build_dir)

            # Assert
            assert len(collection.archive_artifacts) == 1
            artifact = collection.archive_artifacts[0]
            assert artifact.archive_path == Path("test.txt")
        finally:
            os.chdir(original_cwd)

    def test_init_with_nonexistent_file(self, tmp_path):
        """Test initialization with a nonexistent file path."""
        # Arrange
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        nonexistent_file = build_dir / "nonexistent.txt"

        # Act
        collection = ArchiveArtifactsCollection([nonexistent_file], build_dir)

        # Assert
        # Should still create an artifact entry even if file doesn't exist
        assert len(collection.archive_artifacts) == 1
        artifact = collection.archive_artifacts[0]
        assert artifact.archive_path == Path("nonexistent.txt")

    def test_create_archive_default_name(self, tmp_path):
        """Test creating an archive with default filename."""
        # Arrange
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        test_file = build_dir / "test.txt"
        test_file.write_text("test content")

        collection = ArchiveArtifactsCollection([test_file], build_dir)

        # Act
        zip_path = collection.create_archive()

        # Assert
        assert zip_path == build_dir / "artifacts.zip"
        assert zip_path.exists()

        # Verify zip contents
        with zipfile.ZipFile(zip_path, "r") as zip_file:
            assert "test.txt" in zip_file.namelist()
            assert zip_file.read("test.txt").decode() == "test content"

    def test_create_archive_custom_name(self, tmp_path):
        """Test creating an archive with custom filename."""
        # Arrange
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        test_file = build_dir / "test.txt"
        test_file.write_text("test content")

        collection = ArchiveArtifactsCollection([test_file], build_dir)

        # Act
        zip_path = collection.create_archive("custom_archive")

        # Assert
        assert zip_path == build_dir / "custom_archive.zip"
        assert zip_path.exists()

    def test_create_archive_custom_name_with_zip_extension(self, tmp_path):
        """Test creating an archive with custom filename that already has .zip extension."""
        # Arrange
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        test_file = build_dir / "test.txt"
        test_file.write_text("test content")

        collection = ArchiveArtifactsCollection([test_file], build_dir)

        # Act
        zip_path = collection.create_archive("custom_archive.zip")

        # Assert
        assert zip_path == build_dir / "custom_archive.zip"
        assert zip_path.exists()

    def test_create_archive_overwrites_existing(self, tmp_path):
        """Test that creating an archive overwrites an existing zip file."""
        # Arrange
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        test_file = build_dir / "test.txt"
        test_file.write_text("test content")

        # Create existing zip file
        existing_zip = build_dir / "artifacts.zip"
        existing_zip.write_text("old content")

        collection = ArchiveArtifactsCollection([test_file], build_dir)

        # Act
        zip_path = collection.create_archive()

        # Assert
        assert zip_path.exists()
        with zipfile.ZipFile(zip_path, "r") as zip_file:
            assert "test.txt" in zip_file.namelist()

    def test_create_archive_multiple_files(self, tmp_path):
        """Test creating an archive with multiple files."""
        # Arrange
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        test_file1 = build_dir / "test1.txt"
        test_file1.write_text("content 1")
        test_file2 = build_dir / "subdir" / "test2.txt"
        test_file2.parent.mkdir()
        test_file2.write_text("content 2")

        collection = ArchiveArtifactsCollection([test_file1, test_file2], build_dir)

        # Act
        zip_path = collection.create_archive()

        # Assert
        with zipfile.ZipFile(zip_path, "r") as zip_file:
            namelist = zip_file.namelist()
            assert "test1.txt" in namelist
            assert "subdir/test2.txt" in namelist
            assert zip_file.read("test1.txt").decode() == "content 1"
            assert zip_file.read("subdir/test2.txt").decode() == "content 2"

    def test_create_archive_handles_zipfile_error(self, tmp_path):
        """Test that create_archive handles zipfile errors properly."""
        # Arrange
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        test_file = build_dir / "test.txt"
        test_file.write_text("test content")

        collection = ArchiveArtifactsCollection([test_file], build_dir)

        # Act & Assert
        with patch("zipfile.ZipFile", side_effect=Exception("Zip error")):
            with pytest.raises(Exception, match="Zip error"):
                collection.create_archive()

    def test_create_json_default_name(self, tmp_path):
        """Test creating a JSON file with default filename."""
        # Arrange
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        test_file = build_dir / "test.txt"
        test_file.write_text("test content")

        collection = ArchiveArtifactsCollection([test_file], build_dir)

        # Act
        json_path = collection.create_json()

        # Assert
        assert json_path == build_dir / "artifacts.json"
        assert json_path.exists()

        # Verify JSON contents
        json_content = json.loads(json_path.read_text())
        assert "artifacts" in json_content
        assert json_content["artifacts"] == ["test.txt"]

    def test_create_json_custom_name(self, tmp_path):
        """Test creating a JSON file with custom filename."""
        # Arrange
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        test_file = build_dir / "test.txt"
        test_file.write_text("test content")

        collection = ArchiveArtifactsCollection([test_file], build_dir)

        # Act
        json_path = collection.create_json("custom_artifacts")

        # Assert
        assert json_path == build_dir / "custom_artifacts.json"
        assert json_path.exists()

    def test_create_json_custom_name_with_json_extension(self, tmp_path):
        """Test creating a JSON file with custom filename that already has .json extension."""
        # Arrange
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        test_file = build_dir / "test.txt"
        test_file.write_text("test content")

        collection = ArchiveArtifactsCollection([test_file], build_dir)

        # Act
        json_path = collection.create_json("custom_artifacts.json")

        # Assert
        assert json_path == build_dir / "custom_artifacts.json"
        assert json_path.exists()

    def test_create_json_overwrites_existing(self, tmp_path):
        """Test that creating a JSON file overwrites an existing file."""
        # Arrange
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        test_file = build_dir / "test.txt"
        test_file.write_text("test content")

        # Create existing JSON file
        existing_json = build_dir / "artifacts.json"
        existing_json.write_text('{"old": "content"}')

        collection = ArchiveArtifactsCollection([test_file], build_dir)

        # Act
        json_path = collection.create_json()

        # Assert
        json_content = json.loads(json_path.read_text())
        assert "artifacts" in json_content
        assert "old" not in json_content

    def test_create_json_multiple_files(self, tmp_path):
        """Test creating a JSON file with multiple artifacts."""
        # Arrange
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        test_file1 = build_dir / "test1.txt"
        test_file1.write_text("content 1")
        test_file2 = build_dir / "subdir" / "test2.txt"
        test_file2.parent.mkdir()
        test_file2.write_text("content 2")

        collection = ArchiveArtifactsCollection([test_file1, test_file2], build_dir)

        # Act
        json_path = collection.create_json()

        # Assert
        json_content = json.loads(json_path.read_text())
        artifacts = json_content["artifacts"]
        assert "test1.txt" in artifacts
        assert "subdir/test2.txt" in artifacts

    def test_create_json_uses_posix_paths(self, tmp_path):
        """Test that JSON file uses POSIX paths regardless of platform."""
        # Arrange
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        subdir = build_dir / "subdir"
        subdir.mkdir()
        test_file = subdir / "test.txt"
        test_file.write_text("content")

        collection = ArchiveArtifactsCollection([test_file], build_dir)

        # Act
        json_path = collection.create_json()

        # Assert
        json_content = json.loads(json_path.read_text())
        # Should use forward slashes even on Windows
        assert json_content["artifacts"] == ["subdir/test.txt"]

    def test_create_json_handles_json_error(self, tmp_path):
        """Test that create_json handles JSON serialization errors properly."""
        # Arrange
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        test_file = build_dir / "test.txt"
        test_file.write_text("test content")

        collection = ArchiveArtifactsCollection([test_file], build_dir)

        # Act & Assert
        with patch("json.dumps", side_effect=Exception("JSON error")):
            with pytest.raises(Exception, match="JSON error"):
                collection.create_json()

    def test_archive_artifact_dataclass(self):
        """Test the ArchiveArtifact dataclass."""
        # Arrange & Act
        artifact = ArchiveArtifactsCollection.ArchiveArtifact(archive_path=Path("test.txt"), absolute_path=Path("/absolute/path/test.txt"))

        # Assert
        assert artifact.archive_path == Path("test.txt")
        assert artifact.absolute_path == Path("/absolute/path/test.txt")

    def test_empty_artifacts_list(self, tmp_path):
        """Test initialization with empty artifacts list."""
        # Arrange
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        # Act
        collection = ArchiveArtifactsCollection([], build_dir)

        # Assert
        assert len(collection.archive_artifacts) == 0

    def test_create_archive_with_empty_collection(self, tmp_path):
        """Test creating an archive with no artifacts."""
        # Arrange
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        collection = ArchiveArtifactsCollection([], build_dir)

        # Act
        zip_path = collection.create_archive()

        # Assert
        assert zip_path.exists()
        with zipfile.ZipFile(zip_path, "r") as zip_file:
            assert len(zip_file.namelist()) == 0

    def test_create_json_with_empty_collection(self, tmp_path):
        """Test creating a JSON file with no artifacts."""
        # Arrange
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        collection = ArchiveArtifactsCollection([], build_dir)

        # Act
        json_path = collection.create_json()

        # Assert
        json_content = json.loads(json_path.read_text())
        assert json_content["artifacts"] == []

    def test_init_with_directory_outside_build_dir(self, tmp_path):
        """Test directory artifact outside build_dir: files are flattened to their name."""
        # Arrange
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        # External directory (not inside build_dir)
        external_dir = tmp_path / "external"
        external_dir.mkdir()
        file1 = external_dir / "ext_file1.txt"
        file1.write_text("external content 1")
        file2 = external_dir / "ext_file2.txt"
        file2.write_text("external content 2")

        # Act
        collection = ArchiveArtifactsCollection([external_dir], build_dir)

        # Assert - files outside build_dir in a directory are stored by filename only
        assert len(collection.archive_artifacts) == 2
        archive_paths = {artifact.archive_path for artifact in collection.archive_artifacts}
        assert Path("ext_file1.txt") in archive_paths
        assert Path("ext_file2.txt") in archive_paths

    def test_mixed_files_and_directories(self, tmp_path):
        """Test initialization with a mix of files and directories."""
        # Arrange
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        # Create a standalone file
        standalone_file = build_dir / "standalone.txt"
        standalone_file.write_text("standalone content")

        # Create a directory with files
        test_dir = build_dir / "test_dir"
        test_dir.mkdir()
        dir_file = test_dir / "dir_file.txt"
        dir_file.write_text("directory file content")

        # Act
        collection = ArchiveArtifactsCollection([standalone_file, test_dir], build_dir)

        # Assert
        assert len(collection.archive_artifacts) == 2
        archive_paths = [artifact.archive_path for artifact in collection.archive_artifacts]
        assert Path("standalone.txt") in archive_paths
        assert Path("test_dir/dir_file.txt") in archive_paths
