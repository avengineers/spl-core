import tomllib
from pathlib import Path
from typing import Any

import pytest
from bs4 import BeautifulSoup

from spl_core.report_generation.spl_sphinx import SplSphinx
from tests.utils import SplKickstartProjectIntegrationTestBase

VARIANT = "EnglishVariant"
SELECTION_FILE = "ubproject.variants.toml"

VARIANT_MARKER_MD = """# Variant Marker

```{if} var.build_config.target == "reports"
MARKER_TARGET_REPORTS
```

```{if} var.build_config.target == "docs"
MARKER_TARGET_DOCS
```
"""


def _replace_once(file: Path, old: str, new: str) -> None:
    content = file.read_text(encoding="utf-8")
    assert content.count(old) == 1, f"Expected exactly one '{old}' in {file}; the kickstart template has changed."
    file.write_text(content.replace(old, new), encoding="utf-8")


@pytest.mark.integration
class TestUbCodeSelection(SplKickstartProjectIntegrationTestBase):
    """An SPL that sets SPL_UBCODE_SELECTION_FILE and declares its own documents through SPL_PROJECT_DOCS_INCLUDE_PATTERNS (ADR 0005)."""

    @classmethod
    def setup_class(cls) -> None:
        super().setup_class()
        project_root = cls.spl_project.artifacts.project_root_dir

        parts_include = "include(${CMAKE_SOURCE_DIR}/variants/${VARIANT}/parts.cmake)"
        _replace_once(
            project_root / "CMakeLists.txt",
            parts_include,
            f'set(SPL_UBCODE_SELECTION_FILE {SELECTION_FILE})\nset(SPL_PROJECT_DOCS_INCLUDE_PATTERNS "index.md" "doc/**")\n{parts_include}',
        )

        (project_root / "doc/variant_marker.md").write_text(VARIANT_MARKER_MD, encoding="utf-8")
        _replace_once(project_root / "index.md", "doc/common/index\n", "doc/common/index\ndoc/variant_marker\n")

        # The variable now carries the SPL's own patterns; an opted-in SPL declares no include list of its own.
        _replace_once(project_root / "conf.py", 'include_patterns = ["index.md", "doc/**"]', "include_patterns = []")

    @property
    def project_root(self) -> Path:
        return self.spl_project.artifacts.project_root_dir

    @property
    def build_dir(self) -> Path:
        return self.spl_project.artifacts.get_build_dir(VARIANT, "test")

    @property
    def rel_build_dir(self) -> str:
        return self.build_dir.relative_to(self.project_root).as_posix()

    def _build(self, target: str, build_kit: str | None = None) -> None:
        result = self.spl_project.build(VARIANT, target, build_kit)
        assert result is not None and result.returncode == 0, f"Building '{target}' shall not fail."

    def test_selection_file(self) -> None:
        self._build("reports")

        selection_file = self.project_root / SELECTION_FILE
        assert selection_file.exists(), f"{selection_file} not written"
        data: dict[str, Any] = tomllib.loads(selection_file.read_text(encoding="utf-8"))
        rel_build_dir = self.rel_build_dir

        # The current key [variants] data_file, not the legacy [needs] variant_data_file, so the selection wins over [needs] variant keys an SPL may set.
        assert data["variants"]["data_file"] == f"{rel_build_dir}/reports/variant_data.json"
        assert "variant_data_file" not in data.get("needs", {}), "The selection names the variant data file with the legacy key [needs] variant_data_file"

        md_parser = data["parse"]["parsers"]["md"]
        assert md_parser["flavour"] == "myst"
        for pattern in ["./index.md", "doc/**/*.md", "src/greeter/doc/**/*.md"]:
            assert pattern in md_parser["include"], f"'{pattern}' missing in the md parser's include: {md_parser['include']}"
        # ubCode matches a pattern without a slash in every directory: a bare index.md would select every component's doc/index.md.
        assert not [p for p in md_parser["include"] if "/" not in p], f"The md parser has a pattern without a slash: {md_parser['include']}"
        assert not [p for p in md_parser["include"] if p.endswith(".rst")], f"The md parser claims rst pages: {md_parser['include']}"
        # ubCode reads the MyST syntax Sphinx reads, such as :::{if} blocks (colon_fence). It does not implement html_admonition.
        sphinx_extensions = SplSphinx.default_extension_configs["myst_enable_extensions"]
        assert sorted(md_parser["extensions"]) == sorted(set(sphinx_extensions) - {"html_admonition"})

        rst_include = data["parse"]["parsers"]["rst"]["include"]
        for pattern in [f"{rel_build_dir}/reports/**/*.rst", f"{rel_build_dir}/src/greeter/reports/**/*.rst"]:
            assert pattern in rst_include, f"'{pattern}' missing in the rst parser's include: {rst_include}"
        assert not [p for p in rst_include if p.endswith(".md")], f"The rst parser claims md pages: {rst_include}"

        # spl-core's needs model, copied from report_generation/ubproject.toml.
        assert [d["directive"] for d in data["needs"]["types"]] == ["arch", "req", "spec", "impl", "test"]
        assert "predicates" in data["needs"]["links"]["results"]
        # The table makes ubCode read the test-report directive and add the test-case type the results predicate links.
        assert "test_reports" in data, "The selection has no [test_reports] table"
        # With parsers configured, ubCode ignores [source] extend_include and warns about it.
        assert "extend_include" not in data["source"], "The selection sets [source] extend_include, which ubCode ignores in parser mode"

    def test_variant_data_reaches_sphinx(self) -> None:
        self._build("reports")
        reports_text = self._page_text(self.build_dir / "reports/html/doc/variant_marker.html")
        assert "MARKER_TARGET_REPORTS" in reports_text
        assert "MARKER_TARGET_DOCS" not in reports_text

        self._build("docs")
        docs_text = self._page_text(self.build_dir / "docs/html/doc/variant_marker.html")
        assert "MARKER_TARGET_DOCS" in docs_text
        assert "MARKER_TARGET_REPORTS" not in docs_text

    def test_component_report_has_a_generated_root_page(self) -> None:
        self._build("src_greeter_report")

        # The root page sits in the component's binary dir, outside the run output dirs the variant runs read.
        root_md = self.build_dir / "src/greeter/root_reports.md"
        root_text = self._root_page_text(root_md)
        for entry in ["/src/greeter/doc/index", "unit_test_spec", "unit_test_results", "coverage", "__source_docs/index"]:
            assert entry in root_text, f"'{entry}' missing in the toctree of {root_md}"

        html_dir = self.build_dir / "src/greeter/reports/html"
        root_html = html_dir / f"{self.rel_build_dir}/src/greeter/root_reports.html"
        assert root_html.exists(), f"{root_html} not built"

        # The component report is rooted in the generated page, not in the project's index.md.
        assert not (html_dir / "index.html").exists(), "The component report contains a page built from the project's index.md"

    def test_component_docs_has_a_generated_root_page(self) -> None:
        self._build("src_greeter_docs")

        root_md = self.build_dir / "src/greeter/root_docs.md"
        root_text = self._root_page_text(root_md)
        assert "/src/greeter/doc/index" in root_text, f"'/src/greeter/doc/index' missing in the toctree of {root_md}"
        for report_page in ["unit_test_spec", "unit_test_results", "coverage", "__source_docs"]:
            assert report_page not in root_text, f"The docs root page {root_md} lists the report page '{report_page}'"

        html_dir = self.build_dir / "src/greeter/docs/html"
        root_html = html_dir / f"{self.rel_build_dir}/src/greeter/root_docs.html"
        assert root_html.exists(), f"{root_html} not built"

        assert not (html_dir / "index.html").exists(), "The component docs contain a page built from the project's index.md"

    def test_variant_runs_do_not_read_the_root_pages(self) -> None:
        self._build("reports")

        html_dir = self.build_dir / "reports/html"
        for root_page in ["root_docs.html", "root_reports.html"]:
            found = list(html_dir.rglob(root_page))
            assert not found, f"The variant report built a component root page: {found}"

        # The component doc stays nested under its wrapper page: the sidebar of its page links the wrapper.
        # A root page read by the variant run takes the place of the wrapper as its parent and empties the sidebar.
        component_doc_html = html_dir / "src/greeter/doc/index.html"
        assert component_doc_html.exists(), f"{component_doc_html} not built"
        sidebar = BeautifulSoup(component_doc_html.read_text(encoding="utf-8"), "html.parser").find("nav", class_="bd-docs-nav")
        assert sidebar is not None, f"No sidebar navigation in {component_doc_html}"
        sidebar_hrefs = [a.get("href", "") for a in sidebar.find_all("a")]
        assert any(href.endswith("src_greeter_index.html") for href in sidebar_hrefs), f"The sidebar of {component_doc_html} does not link the wrapper page src_greeter_index: {sidebar_hrefs}"

    def test_prod_configure_leaves_the_selection(self) -> None:
        self._build("docs")
        selection_file = self.project_root / SELECTION_FILE
        assert selection_file.exists(), f"{selection_file} not written by the test kit"
        before = selection_file.read_bytes()

        self._build("all", "prod")

        assert selection_file.read_bytes() == before, "A prod configure changed the selection the test kit wrote"

    @staticmethod
    def _root_page_text(root_md: Path) -> str:
        assert root_md.exists(), f"{root_md} not generated"
        root_text = root_md.read_text(encoding="utf-8")
        assert "{toctree}" in root_text, f"No toctree in {root_md}"
        assert not root_text.startswith("---"), f"{root_md} must not carry front matter such as orphan"
        return root_text

    @staticmethod
    def _page_text(html_file: Path) -> str:
        assert html_file.exists(), f"{html_file} not built"
        return BeautifulSoup(html_file.read_text(encoding="utf-8"), "html.parser").get_text()
