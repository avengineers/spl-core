"""Sphinx extension that injects the SPL platform layout CSS and sidebar template.

Add ``"spl_core.report_generation.spl_theme_extension"`` to your Sphinx
``extensions`` list.  The extension automatically registers the static
directory, CSS file, and a custom sidebar template so that downstream
projects don't need to manage paths themselves.

The custom sidebar template replicates the Read the Docs theme behaviour:
on orphan pages (e.g., Doxygen sub-pages from doxysphinx) the root toctree
is shown as fallback navigation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sphinx.application import Sphinx
from sphinx.config import Config

_STATIC_DIR = str(Path(__file__).resolve().parent / "static")
_TEMPLATES_DIR = str(Path(__file__).resolve().parent / "templates")


def setup(app: Sphinx) -> dict[str, Any]:
    """Register static assets and templates with Sphinx."""
    app.connect("config-inited", _add_templates_path)
    app.connect("builder-inited", _add_static_assets)
    return {"version": "1.0", "parallel_read_safe": True, "parallel_write_safe": True}


def _add_templates_path(app: Sphinx, config: Config) -> None:
    """Register template directory early so the Jinja2 loader picks it up."""
    if _TEMPLATES_DIR not in config.templates_path:
        config.templates_path.append(_TEMPLATES_DIR)


def _add_static_assets(app: Sphinx) -> None:
    """Append the package static dir, register CSS file, and set default logo."""
    if _STATIC_DIR not in app.config.html_static_path:
        app.config.html_static_path.append(_STATIC_DIR)
    app.add_css_file("spl_custom.css")

    # Set default logo if no project-level html_logo is configured
    if not app.config.html_logo:
        app.config.html_logo = str(Path(_STATIC_DIR) / "avengineers_logo.jpg")
