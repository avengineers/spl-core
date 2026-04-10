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


def mock_command_execution(return_values=None):
    """
    Context manager for mocking SubprocessExecutor with optional return values or side effects.

    Args:
        return_values: Single return value or list of return values for consecutive calls
    """
    mock_subprocess_executor = patch("spl_core.test_utils.spl_build.SubprocessExecutor")
    mock = mock_subprocess_executor.start()
    mock_instance = MagicMock()

    if return_values:
        if isinstance(return_values, list):
            mock_instance.execute.side_effect = return_values
        else:
            mock_instance.execute.return_value = return_values
    else:
        # Default to success case
        mock_instance.execute.return_value = MagicMock(returncode=0)

    mock.return_value = mock_instance

    class MockContext:
        def __enter__(self):
            # Return both the mock constructor and execute method for assertions
            return mock, mock_instance.execute

        def __exit__(self, *args):
            mock_subprocess_executor.stop()

    return MockContext()


@pytest.mark.parametrize(
    "variant,build_kit,build_type,target,expected_path",
    [
        # Basic configurations without build_type
        ("some_var", "someBuildKit", None, None, "build/some_var/someBuildKit"),
        ("another/var", "anotherBuildKit", None, None, "build/another/var/anotherBuildKit"),
        # With build_type (target parameter doesn't affect build_dir)
        ("my/var", "myBuildKit", "my_type", "my_target", "build/my/var/myBuildKit/my_type"),
        ("my/var", "myBuildKit", "my_type", None, "build/my/var/myBuildKit/my_type"),
        # Without build_type (target parameter doesn't affect build_dir)
        ("my/var", "myBuildKit", None, "my_target", "build/my/var/myBuildKit"),
    ],
)
def test_build_dir(variant: str, build_kit: str, build_type: str | None, target: str | None, expected_path: str) -> None:
    """Test build directory path generation for various configurations."""
    spl_build = SplBuild(variant=variant, build_kit=build_kit, build_type=build_type, target=target)
    assert spl_build.build_dir == Path(expected_path)


def test_execute_success() -> None:
    # Arrange
    spl_build = SplBuild(variant="my_var", build_kit="my_build_kit")

    # Call the method
    with mock_command_execution() as (mock_constructor, mock_executor):
        result = spl_build.execute(target="all")

        # Assertions
        mock_constructor.assert_called_once_with(command=["build.bat", "-build", "-buildKit", "my_build_kit", "-variants", "my_var", "-target", "all", "-reconfigure"])
        mock_executor.assert_called_once_with(handle_errors=False)
        assert result == 0, "Expected execute to return 0 on success"


def test_execute_with_target_from_constructor() -> None:
    # Arrange
    spl_build = SplBuild(variant="my_var", build_kit="my_build_kit", target="my_target")

    # Call the method
    with mock_command_execution() as (mock_constructor, mock_executor):
        result = spl_build.execute()

        # Assertions
        mock_constructor.assert_called_once_with(command=["build.bat", "-build", "-buildKit", "my_build_kit", "-variants", "my_var", "-target", "my_target", "-reconfigure"])
        mock_executor.assert_called_once_with(handle_errors=False)
        assert result == 0, "Expected execute to return 0 on success."


def test_execute_retry_on_license_issue(spl_build: SplBuild) -> None:
    with patch("time.sleep") as mock_sleep:
        # Setup mock outputs to simulate license failure and then success
        failure_output = MagicMock(returncode=1, stdout="No valid floating license")
        success_output = MagicMock(returncode=0)

        with mock_command_execution(return_values=[failure_output, success_output]) as (mock_constructor, mock_executor):
            # Call the method
            result = spl_build.execute(target="all")

            # Assertions
            mock_constructor.assert_called_with(command=["build.bat", "-build", "-buildKit", "defaultKit", "-variants", "my_var", "-target", "all", "-reconfigure"])
            assert mock_executor.call_count == 2
            assert result == 0
            assert mock_sleep.call_count == 1


def test_execute_with_additional_args(spl_build: SplBuild) -> None:
    with mock_command_execution() as (mock_constructor, mock_executor):
        # Call the method
        additional_args = ["-j", "4"]
        spl_build.execute(target="all", additional_args=additional_args)

        # Assertions
        mock_constructor.assert_called_once_with(command=["build.bat", "-build", "-buildKit", "defaultKit", "-variants", "my_var", "-target", "all", "-reconfigure", "-j", "4"])
        mock_executor.assert_called_once_with(handle_errors=False)


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

    assert dict(json.loads(archive_json.read_text())) == {"variant": "my_var", "build_kit": "defaultKit", "artifacts": expected_artifacts}


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

    assert dict(json.loads(archive_json.read_text())) == {"variant": "my_var", "build_kit": "defaultKit", "artifacts": expected_artifacts}


@pytest.mark.parametrize(
    "build_kit,target,component_name,expected_artifacts",
    [
        # No target set
        ("test", None, "some_component", []),
        # Unknown build_kit/target combination
        ("unknown", "unknown", "some_component", []),
        # test/unittests target
        (
            "test",
            "unittests",
            "my_component",
            [
                Path("build/my_var/test/my_component/coverage.json"),
                Path("build/my_var/test/my_component/junit.xml"),
                Path("build/my_var/test/my_component/reports/coverage/index.html"),
            ],
        ),
        # test/reports target
        (
            "test",
            "reports",
            "my_component",
            [
                Path("build/my_var/test/reports/html/build/my_var/test/my_component/reports/coverage.html"),
                Path("build/my_var/test/reports/html/build/my_var/test/my_component/reports/coverage/index.html"),
                Path("build/my_var/test/reports/html/build/my_var/test/my_component/reports/unit_test_results.html"),
                Path("build/my_var/test/reports/html/build/my_var/test/my_component/reports/unit_test_spec.html"),
            ],
        ),
    ],
)
def test_get_component_artifacts(build_kit: str, target: str | None, component_name: str, expected_artifacts: list[Path]) -> None:
    spl_build = SplBuild(variant="my_var", build_kit=build_kit, target=target)

    result = spl_build.get_component_artifacts(component_name)

    assert result == expected_artifacts


@pytest.mark.parametrize(
    "build_kit,target,component_names,expected_count",
    [
        # Empty component list
        ("test", "unittests", [], 0),
        # Single component
        ("test", "unittests", ["component1"], 3),
        # Multiple components
        ("test", "unittests", ["component1", "component2"], 6),
        # No target set
        ("test", None, ["component1", "component2"], 0),
    ],
)
def test_get_components_artifacts(build_kit: str, target: str | None, component_names: list[str], expected_count: int) -> None:
    spl_build = SplBuild(variant="my_var", build_kit=build_kit, target=target)

    result = spl_build.get_components_artifacts(component_names)

    assert len(result) == expected_count
    if expected_count > 0:
        # Verify that artifacts are correctly combined from multiple components
        for component in component_names:
            component_artifacts = spl_build.get_component_artifacts(component)
            assert all(artifact in result for artifact in component_artifacts)


@pytest.mark.parametrize(
    "build_kit,target,build_type,expected_artifacts",
    [
        # No target set
        ("prod", None, None, []),
        # Unknown build_kit/target combination
        ("unknown", "unknown", None, []),
        # prod/all target without build_type
        ("prod", "all", None, [Path("build/my_var/prod/compile_commands.json")]),
        # prod/all target with build_type
        ("prod", "all", "debug", [Path("build/my_var/prod/debug/compile_commands.json")]),
    ],
)
def test_get_variant_artifacts(build_kit: str, target: str | None, build_type: str | None, expected_artifacts: list[Path]) -> None:
    spl_build = SplBuild(variant="my_var", build_kit=build_kit, build_type=build_type, target=target)

    result = spl_build.get_variant_artifacts()

    assert result == expected_artifacts
