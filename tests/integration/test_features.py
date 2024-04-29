import subprocess
import textwrap
import xml.etree.ElementTree as ET

from utils import SplProjectIntegrationTestBase


class TestSplFeatures(SplProjectIntegrationTestBase):
    def test_unittests(self):
        variant = "Variant1"

        "Call IUT"
        result = self.spl_project.build(variant, "unittests")
        assert result.returncode == 0, "Execution shall not fail."

        build_dir = self.spl_project.artifacts.get_build_dir(variant, "test")

        "Expected configuration output"
        assert build_dir.joinpath("kconfig/autoconf.h").exists()
        assert build_dir.joinpath("build.ninja").exists()

        "Expected test results for kit test shall exist"
        assert build_dir.joinpath("src/component/reports/coverage/index.html").exists()
        junitxml = build_dir.joinpath("src/component/junit.xml")
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
        gcno_file = build_dir.joinpath("src/component/CMakeFiles/src_component.dir/src/source_does_not_exist.c.gcno")
        gcno_file.touch()

        "Simulate a single file change"
        self.spl_project.artifacts.src_dir.joinpath("component", "src/component.c").touch()

        "Call IUT"
        result = self.spl_project.build(variant, "unittests")
        assert result.returncode == 0, "Execution shall not fail."

        # Obsolete gcno file shall be deleted
        assert not gcno_file.exists()

        "Simulate a configuration change"
        kconfig_model_file = self.spl_project.artifacts.kconfig_model_file
        content = kconfig_model_file.read_text()
        kconfig_model_file.write_text(content.replace('default "map"', 'default "mdf"'))
        "store workspace status - all files with timestamps"
        self.spl_project.take_files_snapshot()

        "Call IUT"
        result = self.spl_project.build(variant, "unittests")
        assert result.returncode == 0, "Execution shall not fail."

        "Configuration output shall be recreated"
        workspace_status = self.spl_project.get_workspace_files_status()
        assert {"autoconf.h", "autoconf.json", "autoconf.cmake"}.issubset(workspace_status.changed_files_names)
        assert len(workspace_status.deleted_files) == 0
        assert len(workspace_status.new_files) == 0

        "store workspace status - all files with timestamps"
        self.spl_project.take_files_snapshot()

        "Call IUT"
        result = self.spl_project.build(variant, "unittests")
        assert result.returncode == 0, "Execution shall not fail."

        "Configuration output shall not have been recreated"
        workspace_status = self.spl_project.get_workspace_files_status()
        assert {"autoconf.h", "autoconf.json", "autoconf.cmake"}.isdisjoint(workspace_status.changed_files_names)
        assert len(workspace_status.deleted_files) == 0
        assert len(workspace_status.new_files) == 0

        "Simulate a configuration change"
        variant_config_file = self.spl_project.artifacts.get_kconfig_config_file(variant)
        content = variant_config_file.read_text()
        variant_config_file.write_text(content.replace("CONFIG_USE_COMPONENT=y", "CONFIG_USE_COMPONENT=n"))
        "store workspace status - all files with timestamps"
        self.spl_project.take_files_snapshot()

        "Call IUT"
        result = self.spl_project.build(variant, "unittests")
        assert result.returncode == 0, "Execution shall not fail."

        "Configuration output shall be recreated"
        workspace_status = self.spl_project.get_workspace_files_status()
        assert {"autoconf.h", "autoconf.json", "autoconf.cmake"}.issubset(workspace_status.changed_files_names)
        assert len(workspace_status.deleted_files) == 0
        assert len(workspace_status.new_files) == 0

        "Revert configuration changes"
        kconfig_model_file = self.spl_project.artifacts.kconfig_model_file
        content = kconfig_model_file.read_text()
        kconfig_model_file.write_text(content.replace('default "mdf"', 'default "map"'))
        variant_config_file = self.spl_project.artifacts.get_kconfig_config_file(variant)
        content = variant_config_file.read_text()
        variant_config_file.write_text(content.replace("CONFIG_USE_COMPONENT=n", "CONFIG_USE_COMPONENT=y"))
        "store workspace status - all files with timestamps"
        self.spl_project.take_files_snapshot()

        "Call IUT"
        result = self.spl_project.build(variant, "unittests")
        assert result.returncode == 0, "Execution shall not fail."

        "Configuration output shall be recreated"
        workspace_status = self.spl_project.get_workspace_files_status()
        assert {"autoconf.h", "autoconf.json", "autoconf.cmake"}.issubset(workspace_status.changed_files_names)
        assert len(workspace_status.deleted_files) == 0
        assert len(workspace_status.new_files) == 0

    def test_build_modified_file_compile_options(self):
        variant = "Variant1"
        build_dir = self.spl_project.artifacts.get_build_dir(variant, "prod")

        "Modify compile options of a single file"
        self.spl_project.artifacts.src_dir.joinpath("component", "CMakeLists.txt").write_text(
            textwrap.dedent(
                """
                spl_add_source(src/component.c COMPILE_OPTIONS "-DTHE_ANSWER=42")

                spl_add_test_source(test/test_component.cc)

                spl_create_component()
                """
            )
        )

        "Call IUT"
        result = self.spl_project.build(variant, "all")
        assert result.returncode == 0, "Execution shall not fail."

        "Expected build results shall exist"
        executable = build_dir.joinpath("my_main.exe")
        assert executable.exists()
        my_main_result = subprocess.run([executable])
        assert 42 == my_main_result.returncode

        "Modify compile options again"
        self.spl_project.artifacts.src_dir.joinpath("component", "CMakeLists.txt").write_text(
            textwrap.dedent(
                """
                spl_add_source(src/component.c COMPILE_OPTIONS "-DTHE_ANSWER=42" "-DTHE_OFFSET=3")

                spl_add_test_source(test/test_component.cc)

                spl_create_component()
                """
            )
        )

        "Call IUT"
        result = self.spl_project.build(variant, "all")
        assert result.returncode == 0, "Execution shall not fail."

        "Expected build results shall exist"
        executable = build_dir.joinpath("my_main.exe")
        assert executable.exists()
        my_main_result = subprocess.run([executable])
        assert 45 == my_main_result.returncode

        "Modify compile options again"
        self.spl_project.artifacts.src_dir.joinpath("component", "CMakeLists.txt").write_text(
            textwrap.dedent(
                """
                spl_add_source(src/component.c COMPILE_OPTIONS "-DTHE_OFFSET=3")

                spl_add_test_source(test/test_component.cc)

                spl_create_component()
                """
            )
        )

        "Call IUT"
        result = self.spl_project.build(variant, "all")
        assert result.returncode == 0, "Execution shall not fail."

        "Expected build results shall exist"
        executable = build_dir.joinpath("my_main.exe")
        assert executable.exists()
        my_main_result = subprocess.run([executable])
        assert 10 == my_main_result.returncode

        "Modify compile options of a single file using spl_add_compile_options"
        self.spl_project.artifacts.src_dir.joinpath("component", "CMakeLists.txt").write_text(
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
        result = self.spl_project.build(variant, "all")
        assert result.returncode == 0, "Execution shall not fail."

        "Expected build results shall exist"
        executable = build_dir.joinpath("my_main.exe")
        assert executable.exists()
        my_main_result = subprocess.run([executable])
        assert 8 == my_main_result.returncode

        "Modify compile options of a single file using spl_add_compile_options"
        self.spl_project.artifacts.src_dir.joinpath("component", "CMakeLists.txt").write_text(
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
        result = self.spl_project.build(variant, "all")
        assert result.returncode == 0, "Execution shall not fail."

        "Expected build results shall exist"
        executable = build_dir.joinpath("my_main.exe")
        assert executable.exists()
        my_main_result = subprocess.run([executable])
        assert 68 == my_main_result.returncode

        "Call IUT"
        result = self.spl_project.build(variant, "unittests")
        assert result.returncode == 0, "Execution shall not fail."

        "Expected test results for kit test shall exist"
        junitxml = self.spl_project.artifacts.get_build_dir(variant, "test").joinpath("src/component/junit.xml")
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
        variant = "Variant1"

        "Modify compile options of a single file"
        self.spl_project.artifacts.src_dir.joinpath("component", "CMakeLists.txt").write_text(
            textwrap.dedent(
                """
                spl_add_source(src/component.c)

                spl_create_component(LIBRARY_TYPE STATIC)
                """
            )
        )

        "Call IUT"
        result = self.spl_project.build(variant, "all")
        assert result.returncode == 0, "Execution shall not fail."

        "Expected build results shall exist"
        executable = self.spl_project.artifacts.get_build_dir(variant, "prod").joinpath("my_main.exe")
        assert executable.exists()
