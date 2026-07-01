"""Unit tests for the SPL theme Sphinx extension CSS helpers."""

import pytest

from spl_core.report_generation.spl_theme_extension import (
    _generate_needs_dark_css,
    rescope_root_block,
)


@pytest.mark.unit
class TestRescopeRootBlock:
    def test_rescopes_root_to_dark_selector(self):
        out = rescope_root_block(":root {\n  --x: #fff;\n  --y: #000;\n}")
        assert out is not None
        assert out.startswith('html[data-theme="dark"] {')
        assert "--x: #fff;" in out
        assert "--y: #000;" in out
        assert ":root" not in out

    def test_honors_custom_selector(self):
        out = rescope_root_block(":root { --a: 1px; }", selector=".foo")
        assert out is not None
        assert out.startswith(".foo {")

    def test_returns_none_without_root_block(self):
        assert rescope_root_block(".bar { color: red; }") is None


@pytest.mark.unit
class TestGenerateNeedsDarkCss:
    def test_generates_from_installed_sphinx_needs(self):
        # sphinx-needs is a hard dependency, so generation must succeed in the test env.
        css = _generate_needs_dark_css()
        assert css is not None
        assert 'html[data-theme="dark"]' in css
        assert "--sn-color-" in css
        assert ":root" not in css
