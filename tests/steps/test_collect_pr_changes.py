from unittest.mock import MagicMock, patch

import pytest
from pypeline.domain.execution_context import ExecutionContext
from pypeline_semantic_release.check_ci_context import CIContext, CISystem

from spl_core.steps.collect_pr_changes import CollectPRChanges, PR_Changes


@pytest.fixture
def mock_execution_context(tmp_path):
    """Create a mock execution context for testing."""
    mock_context = MagicMock(spec=ExecutionContext)
    mock_context.project_root_dir = tmp_path
    return mock_context


@pytest.fixture
def collect_pr_changes(mock_execution_context):
    """Create CollectPRChanges instance with mocked execution context."""
    step = CollectPRChanges(mock_execution_context, group_name="test_group")
    return step


class TestCollectPRChanges:
    """Test cases for CollectPRChanges pipeline step."""

    @patch("spl_core.steps.collect_pr_changes.SubprocessExecutor")
    @patch("spl_core.steps.collect_pr_changes.CollectPRChanges._get_commit_id")
    @patch("spl_core.steps.collect_pr_changes.CollectPRChanges.get_outputs")
    def test_run(self, mock_get_outputs, mock_get_commit_id, mock_subprocess, collect_pr_changes, tmp_path):
        """Test run method when in PR context."""
        # Arrange
        ci_context = CIContext(ci_system=CISystem.JENKINS, current_branch="feature-branch", target_branch="main", is_pull_request=True)

        # Configure the mock execution context with data_registry
        mock_data_registry = MagicMock()
        mock_data_registry.find_data.return_value = [ci_context]
        collect_pr_changes.execution_context.data_registry = mock_data_registry

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "file1.py\nfile2.py\nfile3.txt\n"

        mock_subprocess_instance = MagicMock()
        mock_subprocess_instance.execute.return_value = mock_result
        mock_subprocess.return_value = mock_subprocess_instance

        mock_get_commit_id.return_value = "abc123"

        mock_get_outputs.return_value = [tmp_path / "pr_changes.json"]

        # Act
        collect_pr_changes.run()

        # Assert
        output_json = tmp_path / "pr_changes.json"
        assert output_json.exists()
        output_json_content = output_json.read_text(encoding="utf-8")
        actual_pr_changes = PR_Changes.from_json(output_json_content)
        assert actual_pr_changes == PR_Changes(ci_system="JENKINS", target_branch="main", current_branch="feature-branch", commit_id="abc123", changed_files=["file1.py", "file2.py", "file3.txt"])

    @pytest.mark.parametrize(
        "stdout, expected_result",
        [
            ("file1.py\nfile2.py\nfile3.txt\n", ["file1.py", "file2.py", "file3.txt"]),
            ("", []),
            ("   \n\n  \n", []),  # Whitespace only
            ("  file1.py  \n\nfile2.py\n  \nfile3.txt  \n", ["file1.py", "file2.py", "file3.txt"]),  # Mixed whitespace
            ("src/module.py\ntests/test_module.py\n", ["src/module.py", "tests/test_module.py"]),
        ],
    )
    @patch("spl_core.steps.collect_pr_changes.SubprocessExecutor")
    def test_get_changed_files_success(self, mock_subprocess, collect_pr_changes, stdout, expected_result):
        """Test _get_changed_files returns list of files when git command succeeds."""
        # Arrange
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = stdout

        mock_subprocess_instance = MagicMock()
        mock_subprocess_instance.execute.return_value = mock_result
        mock_subprocess.return_value = mock_subprocess_instance

        # Act
        result = collect_pr_changes._get_changed_files("develop", "feature-branch")

        # Assert
        assert result == expected_result
        assert mock_subprocess.call_count == 3
        mock_subprocess.assert_any_call(["git", "fetch", "origin", "feature-branch"])
        mock_subprocess.assert_any_call(["git", "fetch", "origin", "develop"])
        mock_subprocess.assert_any_call(["git", "diff", "--name-only", "origin/develop...origin/feature-branch"])
        assert mock_subprocess_instance.execute.call_count == 3

    @patch("spl_core.steps.collect_pr_changes.SubprocessExecutor")
    def test_get_changed_files_git_command_failure(self, mock_subprocess, collect_pr_changes):
        """Test _get_changed_files returns empty list when git command fails."""
        # Arrange
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "fatal: bad revision 'origin/main'"

        mock_subprocess_instance = MagicMock()
        mock_subprocess_instance.execute.return_value = mock_result
        mock_subprocess.return_value = mock_subprocess_instance

        # Act
        result = collect_pr_changes._get_changed_files("main", "feature-branch")

        # Assert
        assert result == []

    @patch("spl_core.steps.collect_pr_changes.logger")
    @patch("spl_core.steps.collect_pr_changes.SubprocessExecutor")
    def test_get_changed_files_exception_handling(self, mock_subprocess, mock_logger, collect_pr_changes):
        """Test _get_changed_files handles exceptions and logs errors."""

        # Arrange
        exception_msg = "Git command failed"
        mock_subprocess_instance = MagicMock()

        def mock_subprocess_side_effect(*args, **kwargs):
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Everything fine"
            if mock_subprocess.call_count < 3:
                return mock_result
            else:
                raise Exception(exception_msg)

        mock_subprocess_instance.execute.side_effect = mock_subprocess_side_effect
        mock_subprocess.return_value = mock_subprocess_instance

        # Act
        result = collect_pr_changes._get_changed_files("main", "feature-branch")

        # Assert
        assert result == []
        assert mock_logger.warning.call_count == 4
        error_call_args = mock_logger.warning.call_args[0][0]
        assert "Git command failed" in error_call_args
        assert exception_msg in error_call_args
        assert mock_subprocess.call_count == 6
        mock_subprocess.assert_any_call(["git", "fetch", "origin", "feature-branch"])
        mock_subprocess.assert_any_call(["git", "fetch", "origin", "main"])
        mock_subprocess.assert_any_call(["git", "diff", "--name-only", "origin/main...origin/feature-branch"])
        mock_subprocess.assert_any_call(["git", "diff", "--name-only", "origin/main", "origin/feature-branch"])
        mock_subprocess.assert_any_call(["git", "diff", "--name-only", "main...feature-branch"])
        mock_subprocess.assert_any_call(["git", "diff", "--name-only", "main", "feature-branch"])

    @patch("spl_core.steps.collect_pr_changes.SubprocessExecutor")
    def test_get_changed_files_none_result(self, mock_subprocess, collect_pr_changes):
        """Test _get_changed_files handles None result from execute."""
        # Arrange
        mock_subprocess_instance = MagicMock()
        mock_subprocess_instance.execute.return_value = None
        mock_subprocess.return_value = mock_subprocess_instance

        # Act
        result = collect_pr_changes._get_changed_files("main", "feature-branch")

        # Assert
        assert result == []

    @patch("spl_core.steps.collect_pr_changes.SubprocessExecutor")
    def test_get_commit_id_with_ci_context(self, mock_subprocess, collect_pr_changes):
        """Test _get_commit_id returns commit ID when CI context is provided."""
        # Arrange
        ci_context = CIContext(ci_system=CISystem.JENKINS, current_branch="feature-branch", target_branch="main", is_pull_request=True)

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "abc123def456"

        mock_subprocess_instance = MagicMock()
        mock_subprocess_instance.execute.return_value = mock_result
        mock_subprocess.return_value = mock_subprocess_instance

        # Act
        result = collect_pr_changes._get_commit_id(ci_context)

        # Assert
        assert result == "abc123def456"
        mock_subprocess.assert_called_once_with(["git", "rev-parse", "origin/feature-branch"])
        mock_subprocess_instance.execute.assert_called_once_with(handle_errors=False)

    @patch("spl_core.steps.collect_pr_changes.SubprocessExecutor")
    def test_get_commit_id_without_ci_context(self, mock_subprocess, collect_pr_changes):
        """Test _get_commit_id returns commit ID when CI context is not provided inside the function call."""
        # Arrange
        ci_context = CIContext(ci_system=CISystem.JENKINS, current_branch="feature-branch", target_branch="main", is_pull_request=True)

        # Configure the mock execution context with data_registry
        mock_data_registry = MagicMock()
        mock_data_registry.find_data.return_value = [ci_context]
        collect_pr_changes.execution_context.data_registry = mock_data_registry

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "abc123def456"

        mock_subprocess_instance = MagicMock()
        mock_subprocess_instance.execute.return_value = mock_result
        mock_subprocess.return_value = mock_subprocess_instance

        # Act
        result = collect_pr_changes._get_commit_id()

        # Assert
        assert result == "abc123def456"
        mock_subprocess.assert_called_once_with(["git", "rev-parse", "origin/feature-branch"])
        mock_subprocess_instance.execute.assert_called_once_with(handle_errors=False)

    def test_get_commit_id_no_ci_context_found(self, collect_pr_changes):
        """Test _get_commit_id returns empty string when no CI context is found."""
        # Arrange
        mock_data_registry = MagicMock()
        mock_data_registry.find_data.return_value = []
        collect_pr_changes.execution_context.data_registry = mock_data_registry

        # Act
        result = collect_pr_changes._get_commit_id()

        # Assert
        assert result == ""
        mock_data_registry.find_data.assert_called_once()

    @patch("spl_core.steps.collect_pr_changes.SubprocessExecutor")
    def test_get_commit_id_not_pull_request(self, mock_subprocess, collect_pr_changes):
        """Test _get_commit_id returns empty string when not a pull request."""
        # Arrange
        ci_context = CIContext(ci_system=CISystem.JENKINS, current_branch="feature-branch", target_branch="main", is_pull_request=False)

        # Act
        result = collect_pr_changes._get_commit_id(ci_context)

        # Assert
        assert result == ""
        mock_subprocess.assert_not_called()

    @patch("spl_core.steps.collect_pr_changes.SubprocessExecutor")
    def test_get_commit_id_git_command_failure(self, mock_subprocess, collect_pr_changes):
        """Test _get_commit_id returns empty string when git command fails."""
        # Arrange
        ci_context = CIContext(ci_system=CISystem.JENKINS, current_branch="feature-branch", target_branch="main", is_pull_request=True)

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "fatal: ambiguous argument"

        mock_subprocess_instance = MagicMock()
        mock_subprocess_instance.execute.return_value = mock_result
        mock_subprocess.return_value = mock_subprocess_instance

        # Act
        result = collect_pr_changes._get_commit_id(ci_context)

        # Assert
        assert result == ""
        mock_subprocess.assert_called_once_with(["git", "rev-parse", "origin/feature-branch"])

    @patch("spl_core.steps.collect_pr_changes.SubprocessExecutor")
    def test_get_commit_id_exception_handling(self, mock_subprocess, collect_pr_changes):
        """Test _get_commit_id handles exceptions gracefully."""
        # Arrange
        ci_context = CIContext(ci_system=CISystem.JENKINS, current_branch="feature-branch", target_branch="main", is_pull_request=True)

        mock_subprocess_instance = MagicMock()
        mock_subprocess_instance.execute.side_effect = Exception("Git not found")
        mock_subprocess.return_value = mock_subprocess_instance

        # Act
        result = collect_pr_changes._get_commit_id(ci_context)

        # Assert
        assert result == ""
        mock_subprocess.assert_called_once_with(["git", "rev-parse", "origin/feature-branch"])
