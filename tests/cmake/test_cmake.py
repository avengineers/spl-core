import subprocess
from pathlib import Path

from tests.utils import TestDir, create_clean_test_dir


class TestCmake:
    test_workspace: TestDir

    @classmethod
    def setup_class(cls):
        # create a new test workspace
        cls.test_workspace = create_clean_test_dir("test_cmake")

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

        # check if the build.json file was created
        assert Path(f"{self.test_workspace}/common.cmake/build.json").exists()

        # check if the build.json file has the correct content
        script_dir = Path(__file__).parent.resolve().as_posix()
        assert (
            Path(f"{self.test_workspace}/common.cmake/build.json").read_text()
            == f"""{{
    "components":[
        {{
            "name": "component",
            "long_name": "",
            "path": "{script_dir}/common.cmake/component",
            "sources": [
                "{script_dir}/common.cmake/component/src/some_file.c",
                "{script_dir}/common.cmake/component/src/some_other_file.c"
            ],
            "test_sources": []
        }},
        {{
            "name": "some_other_component",
            "long_name": "Some amazing other component with a long name",
            "path": "{script_dir}/common.cmake/some_other_component",
            "sources": [
                "{script_dir}/common.cmake/some_other_component/src/some_file.c",
                "{script_dir}/common.cmake/some_other_component/src/some_other_file.c"
            ],
            "test_sources": [
                "{script_dir}/common.cmake/some_other_component/test/some_test_file.cc",
                "{script_dir}/common.cmake/some_other_component/test/some_other_test_file.cc"
            ]
        }},
        {{
            "name": "some_external_component",
            "long_name": "",
            "path": "{script_dir}/common.cmake/external_package/some_external_component",
            "sources": [
                "{script_dir}/common.cmake/external_package/some_external_component/src/some_file.c",
                "{script_dir}/common.cmake/external_package/some_external_component/src/some_other_file.c"
            ],
            "test_sources": []
        }}
    ]
}}"""
        )

    def test_cmake_spl_cmake(self):
        assert 0 == self.run_cmake_unit_test("spl.cmake")
