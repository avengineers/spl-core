# Sphinx Configuration (`conf.py`)

The `conf.py` is the central Sphinx configuration file for the project. Most
settings are provided by `spl_core` and only need to be wired up here.

## Required Imports

```python
from importlib.resources import files
from spl_core.report_generation.spl_sphinx import SplSphinx
from spl_core.report_generation.spl_html_settings import html_theme, html_show_sourcelink, html_theme_options, html_sidebars  # noqa: F401
```

## HTML Theme

The HTML theme settings (`pydata_sphinx_theme`) are provided via the import
above and active automatically. To override them, reassign the variables after
the import:

```python
html_theme = "my_custom_theme"
```

## Extensions

Use `SplSphinx` to get the default set of extensions and their configurations:

```python
extensions = SplSphinx.default_extensions
extension_configs = SplSphinx.default_extension_configs

tr_report_template = extension_configs["tr_report_template"]
myst_enable_extensions = extension_configs["myst_enable_extensions"]
source_suffix = extension_configs["source_suffix"]
```

## sphinx-needs Configuration

The needs configuration (types, extra options, link types) is loaded from a
TOML file shipped with `spl_core`:

```python
needs_from_toml = str(files("spl_core.report_generation").joinpath("ubproject.toml"))
```

To enable linking between test cases and their results, the following settings
must also be configured:

```python
needs_functions = SplSphinx.default_needs_functions
needs_global_options = SplSphinx.default_needs_global_options
```

## HTML Context

Use `SplSphinx.get_default_html_context()` to load the HTML context for Jinja
templating. It reads build and feature configurations from environment variables
(`SPHINX_BUILD_CONFIGURATION_FILE`, `AUTOCONF_JSON_FILE`, `VARIANT`) and
returns a dictionary with `build_config`, `config`, and `timestamp` keys.

```python
html_context = SplSphinx.get_default_html_context()
include_patterns.extend(html_context["build_config"].get("include_patterns", []))
```
