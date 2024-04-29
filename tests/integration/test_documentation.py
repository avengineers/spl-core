from tests.utils import SplKickstartProjectIntegrationTestBase


class TestDocumentation(SplKickstartProjectIntegrationTestBase):
    def test_build_docs(self):
        variant = "GermanVariant"
        result = self.cli.execute(["build.bat", "-build", "-buildKit", "test", "-variants", variant, "-target", "docs"])
        assert result.returncode == 0, "Execution shall not fail."

        # Check all generated artifacts
        build_dir = self.project_dir.joinpath(f"build/{variant}/test")
        assert build_dir.joinpath("docs/html/index.html").exists()
        for component_path in ["src/main", "src/greeter"]:
            assert build_dir.joinpath(f"docs/html/{component_path}/doc/index.html").exists(), "Component documentation expected but not found"

    def test_build_reports(self) -> None:
        variant = "EnglishVariant"
        result = self.cli.execute(["build.bat", "-build", "-buildKit", "test", "-variants", variant, "-target", "reports"])
        assert result.returncode == 0, "Execution shall not fail."

        # Check all generated artifacts
        build_dir = self.project_dir.joinpath(f"build/{variant}/test")
        rel_build_dir = build_dir.relative_to(self.project_dir)
        for component_path in ["src/main", "src/greeter"]:
            assert build_dir.joinpath(f"reports/html/{component_path}/doc/index.html").exists(), "Component report expected but not found"
            # if there are any files in the component test dir
            if len(list(self.project_dir.joinpath(component_path).glob("test/*"))):
                for file in [
                    "unit_test_spec.html",
                    "unit_test_results.html",
                    "coverage.html",
                    "coverage/index.html",
                ]:
                    assert build_dir.joinpath(f"reports/html/{rel_build_dir}/{component_path}/reports/{file}").exists(), f"Component test {file} expected but not found"
