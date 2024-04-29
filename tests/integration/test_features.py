import subprocess
import textwrap
import xml.etree.ElementTree as ET
from os import makedirs

import pytest
from utils import ExecutionTime, IntegrationTestsSplProject

from spl_core.project_creator.variant import Variant


@pytest.mark.skip(reason="Still need to be refactor to use the Kickstart module because the ProjectCreator is obsolete.")
class TestSplFeatures:
    workspace: IntegrationTestsSplProject

    @classmethod
    def setup_class(cls):
        # create a new test workspace
        cls.workspace = IntegrationTestsSplProject("test_spl_features")

    def test_unittests(self):
        # create build output directory for build_kit "test"
        build_dir_test = self.workspace.workspace_artifacts.get_build_dir("Variant1", "test")
        makedirs(build_dir_test, exist_ok=False)

        "Call IUT - clean build"
        with ExecutionTime("CMake Configure (build_kit: test)"):
            assert 0 == self.workspace.run_cmake_configure(build_kit="test").returncode

        "Expected configuration output"
        assert build_dir_test.joinpath("kconfig/autoconf.h").exists()
        assert build_dir_test.joinpath("build.ninja").exists()

        "Call IUT - incremental build"
        with ExecutionTime("CMake (build_kit: test, target=unittests)"):
            assert 0 == self.workspace.run_cmake_build(build_kit="test", target="unittests").returncode

        "Expected test results for kit test shall exist"
        assert build_dir_test.joinpath("components/component/reports/coverage/index.html").exists()
        junitxml = build_dir_test.joinpath("components/component/junit.xml")
        assert junitxml.exists()
        testsuite = ET.parse(junitxml).getroot()  # noqa: S314
        assert 2 == int(testsuite.attrib["tests"])
        assert 0 == int(testsuite.attrib["failures"])
        first_test_case = testsuite.find("testcase")
        if first_test_case is not None:
            assert "component.test_someInterfaceOfComponent" == first_test_case.attrib["name"]
            assert "run" == first_test_case.attrib["status"]
        else:
            raise AssertionError("No test case found in junit.xml")

        "Simulate a gcno leftover from a previous build"
        gcno_file = build_dir_test.joinpath("components/component/CMakeFiles/components_component.dir/src/source_does_not_exist.c.gcno")
        gcno_file.touch()

        "Simulate a single file change"
        self.workspace.get_component_file("component", "src/component.c").touch()

        "Call IUT - incremental build"
        with ExecutionTime("CMake (build_kit: test, target=unittests)"):
            assert 0 == self.workspace.run_cmake_build(build_kit="test", target="unittests").returncode

        # Obsolete gcno file shall be deleted
        assert not gcno_file.exists()

        "Simulate a configuration change"
        kconfig_model_file = self.workspace.workspace_artifacts.kconfig_model_file
        content = kconfig_model_file.read_text()
        kconfig_model_file.write_text(content.replace('default "map"', 'default "mdf"'))
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
        variant_config_file = self.workspace.workspace_artifacts.get_kconfig_config_file(Variant.from_string("Variant1"))
        content = variant_config_file.read_text()
        variant_config_file.write_text(content.replace("CONFIG_USE_COMPONENT=y", "CONFIG_USE_COMPONENT=n"))
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

        "Revert configuration changes"
        kconfig_model_file = self.workspace.workspace_artifacts.kconfig_model_file
        content = kconfig_model_file.read_text()
        kconfig_model_file.write_text(content.replace('default "mdf"', 'default "map"'))
        variant_config_file = self.workspace.workspace_artifacts.get_kconfig_config_file(Variant.from_string("Variant1"))
        content = variant_config_file.read_text()
        variant_config_file.write_text(content.replace("CONFIG_USE_COMPONENT=n", "CONFIG_USE_COMPONENT=y"))
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

    def test_build_modified_file_compile_options(self):
        # create build output directory for build_kit "prod"
        build_dir_prod = self.workspace.workspace_artifacts.get_build_dir("Variant1", "prod")
        makedirs(build_dir_prod, exist_ok=True)

        "Modify compile options of a single file"
        self.workspace.get_component_file("component", "CMakeLists.txt").write_text(
            textwrap.dedent(
                """
                spl_add_source(src/component.c COMPILE_OPTIONS "-DTHE_ANSWER=42")

                spl_add_test_source(test/test_component.cc)

                spl_create_component()
                """
            )
        )

        "Call IUT"
        with ExecutionTime("CMake Configure and Build (build_kit: prod, target: all)"):
            assert 0 == self.workspace.run_cmake_configure(build_kit="prod").returncode
            assert 0 == self.workspace.run_cmake_build(build_kit="prod", target="all").returncode

        "Expected build results shall exist"
        executable = build_dir_prod.joinpath("my_main.exe")
        assert executable.exists()
        my_main_result = subprocess.run([executable])
        assert 42 == my_main_result.returncode

        "Modify compile options again"
        self.workspace.get_component_file("component", "CMakeLists.txt").write_text(
            textwrap.dedent(
                """
                spl_add_source(src/component.c COMPILE_OPTIONS "-DTHE_ANSWER=42" "-DTHE_OFFSET=3")

                spl_add_test_source(test/test_component.cc)

                spl_create_component()
                """
            )
        )

        "Call IUT, CMake shall reconfigure automatically"
        with ExecutionTime("CMake Build (build_kit: prod, target=all)"):
            assert 0 == self.workspace.run_cmake_build(build_kit="prod", target="all").returncode

        "Expected build results shall exist"
        executable = build_dir_prod.joinpath("my_main.exe")
        assert executable.exists()
        my_main_result = subprocess.run([executable])
        assert 45 == my_main_result.returncode

        "Modify compile options again"
        self.workspace.get_component_file("component", "CMakeLists.txt").write_text(
            textwrap.dedent(
                """
                spl_add_source(src/component.c COMPILE_OPTIONS "-DTHE_OFFSET=3")

                spl_add_test_source(test/test_component.cc)

                spl_create_component()
                """
            )
        )

        "Call IUT, CMake shall reconfigure automatically"
        with ExecutionTime("CMake Build (build_kit: prod, target=all)"):
            assert 0 == self.workspace.run_cmake_build(build_kit="prod", target="all").returncode

        "Expected build results shall exist"
        executable = build_dir_prod.joinpath("my_main.exe")
        assert executable.exists()
        my_main_result = subprocess.run([executable])
        assert 10 == my_main_result.returncode

        "Modify compile options of a single file using spl_add_compile_options"
        self.workspace.get_component_file("component", "CMakeLists.txt").write_text(
            textwrap.dedent(
                """
                spl_add_source(src/component.c)
                spl_add_compile_options("src/*.c" COMPILE_OPTIONS "-DTHE_ANSWER=8")
                spl_add_test_source(test/test_component.cc)
                spl_create_component()
                """
            )
        )

        "Call IUT"
        with ExecutionTime("CMake Configure and Build (build_kit: prod, target: all)"):
            assert 0 == self.workspace.run_cmake_configure(build_kit="prod").returncode
            assert 0 == self.workspace.run_cmake_build(build_kit="prod", target="all").returncode

        "Expected build results shall exist"
        executable = build_dir_prod.joinpath("my_main.exe")
        assert executable.exists()
        my_main_result = subprocess.run([executable])
        assert 8 == my_main_result.returncode

        "Modify compile options of a single file using spl_add_compile_options"
        self.workspace.get_component_file("component", "CMakeLists.txt").write_text(
            textwrap.dedent(
                """
                spl_add_source(src/component.c)
                spl_add_compile_options("src/component.c" COMPILE_OPTIONS "-DTHE_ANSWER=65" "-DTHE_OFFSET=3")
                spl_add_test_source(test/test_component.cc)
                spl_create_component()
                """
            )
        )

        "Call IUT"
        with ExecutionTime("CMake Configure and Build (build_kit: prod, target: all)"):
            assert 0 == self.workspace.run_cmake_configure(build_kit="prod").returncode
            assert 0 == self.workspace.run_cmake_build(build_kit="prod", target="all").returncode

        "Expected build results shall exist"
        executable = build_dir_prod.joinpath("my_main.exe")
        assert executable.exists()
        my_main_result = subprocess.run([executable])
        assert 68 == my_main_result.returncode

        # create build output directory for build_kit "test"
        build_dir_test = self.workspace.workspace_artifacts.get_build_dir("Variant1", "test")
        makedirs(build_dir_test, exist_ok=True)

        "Call IUT"
        with ExecutionTime("CMake Configure and Build (build_kit: test, target: unittests)"):
            assert 0 == self.workspace.run_cmake_configure(build_kit="test").returncode
            assert 0 == self.workspace.run_cmake_build(build_kit="test", target="unittests").returncode

        "Expected test results for kit test shall exist"
        junitxml = build_dir_test.joinpath("components/component/junit.xml")
        assert junitxml.exists()
        testsuite = ET.parse(junitxml).getroot()  # noqa: S314
        assert 2 == int(testsuite.attrib["tests"])
        assert 2 == int(testsuite.attrib["failures"])
        first_test_case = testsuite.find("testcase")
        if first_test_case is not None:
            assert "component.test_someInterfaceOfComponent" == first_test_case.attrib["name"]
            assert "fail" == first_test_case.attrib["status"]
        else:
            raise AssertionError("No test case found in junit.xml")

    def test_build_component_as_static_library(self):
        # create build output directory for build_kit "prod"
        build_dir_prod = self.workspace.workspace_artifacts.get_build_dir("Variant1", "prod")
        makedirs(build_dir_prod, exist_ok=True)

        "Modify compile options of a single file"
        self.workspace.get_component_file("component", "CMakeLists.txt").write_text(
            textwrap.dedent(
                """
                spl_add_source(src/component.c)

                spl_create_component(LIBRARY_TYPE STATIC)
                """
            )
        )

        "Call IUT"
        with ExecutionTime("CMake Configure and Build (build_kit: prod, target: all)"):
            assert 0 == self.workspace.run_cmake_configure(build_kit="prod").returncode
            assert 0 == self.workspace.run_cmake_build(build_kit="prod", target="all").returncode

        "Expected build results shall exist"
        executable = build_dir_prod.joinpath("my_main.exe")
        assert executable.exists()
