"""Unit tests for converting JUnit XML into importable test-result needs."""

import hashlib
import json
from pathlib import Path

import pytest

from spl_core.test_report.junit_to_needs import (
    NEEDS_FILE_NAME,
    collect_specs,
    convert,
    results_links,
    write_results,
)

DATA_DIR = Path(__file__).parent.parent / "data" / "junit"
JUNIT_FILE = DATA_DIR / "two_suites.xml"
LISTING_FILE = DATA_DIR / "listing.rst"

FILE_ID = "TEST_RESULT_Demo"


def _digest(text: str, length: int) -> str:
    return hashlib.sha1(text.encode("UTF-8")).hexdigest().upper()[:length]


MATH_SUITE_ID = f"{FILE_ID}_{_digest('MathSuite', 3)}"
PARAM_SUITE_ID = f"{FILE_ID}_{_digest('ParamSuite', 3)}"
ADDITION_CASE_ID = f"{MATH_SUITE_ID}_{_digest('MathTests' + 'test_addition', 5)}"
DIVISION_CASE_ID = f"{MATH_SUITE_ID}_{_digest('MathTests' + 'test_division', 5)}"
SKIP_CASE_ID = f"{MATH_SUITE_ID}_{_digest('MathTests' + 'test_skip_me', 5)}"
PARAM_CASE_ID = f"{PARAM_SUITE_ID}_{_digest('ParamTests' + 'test_param[1]', 5)}"


@pytest.fixture
def needs():
    return convert("Unit Test Results", FILE_ID, str(JUNIT_FILE))


@pytest.mark.unit
def test_ids_follow_the_test_report_scheme(needs):
    assert set(needs) == {
        FILE_ID,
        MATH_SUITE_ID,
        PARAM_SUITE_ID,
        ADDITION_CASE_ID,
        DIVISION_CASE_ID,
        SKIP_CASE_ID,
        PARAM_CASE_ID,
    }
    assert needs[MATH_SUITE_ID]["id"] == MATH_SUITE_ID
    assert needs[ADDITION_CASE_ID]["id"] == ADDITION_CASE_ID


@pytest.mark.unit
def test_testfile_counts_and_fields(needs):
    testfile = needs[FILE_ID]
    assert testfile["type"] == "testfile"
    assert testfile["title"] == "Unit Test Results"
    assert testfile["file"] == str(JUNIT_FILE)
    assert testfile["tags"] == [FILE_ID]
    assert testfile["links"] == []
    assert testfile["suites"] == 2
    assert testfile["cases"] == 4
    assert testfile["passed"] == 2
    assert testfile["skipped"] == 1
    assert testfile["failed"] == 1
    assert testfile["errors"] == 0


@pytest.mark.unit
def test_testsuite_counts_and_fields(needs):
    math = needs[MATH_SUITE_ID]
    assert math["type"] == "testsuite"
    assert math["suite"] == "MathSuite"
    assert math["links"] == [FILE_ID]
    assert (math["cases"], math["passed"], math["skipped"], math["failed"], math["errors"]) == (3, 1, 1, 1, 0)

    param = needs[PARAM_SUITE_ID]
    assert param["suite"] == "ParamSuite"
    assert (param["cases"], param["passed"], param["skipped"], param["failed"], param["errors"]) == (1, 1, 0, 0, 0)


@pytest.mark.unit
def test_passed_case_fields(needs):
    case = needs[ADDITION_CASE_ID]
    assert case["type"] == "testcase"
    assert case["case"] == "test_addition"
    assert case["case_name"] == "test_addition"
    assert case["case_parameter"] == ""
    assert case["classname"] == "MathTests"
    assert case["result"] == "passed"
    assert case["style"] == "tr_passed"
    assert case["suite"] == "MathSuite"
    assert case["links"] == [FILE_ID, MATH_SUITE_ID]
    assert case["content"] == ""


@pytest.mark.unit
def test_failed_case_fields(needs):
    case = needs[DIVISION_CASE_ID]
    assert case["result"] == "failure"
    assert case["style"] == "tr_failure"
    assert case["time"] == "0.2"
    assert "**Message**::" in case["content"]
    assert "division by zero" in case["content"]
    assert "**Text**::" in case["content"]
    assert "Traceback: division by zero" in case["content"]


@pytest.mark.unit
def test_skipped_case_fields(needs):
    case = needs[SKIP_CASE_ID]
    assert case["result"] == "skipped"
    assert case["style"] == "tr_skipped"
    assert "**Message**::" in case["content"]
    assert "not implemented" in case["content"]


@pytest.mark.unit
def test_parameterised_case_is_split(needs):
    case = needs[PARAM_CASE_ID]
    assert case["case"] == "test_param[1]"
    assert case["case_name"] == "test_param"
    assert case["case_parameter"] == "1"


@pytest.mark.unit
def test_collect_specs_reads_id_and_title_pairs():
    specs = collect_specs([LISTING_FILE])
    assert specs == [
        ("TS_ADD", "test_addition"),
        ("TS_DIV", "test_division"),
        ("TS_PARAM", "test_param*"),
    ]


@pytest.mark.unit
def test_results_links_exact_title_and_regex(needs):
    links = results_links(needs, collect_specs([LISTING_FILE]))
    assert links == {
        "TS_ADD": [ADDITION_CASE_ID],
        "TS_DIV": [DIVISION_CASE_ID],
        "TS_PARAM": [PARAM_CASE_ID],
    }


@pytest.mark.unit
def test_write_results_writes_needs_json_and_page(tmp_path):
    page = tmp_path / "reports" / "unit_test_results.rst"
    write_results(page, "Unit Test Results", FILE_ID, JUNIT_FILE, [LISTING_FILE])

    needs_json = json.loads((page.parent / NEEDS_FILE_NAME).read_text(encoding="utf-8"))
    assert needs_json["current_version"] == ""
    assert needs_json["project"] == "SPL"
    assert set(needs_json["versions"]) == {""}
    assert set(needs_json["versions"][""]["needs"]) == {
        FILE_ID,
        MATH_SUITE_ID,
        PARAM_SUITE_ID,
        ADDITION_CASE_ID,
        DIVISION_CASE_ID,
        SKIP_CASE_ID,
        PARAM_CASE_ID,
    }

    page_text = page.read_text(encoding="utf-8")
    assert "Unit Test Results\n=================" in page_text
    assert f".. needimport:: {NEEDS_FILE_NAME}" in page_text
    # needextend blocks are emitted in sorted spec-id order
    assert page_text.index(".. needextend:: TS_ADD") < page_text.index(".. needextend:: TS_DIV")
    assert page_text.index(".. needextend:: TS_DIV") < page_text.index(".. needextend:: TS_PARAM")
    assert f"   :+results: {ADDITION_CASE_ID}" in page_text
    assert f"   :+results: {DIVISION_CASE_ID}" in page_text
    assert f"   :+results: {PARAM_CASE_ID}" in page_text


@pytest.mark.unit
def test_write_results_project_name_is_configurable(tmp_path):
    page = tmp_path / "unit_test_results.rst"
    write_results(page, "Unit Test Results", FILE_ID, JUNIT_FILE, [], project="SPLed")
    needs_json = json.loads((page.parent / NEEDS_FILE_NAME).read_text(encoding="utf-8"))
    assert needs_json["project"] == "SPLed"
