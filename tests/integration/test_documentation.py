from pathlib import Path
from typing import Optional

import pytest
from bs4 import BeautifulSoup

from tests.utils import SplKickstartProjectIntegrationTestBase


@pytest.mark.integration
class TestDocumentation(SplKickstartProjectIntegrationTestBase):
    def test_build_reports(self) -> None:
        variant = "EnglishVariant"
        result = self.spl_project.build(variant, "reports")
        assert result is not None and result.returncode == 0, "Execution shall not fail."

        # Check all generated artifacts
        build_dir = self.spl_project.artifacts.get_build_dir(variant, "test")
        rel_build_dir = build_dir.relative_to(self.spl_project.artifacts.project_root_dir)
        for component_path in self.spl_project.components:
            assert build_dir.joinpath(f"reports/html/{component_path}/doc/index.html").exists(), "Component report expected but not found"
            # if there are any files in the component test dir
            if len(list(self.spl_project.artifacts.project_root_dir.joinpath(component_path).glob("test/*"))):
                # Existence checks for all expected report artifacts
                for file in [
                    "unit_test_spec.html",
                    "unit_test_results.html",
                    "coverage.html",
                    "coverage/index.html",
                    "doxygen/html/index.html",
                ]:
                    assert build_dir.joinpath(f"reports/html/{rel_build_dir}/{component_path}/reports/{file}").exists(), f"Component test {file} expected but not found"

                reports_dir = build_dir / f"reports/html/{rel_build_dir}/{component_path}/reports"

                # Content checks: every sphinx-needs item must be properly linked
                # - spec needs in the component doc must have an "is implemented by" back-link
                component_doc_index = build_dir / f"reports/html/{component_path}/doc/index.html"
                found_any_spec = self._assert_needs_have_link_option(component_doc_index, need_type_class="needs_type_spec", link_span_class="implements")
                assert found_any_spec, f"No spec needs found in doc/index.html for {component_path} - check the component doc."

                # - unit_test_spec: each test spec must have "Tests" (traceability to design) and "Results" (link to test result) filled
                self._assert_needs_table_columns_have_links(
                    reports_dir / "unit_test_spec.html",
                    columns=["Tests", "Results"],
                )

                # - unit_test_results: all result sections must have "Results From" links (empty sections are skipped)
                for section_id in ["passed-test-cases", "failed-test-cases", "skipped-test-cases"]:
                    self._assert_needs_table_columns_have_links(
                        reports_dir / "unit_test_results.html",
                        columns=["Results From"],
                        section_id=section_id,
                    )

                # - impl needs in doxygen HTML must have an :implements: link to a spec
                doxygen_html_dir = reports_dir / "doxygen/html"
                found_any_impl = any(self._assert_needs_have_link_option(html_file, need_type_class="needs_type_impl", link_span_class="implements") for html_file in doxygen_html_dir.glob("*.html"))
                assert found_any_impl, f"No impl needs found in doxygen HTML for {component_path} - check that source files contain :implements: links."

    @staticmethod
    def _assert_needs_have_link_option(html_file: Path, need_type_class: str, link_span_class: str) -> bool:
        """Assert that every need of the given type in the HTML file has a non-empty link option.

        Returns True if at least one matching need was found, False otherwise.
        Used to catch regressions where cross-links are silently dropped from generated docs.

        Examples:
            need_type_class='needs_type_impl', link_span_class='implements'
                -> checks that every impl need has an :implements: link to a spec
            need_type_class='needs_type_spec', link_span_class='implements'
                -> checks that every spec need has an 'is implemented by' back-link
        """
        soup = BeautifulSoup(html_file.read_text(encoding="utf-8"), "html.parser")
        needs = soup.find_all("table", class_=need_type_class)
        for need_table in needs:
            need_id = need_table.get("id", "unknown")
            link_span = need_table.find("span", class_=link_span_class)
            assert link_span is not None and link_span.find("a"), f"Need '{need_id}' in {html_file.name}: '{link_span_class}' link is missing or empty. Every '{need_type_class}' need must have this link filled."
        return bool(needs)

    @staticmethod
    def _assert_needs_table_columns_have_links(html_file: Path, columns: list[str], section_id: Optional[str] = None) -> None:
        """Assert that every row in the sphinx-needs table has links in the specified columns.

        Used to catch regressions where cross-links between test specs, test cases, and test
        results are silently dropped (e.g. 'Is Resulted From' or 'Results' columns left empty).
        """
        soup = BeautifulSoup(html_file.read_text(encoding="utf-8"), "html.parser")
        context = soup.find("section", id=section_id) if section_id else soup
        assert context is not None, f"Section '{section_id}' not found in {html_file.name}"

        table = context.find("table", class_="NEEDS_TABLE")
        if table is None:
            # Section exists but has no matching needs (e.g. no failed or skipped test cases) - nothing to check.
            return

        # Map column names to their index via the table header
        headers = [th.get_text(strip=True) for th in table.thead.find_all("th")]
        col_indices = {col: headers.index(col) for col in columns if col in headers}
        missing_headers = [col for col in columns if col not in headers]
        assert not missing_headers, f"Columns {missing_headers} not found in {html_file.name}. Available: {headers}"

        rows = table.tbody.find_all("tr", class_="need")
        for row in rows:
            cells = row.find_all("td")
            need_id = cells[0].get_text(strip=True) if cells else "unknown"
            for col_name, col_idx in col_indices.items():
                cell = cells[col_idx]
                assert cell.find("a"), f"Need '{need_id}' in {html_file.name}: column '{col_name}' has no links. Every sphinx-needs item must be linked."
