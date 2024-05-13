import locale
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional


class CommandLineExecutor:
    def __init__(
        self,
        cwd: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None,
    ):
        """
        A class for executing command line commands.

        Args:
        - cmd: A string or list of strings representing the command to be executed.
        - cwd: An optional Path object representing the current working directory.
        - env: An optional dictionary of environment variables to be used in the command execution.
        """
        self.current_working_directory = cwd
        self.env = env

    def execute(self, cmd: str | List[str]) -> subprocess.CompletedProcess[str]:
        """
        Executes the command and returns a CompletedProcess object.

        Returns:
        - A subprocess.CompletedProcess object representing the result of the command execution.
        """
        command = " ".join([cmd] if isinstance(cmd, str) else cmd)
        output = ""
        try:
            print("=" * 120)
            print(f"= Running command: {command}")
            print("=" * 120)
            with subprocess.Popen(
                command,
                cwd=str(self.current_working_directory or Path.cwd()),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                text=True,
                env=self.env,
                universal_newlines=True,
                encoding="cp850" if (locale.getlocale()[0] == "de_DE" and sys.platform == "win32") else "utf-8",
            ) as process:
                if process.stdout:
                    for line in process.stdout:
                        print(line, end="")
                        # We have to store the stdout content.
                        # This is necessary because the stdout object is closed after we printed its content
                        output += line
        except Exception:
            raise RuntimeError(f"Command '{command}' failed.")  # noqa: B904
        return subprocess.CompletedProcess(args=command, returncode=process.returncode, stdout=output, stderr=None)
