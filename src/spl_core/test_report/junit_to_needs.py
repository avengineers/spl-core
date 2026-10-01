"""Turn JUnit XML results into needs that every reader can import.

sphinx-test-reports' ``test-report`` directive creates its testfile,
testsuite and testcase needs only while Sphinx runs, so the result data
disappears for any reader that just imports ``needs.json`` (ubCode, ``ubc``).
This module reproduces exactly those needs -- same ids, types and fields --
from the same JUnit XML, using sphinx-test-reports' own parser, and writes them
next to the generated report page. The page itself then holds a plain
``needimport`` of that JSON plus one ``needextend`` per test specification that
links the cases matching it, so the ``results`` links become data instead of a
Sphinx-only needs function.

The ids follow sphinx-test-reports' scheme::

    <file_id>
    <file_id>_<SHA1(suite name)[:3] upper>
    <suite_id>_<SHA1(classname + name)[:5] upper>
"""

from __future__ import annotations

import argparse
import glob as glob_module
import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from sphinxcontrib.test_reports.junitparser import JUnitParser

SUITE_LEN, CASE_LEN = 3, 5  # sphinx-test-reports' tr_suite_id_length, tr_case_id_length
NEEDS_FILE_NAME = "unit_test_results.needs.json"
DEFAULT_PROJECT = "SPL"

_SPEC_RE = re.compile(r"^\.\. test:: (.+)\n\s+:id: (\S+)", re.M)


def sha(text: str, n: int) -> str:
    return hashlib.sha1(text.encode("UTF-8")).hexdigest().upper()[:n]


def block(label: str, value: str) -> str:
    return "\n\n**{}**::\n\n   {}\n\n".format(label, "\n   ".join(x.lstrip() for x in value.split("\n")))


def case_time(value: Any) -> str:
    if isinstance(value, (int, float)):
        return str(float(value) if value >= 0 else 0.0)
    if value is None:
        return str(0.0)
    try:
        return str(float(value))
    except (TypeError, ValueError):
        return str(0.0)


def convert(title: str, file_id: str, junit: str) -> dict[str, dict[str, Any]]:
    """The needs sphinx-test-reports' test-report directive creates for one JUnit file."""
    suites = JUnitParser(junit).parse()
    needs: dict[str, dict[str, Any]] = {}
    tags = [file_id]
    needs[file_id] = dict(
        id=file_id, type="testfile", title=title, file=junit, tags=tags, links=[], content="[]",
        suites=len(suites), cases=sum(int(s["tests"]) for s in suites), passed=sum(s["passed"] for s in suites),
        skipped=sum(s["skips"] for s in suites), failed=sum(s["failures"] for s in suites),
        errors=sum(s["errors"] for s in suites))
    for suite in suites:
        suite_id = f"{file_id}_{sha(suite['name'], SUITE_LEN)}"
        needs[suite_id] = dict(
            id=suite_id, type="testsuite", title=suite["name"], suite=suite["name"], file=junit, tags=tags,
            links=[file_id], content="", cases=int(suite["tests"]), passed=suite["passed"], skipped=suite["skips"],
            failed=suite["failures"], errors=suite["errors"])
        for case in suite["testcases"]:
            case_id = f"{suite_id}_{sha(case['classname'] + case['name'], CASE_LEN)}"
            groups = re.match(r"^(?P<name>[^\[]+)($|\[(?P<param>.*)?\])", case["name"])
            name, param = (groups["name"], groups["param"] or "") if groups else (case["name"], "")
            content = ""
            for key, label in (("text", "Text"), ("message", "Message"), ("system-out", "System-out")):
                if case.get(key):
                    content += block(label, case[key])
            needs[case_id] = dict(
                id=case_id, type="testcase", title=case["name"], case=case["name"], case_name=name,
                case_parameter=param, classname=case["classname"], result=case["result"], time=case_time(case["time"]),
                suite=suite["name"], style="tr_" + case["result"], file=junit, tags=tags,
                links=[file_id, suite_id], content=content)
    return needs


def _iter_listing_files(listing_paths: Iterable[str | Path]) -> Iterable[Path]:
    for entry in listing_paths:
        text = str(entry)
        matches = sorted(glob_module.glob(text, recursive=True))
        if matches:
            for match in matches:
                yield Path(match)
        else:
            yield Path(entry)


def collect_specs(listing_paths: Iterable[str | Path]) -> list[tuple[str, str]]:
    """The (spec_id, spec_title) pairs the ``.. test::`` directives declare in RST listings."""
    specs: list[tuple[str, str]] = []
    for path in _iter_listing_files(listing_paths):
        text = path.read_text(encoding="utf-8")
        specs.extend((m.group(2), m.group(1).strip()) for m in _SPEC_RE.finditer(text))
    return specs


def results_links(needs: Mapping[str, Mapping[str, Any]], specs: Iterable[tuple[str, str]]) -> dict[str, list[str]]:
    """Map each spec id to the case ids whose ``case`` equals or matches its title."""
    links: dict[str, list[str]] = {}
    for need in needs.values():
        if need["type"] != "testcase":
            continue
        for spec_id, spec_title in specs:
            if spec_title == need["case"] or ("*" in spec_title and re.match(spec_title, need["case"])):
                links.setdefault(spec_id, []).append(need["id"])
    return links


def write_results(
    page_path: str | Path,
    title: str,
    file_id: str,
    junit_path: str | Path,
    listing_paths: Iterable[str | Path],
    project: str = DEFAULT_PROJECT,
) -> None:
    """Write the needs JSON next to the report page and rewrite the page to import it."""
    page_path = Path(page_path)
    needs = convert(title, file_id, str(junit_path))
    needs_json = {"current_version": "", "project": project, "versions": {"": {"needs": needs}}}

    page_path.parent.mkdir(parents=True, exist_ok=True)
    (page_path.parent / NEEDS_FILE_NAME).write_text(json.dumps(needs_json, indent=1), encoding="utf-8")

    links = results_links(needs, collect_specs(listing_paths))
    lines = ["", title, "=" * len(title), "", f".. needimport:: {NEEDS_FILE_NAME}", ""]
    for spec_id, case_ids in sorted(links.items()):
        lines += [f".. needextend:: {spec_id}", f"   :+results: {', '.join(case_ids)}", ""]
    page_path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--page", required=True, help="path of the report page to (re)write")
    parser.add_argument("--title", required=True, help="title for the testfile need")
    parser.add_argument("--id", required=True, dest="file_id", help="id for the testfile need")
    parser.add_argument("--junit", required=True, help="path of the JUnit XML file")
    parser.add_argument("--listings", nargs="*", default=[], metavar="GLOB", help="RST listing files that declare test specs")
    parser.add_argument("--project", default=DEFAULT_PROJECT, help="project name for the needs.json envelope")
    args = parser.parse_args(argv)
    write_results(args.page, args.title, args.file_id, args.junit, args.listings, project=args.project)


if __name__ == "__main__":
    main()
