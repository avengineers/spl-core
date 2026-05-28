"""Unit tests for coverage_to_md: Markdown coverage table generation from gcovr JSON."""

import json
from pathlib import Path
from typing import Any

import pytest

from spl_core.coverage_to_md import (
    _compute_branch_coverage_from_trace,
    _compute_condition_coverage_from_trace,
    _compute_line_coverage_from_trace,
    _find_detail_file,
    generate_coverage_markdown,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TRACE_JSON: dict[str, Any] = {
    "gcovr/format_version": "0.14",
    "files": [
        {
            "file": "src/module_a/foo.c",
            "lines": [
                {"line_number": 1, "count": 1, "branches": []},
                {"line_number": 2, "count": 0, "branches": []},
                {"line_number": 3, "count": 1, "branches": [{"count": 1}, {"count": 0}]},
            ],
        },
        {
            "file": "src/module_b/bar.c",
            "lines": [
                {"line_number": 10, "count": 1, "branches": []},
                {"line_number": 11, "count": 1, "branches": []},
            ],
        },
    ],
}


TRACE_JSON_WITH_CONDITIONS: dict[str, Any] = {
    "gcovr/format_version": "0.14",
    "files": [
        {
            "file": "src/module_a/foo.c",
            "lines": [
                {"line_number": 1, "count": 1, "branches": []},
                {"line_number": 2, "count": 0, "branches": []},
                {
                    "line_number": 3,
                    "count": 1,
                    "branches": [{"count": 1}, {"count": 0}],
                    "conditions": [{"conditionno": 0, "count": 2, "covered": 1, "not_covered_false": [], "not_covered_true": [0]}],
                },
            ],
        },
        {
            "file": "src/module_b/bar.c",
            "lines": [
                {
                    "line_number": 10,
                    "count": 1,
                    "branches": [{"count": 5}, {"count": 3}],
                    "conditions": [{"conditionno": 0, "count": 4, "covered": 4, "not_covered_false": [], "not_covered_true": []}],
                },
                {"line_number": 11, "count": 1, "branches": []},
            ],
        },
    ],
}


SUMMARY_JSON: dict[str, Any] = {
    "gcovr/summary_format_version": "0.6",
    "files": [
        {
            "filename": "src/module_a/foo.c",
            "line_total": 3,
            "line_covered": 2,
            "branch_total": 2,
            "branch_covered": 1,
        },
        {
            "filename": "src/module_b/bar.c",
            "line_total": 2,
            "line_covered": 2,
            "branch_total": 0,
            "branch_covered": 0,
        },
    ],
    "line_total": 5,
    "line_covered": 4,
    "branch_total": 2,
    "branch_covered": 1,
}


# ---------------------------------------------------------------------------
# _compute_line_coverage_from_trace
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestComputeLineCoverageFromTrace:
    def test_basic(self) -> None:
        file_data = TRACE_JSON["files"][0]
        covered, total = _compute_line_coverage_from_trace(file_data)
        assert total == 3
        assert covered == 2

    def test_all_covered(self) -> None:
        file_data = TRACE_JSON["files"][1]
        covered, total = _compute_line_coverage_from_trace(file_data)
        assert total == 2
        assert covered == 2

    def test_empty_lines(self) -> None:
        covered, total = _compute_line_coverage_from_trace({"lines": []})
        assert total == 0
        assert covered == 0


# ---------------------------------------------------------------------------
# _compute_branch_coverage_from_trace
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestComputeBranchCoverageFromTrace:
    def test_with_branches(self) -> None:
        file_data = TRACE_JSON["files"][0]
        covered, total = _compute_branch_coverage_from_trace(file_data)
        assert total == 2
        assert covered == 1

    def test_no_branches(self) -> None:
        file_data = TRACE_JSON["files"][1]
        covered, total = _compute_branch_coverage_from_trace(file_data)
        assert total == 0
        assert covered == 0


# ---------------------------------------------------------------------------
# _compute_condition_coverage_from_trace
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestComputeConditionCoverageFromTrace:
    def test_with_conditions(self) -> None:
        file_data = TRACE_JSON_WITH_CONDITIONS["files"][0]
        covered, total = _compute_condition_coverage_from_trace(file_data)
        assert total == 2
        assert covered == 1

    def test_all_conditions_covered(self) -> None:
        file_data = TRACE_JSON_WITH_CONDITIONS["files"][1]
        covered, total = _compute_condition_coverage_from_trace(file_data)
        assert total == 4
        assert covered == 4

    def test_no_conditions(self) -> None:
        file_data = TRACE_JSON["files"][0]
        covered, total = _compute_condition_coverage_from_trace(file_data)
        assert total == 0
        assert covered == 0

    def test_empty_lines(self) -> None:
        covered, total = _compute_condition_coverage_from_trace({"lines": []})
        assert total == 0
        assert covered == 0


# ---------------------------------------------------------------------------
# _find_detail_file
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestFindDetailFile:
    def test_finds_matching_file(self, tmp_path: Path) -> None:
        (tmp_path / "index.src.module_a.foo.c.html").touch()
        result = _find_detail_file(tmp_path, "src/module_a/foo.c")
        assert result == "index.src.module_a.foo.c.html"

    def test_no_match_returns_none(self, tmp_path: Path) -> None:
        (tmp_path / "index.other.file.c.html").touch()
        result = _find_detail_file(tmp_path, "src/module_a/foo.c")
        assert result is None

    def test_ignores_index_html(self, tmp_path: Path) -> None:
        (tmp_path / "index.html").touch()
        result = _find_detail_file(tmp_path, "index")
        assert result is None

    def test_nonexistent_dir_returns_none(self, tmp_path: Path) -> None:
        result = _find_detail_file(tmp_path / "nonexistent", "foo.c")
        assert result is None

    def test_windows_path_separator(self, tmp_path: Path) -> None:
        (tmp_path / "index.src.module.foo.c.html").touch()
        result = _find_detail_file(tmp_path, "src\\module\\foo.c")
        assert result == "index.src.module.foo.c.html"

    def test_gcovr8_hash_format(self, tmp_path: Path) -> None:
        """gcovr 8.x names detail files as <stem>.<basename>.<md5_hash>.html"""
        (tmp_path / "index.foo.c.26b0df71607644e72398345aec5b66eb.html").touch()
        result = _find_detail_file(tmp_path, "src/module_a/foo.c")
        assert result == "index.foo.c.26b0df71607644e72398345aec5b66eb.html"

    def test_gcovr8_no_false_positive_on_similar_basename(self, tmp_path: Path) -> None:
        """Ensure 'greeter.c' doesn't match 'some_greeter.c' detail file."""
        (tmp_path / "index.some_greeter.c.abcdef01234567890abcdef012345678.html").touch()
        result = _find_detail_file(tmp_path, "src/greeter.c")
        assert result is None

    def test_gcovr7_preferred_over_gcovr8(self, tmp_path: Path) -> None:
        """Full path match (gcovr 7.x) takes priority over basename match (gcovr 8.x)."""
        (tmp_path / "index.src.module_a.foo.c.html").touch()
        (tmp_path / "index.foo.c.abcdef01234567890abcdef012345678.html").touch()
        result = _find_detail_file(tmp_path, "src/module_a/foo.c")
        assert result == "index.src.module_a.foo.c.html"


# ---------------------------------------------------------------------------
# generate_coverage_markdown — trace format
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestGenerateCoverageMarkdownTrace:
    def test_generates_table_with_branches(self, tmp_path: Path) -> None:
        json_path = tmp_path / "coverage.json"
        json_path.write_text(json.dumps(TRACE_JSON), encoding="utf-8")
        output = tmp_path / "coverage.md"

        generate_coverage_markdown(json_path, output)

        md = output.read_text(encoding="utf-8")
        assert "# Code Coverage" in md
        assert "| File |" in md
        assert "Line %" in md
        assert "Branch %" in md
        assert "`src/module_a/foo.c`" in md
        assert "`src/module_b/bar.c`" in md
        assert "**TOTAL**" in md
        # Lines column shows covered/total format
        assert "2/3" in md  # foo.c lines
        assert "2/2" in md  # bar.c lines

    def test_line_percentages(self, tmp_path: Path) -> None:
        json_path = tmp_path / "coverage.json"
        json_path.write_text(json.dumps(TRACE_JSON), encoding="utf-8")
        output = tmp_path / "coverage.md"

        generate_coverage_markdown(json_path, output)

        md = output.read_text(encoding="utf-8")
        assert "66.7%" in md  # foo.c: 2/3
        assert "100.0%" in md  # bar.c: 2/2

    def test_branch_values(self, tmp_path: Path) -> None:
        json_path = tmp_path / "coverage.json"
        json_path.write_text(json.dumps(TRACE_JSON), encoding="utf-8")
        output = tmp_path / "coverage.md"

        generate_coverage_markdown(json_path, output)

        md = output.read_text(encoding="utf-8")
        assert "1/2" in md  # foo.c branches


# ---------------------------------------------------------------------------
# generate_coverage_markdown — summary format
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestGenerateCoverageMarkdownSummary:
    def test_generates_table(self, tmp_path: Path) -> None:
        json_path = tmp_path / "summary.json"
        json_path.write_text(json.dumps(SUMMARY_JSON), encoding="utf-8")
        output = tmp_path / "coverage.md"

        generate_coverage_markdown(json_path, output)

        md = output.read_text(encoding="utf-8")
        assert "# Code Coverage" in md
        assert "`src/module_a/foo.c`" in md
        assert "**TOTAL**" in md


# ---------------------------------------------------------------------------
# generate_coverage_markdown — with HTML links
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestGenerateCoverageMarkdownWithLinks:
    def test_links_to_detail_pages(self, tmp_path: Path) -> None:
        json_path = tmp_path / "coverage.json"
        json_path.write_text(json.dumps(TRACE_JSON), encoding="utf-8")
        html_dir = tmp_path / "html"
        html_dir.mkdir()
        (html_dir / "index.html").touch()
        (html_dir / "index.src.module_a.foo.c.html").touch()
        (html_dir / "index.src.module_b.bar.c.html").touch()
        output = tmp_path / "coverage.md"

        generate_coverage_markdown(json_path, output, html_dir=html_dir, html_link_prefix="coverage")

        md = output.read_text(encoding="utf-8")
        assert '<a href="coverage/index.src.module_a.foo.c.html"><code>src/module_a/foo.c</code></a>' in md
        assert '<a href="coverage/index.src.module_b.bar.c.html"><code>src/module_b/bar.c</code></a>' in md

    def test_partial_links(self, tmp_path: Path) -> None:
        """Only files with matching detail pages get links."""
        json_path = tmp_path / "coverage.json"
        json_path.write_text(json.dumps(TRACE_JSON), encoding="utf-8")
        html_dir = tmp_path / "html"
        html_dir.mkdir()
        (html_dir / "index.src.module_a.foo.c.html").touch()
        output = tmp_path / "coverage.md"

        generate_coverage_markdown(json_path, output, html_dir=html_dir, html_link_prefix="coverage")

        md = output.read_text(encoding="utf-8")
        assert '<a href="coverage/index.src.module_a.foo.c.html"><code>src/module_a/foo.c</code></a>' in md
        assert "`src/module_b/bar.c`" in md
        assert "bar.c</code></a>" not in md

    def test_links_gcovr8_hash_format(self, tmp_path: Path) -> None:
        """gcovr 8.x detail file naming: <stem>.<basename>.<md5_hash>.html"""
        json_path = tmp_path / "coverage.json"
        json_path.write_text(json.dumps(TRACE_JSON), encoding="utf-8")
        html_dir = tmp_path / "html"
        html_dir.mkdir()
        (html_dir / "index.html").touch()
        (html_dir / "index.foo.c.aaaabbbbccccddddeeee111122223333.html").touch()
        (html_dir / "index.bar.c.11112222333344445555666677778888.html").touch()
        output = tmp_path / "coverage.md"

        generate_coverage_markdown(json_path, output, html_dir=html_dir, html_link_prefix="coverage")

        md = output.read_text(encoding="utf-8")
        assert '<a href="coverage/index.foo.c.aaaabbbbccccddddeeee111122223333.html"><code>src/module_a/foo.c</code></a>' in md
        assert '<a href="coverage/index.bar.c.11112222333344445555666677778888.html"><code>src/module_b/bar.c</code></a>' in md


# ---------------------------------------------------------------------------
# generate_coverage_markdown — edge cases
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestGenerateCoverageMarkdownEdgeCases:
    def test_empty_files_list(self, tmp_path: Path) -> None:
        json_path = tmp_path / "empty.json"
        json_path.write_text(json.dumps({"files": []}), encoding="utf-8")
        output = tmp_path / "coverage.md"

        generate_coverage_markdown(json_path, output)

        md = output.read_text(encoding="utf-8")
        assert "# Code Coverage" in md
        assert "**TOTAL**" in md
        assert "**0/0**" in md

    def test_no_branches_omits_branch_columns(self, tmp_path: Path) -> None:
        trace_no_branches = {
            "gcovr/format_version": "0.14",
            "files": [
                {
                    "file": "main.c",
                    "lines": [
                        {"line_number": 1, "count": 1, "branches": []},
                    ],
                }
            ],
        }
        json_path = tmp_path / "coverage.json"
        json_path.write_text(json.dumps(trace_no_branches), encoding="utf-8")
        output = tmp_path / "coverage.md"

        generate_coverage_markdown(json_path, output)

        md = output.read_text(encoding="utf-8")
        assert "Branch" not in md
        assert "Condition" not in md
        assert "Coverage" in md

    def test_custom_heading(self, tmp_path: Path) -> None:
        json_path = tmp_path / "coverage.json"
        json_path.write_text(json.dumps({"files": []}), encoding="utf-8")
        output = tmp_path / "coverage.md"

        generate_coverage_markdown(json_path, output, heading="My Custom Heading")

        md = output.read_text(encoding="utf-8")
        assert "# My Custom Heading" in md

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        json_path = tmp_path / "coverage.json"
        json_path.write_text(json.dumps({"files": []}), encoding="utf-8")
        output = tmp_path / "deep" / "nested" / "coverage.md"

        generate_coverage_markdown(json_path, output)

        assert output.exists()


# ---------------------------------------------------------------------------
# generate_coverage_markdown — with condition coverage
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestGenerateCoverageMarkdownConditions:
    def test_condition_columns_present(self, tmp_path: Path) -> None:
        json_path = tmp_path / "coverage.json"
        json_path.write_text(json.dumps(TRACE_JSON_WITH_CONDITIONS), encoding="utf-8")
        output = tmp_path / "coverage.md"

        generate_coverage_markdown(json_path, output)

        md = output.read_text(encoding="utf-8")
        assert "Condition %" in md
        assert "Conditions" in md

    def test_condition_values(self, tmp_path: Path) -> None:
        json_path = tmp_path / "coverage.json"
        json_path.write_text(json.dumps(TRACE_JSON_WITH_CONDITIONS), encoding="utf-8")
        output = tmp_path / "coverage.md"

        generate_coverage_markdown(json_path, output)

        md = output.read_text(encoding="utf-8")
        assert "1/2" in md  # foo.c conditions: 1 covered out of 2
        assert "4/4" in md  # bar.c conditions: 4 covered out of 4

    def test_total_conditions(self, tmp_path: Path) -> None:
        json_path = tmp_path / "coverage.json"
        json_path.write_text(json.dumps(TRACE_JSON_WITH_CONDITIONS), encoding="utf-8")
        output = tmp_path / "coverage.md"

        generate_coverage_markdown(json_path, output)

        md = output.read_text(encoding="utf-8")
        assert "**5/6**" in md  # total: 1+4=5 covered, 2+4=6 total

    def test_no_conditions_omits_condition_columns(self, tmp_path: Path) -> None:
        """When branches exist but no conditions, condition columns are omitted."""
        json_path = tmp_path / "coverage.json"
        json_path.write_text(json.dumps(TRACE_JSON), encoding="utf-8")
        output = tmp_path / "coverage.md"

        generate_coverage_markdown(json_path, output)

        md = output.read_text(encoding="utf-8")
        assert "Branch %" in md
        assert "Condition" not in md

    def test_summary_format_with_conditions(self, tmp_path: Path) -> None:
        summary_with_cond = {
            "gcovr/summary_format_version": "0.6",
            "files": [
                {
                    "filename": "src/foo.c",
                    "line_total": 10,
                    "line_covered": 8,
                    "branch_total": 4,
                    "branch_covered": 3,
                    "condition_total": 6,
                    "condition_covered": 5,
                },
            ],
        }
        json_path = tmp_path / "summary.json"
        json_path.write_text(json.dumps(summary_with_cond), encoding="utf-8")
        output = tmp_path / "coverage.md"

        generate_coverage_markdown(json_path, output)

        md = output.read_text(encoding="utf-8")
        assert "Condition %" in md
        assert "5/6" in md
