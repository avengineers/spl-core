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
reader of needs.json sees the results, not only Sphinx.

Turning the option on needs these changes in `conf.py`:

- Remove the `results` default from `needs_global_options` (the `SplSphinx` default
  `[[sple_tr_link('title', 'case')]]`). Otherwise `sple_tr_link` finds the same
  cases again and each specification lists every case twice.
- Keep the `sphinxcontrib.test_reports` extension, or declare what it registers: the
  need types `testfile`, `testsuite` and `testcase`, the fields `file`, `suite`,
  `case`, `case_name`, `case_parameter`, `classname`, `result`, `time`, `suites`,
  `cases`, `passed`, `skipped`, `failed` and `errors`, and the `tr_*` styles they
  use. Without them `needimport` skips every need and the page stays empty.

The page is a fixed `needimport`: the project's
`tr_report_template` is no longer used, so its statistics and tables are gone.

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
