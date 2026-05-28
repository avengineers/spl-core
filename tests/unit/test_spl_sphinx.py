"""Unit tests for SplSphinx class."""

import pytest

from spl_core.report_generation.spl_sphinx import SplSphinx


@pytest.mark.unit
class TestSplSphinxExtensions:
    def test_no_rtd_size_in_default_extensions(self):
        assert "sphinx_rtd_size" not in SplSphinx.default_extensions

    def test_no_rtd_size_width_in_default_extension_configs(self):
        assert "sphinx_rtd_size_width" not in SplSphinx.default_extension_configs

    def test_required_extensions_present(self):
        required = [
            "sphinxcontrib.mermaid",
            "sphinx_needs",
            "sphinxcontrib.test_reports",
            "sphinx.ext.todo",
            "sphinxcontrib.datatemplates",
            "myst_parser",
        ]
        for ext in required:
            assert ext in SplSphinx.default_extensions, f"Missing required extension: {ext}"

    def test_myst_enable_extensions_present(self):
        assert "myst_enable_extensions" in SplSphinx.default_extension_configs
        myst_exts = SplSphinx.default_extension_configs["myst_enable_extensions"]
        for ext in ["colon_fence", "deflist", "html_admonition", "html_image"]:
            assert ext in myst_exts, f"Missing MyST extension: {ext}"

    def test_source_suffix_includes_rst_and_md(self):
        suffixes = SplSphinx.default_extension_configs["source_suffix"]
        assert ".rst" in suffixes
        assert ".md" in suffixes

    def test_tr_report_template_present(self):
        assert "tr_report_template" in SplSphinx.default_extension_configs
