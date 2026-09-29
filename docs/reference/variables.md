# CMake Variables

(GCOVR_ADDITIONAL_OPTIONS)=

## GCOVR_ADDITIONAL_OPTIONS

A CMake variable to pass additional options to all `gcovr` invocations. This affects
per-component coverage JSON and HTML generation as well as variant-level report generation.

**Default:** empty (no additional options)

Example — exclude generated and third-party files from coverage:

```cmake
set(GCOVR_ADDITIONAL_OPTIONS "--exclude=.*test.*" "--exclude=.*mock.*")
```

Example — set a minimum coverage threshold:

```cmake
set(GCOVR_ADDITIONAL_OPTIONS "--fail-under-line=80")
```

(SPL_SOURCE_DOCS_JINJA_RAW_TAGS)=

## SPL_SOURCE_DOCS_JINJA_RAW_TAGS

Whether clanguru wraps each code listing it generates under `__source_docs` in
Jinja `{% raw %}` and `{% endraw %}` lines. The markers protect the C code from a
Jinja `source-read` hook that renders every document, as the kickstart template's
`conf.py` does. A project without such a hook turns the option off; otherwise the
two markers appear as text on every listing page.

**Default:** `ON`

```cmake
set(SPL_SOURCE_DOCS_JINJA_RAW_TAGS OFF)
```

(SPL_VARIANT_DATA_FILE_DOCS)=

## SPL_VARIANT_DATA_FILE_DOCS and SPL_VARIANT_DATA_FILE_REPORTS

The sphinx-needs variant data file for the `docs` and the `reports` Sphinx builds,
including the per-component ones. When set, `sphinx-build` gets
`-D needs_variant_data_file=<path>`. sphinx-needs keeps a command-line override
even when the file named by `needs_from_toml` sets another one, so each build
evaluates its `{if}` directives and variant conditions against the data for its
own shape, with no code in `conf.py`. It is the same key `ubc` overrides with
`-c "needs.variant_data_file = '<path>'"`.

**Default:** empty (the build reads whatever the project configures)

```cmake
set(SPL_VARIANT_DATA_FILE_DOCS ${CMAKE_SOURCE_DIR}/build/variants/${VARIANT}/${BUILD_KIT}/docs.json)
set(SPL_VARIANT_DATA_FILE_REPORTS ${CMAKE_SOURCE_DIR}/build/variants/${VARIANT}/${BUILD_KIT}/reports.json)
```

(SPL_SPHINX_SOURCE_DIR)=

## SPL_SPHINX_SOURCE_DIR

The directory `sphinx-build` reads its documents and `conf.py` from, for every docs
and reports target. A relative path is taken relative to the project root. Every
path spl-core writes for Sphinx, in the `config.json` include patterns, the
component information and the generated toctrees, is relative to this directory,
so what a build includes has to be reachable inside it.

**Default:** the project root (`PROJECT_SOURCE_DIR`)

```cmake
set(SPL_SPHINX_SOURCE_DIR docs)
```

(SPL_SPHINX_OPTIONS)=

## SPL_SPHINX_OPTIONS and SPL_SPHINX_COMPONENT_OPTIONS

Options added to every `sphinx-build` spl-core runs: `SPL_SPHINX_OPTIONS` to the
variant `docs` and `reports` builds, `SPL_SPHINX_COMPONENT_OPTIONS` to the
per-component docs and report builds. In both, `@SHAPE@` becomes `docs` or
`reports` and `@COMPONENT_PATH@` the component's path relative to the project
root (empty for the variant builds), so each run can name a file of its own.

**Default:** none

```cmake
set(SPL_SPHINX_OPTIONS -D spl_selection=${CMAKE_BINARY_DIR}/selection/@SHAPE@.toml)
set(SPL_SPHINX_COMPONENT_OPTIONS -D spl_selection=${CMAKE_BINARY_DIR}/selection/@COMPONENT_PATH@/@SHAPE@.toml)
```

(SPL_TEST_RESULTS_AS_NEEDS)=

## SPL_TEST_RESULTS_AS_NEEDS

When `ON`, a component's unit test results page is written after each test run
from its JUnit XML, instead of at configure time with sphinx-test-reports'
`test-report` directive. `spl_core.test_report.junit_to_needs` converts the JUnit
XML into `unit_test_results.needs.json`, with the same needs, IDs and fields the
directive creates, and writes a page that imports it with `needimport`. The page
also carries the `results` links of the component's test specifications as
`needextend` blocks: a specification links every test case whose name equals its
title, or matches it as a regular expression when the title contains `*`. Every
reader of needs.json sees the results, not only Sphinx, and the project can drop
the `sphinxcontrib.test_reports` extension and the `sple_tr_link` needs function.

**Default:** `OFF`

```cmake
set(SPL_TEST_RESULTS_AS_NEEDS ON)
```

## COMPONENT_NAMES

## PROD_SOURCES

List of all productive source files of all components of the current variant.

(target_include_directories__INCLUDES)=

## target_include_directories__INCLUDES

List of all include directories of all components of the current variant.

```{attention}
This variable is deprecated and will be removed in a future release.
Use {ref}`spl_add_provided_interface <spl_add_provided_interface>` and {ref}`spl_add_required_interface <spl_add_required_interface>` instead.
```
