import subprocess

from tests.utils import TestDir, TestUtils


class TestCmake:
    test_workspace: TestDir

    @classmethod
    def setup_class(cls):
        # create a new test workspace
        cls.test_workspace = TestUtils.create_clean_test_dir("test_cmake")

    def run_cmake_unit_test(self, unit_test: str) -> int:
        """
        CMake unit test runner

        Args:
        ----
            unit_test (str): a sub directory in tests containing a CMakeLists.txt
            with unit tests inside.

        Returns:
        -------
            int: exit (return) code of the cmake command

        """
        unit_test_command = f"cmake -S tests\\cmake\\{unit_test} -B {self.test_workspace}\\{unit_test} -G Ninja --log-level=DEBUG"
        print(f"Execute: {unit_test_command}")
        return subprocess.run(unit_test_command).returncode

    def test_cmake_common_cmake(self):
        assert 0 == self.run_cmake_unit_test("common.cmake")

    def test_cmake_spl_cmake(self):
        assert 0 == self.run_cmake_unit_test("spl.cmake")
