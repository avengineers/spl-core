from tests.utils import SplKickstartProjectIntegrationTestBase


class TestDocumentation(SplKickstartProjectIntegrationTestBase):
    def test_build_docs(self):
        variant = "GermanVariant"
        result = self.spl_project.build(variant, "docs")
        assert result.returncode == 0, "Execution shall not fail."

        # Check all generated artifacts
        build_dir = self.spl_project.artifacts.get_build_dir(variant, "test")
        assert build_dir.joinpath("docs/html/index.html").exists()
        for component_path in self.spl_project.components:
            assert build_dir.joinpath(f"docs/html/{component_path}/doc/index.html").exists(), "Component documentation expected but not found"

    def test_build_reports(self) -> None:
        variant = "EnglishVariant"
        result = self.spl_project.build(variant, "reports")
        assert result.returncode == 0, "Execution shall not fail."

        # Check all generated artifacts
        build_dir = self.spl_project.artifacts.get_build_dir(variant, "test")
        rel_build_dir = build_dir.relative_to(self.spl_project.artifacts.project_root_dir)
        for component_path in self.spl_project.components:
            assert build_dir.joinpath(f"reports/html/{component_path}/doc/index.html").exists(), "Component report expected but not found"
            # if there are any files in the component test dir
            if len(list(self.spl_project.artifacts.project_root_dir.joinpath(component_path).glob("test/*"))):
                for file in [
                    "unit_test_spec.html",
                    "unit_test_results.html",
                    "coverage.html",
                    "coverage/index.html",
                ]:
                    assert build_dir.joinpath(f"reports/html/{rel_build_dir}/{component_path}/reports/{file}").exists(), f"Component test {file} expected but not found"
