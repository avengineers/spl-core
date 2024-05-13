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
        result = CommandLineExecutor().execute(command)
        assert result.stdout == exp_stdout
        assert result.stderr == exp_stderr
        assert result.returncode == exp_returncode

    def test_CommandLineExecuter_exception(self, tmp_path: Path) -> None:
        test_path = tmp_path.joinpath("test")
        test_path.mkdir()
        link_path = test_path.joinpath("link")
        result = CommandLineExecutor().execute(["cmd", "/c", "mklink", "/J", str(link_path), str(test_path)])
        assert result.returncode == 0
