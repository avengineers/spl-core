import pytest
from junitparser import Failure, JUnitXml, TestCase, TestSuite

from spl_core.test_utils.junit_merger import JUnitMerger, JUnitMergerError, main


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for testing"""
    yield tmp_path


@pytest.fixture
def sample_junit_xml_1(temp_dir):
    """Create first sample JUnit XML file"""
    xml_path = temp_dir / "component1_junit.xml"

    # Create test suite with some passing and failing tests
    suite = TestSuite("Component1TestSuite")

    test1 = TestCase("test_addition")
    test1.classname = "MathTests"
    suite.add_testcase(test1)

    test2 = TestCase("test_subtraction")
    test2.classname = "MathTests"
    test2.result = [Failure("Expected 2 but got 3", "AssertionError")]
    suite.add_testcase(test2)

    xml = JUnitXml()
    xml.add_testsuite(suite)
    xml.write(str(xml_path))

    return xml_path


@pytest.fixture
def sample_junit_xml_2(temp_dir):
    """Create second sample JUnit XML file"""
    xml_path = temp_dir / "component2_junit.xml"

    # Create test suite with different tests
    suite = TestSuite("Component2TestSuite")

    test1 = TestCase("test_multiplication")
    test1.classname = "AdvancedMathTests"
    suite.add_testcase(test1)

    test2 = TestCase("test_division")
    test2.classname = "AdvancedMathTests"
    suite.add_testcase(test2)

    xml = JUnitXml()
    xml.add_testsuite(suite)
    xml.write(str(xml_path))

    return xml_path


@pytest.fixture
def sample_junit_xml_empty(temp_dir):
    """Create empty JUnit XML file (no test cases)"""
    xml_path = temp_dir / "component3_junit.xml"

    suite = TestSuite("EmptyTestSuite")

    xml = JUnitXml()
    xml.add_testsuite(suite)
    xml.write(str(xml_path))

    return xml_path


@pytest.fixture
def malformed_xml_file(temp_dir):
    """Create malformed XML file"""
    xml_path = temp_dir / "malformed.xml"
    xml_path.write_text("<invalid><xml>No closing tag")
    return xml_path


@pytest.fixture
def single_testsuite_xml_file(temp_dir):
    """Create JUnit XML file with single testsuite structure (like GoogleTest generates)"""
    # Create component subdirectory to match production structure
    component_dir = temp_dir / "component1"
    component_dir.mkdir()
    xml_path = component_dir / "junit.xml"

    # Write XML manually to match GoogleTest output structure: single <testsuite> without <testsuites> wrapper
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="(empty)" tests="3" failures="0" disabled="0" skipped="0" hostname="" time="0" timestamp="2026-02-04T09:37:47">
    <testcase name="test_case_1" classname="component1.test_case_1" time="0.001" status="run">
    </testcase>
    <testcase name="test_case_2" classname="component1.test_case_2" time="0.002" status="run">
    </testcase>
    <testcase name="test_case_3" classname="component1.test_case_3" time="0.003" status="run">
    </testcase>
</testsuite>
"""
    xml_path.write_text(xml_content)
    return xml_path


@pytest.fixture
def another_single_testsuite_xml_file(temp_dir):
    """Create another JUnit XML file with single testsuite structure"""
    # Create component subdirectory to match production structure
    component_dir = temp_dir / "component2"
    component_dir.mkdir()
    xml_path = component_dir / "junit.xml"

    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="(empty)" tests="2" failures="0" disabled="0" skipped="0" hostname="" time="0" timestamp="2026-02-04T09:37:48">
    <testcase name="test_foo" classname="component2.test_foo" time="0.001" status="run">
    </testcase>
    <testcase name="test_bar" classname="component2.test_bar" time="0.002" status="run">
    </testcase>
</testsuite>
"""
    xml_path.write_text(xml_content)
    return xml_path


def test_merge_junit_files_success(temp_dir, sample_junit_xml_1, sample_junit_xml_2):
    """Test successful merge of multiple JUnit XML files"""
    # Arrange
    output_path = temp_dir / "variant-junit.xml"
    input_files = [str(sample_junit_xml_1), str(sample_junit_xml_2)]
    merger = JUnitMerger(input_files, str(output_path))

    # Act
    merger.merge()

    # Assert
    assert output_path.exists()
    merged_xml = JUnitXml.fromfile(str(output_path))
    assert len(list(merged_xml)) == 2
    total_tests = sum(len(list(suite)) for suite in merged_xml)
    assert total_tests == 4
    suite_names = [suite.name for suite in merged_xml]
    assert "Component1TestSuite" in suite_names
    assert "Component2TestSuite" in suite_names


def test_merge_junit_files_with_empty_suite(temp_dir, sample_junit_xml_1, sample_junit_xml_empty):
    """Test merge handling empty test suites"""
    # Arrange
    output_path = temp_dir / "variant-junit.xml"
    input_files = [str(sample_junit_xml_1), str(sample_junit_xml_empty)]
    merger = JUnitMerger(input_files, str(output_path))

    # Act
    merger.merge()

    # Assert
    assert output_path.exists()
    merged_xml = JUnitXml.fromfile(str(output_path))
    assert len(list(merged_xml)) == 2


def test_merge_junit_files_single_file(temp_dir, sample_junit_xml_1):
    """Test merge with single input file"""
    # Arrange
    output_path = temp_dir / "variant-junit.xml"
    input_files = [str(sample_junit_xml_1)]
    merger = JUnitMerger(input_files, str(output_path))

    # Act
    merger.merge()

    # Assert
    assert output_path.exists()
    merged_xml = JUnitXml.fromfile(str(output_path))
    assert len(list(merged_xml)) == 1


def test_merge_junit_files_missing_file(temp_dir, sample_junit_xml_1):
    """Test merge when one input file is missing"""
    # Arrange
    output_path = temp_dir / "variant-junit.xml"
    missing_file = temp_dir / "nonexistent.xml"
    input_files = [str(sample_junit_xml_1), str(missing_file)]
    merger = JUnitMerger(input_files, str(output_path))

    # Act & Assert
    with pytest.raises(FileNotFoundError):
        merger.merge()


def test_merge_junit_files_malformed_xml(temp_dir, sample_junit_xml_1, malformed_xml_file):
    """Test merge when one file contains malformed XML"""
    # Arrange
    output_path = temp_dir / "variant-junit.xml"
    input_files = [str(sample_junit_xml_1), str(malformed_xml_file)]
    merger = JUnitMerger(input_files, str(output_path))

    # Act & Assert
    with pytest.raises(JUnitMergerError):
        merger.merge()


def test_merge_junit_files_empty_input_list(temp_dir):
    """Test merge with no input files"""
    # Arrange
    output_path = temp_dir / "variant-junit.xml"
    input_files: list[str] = []

    # Act & Assert
    with pytest.raises(ValueError):
        JUnitMerger(input_files, str(output_path))


def test_merge_junit_files_preserves_test_attributes(temp_dir, sample_junit_xml_1):
    """Test that merge preserves test case attributes like classname"""
    # Arrange
    output_path = temp_dir / "variant-junit.xml"
    input_files = [str(sample_junit_xml_1)]
    merger = JUnitMerger(input_files, str(output_path))

    # Act
    merger.merge()

    # Assert
    merged_xml = JUnitXml.fromfile(str(output_path))
    suite = next(iter(merged_xml))
    test_cases = list(suite)
    assert any(tc.classname == "MathTests" for tc in test_cases)


def test_merge_junit_files_preserves_failure_info(temp_dir, sample_junit_xml_1):
    """Test that merge preserves test failure information"""
    # Arrange
    output_path = temp_dir / "variant-junit.xml"
    input_files = [str(sample_junit_xml_1)]
    merger = JUnitMerger(input_files, str(output_path))

    # Act
    merger.merge()

    # Assert
    merged_xml = JUnitXml.fromfile(str(output_path))
    suite = next(iter(merged_xml))
    test_cases = list(suite)
    failing_test = next((tc for tc in test_cases if tc.name == "test_subtraction"), None)
    assert failing_test is not None
    assert failing_test.result is not None


def test_main_cli_success(temp_dir, sample_junit_xml_1, sample_junit_xml_2, monkeypatch):
    """Test CLI interface with successful merge"""
    # Arrange
    output_path = temp_dir / "variant-junit.xml"
    test_args = ["junit_merger.py", "--output", str(output_path), "--inputs", str(sample_junit_xml_1), str(sample_junit_xml_2)]
    monkeypatch.setattr("sys.argv", test_args)

    # Act
    exit_code = main()

    # Assert
    assert exit_code == 0
    assert output_path.exists()


def test_main_cli_with_error(temp_dir, malformed_xml_file, monkeypatch, capsys):
    """Test CLI interface handles errors and prints warnings"""
    # Arrange
    output_path = temp_dir / "variant-junit.xml"
    test_args = ["junit_merger.py", "--output", str(output_path), "--inputs", str(malformed_xml_file)]
    monkeypatch.setattr("sys.argv", test_args)

    # Act
    exit_code = main()

    # Assert
    assert exit_code != 0
    captured = capsys.readouterr()
    assert "error" in captured.err.lower() or "warning" in captured.err.lower()


def test_merge_validates_output(temp_dir, sample_junit_xml_1, sample_junit_xml_2):
    """Test that merged output is valid JUnit XML"""
    # Arrange
    output_path = temp_dir / "variant-junit.xml"
    input_files = [str(sample_junit_xml_1), str(sample_junit_xml_2)]
    merger = JUnitMerger(input_files, str(output_path))

    # Act
    merger.merge()

    # Assert
    merged_xml = JUnitXml.fromfile(str(output_path))
    assert len(list(merged_xml)) > 0


def test_merge_single_testsuite_files(temp_dir, single_testsuite_xml_file, another_single_testsuite_xml_file):
    """Test merging files with single testsuite structure (GoogleTest format)"""
    # Arrange
    output_path = temp_dir / "variant-junit.xml"
    input_files = [str(single_testsuite_xml_file), str(another_single_testsuite_xml_file)]
    merger = JUnitMerger(input_files, str(output_path))

    # Act
    merger.merge()

    # Assert
    assert output_path.exists()
    merged_xml = JUnitXml.fromfile(str(output_path))

    # Should have 2 test suites
    suites = list(merged_xml)
    assert len(suites) == 2

    # Verify suite names (should use parent directory names since original names are empty)
    suite_names = [suite.name for suite in suites]
    assert "component1" in suite_names
    assert "component2" in suite_names

    # Verify test counts
    suite1 = next(s for s in suites if s.name == "component1")
    suite2 = next(s for s in suites if s.name == "component2")
    assert len(list(suite1)) == 3  # 3 testcases
    assert len(list(suite2)) == 2  # 2 testcases


def test_merge_mixed_testsuite_formats(temp_dir, sample_junit_xml_1, single_testsuite_xml_file):
    """Test merging files with both multi-testsuite and single-testsuite formats"""
    # Arrange
    output_path = temp_dir / "variant-junit.xml"
    input_files = [str(sample_junit_xml_1), str(single_testsuite_xml_file)]
    merger = JUnitMerger(input_files, str(output_path))

    # Act
    merger.merge()

    # Assert
    assert output_path.exists()
    merged_xml = JUnitXml.fromfile(str(output_path))

    # Should have 2 test suites (one from each file)
    suites = list(merged_xml)
    assert len(suites) == 2

    # Verify both suite names are present
    suite_names = [suite.name for suite in suites]
    assert "Component1TestSuite" in suite_names  # from multi-testsuite file
    assert "component1" in suite_names  # from single-testsuite file (using parent directory)


def test_merge_with_variant_name(temp_dir, sample_junit_xml_1, sample_junit_xml_2):
    """Test merge with variant name prefixes all suite names"""
    # Arrange
    output_path = temp_dir / "variant-junit.xml"
    input_files = [str(sample_junit_xml_1), str(sample_junit_xml_2)]
    variant_name = "my_variant"
    merger = JUnitMerger(input_files, str(output_path), variant=variant_name)

    # Act
    merger.merge()

    # Assert
    assert output_path.exists()
    merged_xml = JUnitXml.fromfile(str(output_path))

    # All suite names should be prefixed with variant
    suite_names = [suite.name for suite in merged_xml]
    assert "my_variant.Component1TestSuite" in suite_names
    assert "my_variant.Component2TestSuite" in suite_names
    assert len(suite_names) == 2


def test_merge_with_variant_name_with_underscores(temp_dir, sample_junit_xml_1):
    """Test merge with variant name that has underscores (pre-sanitized)"""
    # Arrange
    output_path = temp_dir / "variant-junit.xml"
    input_files = [str(sample_junit_xml_1)]
    variant_name = "my_complex_variant"
    merger = JUnitMerger(input_files, str(output_path), variant=variant_name)

    # Act
    merger.merge()

    # Assert
    assert output_path.exists()
    merged_xml = JUnitXml.fromfile(str(output_path))

    suite = next(iter(merged_xml))
    assert suite.name == "my_complex_variant.Component1TestSuite"


def test_merge_without_variant_backward_compatibility(temp_dir, sample_junit_xml_1, sample_junit_xml_2):
    """Test that merge without variant argument works as before (backward compatibility)"""
    # Arrange
    output_path = temp_dir / "variant-junit.xml"
    input_files = [str(sample_junit_xml_1), str(sample_junit_xml_2)]
    merger = JUnitMerger(input_files, str(output_path))  # No variant argument

    # Act
    merger.merge()

    # Assert
    assert output_path.exists()
    merged_xml = JUnitXml.fromfile(str(output_path))

    # Suite names should NOT be prefixed
    suite_names = [suite.name for suite in merged_xml]
    assert "Component1TestSuite" in suite_names
    assert "Component2TestSuite" in suite_names
    assert len(suite_names) == 2


def test_merge_with_variant_and_empty_suite_names(temp_dir, single_testsuite_xml_file, another_single_testsuite_xml_file):
    """Test merge with variant when suite names are empty (should use parent dir + variant prefix)"""
    # Arrange
    output_path = temp_dir / "variant-junit.xml"
    input_files = [str(single_testsuite_xml_file), str(another_single_testsuite_xml_file)]
    variant_name = "production"
    merger = JUnitMerger(input_files, str(output_path), variant=variant_name)

    # Act
    merger.merge()

    # Assert
    assert output_path.exists()
    merged_xml = JUnitXml.fromfile(str(output_path))

    # Suite names should be variant.component_name
    suite_names = [suite.name for suite in merged_xml]
    assert "production.component1" in suite_names
    assert "production.component2" in suite_names
    assert len(suite_names) == 2


def test_main_cli_with_variant_argument(temp_dir, sample_junit_xml_1, sample_junit_xml_2, monkeypatch):
    """Test CLI interface with variant argument"""
    # Arrange
    output_path = temp_dir / "variant-junit.xml"
    variant_name = "test_variant"
    test_args = ["junit_merger.py", "--output", str(output_path), "--variant", variant_name, "--inputs", str(sample_junit_xml_1), str(sample_junit_xml_2)]
    monkeypatch.setattr("sys.argv", test_args)

    # Act
    exit_code = main()

    # Assert
    assert exit_code == 0
    assert output_path.exists()

    # Verify variant was applied
    merged_xml = JUnitXml.fromfile(str(output_path))
    suite_names = [suite.name for suite in merged_xml]
    assert "test_variant.Component1TestSuite" in suite_names
    assert "test_variant.Component2TestSuite" in suite_names


def test_merge_removes_properties_and_system_out(temp_dir):
    """Test that merge removes <properties> and <system-out> from testcases while preserving test results"""
    # Arrange - Create input file with verbose blocks
    component_dir = temp_dir / "test_component"
    component_dir.mkdir()
    input_file = component_dir / "junit.xml"

    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="TestSuite" tests="2" failures="1" disabled="0" skipped="0">
    <testcase name="test_pass" classname="Tests.test_pass" time="0.001" status="run">
        <properties>
            <property name="key" value="value"/>
        </properties>
        <system-out>Verbose output from passing test</system-out>
    </testcase>
    <testcase name="test_fail" classname="Tests.test_fail" time="0.002" status="run">
        <properties/>
        <system-out>Verbose output from failing test</system-out>
        <system-err>Some error output that should be preserved</system-err>
        <failure message="Test failed" type="AssertionError">Stack trace here</failure>
    </testcase>
</testsuite>
"""
    input_file.write_text(xml_content)

    output_path = temp_dir / "merged-junit.xml"
    merger = JUnitMerger([str(input_file)], str(output_path))

    # Act
    merger.merge()

    # Assert - Verify output exists and is valid
    assert output_path.exists()
    merged_xml = JUnitXml.fromfile(str(output_path))

    # Get the test suite and testcases
    suite = next(iter(merged_xml))
    testcases = list(suite)
    assert len(testcases) == 2

    # Check that properties and system-out are removed
    for testcase in testcases:
        # Verify system_out is None or empty
        assert testcase.system_out is None or testcase.system_out == ""

        # Verify properties element is not present in the XML
        if hasattr(testcase, "_elem") and testcase._elem is not None:
            properties_elem = testcase._elem.find("properties")
            assert properties_elem is None, "Properties element should be removed"

            # Verify system-out element is not present
            system_out_elem = testcase._elem.find("system-out")
            assert system_out_elem is None or (system_out_elem.text is None or system_out_elem.text.strip() == ""), "System-out element should be removed or empty"

    # Verify that critical test result elements are preserved
    failing_test = next((tc for tc in testcases if tc.name == "test_fail"), None)
    assert failing_test is not None
    assert failing_test.result is not None, "Failure information should be preserved"

    # Verify essential attributes are preserved
    passing_test = next((tc for tc in testcases if tc.name == "test_pass"), None)
    assert passing_test is not None
    assert passing_test.classname == "Tests.test_pass"
    assert passing_test.time == 0.001


def test_variant_prefixes_testcase_classnames(temp_dir, sample_junit_xml_1, sample_junit_xml_2):
    """Test that variant name prefixes both suite names and testcase classnames"""
    # Arrange
    output_path = temp_dir / "variant-junit.xml"
    input_files = [str(sample_junit_xml_1), str(sample_junit_xml_2)]
    variant_name = "MyVariant"
    merger = JUnitMerger(input_files, str(output_path), variant=variant_name)

    # Act
    merger.merge()

    # Assert
    assert output_path.exists()
    merged_xml = JUnitXml.fromfile(str(output_path))

    # All suite names should be prefixed with variant
    suite_names = [suite.name for suite in merged_xml]
    assert "MyVariant.Component1TestSuite" in suite_names
    assert "MyVariant.Component2TestSuite" in suite_names

    # All testcase classnames should also be prefixed with variant
    for suite in merged_xml:
        for testcase in suite:
            assert testcase.classname.startswith("MyVariant."), f"Classname '{testcase.classname}' should start with variant prefix 'MyVariant.'"

    # Verify specific classnames from the test fixtures
    suite1 = next((s for s in merged_xml if s.name == "MyVariant.Component1TestSuite"), None)
    assert suite1 is not None
    testcases1 = list(suite1)
    assert any(tc.classname == "MyVariant.MathTests" for tc in testcases1), "Should have 'MyVariant.MathTests' classname"

    suite2 = next((s for s in merged_xml if s.name == "MyVariant.Component2TestSuite"), None)
    assert suite2 is not None
    testcases2 = list(suite2)
    assert any(tc.classname == "MyVariant.AdvancedMathTests" for tc in testcases2), "Should have 'MyVariant.AdvancedMathTests' classname"


def test_variant_with_empty_classnames(temp_dir):
    """Test that variant prefixing handles testcases with None or empty classnames gracefully"""
    # Arrange
    xml_path = temp_dir / "test_empty_classname.xml"

    suite = TestSuite("TestSuite")

    # Test case with normal classname
    test1 = TestCase("test_with_classname")
    test1.classname = "NormalClass"
    suite.add_testcase(test1)

    # Test case with None classname
    test2 = TestCase("test_without_classname")
    test2.classname = None
    suite.add_testcase(test2)

    # Test case with empty string classname
    test3 = TestCase("test_with_empty_classname")
    test3.classname = ""
    suite.add_testcase(test3)

    xml = JUnitXml()
    xml.add_testsuite(suite)
    xml.write(str(xml_path))

    output_path = temp_dir / "output.xml"
    variant_name = "MyVariant"
    merger = JUnitMerger([str(xml_path)], str(output_path), variant=variant_name)

    # Act
    merger.merge()

    # Assert
    assert output_path.exists()
    merged_xml = JUnitXml.fromfile(str(output_path))

    suite = next(iter(merged_xml))
    assert suite.name == "MyVariant.TestSuite"

    testcases = list(suite)
    assert len(testcases) == 3

    # Test case with normal classname should be prefixed
    tc1 = next((tc for tc in testcases if tc.name == "test_with_classname"), None)
    assert tc1 is not None
    assert tc1.classname == "MyVariant.NormalClass"

    # Test case with None classname should remain None (not prefixed)
    tc2 = next((tc for tc in testcases if tc.name == "test_without_classname"), None)
    assert tc2 is not None
    assert tc2.classname is None

    # Test case with empty classname should remain empty (not prefixed)
    tc3 = next((tc for tc in testcases if tc.name == "test_with_empty_classname"), None)
    assert tc3 is not None
    assert tc3.classname == ""
