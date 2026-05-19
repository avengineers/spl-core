"""Centralized Sphinx configuration for SPL projects."""

import datetime
import json
import os
import re
from typing import Any, ClassVar

from sphinx.application import Sphinx
from sphinx_needs.data import NeedsMutable, NeedsView
from sphinx_needs.need_item import NeedItem, NeedPartItem


def sple_tr_link(
    app: Sphinx,
    need: NeedItem | NeedPartItem,
    needs: NeedsView | NeedsMutable,
    first_option_name: str,
    second_option_name: str,
    *args: Any,
    **kwargs: Any,
) -> list[str]:
    """Make links between 'needs'. In comparison to the default 'tr_link' function,
    this function supports regular expression pattern matching."""
    if first_option_name not in need:
        return []
    # Get the value of the 'first_option_name'
    first_option_value = need[first_option_name]

    links = []
    for need_target in needs.values():
        # Skip linking to itself
        if need_target["id"] == need["id"]:
            continue
        if second_option_name not in need_target:
            continue

        if first_option_value is not None and len(first_option_value) > 0:
            second_option_value = need_target[second_option_name]
            if second_option_value is not None and len(second_option_value) > 0:
                if first_option_value == second_option_value:
                    links.append(need_target["id"])
                # if the first option value has a *, use regex matching
                elif "*" in first_option_value:
                    if re.match(first_option_value, second_option_value):
                        links.append(need_target["id"])

    return links


class SplSphinx:
    """Centralized Sphinx configuration for SPL projects.

    This class provides default configurations for sphinx-needs extension,
    including custom need types, link types, and linking functions.

    All configurations are available as class properties:
    - default_needs_types: Need type configurations (req, spec, impl, test)
    - default_needs_extra_options: Additional need options
    - default_needs_extra_links: Link type configurations for traceability
    - default_needs_global_options: Global options for needs
    - default_needs_functions: Custom needs functions
    - default_extensions: List of Sphinx extensions
    - default_extension_configs: Extension-specific configurations
    """

    # Needs Global Options - automatically links test results to test cases
    # sphinx-needs 6.x requires FieldDefault format: {"default": ...}
    default_needs_global_options: ClassVar[dict[str, dict[str, str]]] = {
        "results": {"default": "[[sple_tr_link('title', 'case')]]"},
    }

    # Needs Functions - custom linking functions
    default_needs_functions: ClassVar[list[Any]] = [sple_tr_link]

    # Default Sphinx Extensions
    default_extensions: ClassVar[list[str]] = [
        "sphinx_rtd_size",
        "sphinxcontrib.mermaid",
        "sphinx_needs",
        "sphinxcontrib.test_reports",
        "sphinx.ext.todo",
        "sphinxcontrib.datatemplates",
        "myst_parser",
    ]

    # Extension-specific configurations
    default_extension_configs: ClassVar[dict[str, str | list[str]]] = {
        "sphinx_rtd_size_width": "90%",
        "tr_report_template": "doc/test_report_template.txt",
        "myst_enable_extensions": [
            "colon_fence",
            "deflist",
            "html_admonition",
            "html_image",
        ],
        "source_suffix": [
            ".rst",
            ".md",
        ],
    }

    @classmethod
    def get_default_html_context(cls) -> dict[str, Any]:
        """Get the default HTML context for Sphinx builds.

        Loads build and feature configurations from environment variables:
        - SPHINX_BUILD_CONFIGURATION_FILE: JSON file with build configuration
        - AUTOCONF_JSON_FILE: JSON file with feature configuration
        - VARIANT: variant name

        Returns a dictionary with ``build_config``, ``config``, and ``timestamp`` keys.
        Note: call ``include_patterns.extend(html_context["build_config"].get("include_patterns", []))
        in conf.py`` to propagate include patterns from the build configuration.
        """
        context: dict[str, Any] = {
            "build_config": {},
            "config": {},
            "timestamp": f"{datetime.datetime.now(tz=datetime.UTC).strftime('%Y-%m-%d %H:%M:%S')} UTC",
        }

        if "SPHINX_BUILD_CONFIGURATION_FILE" in os.environ:
            with open(os.environ["SPHINX_BUILD_CONFIGURATION_FILE"]) as file:
                context["build_config"] = json.load(file)

        if "AUTOCONF_JSON_FILE" in os.environ:
            with open(os.environ["AUTOCONF_JSON_FILE"]) as file:
                context["config"] = json.load(file)["features"]

        if "VARIANT" in os.environ:
            context["build_config"]["variant"] = os.environ["VARIANT"]

        return context
