# -*- coding: utf-8 -*-
"""Configuration"""

import json
import os
import datetime

from spl_core.report_generation.spl_sphinx import SplSphinx
from spl_core.report_generation.spl_html_settings import html_theme, html_show_sourcelink, html_theme_options  # noqa: F401

day = datetime.date.today()
# meta data #################################################################

project = "Hello SPL"
copyright = f"{day.year} Avengineers"
release = f"{day}"

# file handling #############################################################
# @see https://www.sphinx-doc.org/en/master/usage/configuration.html

templates_path = [
    "doc/_tmpl",
]

exclude_patterns = [
    "README.md",
    "build/modules",
    "build/deps",
    ".venv",
    ".git",
    "**/test_results.rst",  # We renamed this file, but nobody deletes it.
]

include_patterns = ["index.md", "doc/**"]

# configuration of built-in stuff ###########################################
# @see https://www.sphinx-doc.org/en/master/usage/configuration.html

numfig = True

# html config ###############################################################
# @see https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# Omit "documentation" in title
html_title = f"{project} {release}"

# Use default SPL HTML theme configuration (imported from spl_html_settings)
# Can be overridden after import if needed


# EXTENSIONS AND THEIR CONFIGS ##############################################

# Get default SPL extensions and their configurations
extensions = SplSphinx.default_extensions
extension_configs = SplSphinx.default_extension_configs

# Apply extension-specific configurations
sphinx_rtd_size_width = extension_configs["sphinx_rtd_size_width"]
tr_report_template = extension_configs["tr_report_template"]
myst_enable_extensions = extension_configs["myst_enable_extensions"]
source_suffix = extension_configs["source_suffix"]

# Import default SPL sphinx-needs configuration
needs_from_toml = ".venv/Lib/site-packages/spl_core/report_generation/ubproject.toml"
# Additional import required because the configuration references custom functions defined in this module
needs_functions = SplSphinx.default_needs_functions
needs_global_options = SplSphinx.default_needs_global_options
                                                                                                                                                                                                                                                                                                                                                                                                     
# Provide all config values to jinja
html_context = {
    "build_config": {},
    "config": {},
    "timestamp": f"{datetime.datetime.now(tz=datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC",
}

# pass build configuration to jinja
if "SPHINX_BUILD_CONFIGURATION_FILE" in os.environ:
    with open(os.environ["SPHINX_BUILD_CONFIGURATION_FILE"], "r") as file:
        html_context["build_config"] = json.load(file)
        include_patterns.extend(html_context["build_config"].get("include_patterns", []))

# pass feature configuration to jinja
if "AUTOCONF_JSON_FILE" in os.environ:
    with open(os.environ["AUTOCONF_JSON_FILE"], "r") as file:
        html_context["config"] = json.load(file)["features"]

# we almost forgot the variant :o)
if "VARIANT" in os.environ:
    html_context["build_config"]["variant"] = os.environ["VARIANT"]


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
