# Report Generation Mechanism

The report navigation (which pages appear, and how they are grouped, per report
type) is built from two cooperating mechanisms:

1. **Data-driven Jinja templates** — the CMake build writes a `config.json`
   describing the current build target; the project's `conf.py` loads it into
   the Sphinx `html_context`, and every source page is rendered as a Jinja
   template against that context.
2. **CMake-generated per-component wrapper pages** — for the variant `reports`
   target, `common.cmake` emits one `{component}_index.md` file per component
   with documentation. Each wrapper is a real Sphinx document, so it becomes a
   collapsible node in the PyData Sphinx Theme left sidebar.

```{important}
Under the PyData Sphinx Theme the left sidebar only shows actual documents
(toctree targets); Markdown headings are relegated to the right-hand "On this
page" TOC. A flat `doc/components/index.md` that emits one `##` heading per
component therefore collapses into a single "Components" node. To restore a
collapsible node per component we generate one wrapper document per component.
See {doc}`../decisions/0001-report-navigation-is-jinja-driven`.
```

## Sphinx Build Configuration

Sphinx build required configuration file (conf.py) and main md (index.md) file are located in the same folder.
Because of this:

* we need conf.py and index.md files in the root directory
* the index.md file dynamically includes the target index.md
* the conf.py file needs to read a configuration file (config.json) to be able to find all the relevant files for the current CMake docs target

### conf.py

* conf.py is a static file and we do not know the path of the config.json file, so we get the path to it as an environment variable
* it checks whether the environment variable `SPHINX_BUILD_CONFIGURATION_FILE` exists, loads the content and stores it into the [html_context](https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-html_context)

### index.md

This file just includes the target index.md depending on the `docs` / `reports` CMake target.

## The `build_config` contract

`common.cmake` writes a `config.json` per Sphinx build and points the
`SPHINX_BUILD_CONFIGURATION_FILE` environment variable at it. Its content
depends on the target:

* **Component target** (`<component>_docs` / `<component>_report`): a single
  `component_info` object with `name`, `long_name`, `path`, `has_docs`,
  `has_reports`, `reports_output_dir`, plus `include_patterns`. For
  `<component>_report`, `component_info.source_docs_dir` and `include_patterns`
  also carry the clanguru source docs, which hold the test specifications.
* **Variant reports target** (`reports`): `target: "reports"`,
  `reports_output_dir`, `include_patterns`, and a `components_info` array whose
  entries have the same per-component fields as above.

`VARIANT` and `AUTOCONF_JSON_FILE` are passed as additional environment
variables (the latter exposes the KConfig feature selection).

## Files for ubCode and the variant data

See {doc}`../decisions/0005-configure-writes-the-selected-variant-for-ubcode`. Configure
writes these files next to `config.json`:

| File | Where | Written | Source |
| --- | --- | --- | --- |
| `features.json` | `<build>/kconfig/` | when the SPL has a KConfig model | `kconfig.py --out_features_file`: every KConfig symbol and every declared boolean |
| `variant_data.json` | next to each Sphinx run's `config.json` (variant and component, `docs` and `reports`) | always | `_spl_write_variant_data()` in `common.cmake`: `features` from `features.json` (`{}` without a model) and `build_config` with `variant`, `kit`, `target`, `scope`, `component`, `components` |
| `root_docs.md`, `root_reports.md` | the component's binary directory, outside the run output directories | only with `SPL_UBCODE_SELECTION_FILE` | `_spl_write_component_root_page()`: the component's title and a toctree of its pages; passed to the component run with `-D root_doc` |
| the selection file (`SPL_UBCODE_SELECTION_FILE`) | the project root | only with `SPL_UBCODE_SELECTION_FILE`, by a test-kit configure | `_spl_write_ubcode_selection()`: `[variants] data_file`, the md and rst parser `include` lists, then `report_generation/ubproject.toml` verbatim |

Only with `SPL_UBCODE_SELECTION_FILE` do the Sphinx commands carry
`-D needs_variant_data_file=<variant_data.json>`, and the component runs also
`-D root_doc` and the root page in their `include_patterns`. Without it, the commands
and the `config.json` files are as before, and configure removes root pages of an earlier
configure. The variant report wrapper pages and the root pages share one toctree source,
`_spl_component_page_content()`.

The selection's parser lists come from the include patterns of the variant `reports`
run, which start with `SPL_PROJECT_DOCS_INCLUDE_PATTERNS`. The ADR states the rule that
splits them between the md and the rst parser, and the warning for a pattern that fits
neither.

## From `config.json` to `html_context`

`spl_core.report_generation.spl_sphinx.SplSphinx.get_default_html_context()`
reads those environment variables and returns a context dictionary with:

* `build_config` — the parsed `config.json` (plus `variant`)
* `config` — the KConfig features from `AUTOCONF_JSON_FILE`
* `timestamp` — the build time

The project `conf.py` assigns it to `html_context` and extends the Sphinx
`include_patterns` from `build_config`:

```python
html_context = SplSphinx.get_default_html_context()
include_patterns.extend(html_context["build_config"].get("include_patterns", []))
```

## Rendering pages as Jinja templates

The project `conf.py` connects a `source-read` handler that renders every page
as a Jinja template against `html_context`:

```python
def rstjinja(app, docname, source):
    if app.builder.format != "html":
        return
    source[0] = app.builder.templates.render_string(source[0], app.config.html_context)

def setup(app):
    app.connect("source-read", rstjinja)
```

## Per-component wrapper pages

For the variant `reports` target, `_spl_create_reports_target()` in
`common.cmake` writes one wrapper document per component that has documentation
into the reports output directory (`{reports_output_dir}/{name}_index.md`):

````markdown
# <component long name or name>

```{toctree}
:maxdepth: 2

/<path>/doc/index
/<reports_output_dir>/unit_test_spec
/<reports_output_dir>/unit_test_results
/<reports_output_dir>/coverage
```
````

The report pages (`unit_test_spec`, `unit_test_results`, `coverage`) are only
linked when the component has reports (`has_reports`). The files live in the
build output directory and are regenerated on every CMake reconfigure (they are
registered via `CMAKE_CONFIGURE_DEPENDS`), so the wrapper set always matches the
variant's active component set. No wrapper is written for a component without
documentation.

## How pages are collected per report type

* **Root `index.md`** branches on `build_config.component_info` (present →
  Component Report) vs. otherwise (Variant Report), and on
  `build_config.target == 'reports'`, and builds the top-level `toctree`
  accordingly.
* **`doc/components/index.md`** loops over `build_config.components_info`. For
  the `reports` target it links each component (with docs) to its generated
  `{name}_index` wrapper page — one collapsible sidebar node per component. For
  the `docs` target (no wrapper pages) it links directly to each component's
  `doc/index`.

Report *content* per type is a pure function of `build_config` + the project
templates; the wrapper pages add the per-component sidebar hierarchy that the
PyData theme cannot express from Markdown headings alone.
