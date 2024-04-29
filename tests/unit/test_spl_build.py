import json
import os
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from spl_core.test_utils.spl_build import SplBuild


@pytest.fixture
def spl_build(tmp_path_factory):
    os.chdir(tmp_path_factory.mktemp("spl_build"))
    return SplBuild(variant="my_var", build_kit="defaultKit")

def test_build_dir(spl_build: SplBuild) -> None:
    """
    Test that the build directory is constructed correctly.
    """
    assert spl_build.build_dir == Path("build/my_var/defaultKit")


@patch("spl_core.common.command_line_executor.CommandLineExecutor.execute")
def test_execute_success(mock_execute: MagicMock, spl_build: SplBuild) -> None:
    """
    Test that execute returns 0 when the build succeeds.
    """
    mock_execute.return_value = MagicMock(returncode=0)

    # Call the method
    result = spl_build.execute(target="all")

    # Assertions
    mock_execute.assert_called_once()
    assert result == 0


@patch("time.sleep")
@patch("spl_core.common.command_line_executor.CommandLineExecutor.execute")
def test_execute_failure_due_to_license_issue(mock_execute: MagicMock, mock_sleep: MagicMock, spl_build: SplBuild) -> None:
    """
    Test that execute retries on specific license failure messages.
    """
    # Setup mock outputs to simulate license failure and then success
    failure_output = MagicMock(returncode=1, stdout="No valid floating license")
    success_output = MagicMock(returncode=0)
    mock_execute.side_effect = [failure_output, success_output]

    # Call the method
    result = spl_build.execute(target="all")

    # Assertions
    assert mock_execute.call_count == 2
    assert result == 0
    assert mock_sleep.call_count == 1


@patch("spl_core.common.command_line_executor.CommandLineExecutor.execute")
def test_execute_with_additional_args(mock_execute: MagicMock, spl_build: SplBuild) -> None:
    """
    Test that additional arguments are passed to the command line executor correctly.
    """
    # Setup mock
    mock_execute.return_value = MagicMock(returncode=0)

    # Call the method
    additional_args = ["-j", "4"]
    spl_build.execute(target="all", additional_args=additional_args)

    # Assertions
    mock_execute.assert_called_once_with(["build.bat", "-buildKit", "defaultKit", "-variants", "my_var", "-target", "all", "-reconfigure", "-j", "4"])


def test_create_artifacts_archive_inside_spl_build(spl_build: SplBuild) -> None:
    """
    Test the creation of artifacts archive and json for artifacts inside of the spl_build folder
    """
    # Generate some files and folder inside the spl build dir
    file_1 = spl_build.build_dir.joinpath("out", "some_file.exe")
    file_2 = spl_build.build_dir.joinpath("other_file.exe")
    folder_1 = spl_build.build_dir.joinpath("some_folder")
    file_3 = folder_1.joinpath("other_file.exe")
    artifacts = [file_1, file_2, file_3]
    for file in artifacts:
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text("some_text")

    # create artifacts archive and artifacts json
    archive_dir = spl_build.create_artifacts_archive([Path("some_folder"), Path("out/some_file.exe"), Path("other_file.exe")])
    archive_json = spl_build.create_artifacts_json([Path("some_folder"), Path("out/some_file.exe"), Path("other_file.exe")])
    assert archive_dir.exists()
    assert archive_json.exists()

    # check content of archive and json file
    expected_artifacts = ["some_folder/other_file.exe", "out/some_file.exe", "other_file.exe"]
    with zipfile.ZipFile(archive_dir) as zip_ref:
        file_list = zip_ref.namelist()
        assert file_list == expected_artifacts

    assert dict(json.loads(archive_json.read_text())) == {'variant': 'my_var',
                                                          'build_kit': 'defaultKit',
                                                          'artifacts': expected_artifacts
                                                          }

def test_create_artifacts_archive_outside_spl_build(spl_build: SplBuild, tmp_path: Path) -> None:
    """
    Test the creation of artifacts archive and json for artifacts outsice of the spl_build folder
    """
    # Generate a file and folder outside the spl build dir
    spl_build.build_dir.mkdir(parents=True, exist_ok=True)
    test_dir = tmp_path
    outside_file = test_dir.joinpath("some_file.txt")
    outside_file.write_text("something")

    # create artifacts archive and artifacts json
    archive_dir = spl_build.create_artifacts_archive([test_dir.absolute()])
    archive_json = spl_build.create_artifacts_json([test_dir.absolute()])
    assert archive_dir.exists()
    assert archive_json.exists()

    # check content of archive and json file
    expected_artifacts = [outside_file.name]
    with zipfile.ZipFile(archive_dir) as zip_ref:
        file_list = zip_ref.namelist()
        assert file_list == expected_artifacts

    assert dict(json.loads(archive_json.read_text())) == {'variant': 'my_var',
                                                          'build_kit': 'defaultKit',
                                                          'artifacts': expected_artifacts
                                                          }
