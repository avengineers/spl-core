from tests.utils import TestWorkspace, ExecutionTime
import subprocess
import xml.etree.ElementTree as ET


class TestIntegration:
    def test_incremental_build(self):
        # create a new test workspace
        workspace = TestWorkspace("test_incremental_build")

        "Call IUT: call selftests without dependency installation (build.bat -install)"
        with ExecutionTime("build and run unit tests"):
            assert workspace.selftests().returncode == 0

        "Expected build results for kit prod shall exist"
        executable = workspace.workspace_artifacts.get_build_dir("Flv1/Sys1", "prod").joinpath("my_main.exe")
        assert executable.exists()
        my_main_result = subprocess.run([executable], capture_output=True)
        assert 7 == my_main_result.returncode
        assert "Main program calculating ..." == my_main_result.stdout.decode("utf-8").strip()

        "Expected test results for kit test shall exist"
        junitxml = workspace.workspace_artifacts.get_build_dir("Flv1/Sys2", "test").joinpath("components/component/junit.xml")
        assert junitxml.exists()
        testsuite = ET.parse(junitxml).getroot()
        assert 1 == int(testsuite.attrib["tests"])
        assert 0 == int(testsuite.attrib["failures"])
        first_test_case = testsuite.find("testcase")
        assert "component.test_someInterfaceOfComponent" == first_test_case.attrib["name"]
        assert "run" == first_test_case.attrib["status"]

        "store workspace status - all files with timestamps"
        workspace.take_files_snapshot()
        "touch a *.c file to simulate a single file change"
        workspace.get_component_file("main", "src/main.c").touch()

        "Call IUT: call link target only"
        with ExecutionTime("Run CMake: link"):
            assert workspace.run_cmake(target="link").returncode == 0

        "only one object is recompiled and the binary is linked again"
        workspace_status = workspace.get_workspace_files_status()
        assert set(workspace_status.changed_files_names) == {".ninja_deps", ".ninja_log", "main.c", "main.c.obj", "my_main.exe"}
        assert len(workspace_status.deleted_files) == 0
        assert len(workspace_status.new_files) == 0

        "reset files status before running the link again"
        workspace.take_files_snapshot()

        "Call IUT: call link target only"
        with ExecutionTime("Run CMake 'link' with no changes"):
            assert workspace.run_cmake(target="link").returncode == 0

        "No files were touched, so nothing was compiled again"
        workspace_status = workspace.get_workspace_files_status()
        assert len(workspace_status.changed_files_names) == 0
        assert len(workspace_status.deleted_files) == 0
        assert len(workspace_status.new_files) == 0
