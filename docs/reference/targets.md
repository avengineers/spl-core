# CMake Targets

## reports

Generates the overall variant report.

**Output path:** `build/<Variant>/test/Debug/reports/html/index.html`

## unittests

Runs all unit tests for the given variant.

**Output paths:**

- Unit test results (JUnit XML): `build/<Variant>/test/Debug/<component path>/junit.xml`
- Coverage report: `build/<Variant>/test/Debug/<component path>/reports/coverage/index.html`

(component_cmake_targets)=

## \<component\>_report

Generate component report with full traceability between documentation, code and tests.

**Output path:** `build/<Variant>/test/Debug/<component path>/reports/html/index.html`

## \<component\>_unittests

Runs the unit tests for the given component.

**Output paths:**

- Unit test results (JUnit XML): `build/<Variant>/test/Debug/<component path>/junit.xml`
- Coverage report: `build/<Variant>/test/Debug/<component path>/reports/coverage/index.html`
