from pathlib import Path
from unittest.mock import MagicMock, patch

from spl_core.test_utils.base_variant_test_runner import BaseVariantTestRunner


class Test_SomeVariant(BaseVariantTestRunner):
    def test_variant(self):
        assert self.variant == "SomeVariant"

    @property
    def create_artifacts_archive(self):
        return False

    @property
    def create_artifacts_json(self):
        return False

    @property
    def component_paths(self):
        return [Path("component1"), Path("component2")]

    @property
    def expected_build_artifacts(self):
        return [Path("artifact1.txt"), Path("artifact2.txt")]

    @patch("pathlib.Path.exists", return_value=True)
    @patch("spl_core.test_utils.spl_build.SplBuild.execute")
    def test_build(self, mock_execute: MagicMock, mock_exists: MagicMock) -> None:
        mock_execute.return_value = 0
        super().test_build()
        mock_execute.assert_called_once_with(target="all")
        mock_exists.assert_any_call()

    @patch("pathlib.Path.exists", return_value=True)
    @patch("spl_core.test_utils.spl_build.SplBuild.execute")
    def test_unittest(self, mock_execute: MagicMock, mock_exists: MagicMock) -> None:
        mock_execute.return_value = 0
        super().test_unittest()
        mock_execute.assert_called_once_with(target="unittests")
        mock_exists.assert_any_call()

    @patch("pathlib.Path.exists", return_value=True)
    @patch("spl_core.test_utils.spl_build.SplBuild.execute")
    def test_reports(self, mock_execute: MagicMock, mock_exists: MagicMock) -> None:
        mock_execute.return_value = 0
        super().test_reports()
        mock_execute.assert_called_once_with(target="all")
        mock_exists.assert_any_call()


class Test_Other__Variant(Test_SomeVariant):
    def test_variant(self):
        assert self.variant == "Other/Variant"

    @property
    def component_paths(self):
        return [Path("component3"), Path("component4")]

    @property
    def expected_build_artifacts(self):
        return [Path("artifact3"), Path("artifact4")]
