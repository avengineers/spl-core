"""Default Sphinx configuration for SPL projects.

Central definition of the PyData Sphinx Theme settings, extensions, and MyST
parser configuration used across all SPLE reports. Projects import variables
from this module into their conf.py to ensure a consistent look and feel.

Usage in downstream conf.py::

    from spl_core.report_generation.spl_html_settings import (
        copyright, extensions, html_last_updated_fmt, html_show_sourcelink,
        html_sidebars, html_theme, html_theme_options, master_doc,
        myst_enable_extensions, myst_heading_anchors, myst_url_schemes,
    )

    # Override copyright if needed:
    # copyright = f"{datetime.date.today().year} My Company"

    # Override logo if needed:
    # html_logo = "path/to/my_logo.png"
"""

import datetime

# ---------------------------------------------------------------------------
# Extensions and MyST parser settings
# ---------------------------------------------------------------------------

# Extensions required for MyST markdown, sphinx-design directives, and SPL theme
extensions = [
    "myst_parser",
    "sphinx_design",
    "sphinx_new_tab_link",
    "spl_core.report_generation.spl_theme_extension",
]

# MyST parser extensions for enhanced markdown support
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "html_admonition",
    "html_image",
    "replacements",
    "smartquotes",
    "substitution",
    "tasklist",
]

# Heading anchor depth (clickable # links)
myst_heading_anchors = 3

# Accepted URL schemes for MyST links (adds ssh:// for repository URLs)
myst_url_schemes = ("http", "https", "mailto", "ftp", "ssh")

# Master document (Sphinx root)
master_doc = "index"

# ---------------------------------------------------------------------------
# HTML theme settings
# ---------------------------------------------------------------------------

# Default copyright — downstream projects can override after import
copyright = f"{datetime.date.today().year}, Avengineers"

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
