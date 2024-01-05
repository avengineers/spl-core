from tests.utils import ExecutionTime, TestWorkspace


class TestDocumentation:
    @classmethod
    def setup_class(cls):
        # create a new test workspace
        cls.workspace: TestWorkspace = TestWorkspace("test_documentation")

    def test_build_docs(self):
        build_dir_test = self.workspace.workspace_artifacts.get_build_dir(
            "Flv1/Sys1", "test"
        )

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

        assert build_dir_test.joinpath("docs/html/index.html").exists()
        assert build_dir_test.joinpath(
            "docs/html/components/main/doc/index.html"
        ).exists()
        assert build_dir_test.joinpath(
            "docs/html/components/component/doc/index.html"
        ).exists()

    def test_build_reports(self):
        build_dir_test = self.workspace.workspace_artifacts.get_build_dir(
            "Flv1/Sys1", "test"
        )

        "Call IUT"
        with ExecutionTime("CMake Configure (build_kit: test)"):
            assert 0 == self.workspace.run_cmake_configure(build_kit="test").returncode

        "Expected configuration output"
        assert build_dir_test.joinpath("build.ninja").exists()

        "Call IUT"
        with ExecutionTime("CMake (build_kit: test, target=reports)"):
            assert (
                0
                == self.workspace.run_cmake_build(
                    build_kit="test", target="reports"
                ).returncode
            )

        assert build_dir_test.joinpath("reports/html/index.html").exists()
        assert build_dir_test.joinpath(
            "reports/html/components/main/doc/index.html"
        ).exists()
        assert build_dir_test.joinpath(
            "reports/html/components/component/doc/index.html"
        ).exists()
        assert build_dir_test.joinpath(
            "reports/html/build/Flv1/Sys1/test/components/component/reports/unit_test_results.html"
        ).exists()
