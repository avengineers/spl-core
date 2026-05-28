"""HTML theme configuration for SPL projects.

Central definition of the PyData Sphinx Theme settings used across all SPLE reports.
Projects import html_theme and html_theme_options from this module to ensure a
consistent look and feel company-wide.

Usage in downstream conf.py::

    from spl_core.report_generation.spl_html_settings import (
        html_theme, html_show_sourcelink, html_theme_options, html_sidebars,
        copyright, html_last_updated_fmt,
    )
    extensions.append("spl_core.report_generation.spl_theme_extension")

    # Override copyright if needed:
    # copyright = f"{datetime.date.today().year} My Company"

    # Override logo if needed:
    # html_logo = "path/to/my_logo.png"
"""

import datetime

# Default copyright — downstream projects can override after import
copyright = f"{datetime.date.today().year}, RMT and Friends"

# Show "Last updated on ..." in footer
html_last_updated_fmt = "%b %d, %Y"

# HTML Theme
html_theme = "pydata_sphinx_theme"

# Show source links
html_show_sourcelink = True

# PyData Sphinx Theme Options — aligned with the SPLE Platform Page (theme 0.18+)
html_theme_options = {
    "show_nav_level": 2,
    "show_toc_level": 4,
    "navigation_depth": 4,
    "header_links_before_dropdown": 8,
    "footer_start": ["copyright", "last-updated"],
    "footer_end": ["sphinx-version", "theme-version"],
}

# Use the native PyData theme sidebar with collapsible navigation (theme 0.18+).
# "sidebar-collapse" renders the toggle button, "sidebar-nav-bs" the navigation tree.
# These are the theme defaults from theme.conf — we state them explicitly so that
# downstream conf.py files importing this module get consistent behavior.
html_sidebars = {
    "**": ["sidebar-collapse", "sidebar-nav-bs"],
}
