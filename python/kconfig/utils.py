import dataclasses
import shutil
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


class TestUtils:
    DEFAULT_TEST_DIR = 'tmp_test'

    @staticmethod
    def create_clean_test_dir(name: str) -> TestDir:
        out_dir = Path(__file__).joinpath('../../out').resolve(False)
        test_dir = out_dir.joinpath(name if name else TestUtils.DEFAULT_TEST_DIR).absolute()
        if test_dir.exists():
            shutil.rmtree(test_dir)
        test_dir.mkdir(parents=True, exist_ok=True)
        print(f"New clean test directory created: {test_dir}")
        return TestDir(test_dir)
