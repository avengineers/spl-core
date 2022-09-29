import dataclasses
import os
import shutil
import subprocess
from pathlib import Path


@dataclasses.dataclass
class TestDir:
    path: Path

    def write_file(self, content: str, name: str) -> Path:
        file = self.path.joinpath(name)
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content)
        return file

    def joinpath(self, path: str) -> Path:
        return self.path.joinpath(path)

    def __str__(self):
        return f"{self.path}"


class TestUtils:
    DEFAULT_TEST_DIR = 'tmp_test'

    @staticmethod
    def create_clean_test_dir(name: str = None) -> TestDir:
        out_dir = TestUtils.project_root_dir().joinpath('out')
        test_dir = out_dir.joinpath(name if name else TestUtils.DEFAULT_TEST_DIR).absolute()
        if test_dir.exists():
            # rmtree throws an exception if any of the files to be deleted is read-only
            if os.name == 'nt':
                rm_dir_cmd = f"cmd /c rmdir /S /Q {test_dir}"
                print(f"Execute: {rm_dir_cmd}")
                subprocess.call(rm_dir_cmd)
            else:
                shutil.rmtree(test_dir)
        test_dir.mkdir(parents=True, exist_ok=True)
        print(f"New clean test directory created: {test_dir}")
        return TestDir(test_dir)

    @staticmethod
    def project_root_dir() -> Path:
        return Path(__file__).parent.parent.absolute()
