# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import json
import os


project = "Project"
copyright = "2023"
author = "RMT"
release = "0.0.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = []
exclude_patterns = [".git", ".venv", "build/modules", "**/.venv"]
include_patterns = ["index.rst", "doc/**"]


# mermaid config - @see https://pypi.org/project/sphinxcontrib-mermaid/
extensions.append("sphinxcontrib.mermaid")

# sphinx_needs
extensions.append("sphinx_needs")


# needs_types - this option allows the setup of own need types like bugs, user_stories and more.

needs_types = [
    dict(directive="req", title="Requirement", prefix="R_", color="#BFD8D2", style="node"),
    dict(directive="spec", title="Specification", prefix="S_", color="#FEDCD2", style="node"),
    dict(directive="impl", title="Implementation", prefix="I_", color="#DF744A", style="node"),
    dict(directive="test", title="Test Case", prefix="T_", color="#DCB239", style="node"),
    # Kept for backwards compatibility
    dict(directive="need", title="Need", prefix="N_", color="#9856a5", style="node"),
    dict(directive="image", title="Image", prefix="IMG_", color="#FFCC00", style="node"),
]

# Define own options
needs_extra_options = ["integrity", "assignee", "version"]

# Define own link types

needs_extra_links = [
    {"option": "checks", "incoming": "is checked by", "outgoing": "checks"},
    {"option": "implements", "incoming": "is implemented by", "outgoing": "implements"},
    {"option": "tests", "incoming": "is tested by", "outgoing": "tests requirement(s)"},
    {"option": "results", "incoming": "is resulted from", "outgoing": "test results"},
    {"option": "requirement", "incoming": "specification", "outgoing": "requirement"},
    {"option": "specified", "incoming": "tested by", "outgoing": "specified by"},
]


# sphinxcontrib-test-reports
extensions.append("sphinxcontrib.test_reports")
tr_report_template = "doc/test_report_template.txt"

# The suffix of source filenames.
source_suffix = [".rst"]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"

# Hide hyper link which leeds to the source of page displayed
html_show_sourcelink = True

html_theme_options = {
    "canonical_url": "",
    "analytics_id": "",  #  Provided by Google in your dashboard
    "display_version": True,
    "prev_next_buttons_location": "bottom",
    "style_external_links": True,
    "logo_only": False,
    "style_nav_header_background": "white",
    # Toc options
    "collapse_navigation": True,
    "sticky_navigation": True,
    "navigation_depth": 6,
    "includehidden": True,
    "titles_only": False,
}

# Check if the SPHINX_BUILD_CONFIGURATION_FILE environment variable exists
# and if so, load the JSON file and set the 'html_context' variable
if "SPHINX_BUILD_CONFIGURATION_FILE" in os.environ:
    with open(os.environ["SPHINX_BUILD_CONFIGURATION_FILE"], "r") as file:
        html_context = json.load(file)
        include_patterns.extend(html_context.get("include_patterns", []))
        
html_context["config"] = {}

# Check if the SPHINX_BUILD_CONFIGURATION_FILE environment variable exists
# and if so, load the JSON file and set the 'html_context' variable
if "AUTOCONF_JSON_FILE" in os.environ:
    with open(os.environ["AUTOCONF_JSON_FILE"], "r") as file:
        html_context["config"] = json.load(file)["features"]

if "VARIANT" in os.environ:
    html_context["config"]["variant"] = os.environ["VARIANT"]


def rstjinja(app, docname, source):
    """
    Render our pages as a jinja template for fancy templating goodness.
    """
    # Make sure we're outputting HTML
    if app.builder.format != "html":
        return
    src = source[0]
    rendered = app.builder.templates.render_string(src, app.config.html_context)
    source[0] = rendered


def setup(app):
    app.connect("source-read", rstjinja)
