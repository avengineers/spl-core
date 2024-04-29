from typing import List

from spl_core.project_creator.variant import Variant
from tests.utils import ExecutionTime, TestWorkspace


class TestDocumentation:
    workspace: TestWorkspace
    variant_name: Variant
    component_paths: List[str]

    @classmethod
    def setup_class(cls):
        # create a new test workspace
        cls.workspace = TestWorkspace("test_documentation")
        cls.variant_name = Variant("Flv1", "Sys1")
        cls.component_paths = ["components/main", "components/component"]

    def test_build_docs(self):
        build_dir_test = self.workspace.workspace_artifacts.get_build_dir(self.variant_name, "test")

        "Call IUT"
        with ExecutionTime("CMake Configure (build_kit: test)"):
            assert 0 == self.workspace.run_cmake_configure(build_kit="test").returncode

        "Expected configuration output"
        assert build_dir_test.joinpath("build.ninja").exists()

        "Call IUT"
        with ExecutionTime("CMake (build_kit: test, target=docs)"):
            assert 0 == self.workspace.run_cmake_build(build_kit="test", target="docs").returncode

        assert build_dir_test.joinpath("docs/html/index.html").exists()
        assert build_dir_test.joinpath("docs/html/components/main/doc/index.html").exists()
        assert build_dir_test.joinpath("docs/html/components/component/doc/index.html").exists()

    def test_build_reports(self):
        build_dir_test = self.workspace.workspace_artifacts.get_build_dir(self.variant_name, "test")

        "Call IUT"
        with ExecutionTime("CMake Configure (build_kit: test)"):
            assert 0 == self.workspace.run_cmake_configure(build_kit="test").returncode

        "Expected configuration output"
        assert build_dir_test.joinpath("build.ninja").exists()

        "Call IUT"
        with ExecutionTime("CMake (build_kit: test, target=reports)"):
            assert 0 == self.workspace.run_cmake_build(build_kit="test", target="reports").returncode

        assert build_dir_test.joinpath("reports/html/index.html").exists()

        project_root_dir = self.workspace.workspace_artifacts.root_dir
        rel_build_dir = build_dir_test.relative_to(project_root_dir)
        for component_path in self.component_paths:
            assert build_dir_test.joinpath(f"reports/html/{component_path}/doc/index.html").exists(), "Component documentation expected but not found"
            # if there are any files in the component test dir
            if len(list(project_root_dir.joinpath(component_path).glob("test/*"))):
                for file in [
                    "unit_test_spec.html",
                    "unit_test_results.html",
                    "coverage.html",
                    "coverage/index.html",
                ]:
                    assert build_dir_test.joinpath(f"reports/html/{rel_build_dir}/{component_path}/reports/{file}").exists(), f"Component test {file} expected but not found"
