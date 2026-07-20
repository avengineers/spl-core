# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import datetime
import sys
from pathlib import Path

sources_path = Path(__file__).parent.parent.joinpath("src")
sys.path.insert(0, sources_path.as_posix())

# Reuse the shared SPL theme name so this documentation follows the platform
# theme automatically if it ever changes. Imported after sys.path setup above.
from spl_core.report_generation.spl_html_settings import html_theme  # noqa: E402, F401, I001


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "SPL Core"
copyright = f"{datetime.date.today().year}, Avengineers"
author = "Avengineers"
release = "8.7.0-rc.2"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = []

# https://myst-parser.readthedocs.io/en/latest/intro.html
extensions.append("myst_parser")

# TODO: enable this extension when is is supported by readthedocs
# draw.io config - @see https://pypi.org/project/sphinxcontrib-drawio/
# extensions.append("sphinxcontrib.drawio")
# drawio_default_transparency = True

# mermaid config - @see https://pypi.org/project/sphinxcontrib-mermaid/
extensions.append("sphinxcontrib.mermaid")

# Configure extensions for include doc-strings from code
extensions.extend(
    [
        "sphinx.ext.autodoc",
        "sphinx.ext.autosummary",
        "sphinx.ext.napoleon",
        "sphinx.ext.viewcode",
        "sphinx_new_tab_link",
    ]
)

# sphinx-design for grids, cards, tabs
extensions.append("sphinx_design")

# sphinx_needs
extensions.append("sphinx_needs")

# copy button for code block
extensions.append("sphinx_copybutton")

# Shared SPL branding (logo + spl_custom.css). Dogfoods spl_theme_extension in
# this project's own GenerateDocs CI step.
extensions.append("spl_core.report_generation.spl_theme_extension")

# The suffix of source filenames.
# Keep Markdown as the primary source, but allow reStructuredText so
# autosummary-generated .rst stubs are processed correctly.
source_suffix = {
    ".md": "markdown",
    ".rst": "restructuredtext",
}

# Ensure autosummary generates API stubs
autosummary_generate = True

templates_path = ["_templates"]
exclude_patterns = ["build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# html_theme is imported from spl_html_settings (see top of file).
# Theme options are intentionally minimal here: this is spl-core's own API
# reference (autodoc/autosummary), not a multi-component SPL report, so it uses
# a stripped-down navbar rather than the shared report defaults.
html_theme_options = {
    "navbar_start": [],
    "navbar_center": [],
    "navbar_end": [],
    "show_nav_level": 0,
    "show_toc_level": 0,
    "header_links_before_dropdown": 0,
}
# html_static_path = ["_static"]
