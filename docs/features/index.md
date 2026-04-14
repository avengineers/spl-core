# ✨ Features

## Code Coverage

SPL Core automatically collects code coverage data when running unit tests and generates
both per-component and variant-level reports using [gcovr](https://gcovr.com).

### Per-component coverage

After running the `<component>_unittests` or `unittests` target, each component produces:

- `coverage.json` — raw coverage data in gcovr JSON format
- `reports/coverage/index.html` — HTML coverage report

Both files are located under `build/<Variant>/test/Debug/<component path>/`.

### Variant-level coverage

After running the `unittests` target, SPL Core merges all component coverage files into
a single variant-level summary:

- `variant-coverage.json` — merged JSON summary (gcovr `--json-summary-pretty` format)

This file is located at `build/<Variant>/test/Debug/`.

### Customization

Additional gcovr options can be passed via the CMake variable `GCOVR_ADDITIONAL_OPTIONS`.
See {ref}`GCOVR_ADDITIONAL_OPTIONS <GCOVR_ADDITIONAL_OPTIONS>` for details.

### Incremental build safety

The `coverage.json` generation depends on the `gcovr` executable itself. This means
CMake automatically regenerates coverage data when gcovr is updated, preventing
format version mismatches in incremental builds.

## Component Report

To support the {ref}`component <glossary_component>` development, SPL Core provides features to:

- document the component behavior - see {ref}`How to create a component detail design <how_to_component_detail_design>`
- test the component behavior - see {ref}`How to create a component test cases <how_to_component_test_cases>`
- generate component report with full traceability between documentation, code and tests - see {ref}`Component relevant CMake Targets <component_cmake_targets>`

The component report can be found at: `build/<Variant>/test/Debug/<component path>/reports/html/index.html`

## Variant Report

To support the {ref}`variant <glossary_variant>` development, SPL Core provides features to generate variant report including all component reports with full traceability

The variant report can be found at: `build/<Variant>/test/Debug/reports/html/index.html`

## Multi-Binary Support

To support variants with related multiple binaries, SPL Core provides the possibility to define
multiple executables and specify to which executable to add a component.

The use case can be building the application and its corresponding bootloader as two separate binaries
for a variant.

For this, one can specify the target executable when using the `spl_add_component()`
and `spl_add_named_component()` macros.

Example of defining multiple executables:

```cmake
# parts.cmake

# Components added to the default executable created automatically by spl_core
spl_add_component(src/compA)
spl_add_component(src/compB)

# Add new executable
add_executable(bootloader)
# Bootloader-specific components
spl_add_component(src/compA bootloader)
spl_add_component(src/boot  bootloader)
```

## Pypeline Steps

Spl-Core provides the step CollectPRChanges for [Pypeline](https://github.com/cuinixam/pypeline) to be used in an SPL.
This step fetches the list of changed files inside a pull request (PR), which can then be used for granular quality gate checks inside an SPL.
To use this step, you need to add it to your pypeline.yaml file as follows:

```yaml
...
- step: CheckCIContext
  module: pypeline_semantic_release.check_ci_context
- step: CollectPRChanges
  module: spl_core.steps.collect_pr_changes
...
```

It is mandatory that the CheckCIContext step is executed before the CollectPRChanges step.
