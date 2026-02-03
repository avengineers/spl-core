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
