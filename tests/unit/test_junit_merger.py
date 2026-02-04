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
        <properties/>
        <system-out>Test output 1</system-out>
    </testcase>
    <testcase name="test_case_2" classname="component1.test_case_2" time="0.002" status="run">
        <properties/>
        <system-out>Test output 2</system-out>
    </testcase>
    <testcase name="test_case_3" classname="component1.test_case_3" time="0.003" status="run">
        <properties/>
        <system-out>Test output 3</system-out>
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
        <properties/>
        <system-out>Foo test output</system-out>
    </testcase>
    <testcase name="test_bar" classname="component2.test_bar" time="0.002" status="run">
        <properties/>
        <system-out>Bar test output</system-out>
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
