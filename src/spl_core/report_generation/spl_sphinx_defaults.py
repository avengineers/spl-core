"""Default Sphinx configuration for SPL reports.

Provides shared extension lists and MyST parser settings used across all SPLE
report generators. Projects import these into their conf.py to ensure consistent
behavior without duplicating configuration.

Usage in downstream conf.py::

    from spl_core.report_generation.spl_sphinx_defaults import extensions, myst_enable_extensions, myst_heading_anchors
"""

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

# Master document (Sphinx root)
master_doc = "index"
