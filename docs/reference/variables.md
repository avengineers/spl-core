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
