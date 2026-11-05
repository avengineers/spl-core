"""Build a report the way the kickstart project does and check what it shows."""

import json
import shutil
from importlib.resources import files
from pathlib import Path

import pytest
from sphinx.cmd.build import build_main

from spl_core.report_generation.spl_sphinx import SplSphinx

KICKSTART_PROJECT = Path(__file__).parents[2] / "src" / "spl_core" / "kickstart" / "templates" / "project"

JUNIT = """<?xml version="1.0" encoding="UTF-8"?>
<testsuites>
  <testsuite name="greeter" tests="6" failures="1" errors="0" skipped="0" time="0.06">
    <testcase name="GreeterTest.SaysHello" classname="greeter" time="0.01"/>
    <testcase name="GreeterTest.SaysGoodbye" classname="greeter" time="0.01">
      <failure message="expected 'Goodbye'">assert farewell() == "Goodbye"</failure>
    </testcase>
    <testcase name="LanguageTests/GreeterTest.Greets/0" classname="greeter" time="0.01"/>
    <testcase name="LanguageTests/GreeterTest.Greets/1" classname="greeter" time="0.01"/>
    <testcase name="PoliteTests/GreeterTest.Thanks/Thanks, friend" classname="greeter" time="0.01"/>
    <testcase name="PoliteTests/GreeterTest.Thanks/Cheers, friend" classname="greeter" time="0.01"/>
  </testsuite>
</testsuites>
"""

INDEX = """
Report
======

.. test:: GreeterTest.SaysHello
   :id: T_HELLO

.. test:: LanguageTests/GreeterTest.Greets
   :id: T_GREETS
   :results: [[links_from_filter("type == 'testcase' and search('^LanguageTests/GreeterTest.Greets/', case)")]]

Unit Test Results
-----------------

.. test-report:: Unit Test Results
   :id: TEST_RESULT_GREETER
   :file: junit.xml
"""


def conf_py() -> str:
    """The report configuration of the kickstart project's conf.py, without its theme."""
    ubproject = files("spl_core.report_generation").joinpath("ubproject.toml")
    return f"""
from spl_core.report_generation.spl_sphinx import SplSphinx

extensions = SplSphinx.default_extensions
tr_report_template = SplSphinx.default_extension_configs["tr_report_template"]
needs_from_toml = {str(ubproject)!r}
"""


# What a conf.py written for spl-core 8 adds, which the shared ubproject.toml now covers.
OLDER_CONF_PY_LINES = """
needs_functions = SplSphinx.default_needs_functions
needs_global_options = SplSphinx.default_needs_global_options
"""

# Test specs written for spl-core 8, which call sple_tr_link themselves.
OLDER_TEST_SPECS = """
.. test:: GreeterTest.SaysHello
   :id: T_HELLO_OLDER
   :results: [[sple_tr_link('title', 'case')]]

.. test:: LanguageTests/GreeterTest.Greets/*
   :id: T_GREETS_OLDER
   :results: [[sple_tr_link('title', 'case')]]
"""


def build_report(src: Path, conf: str, index: str = INDEX) -> tuple[dict[str, dict[str, object]], str, str]:
    """The needs, the HTML page and the warnings of a report built from ``conf`` and ``index``."""
    (src / "conf.py").write_text(conf)
    (src / "index.rst").write_text(index)
    (src / "junit.xml").write_text(JUNIT)
    (src / "doc").mkdir()
    shutil.copy(KICKSTART_PROJECT / str(SplSphinx.default_extension_configs["tr_report_template"]), src / "doc")
    out = src / "_build"
    warnings = out / "warnings.txt"

    assert build_main(["-q", "-E", "-b", "html", "-w", str(warnings), str(src), str(out / "html")]) == 0
    assert build_main(["-q", "-E", "-b", "needs", str(src), str(out / "needs")]) == 0

    needs_json = json.loads((out / "needs" / "needs.json").read_text())
    needs = needs_json["versions"][needs_json["current_version"]]["needs"]
    return needs, (out / "html" / "index.html").read_text(), warnings.read_text()


@pytest.fixture(scope="module")
def report(tmp_path_factory: pytest.TempPathFactory) -> tuple[dict[str, dict[str, object]], str]:
    needs, html, _ = build_report(tmp_path_factory.mktemp("report"), conf_py())
    return needs, html


@pytest.fixture(scope="module")
def report_of_an_older_conf(tmp_path_factory: pytest.TempPathFactory) -> tuple[dict[str, dict[str, object]], str]:
    needs, _, warnings = build_report(tmp_path_factory.mktemp("older"), conf_py() + OLDER_CONF_PY_LINES, INDEX + OLDER_TEST_SPECS)
    return needs, warnings


def case_id(needs: dict[str, dict[str, object]], case: str) -> str:
    return next(need_id for need_id, need in needs.items() if need.get("case") == case)


@pytest.mark.unit
class TestKickstartReport:
    def test_a_test_spec_links_the_case_of_the_same_name(self, report):
        needs, _ = report
        assert needs["T_HELLO"]["results"] == [case_id(needs, "GreeterTest.SaysHello")]

    def test_a_test_spec_with_a_filter_links_every_case_it_selects(self, report):
        needs, _ = report
        assert sorted(needs["T_GREETS"]["results"]) == sorted(
            [
                case_id(needs, "LanguageTests/GreeterTest.Greets/0"),
                case_id(needs, "LanguageTests/GreeterTest.Greets/1"),
            ]
        )

    def test_a_test_case_links_no_results(self, report):
        # Case names with a comma share a value once split on it ("friend" here), which
        # once linked such cases to each other.
        needs, _ = report
        assert {need_id: need["results"] for need_id, need in needs.items() if need["type"] == "testcase" and need["results"]} == {}

    def test_the_report_lists_the_failed_case(self, report):
        needs, html = report
        failed_case = case_id(needs, "GreeterTest.SaysGoodbye")
        failed_section = html[html.index('id="failed-test-cases"') : html.index('id="skipped-test-cases"')]
        assert failed_case in failed_section


@pytest.mark.unit
class TestOlderConf:
    def test_a_test_spec_still_links_the_case_of_the_same_name(self, report_of_an_older_conf):
        needs, _ = report_of_an_older_conf
        assert needs["T_HELLO"]["results"] == [case_id(needs, "GreeterTest.SaysHello")]

    def test_the_build_warns_about_no_needs_option(self, report_of_an_older_conf):
        _, warnings = report_of_an_older_conf
        assert "needs." not in warnings

    def test_a_test_spec_calling_sple_tr_link_links_the_case_of_the_same_name(self, report_of_an_older_conf):
        needs, _ = report_of_an_older_conf
        assert needs["T_HELLO_OLDER"]["results"] == [case_id(needs, "GreeterTest.SaysHello")]

    def test_a_test_spec_calling_sple_tr_link_with_a_pattern_links_every_case_it_matches(self, report_of_an_older_conf):
        needs, _ = report_of_an_older_conf
        assert sorted(needs["T_GREETS_OLDER"]["results"]) == sorted(
            [
                case_id(needs, "LanguageTests/GreeterTest.Greets/0"),
                case_id(needs, "LanguageTests/GreeterTest.Greets/1"),
            ]
        )
