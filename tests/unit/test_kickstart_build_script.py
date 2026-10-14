"""Unit tests for the build kit selection of the kickstart project build.ps1."""

import shutil
import subprocess
from pathlib import Path

import pytest

TEMPLATE_BUILD_SCRIPT = Path("src/spl_core/kickstart/templates/project/build.ps1")

# Every target that spl-core creates only in the 'test' build kit, and targets that exist in 'prod'
GUESSED_BUILD_KITS = {
    "all": "prod",
    "src_greeter": "prod",
    "src_greeter_reporter": "prod",
    "unittests": "test",
    "src_greeter_unittests": "test",
    "reports": "test",
    "src_greeter_report": "test",
    "docs": "test",
    "src_greeter_docs": "test",
    "source_docs": "test",
    "src_greeter_source_docs": "test",
    "coverage": "test",
    "src_greeter_coverage": "test",
    "coverage_overall_report": "test",
}


def run_build_script_functions(commands: str) -> subprocess.CompletedProcess[str]:
    """Define the functions of the template build.ps1 without running its main part, then run the commands."""
    loader = (
        "$ErrorActionPreference = 'Stop'; "
        f"$script = [System.Management.Automation.Language.Parser]::ParseFile('{TEMPLATE_BUILD_SCRIPT.absolute()}', [ref]$null, [ref]$null); "
        "foreach ($function in $script.FindAll({ $args[0] -is [System.Management.Automation.Language.FunctionDefinitionAst] }, $false)) { "
        ". ([ScriptBlock]::Create($function.Extent.Text)) }; "
    )
    powershell = shutil.which("powershell")
    assert powershell, "Windows PowerShell runs the kickstart build.ps1"
    return subprocess.run([powershell, "-NoProfile", "-NonInteractive", "-Command", loader + commands], capture_output=True, text=True, check=False)


@pytest.fixture(scope="module")
def guessed_build_kits() -> dict[str, str]:
    targets = ",".join(f"'{target}'" for target in GUESSED_BUILD_KITS)
    result = run_build_script_functions(f"foreach ($target in @({targets})) {{ \"$target=$(Get-BuildKit -target $target)\" }}")
    assert result.returncode == 0, result.stderr
    return dict(line.split("=") for line in result.stdout.split())


@pytest.mark.unit
class TestKickstartBuildScriptBuildKit:
    @pytest.mark.parametrize(("target", "expected_build_kit"), GUESSED_BUILD_KITS.items())
    def test_build_kit_is_guessed_from_the_target(self, guessed_build_kits: dict[str, str], target: str, expected_build_kit: str) -> None:
        assert guessed_build_kits[target] == expected_build_kit

    def test_given_build_kit_wins_over_the_guess(self) -> None:
        result = run_build_script_functions("Get-BuildKit -target 'reports' -buildKit 'prod'; Get-BuildKit -target 'all' -buildKit 'test'")
        assert result.returncode == 0, result.stderr
        assert result.stdout.split() == ["prod", "test"]

    @pytest.mark.parametrize("target", ["known", "known also_known"])
    def test_existing_targets_pass_the_check(self, tmp_path: Path, target: str) -> None:
        tmp_path.joinpath("build.ninja").write_text("build known: phony\nbuild also_known: phony\n", encoding="utf-8")
        result = run_build_script_functions(f"Assert-BuildTarget -buildFolder '{tmp_path}' -target '{target}' -buildKit 'prod'")
        assert result.returncode == 0, result.stderr

    def test_unknown_target_in_prod_suggests_the_test_build_kit(self, tmp_path: Path) -> None:
        tmp_path.joinpath("build.ninja").write_text("build known: phony\n", encoding="utf-8")
        result = run_build_script_functions(f"Assert-BuildTarget -buildFolder '{tmp_path}' -target 'src_greeter_test_results' -buildKit 'prod'")
        assert result.returncode != 0
        assert "src_greeter_test_results" in result.stderr
        assert "-buildKit test" in result.stderr

    def test_unknown_target_in_test_does_not_suggest_the_test_build_kit(self, tmp_path: Path) -> None:
        tmp_path.joinpath("build.ninja").write_text("build known: phony\n", encoding="utf-8")
        result = run_build_script_functions(f"Assert-BuildTarget -buildFolder '{tmp_path}' -target 'no_such_target' -buildKit 'test'")
        assert result.returncode != 0
        assert "no_such_target" in result.stderr
        assert "-buildKit test" not in result.stderr
