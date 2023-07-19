from os import makedirs
from tests.utils import ExecutionTime, TestWorkspace


class TestDocumentation:
    @classmethod
    def setup_class(cls):
        # create a new test workspace
        cls.workspace: TestWorkspace = TestWorkspace("test_documentation")

    def test_build_docs(self):
        # create build output directory for build_kit "test"
        build_dir_test = self.workspace.workspace_artifacts.get_build_dir("Flv1/Sys1", "test")
        makedirs(build_dir_test, exist_ok=False)

        "Call IUT"
        with ExecutionTime("CMake Configure (build_kit: test)"):
            assert 0 == self.workspace.run_cmake_configure(build_kit="test").returncode

        "Expected configuration output"
        assert build_dir_test.joinpath("build.ninja").exists()

        "Call IUT"
        with ExecutionTime("CMake (build_kit: test, target=docs)"):
            assert 0 == self.workspace.run_cmake_build(build_kit="test", target="docs").returncode

        assert build_dir_test.joinpath("components/component/doc/html/index.html").exists()
        assert build_dir_test.joinpath("components/component/doc/html/design.html").exists()
        assert build_dir_test.joinpath("components/component/doc/html/_images/screenshot.png").exists()
