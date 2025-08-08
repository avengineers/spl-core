import os
import tempfile
from pathlib import Path

import pytest

from spl_core.common.command_line_executor import CommandLineExecutor


class TestCommandLineExecuter:
    @pytest.mark.parametrize(
        "command, exp_stdout, exp_stderr, exp_returncode",
        [
            (["python", "-c", "\"print('Hello World!')\""], "Hello World!\n", None, 0),
            # There is never a STDERR, CommandLineExecutor redirects it to STDOUT
            (
                [
                    "python",
                    "-c",
                    "\"import sys; print('Hello World!', file=sys.stderr)\"",
                ],
                "Hello World!\n",
                None,
                0,
            ),
            (["python", "-c", "exit(0)"], "", None, 0),
            (["python", "-c", "exit(1)"], "", None, 1),
            (["python", "-c", "exit(42)"], "", None, 42),
        ],
    )
    def test_CommandLineExecuter(self, command, exp_stdout, exp_stderr, exp_returncode):
        # Arrange
        executor = CommandLineExecutor()

        # Act
        result = executor.execute(command)

        # Assert
        assert result.stdout == exp_stdout
        assert result.stderr == exp_stderr
        assert result.returncode == exp_returncode

    def test_CommandLineExecuter_exception(self, tmp_path: Path) -> None:
        # Arrange
        test_path = tmp_path.joinpath("test")
        test_path.mkdir()
        link_path = test_path.joinpath("link")
        command = ["cmd", "/c", "mklink", "/J", str(link_path), str(test_path)]
        executor = CommandLineExecutor()

        # Act
        result = executor.execute(command)

        # Assert
        assert result.returncode == 0

    def test_CommandLineExecuter_undecodable_stdout(self) -> None:
        """Test that undecodable bytes in stdout are handled gracefully."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as tmp:
            # Write bytes that are invalid in UTF-8 (e.g., 0x85)
            tmp.write(b"Hello\x85World\n")
            tmp_path = tmp.name

        try:
            py_cmd = ["python", "-c", f"\"import sys; sys.stdout.buffer.write(open(r'{tmp_path}', 'rb').read())\""]
            executor = CommandLineExecutor()

            # Act
            result = executor.execute(py_cmd)

            # Assert
            assert "Hello" in result.stdout
            assert "World" in result.stdout
            # Should not raise UnicodeDecodeError
            assert result.returncode == 0
        finally:
            os.remove(tmp_path)

    def test_CommandLineExecuter_undecodable_stderr(self) -> None:
        """Test that undecodable bytes in stderr (redirected to stdout) are handled gracefully."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as tmp:
            # Write bytes that are invalid in UTF-8 (e.g., 0x85)
            tmp.write(b"Error\x85Message\n")
            tmp_path = tmp.name

        try:
            py_cmd = ["python", "-c", f"\"import sys; sys.stderr.buffer.write(open(r'{tmp_path}', 'rb').read())\""]
            executor = CommandLineExecutor()

            # Act
            result = executor.execute(py_cmd)

            # Assert
            assert "Error" in result.stdout
            assert "Message" in result.stdout
            # Should not raise UnicodeDecodeError
            assert result.returncode == 0
        finally:
            os.remove(tmp_path)
