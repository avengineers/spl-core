import textwrap
from project_creator.variant import Variant
from utils import TestWorkspace, ExecutionTime
import subprocess
import xml.etree.ElementTree as ET
from os import makedirs


def test_build_prod():
    # create build output directory for build_kit "prod"
    workspace = TestWorkspace("test_build_prod")
    build_dir_prod = workspace.workspace_artifacts.get_build_dir("Flv1/Sys1", "prod")
    makedirs(build_dir_prod, exist_ok=False)

    "Call IUT"
    with ExecutionTime("CMake Configure (build_kit: prod)"):
        assert 0 == workspace.run_cmake_configure(build_kit="prod").returncode

    "Expected configuration output"
    assert build_dir_prod.joinpath("kconfig/autoconf.h").exists()
    assert build_dir_prod.joinpath("build.ninja").exists()

    "Call IUT"
    with ExecutionTime("CMake Build (build_kit: prod, target=all)"):
        assert 0 == workspace.run_cmake_build(build_kit="prod", target="all").returncode

    "Expected build results for kit prod shall exist"
    executable = build_dir_prod.joinpath("my_main.exe")
    assert executable.exists()
    my_main_result = subprocess.run([executable], capture_output=True)
    assert 7 == my_main_result.returncode
    assert "Main program calculating ..." == my_main_result.stdout.decode("utf-8").strip()

    "touch a *.c file to simulate a single file change"
    workspace.get_component_file("main", "src/main.c").touch()
    "store workspace status - all files with timestamps"
    workspace.take_files_snapshot()

    "Call IUT"
    with ExecutionTime("CMake (build_kit: prod, target=link)"):
        assert workspace.run_cmake_build(build_kit="prod", target="link").returncode == 0

    "only one object is recompiled and the binary is linked again"
    workspace_status = workspace.get_workspace_files_status()
    assert set(workspace_status.changed_files_names) == {".ninja_deps", ".ninja_log", "main.c.obj", "my_main.exe"}
    assert len(workspace_status.deleted_files) == 0
    assert len(workspace_status.new_files) == 0

    "reset files status before running the link again"
    workspace.take_files_snapshot()

    "Call IUT"
    with ExecutionTime("CMake (build_kit: prod, target=link)"):
        assert workspace.run_cmake_build(build_kit="prod", target="link").returncode == 0

    "No files were touched, so nothing was compiled again"
    workspace_status = workspace.get_workspace_files_status()
    assert len(workspace_status.changed_files_names) == 0
    assert len(workspace_status.deleted_files) == 0
    assert len(workspace_status.new_files) == 0


def test_build_test():
    # create build output directory for build_kit "test"
    workspace = TestWorkspace("test_build_test")
    build_dir_test = workspace.workspace_artifacts.get_build_dir("Flv1/Sys1", "test")
    makedirs(build_dir_test, exist_ok=False)

    "Call IUT"
    with ExecutionTime("CMake Configure (build_kit: test)"):
        assert 0 == workspace.run_cmake_configure(build_kit="test").returncode

    "Expected configuration output"
    assert build_dir_test.joinpath("kconfig/autoconf.h").exists()
    assert build_dir_test.joinpath("build.ninja").exists()

    "Call IUT"
    with ExecutionTime("CMake (build_kit: test, target=unittests)"):
        assert 0 == workspace.run_cmake_build(build_kit="test", target="unittests").returncode

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
    kconfig_file = workspace.workspace_artifacts.kconfig_model_file
    content = kconfig_file.read_text()
    kconfig_file.write_text(content.replace('default "map"', 'default "mdf"'))
    "store workspace status - all files with timestamps"
    workspace.take_files_snapshot()

    "Call IUT"
    with ExecutionTime("CMake (build_kit: test, target=unittests)"):
        assert 0 == workspace.run_cmake_build(build_kit="test", target="unittests").returncode

    "Configuration output shall be recreated"
    workspace_status = workspace.get_workspace_files_status()
    assert {"autoconf.h", "autoconf.json", "autoconf.cmake"}.issubset(workspace_status.changed_files_names)
    assert len(workspace_status.deleted_files) == 0
    assert len(workspace_status.new_files) == 0

    "store workspace status - all files with timestamps"
    workspace.take_files_snapshot()

    "Call IUT"
    with ExecutionTime("CMake (build_kit: test, target=unittests)"):
        assert 0 == workspace.run_cmake_build(build_kit="test", target="unittests").returncode

    "Configuration output shall not have been recreated"
    workspace_status = workspace.get_workspace_files_status()
    assert len(workspace_status.changed_files_names) == 0
    assert len(workspace_status.deleted_files) == 0
    assert len(workspace_status.new_files) == 0

    "Simulate a configuration change"
    variant_config_file = workspace.workspace_artifacts.get_kconfig_config_file(Variant.from_string("Flv1/Sys1"))
    content = variant_config_file.read_text()
    variant_config_file.write_text(content.replace("CONFIG_USE_COMPONENT=y", "CONFIG_USE_COMPONENT=n"))
    "store workspace status - all files with timestamps"
    workspace.take_files_snapshot()

    "Call IUT"
    with ExecutionTime("CMake (build_kit: test, target=unittests)"):
        assert 0 == workspace.run_cmake_build(build_kit="test", target="unittests").returncode

    "Configuration output shall be recreated"
    workspace_status = workspace.get_workspace_files_status()
    assert {"autoconf.h", "autoconf.json", "autoconf.cmake"}.issubset(workspace_status.changed_files_names)
    assert len(workspace_status.deleted_files) == 0
    assert len(workspace_status.new_files) == 0


def test_build_selftests():
    with ExecutionTime("Build Wrapper (target: selftests)"):
        assert 0 == TestWorkspace("test_build_selftests").selftests().returncode


def test_build_modified_file_compile_options():
    # create build output directory for build_kit "prod"
    workspace = TestWorkspace("test_build_modified_file_compile_options")
    build_dir_prod = workspace.workspace_artifacts.get_build_dir("Flv1/Sys1", "prod")
    makedirs(build_dir_prod, exist_ok=True)

    "Modify compile options of a single file"
    workspace.get_component_file("component", "parts.cmake").write_text(
        textwrap.dedent(
            """
            spl_add_source(src/component.c COMPILE_OPTIONS "-DTHE_ANSWER=42")

            spl_add_test_source(test/test_component.cc)
            """
        )
    )

    "Call IUT"
    with ExecutionTime("CMake Configure and Build (build_kit: prod, target: all)"):
        assert 0 == workspace.run_cmake_configure(build_kit="prod").returncode
        assert 0 == workspace.run_cmake_build(build_kit="prod", target="all").returncode

    "Expected build results shall exist"
    executable = build_dir_prod.joinpath("my_main.exe")
    assert executable.exists()
    my_main_result = subprocess.run([executable])
    assert 42 == my_main_result.returncode

    "Modify compile options again"
    workspace.get_component_file("component", "parts.cmake").write_text(
        textwrap.dedent(
            """
            spl_add_source(src/component.c COMPILE_OPTIONS "-DTHE_ANSWER=42" "-DTHE_OFFSET=3")

            spl_add_test_source(test/test_component.cc)
            """
        )
    )

    "Call IUT, CMake shall reconfigure automatically"
    with ExecutionTime("CMake Build (build_kit: prod, target=all)"):
        assert 0 == workspace.run_cmake_build(build_kit="prod", target="all").returncode

    "Expected build results shall exist"
    executable = build_dir_prod.joinpath("my_main.exe")
    assert executable.exists()
    my_main_result = subprocess.run([executable])
    assert 45 == my_main_result.returncode

    "Modify compile options again"
    workspace.get_component_file("component", "parts.cmake").write_text(
        textwrap.dedent(
            """
            spl_add_source(src/component.c COMPILE_OPTIONS "-DTHE_OFFSET=3")

            spl_add_test_source(test/test_component.cc)
            """
        )
    )

    "Call IUT, CMake shall reconfigure automatically"
    with ExecutionTime("CMake Build (build_kit: prod, target=all)"):
        assert 0 == workspace.run_cmake_build(build_kit="prod", target="all").returncode

    "Expected build results shall exist"
    executable = build_dir_prod.joinpath("my_main.exe")
    assert executable.exists()
    my_main_result = subprocess.run([executable])
    assert 10 == my_main_result.returncode

    # create build output directory for build_kit "test"
    build_dir_test = workspace.workspace_artifacts.get_build_dir("Flv1/Sys1", "test")
    makedirs(build_dir_test, exist_ok=True)

    "Call IUT"
    with ExecutionTime("CMake Configure and Build (build_kit: test, target: unittests)"):
        assert 0 == workspace.run_cmake_configure(build_kit="test").returncode
        assert 1 == workspace.run_cmake_build(build_kit="test", target="unittests").returncode

    "Expected test results for kit test shall exist"
    junitxml = build_dir_test.joinpath("components/component/junit.xml")
    assert junitxml.exists()
    testsuite = ET.parse(junitxml).getroot()
    assert 1 == int(testsuite.attrib["tests"])
    assert 1 == int(testsuite.attrib["failures"])
    first_test_case = testsuite.find("testcase")
    assert "component.test_someInterfaceOfComponent" == first_test_case.attrib["name"]
    assert "fail" == first_test_case.attrib["status"]
