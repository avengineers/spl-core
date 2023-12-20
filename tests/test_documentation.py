from os import makedirs
from tests.utils import ExecutionTime, TestWorkspace


class TestDocumentation:
    @classmethod
    def setup_class(cls):
        # create a new test workspace
        cls.workspace: TestWorkspace = TestWorkspace("test_documentation")

    def test_build_docs(self):
        # create build output directory for build_kit "test"
        build_dir_test = self.workspace.workspace_artifacts.get_build_dir(
            "Flv1/Sys1", "test"
        )
        makedirs(build_dir_test, exist_ok=False)

        "Call IUT"
        with ExecutionTime("CMake Configure (build_kit: test)"):
            assert 0 == self.workspace.run_cmake_configure(build_kit="test").returncode

        "Expected configuration output"
        assert build_dir_test.joinpath("build.ninja").exists()

        "Call IUT"
        with ExecutionTime("CMake (build_kit: test, target=docs)"):
            assert (
                0
                == self.workspace.run_cmake_build(
                    build_kit="test", target="docs"
                ).returncode
            )

        # assert build_dir_test.joinpath("components/component/docs/html/index.html").exists()
        # assert build_dir_test.joinpath("components/component/docs/html/components/component/doc/index.html").exists()
        # assert build_dir_test.joinpath("components/component/docs/html/components/component/doc/design.html").exists()
        # assert build_dir_test.joinpath("components/component/docs/html/_images/screenshot.png").exists()
        assert build_dir_test.joinpath("docs/html/index.html").exists()

        pass

        "Call IUT"
        with ExecutionTime("CMake (build_kit: test, target=reports)"):
            assert (
                0
                == self.workspace.run_cmake_build(
                    build_kit="test", target="reports"
                ).returncode
            )

        assert build_dir_test.joinpath(
            "components/component/reports/html/index.html"
        ).exists()
        assert build_dir_test.joinpath(
            "components/component/reports/doxygen/html/index.html"
        ).exists()
        assert build_dir_test.joinpath(
            "components/component/reports/doxygen/html/index.rst"
        ).exists()

        # Delete the config.json files and run the build again - this should retrigger cmake configure and not fail
        build_dir_test.joinpath("components/component/reports/config.json").unlink()

        "Call IUT"
        with ExecutionTime("CMake (build_kit: test, target=reports)"):
            assert (
                0
                == self.workspace.run_cmake_build(
                    build_kit="test", target="reports"
                ).returncode
            )
