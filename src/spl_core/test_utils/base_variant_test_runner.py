import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

import pytest

from spl_core.test_utils.spl_build import SplBuild


class BaseVariantTestRunner(ABC):
    @property
    def variant(self) -> str:
        return re.sub(r"^Test_", "", self.__class__.__name__).replace("__", "/")

    @property
    @abstractmethod
    def component_paths(self) -> List[Path]:
        pass

    @property
    @abstractmethod
    def expected_build_artifacts(self) -> List[Path]:
        pass

    @property
    def expected_test_artifacts(self) -> List[Path]:
        return [Path("reports/coverage/index.html")]

    @property
    def expected_variant_report_artifacts(self) -> List[Path]:
        return [Path("reports/html/index.html")]

    @property
    def expected_component_report_artifacts(self) -> List[Path]:
        return [
            Path("coverage.html"),
            Path("unit_test_results.html"),
            Path("unit_test_spec.html"),
            Path("doxygen/html/index.html"),
            Path("coverage/index.html"),
        ]

    @property
    def create_artifacts_archive(self) -> bool:
        return True

    @property
    def create_artifacts_json(self) -> bool:
        return True

    @property
    def expected_archive_artifacts(self) -> List[Path]:
        return self.expected_build_artifacts

    def assert_artifact_exists(self, dir: Path, artifact: Path) -> None:
        if artifact.is_absolute():
            assert artifact.exists(), f"Artifact {artifact} does not exist"  # noqa: S101
        else:
            assert Path.joinpath(dir, artifact).exists(), f"Artifact {Path.joinpath(dir, artifact)} does not exist"  # noqa: S101

    @pytest.mark.build
    def test_build(self, build_type: Optional[str] = None) -> None:
        spl_build: SplBuild = SplBuild(variant=self.variant, build_kit="prod", build_type=build_type)
        assert 0 == spl_build.execute(target="all")  # noqa: S101
        for artifact in self.expected_build_artifacts:
            self.assert_artifact_exists(dir=spl_build.build_dir, artifact=artifact)
        if self.create_artifacts_archive:
            # create artifacts archive
            spl_build.create_artifacts_archive(self.expected_archive_artifacts)
        if self.create_artifacts_json:
            spl_build.create_artifacts_json(self.expected_archive_artifacts)

    @pytest.mark.unittests
    def test_unittests(self, build_type: Optional[str] = None) -> None:
        spl_build: SplBuild = SplBuild(variant=self.variant, build_kit="test", build_type=build_type)
        assert 0 == spl_build.execute(target="unittests")  # noqa: S101
        for artifact in self.expected_test_artifacts:
            self.assert_artifact_exists(dir=spl_build.build_dir, artifact=artifact)

    @pytest.mark.reports
    def test_reports(self, build_type: Optional[str] = None) -> None:
        spl_build: SplBuild = SplBuild(variant=self.variant, build_kit="test", build_type=build_type)
        assert 0 == spl_build.execute(target="all")  # noqa: S101
        for artifact in self.expected_variant_report_artifacts:
            self.assert_artifact_exists(dir=spl_build.build_dir, artifact=artifact)
        for component in self.component_paths:
            for artifact in self.expected_component_report_artifacts:
                self.assert_artifact_exists(dir=Path.joinpath(spl_build.build_dir, "reports", "html", spl_build.build_dir, component, "reports"), artifact=artifact)
