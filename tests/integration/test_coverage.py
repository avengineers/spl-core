import json
import shutil
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest

from tests.utils import SplProjectIntegrationTestBase

VARIANT = "Variant1"
STALE_FILE_NAME = "stale/removed_file.c"


@pytest.mark.integration
class TestVariantCoverageIgnoresStaleFiles(SplProjectIntegrationTestBase):
    """A coverage.json that the current build did not write must not enter the variant coverage."""

    @property
    def build_dir(self) -> Path:
        return self.spl_project.artifacts.get_build_dir(VARIANT, "test")

    @property
    def variant_coverage_json(self) -> Path:
        return self.build_dir / "variant-coverage.json"

    def _build(self, target: str) -> None:
        result = self.spl_project.build(VARIANT, target)
        assert result is not None and result.returncode == 0, f"Building {target} shall not fail."

    def _force_variant_coverage_regeneration(self) -> None:
        """Remove the variant level outputs, so the next build runs gcovr on them again."""
        rel_build_dir = self.build_dir.relative_to(self.spl_project.artifacts.project_root_dir)
        for output in [
            self.variant_coverage_json,
            self.build_dir / "reports/coverage/index.html",
            self.build_dir / f"reports/html/{rel_build_dir}/reports/coverage/index.html",
        ]:
            output.unlink(missing_ok=True)

    def _component_coverage_json(self, stale_dir: Path) -> Path:
        candidates = sorted(path for path in self.build_dir.rglob("coverage.json") if stale_dir not in path.parents)
        assert candidates, "The build shall have written a coverage.json for at least one component."
        return candidates[0]

    @contextmanager
    def _stale_coverage_json(self, content: dict[str, Any]) -> Iterator[Path]:
        stale_dir = self.build_dir / "stale_component"
        stale_dir.mkdir(parents=True, exist_ok=True)
        stale_file = stale_dir / "coverage.json"
        stale_file.write_text(json.dumps(content), encoding="utf-8")
        try:
            yield stale_file
        finally:
            shutil.rmtree(stale_dir, ignore_errors=True)

    def test_stale_coverage_json_in_old_format_does_not_break_the_variant_coverage(self) -> None:
        self._build("unittests")

        with self._stale_coverage_json({"gcovr/format_version": "0.0", "files": []}):
            self._force_variant_coverage_regeneration()
            self._build("unittests")
            assert self.variant_coverage_json.exists(), "The variant coverage shall be generated."

    def test_stale_coverage_json_does_not_change_the_variant_coverage(self) -> None:
        self._build("unittests")
        expected_files = json.loads(self.variant_coverage_json.read_text(encoding="utf-8"))["files"]

        stale_dir = self.build_dir / "stale_component"
        stale_content = json.loads(self._component_coverage_json(stale_dir).read_text(encoding="utf-8"))
        assert stale_content["files"], "The component coverage.json shall list at least one file."
        stale_content["files"][0]["file"] = STALE_FILE_NAME

        with self._stale_coverage_json(stale_content):
            self._force_variant_coverage_regeneration()
            self._build("unittests")
            variant_coverage = self.variant_coverage_json.read_text(encoding="utf-8")

        assert STALE_FILE_NAME not in variant_coverage, "A file of the stale coverage.json shall not be in the variant coverage."
        assert json.loads(variant_coverage)["files"] == expected_files

    def test_reports_coverage_ignores_stale_coverage_json(self) -> None:
        self._build("unittests")

        with self._stale_coverage_json({"gcovr/format_version": "0.0", "files": []}):
            self._force_variant_coverage_regeneration()
            self._build("reports")
