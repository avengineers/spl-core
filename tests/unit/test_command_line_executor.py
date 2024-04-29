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
