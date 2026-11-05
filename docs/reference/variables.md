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
two markers appear as text on every listing page. ubCode and `ubc` render no
Jinja, so a project they read turns it off.

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
root (empty for the variant builds), so each run can name a file or directory of
its own, such as a configuration file passed with `-D` that a project's `conf.py`
reads.

**Default:** none

```cmake
set(SPL_SPHINX_OPTIONS -d ${CMAKE_BINARY_DIR}/doctrees/@SHAPE@)
set(SPL_SPHINX_COMPONENT_OPTIONS -d ${CMAKE_BINARY_DIR}/doctrees/@COMPONENT_PATH@/@SHAPE@)
```

(SPL_UBCODE_SELECTION_FILE)=

## SPL_UBCODE_SELECTION_FILE

Path, relative to the project root, of a ubCode configuration file that a test-kit
configure writes. It selects the documents and the variant data of the configured build,
so ubCode and `ubc` show the same variant as CMake Tools. The project's committed
`ubproject.toml` names the file with `extend`; keep it out of git. Setting the variable
also gives every Sphinx run `-D needs_variant_data_file`, and the runs of every component
with a doc index a generated root page. See ADR 0005.

Set the variable before `include(.../parts.cmake)`. Otherwise the components miss
their Sphinx options and root pages. Removing the variable leaves a selection file written
earlier in place; delete it yourself.

**Default:** none (configure writes nothing into the source tree)

```cmake
set(SPL_UBCODE_SELECTION_FILE ubproject.variants.toml)
```

(SPL_PROJECT_DOCS_INCLUDE_PATTERNS)=

## SPL_PROJECT_DOCS_INCLUDE_PATTERNS

Include patterns for the project's own documents outside its components, such as
`index.md` or `doc/**`. spl-core puts them before the component patterns in the
`include_patterns` of the variant `docs` and `reports` runs. ubCode reads the same list
through `SPL_UBCODE_SELECTION_FILE`. With that variable set, a pattern that is not
`…/**` and does not end in `.md` or `.rst` is not read by ubCode, and a test-kit
configure warns (see ADR 0005).

**Default:** empty

```cmake
set(SPL_PROJECT_DOCS_INCLUDE_PATTERNS index.md "doc/**")
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
