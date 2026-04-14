# CMake Targets

## reports

Generates the overall variant report.

**Output path:** `build/<Variant>/test/Debug/reports/html/index.html`

## unittests

Runs all unit tests for the given variant and generates merged coverage and test result artifacts.

**Output paths:**

- Unit test results (JUnit XML, per component): `build/<Variant>/test/Debug/<component path>/junit.xml`
- Coverage report (HTML, per component): `build/<Variant>/test/Debug/<component path>/reports/coverage/index.html`
- Coverage data (JSON, per component): `build/<Variant>/test/Debug/<component path>/coverage.json`
- Merged coverage summary (variant-level): `build/<Variant>/test/Debug/variant-coverage.json`
- Merged test results (variant-level): `build/<Variant>/test/Debug/variant-junit.xml`

## coverage

Aggregates all `<component>_coverage` targets. Generates coverage HTML and JSON for every
component in the variant.

## \<component\>_coverage

Generates coverage data and HTML report for the given component.

**Output paths:**

- Coverage data (JSON): `build/<Variant>/test/Debug/<component path>/coverage.json`
- Coverage report (HTML): `build/<Variant>/test/Debug/<component path>/reports/coverage/index.html`

(component_cmake_targets)=

## \<component\>_report

Generate component report with full traceability between documentation, code and tests.

**Output path:** `build/<Variant>/test/Debug/<component path>/reports/html/index.html`

## \<component\>_unittests

Runs the unit tests for the given component.

**Output paths:**

- Unit test results (JUnit XML): `build/<Variant>/test/Debug/<component path>/junit.xml`
- Coverage report (HTML): `build/<Variant>/test/Debug/<component path>/reports/coverage/index.html`
