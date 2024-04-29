from tests.utils import SplKickstartProjectIntegrationTestBase


class TestSelftests(SplKickstartProjectIntegrationTestBase):
    def test_selftests(self):
        result = self.spl_project.selftests()
        assert result.returncode == 0, "Execution shall not fail."
