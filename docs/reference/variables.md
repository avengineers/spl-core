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
