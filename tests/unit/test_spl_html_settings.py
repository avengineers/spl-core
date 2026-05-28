"""Unit tests for spl_html_settings module."""

import pytest

from spl_core.report_generation import spl_html_settings


@pytest.mark.unit
class TestSplHtmlSettings:
    def test_html_theme_is_pydata(self):
        assert spl_html_settings.html_theme == "pydata_sphinx_theme"

    def test_html_show_sourcelink_enabled(self):
        assert spl_html_settings.html_show_sourcelink is True

    def test_html_theme_options_is_dict(self):
        assert isinstance(spl_html_settings.html_theme_options, dict)

    def test_nav_levels_match_platform(self):
        opts = spl_html_settings.html_theme_options
        assert opts["show_nav_level"] == 2
        assert opts["show_toc_level"] == 4
        assert opts["navigation_depth"] == 4

    def test_header_links_before_dropdown(self):
        assert spl_html_settings.html_theme_options["header_links_before_dropdown"] == 8

    def test_footer_sections(self):
        opts = spl_html_settings.html_theme_options
        assert opts["footer_start"] == ["copyright", "last-updated"]
        assert opts["footer_end"] == ["sphinx-version", "theme-version"]

    def test_no_rtd_theme_options_remain(self):
        """Ensure no Read the Docs theme options leaked through."""
        rtd_only_keys = {
            "canonical_url",
            "analytics_id",
            "display_version",
            "prev_next_buttons_location",
            "style_external_links",
            "logo_only",
            "style_nav_header_background",
            "collapse_navigation",
            "sticky_navigation",
            "includehidden",
            "titles_only",
        }
        actual_keys = set(spl_html_settings.html_theme_options.keys())
        leftover = actual_keys & rtd_only_keys
        assert leftover == set(), f"RTD-specific options still present: {leftover}"

    def test_html_sidebars_uses_theme_default(self):
        """Sidebar navigation uses native theme templates for collapsible nav."""
        assert "**" in spl_html_settings.html_sidebars
        assert "sidebar-collapse" in spl_html_settings.html_sidebars["**"]
        assert "sidebar-nav-bs" in spl_html_settings.html_sidebars["**"]

    def test_copyright_default(self):
        """Default copyright should be set to RMT and Friends with current year."""
        import datetime

        year = datetime.date.today().year
        assert spl_html_settings.copyright == f"{year}, RMT and Friends"

    def test_last_updated_fmt(self):
        """Footer should show 'Last updated on Mon DD, YYYY' format."""
        assert spl_html_settings.html_last_updated_fmt == "%b %d, %Y"
