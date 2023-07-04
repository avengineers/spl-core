from project_creator.variant import Variant
from utils import TestUtils, TestWorkspace, ExecutionTime
import subprocess
import xml.etree.ElementTree as ET
from os import makedirs


class TestIntegration:
    @classmethod
    def setup_class(cls):
        # create a new test workspace
        cls.workspace: TestWorkspace = TestWorkspace("test_integration")

    def test_build_prod(self):
        # create build output directory for build_kit "prod"
        build_dir_prod = self.workspace.workspace_artifacts.get_build_dir("Flv1/Sys1", "prod")
        makedirs(build_dir_prod, exist_ok=False)

        "Call IUT"
        with ExecutionTime("CMake Configure (build_kit: prod)"):
            assert 0 == self.workspace.run_cmake_configure(build_kit="prod").returncode

        "Expected configuration output"
        assert build_dir_prod.joinpath("kconfig/autoconf.h").exists()
        assert build_dir_prod.joinpath("build.ninja").exists()

        "Call IUT"
        with ExecutionTime("CMake Build (build_kit: prod, target=all)"):
            assert 0 == self.workspace.run_cmake_build(build_kit="prod", target="all").returncode

        "Expected build results for kit prod shall exist"
        executable = build_dir_prod.joinpath("my_main.exe")
        assert executable.exists()
        my_main_result = subprocess.run([executable], capture_output=True)
        assert 7 == my_main_result.returncode
        assert "Main program calculating ..." == my_main_result.stdout.decode("utf-8").strip()

        "touch a *.c file to simulate a single file change"
        self.workspace.get_component_file("main", "src/main.c").touch()
        "store workspace status - all files with timestamps"
        self.workspace.take_files_snapshot()

        "Call IUT"
        with ExecutionTime("CMake (build_kit: prod, target=link)"):
            assert self.workspace.run_cmake_build(build_kit="prod", target="link").returncode == 0

        "only one object is recompiled and the binary is linked again"
        workspace_status = self.workspace.get_workspace_files_status()
        assert set(workspace_status.changed_files_names) == {".ninja_deps", ".ninja_log", "main.c.obj", "my_main.exe"}
        assert len(workspace_status.deleted_files) == 0
        assert len(workspace_status.new_files) == 0

        "reset files status before running the link again"
        self.workspace.take_files_snapshot()

        "Call IUT"
        with ExecutionTime("CMake (build_kit: prod, target=link)"):
            assert self.workspace.run_cmake_build(build_kit="prod", target="link").returncode == 0

        "No files were touched, so nothing was compiled again"
        workspace_status = self.workspace.get_workspace_files_status()
        assert len(workspace_status.changed_files_names) == 0
        assert len(workspace_status.deleted_files) == 0
        assert len(workspace_status.new_files) == 0

    def test_build_test(self):
        # create build output directory for build_kit "test"
        build_dir_test = self.workspace.workspace_artifacts.get_build_dir("Flv1/Sys1", "test")
        makedirs(build_dir_test, exist_ok=False)

        "Call IUT"
        with ExecutionTime("CMake Configure (build_kit: test, target=all)"):
            assert 0 == self.workspace.run_cmake_configure(build_kit="test").returncode

        "Expected configuration output"
        assert build_dir_test.joinpath("kconfig/autoconf.h").exists()
        assert build_dir_test.joinpath("build.ninja").exists()

        "Call IUT"
        with ExecutionTime("CMake (build_kit: test, target=unittests)"):
            assert 0 == self.workspace.run_cmake_build(build_kit="test", target="unittests").returncode

        "Expected test results for kit test shall exist"
        junitxml = build_dir_test.joinpath("components/component/junit.xml")
        assert junitxml.exists()
        testsuite = ET.parse(junitxml).getroot()
        assert 1 == int(testsuite.attrib["tests"])
        assert 0 == int(testsuite.attrib["failures"])
        first_test_case = testsuite.find("testcase")
        assert "component.test_someInterfaceOfComponent" == first_test_case.attrib["name"]
        assert "run" == first_test_case.attrib["status"]

        "Simulate a configuration change"
        self.workspace.workspace_artifacts.kconfig_model_file.touch()
        "store workspace status - all files with timestamps"
        self.workspace.take_files_snapshot()

        "Call IUT"
        with ExecutionTime("CMake (build_kit: test, target=unittests)"):
            assert 0 == self.workspace.run_cmake_build(build_kit="test", target="unittests").returncode

        "Configuration output shall be recreated"
        workspace_status = self.workspace.get_workspace_files_status()
        assert {"autoconf.h", "autoconf.json", "autoconf.cmake"}.issubset(workspace_status.changed_files_names)
        assert len(workspace_status.deleted_files) == 0
        assert len(workspace_status.new_files) == 0

        "store workspace status - all files with timestamps"
        self.workspace.take_files_snapshot()

        "Call IUT"
        with ExecutionTime("CMake (build_kit: test, target=unittests)"):
            assert 0 == self.workspace.run_cmake_build(build_kit="test", target="unittests").returncode

        "Configuration output shall not have been recreated"
        workspace_status = self.workspace.get_workspace_files_status()
        assert len(workspace_status.changed_files_names) == 0
        assert len(workspace_status.deleted_files) == 0
        assert len(workspace_status.new_files) == 0

        "Simulate a configuration change"
        self.workspace.workspace_artifacts.get_kconfig_config_file(Variant.from_string("Flv1/Sys1")).touch()
        "store workspace status - all files with timestamps"
        self.workspace.take_files_snapshot()

        "Call IUT"
        with ExecutionTime("CMake (build_kit: test, target=unittests)"):
            assert 0 == self.workspace.run_cmake_build(build_kit="test", target="unittests").returncode

        "Configuration output shall be recreated"
        workspace_status = self.workspace.get_workspace_files_status()
        assert {"autoconf.h", "autoconf.json", "autoconf.cmake"}.issubset(workspace_status.changed_files_names)
        assert len(workspace_status.deleted_files) == 0
        assert len(workspace_status.new_files) == 0

    def test_build_selftests(self):
        "Call IUT"
        with ExecutionTime("Build Wrapper (target: selftests)"):
            assert 0 == self.workspace.selftests().returncode
