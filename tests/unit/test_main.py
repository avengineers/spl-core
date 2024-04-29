from pathlib import Path
from typing import List

import pytest
from typer.testing import CliRunner

from spl_core import __version__
from spl_core.main import app

runner = CliRunner()


@pytest.fixture
def kickstart_files() -> List[str]:
    """Collect all project template files."""
    project_template_path = Path("src/spl_core/kickstart/templates/project")
    all_files = [str(path.relative_to(project_template_path)) for path in project_template_path.rglob("*") if path.is_file()]
    assert len(all_files), "the project template shall not be empty"
    return all_files


def test_init_default(kickstart_files: List[str], tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", "--project-dir", tmp_path.as_posix()])
    assert result.exit_code == 0

    for file in kickstart_files:
        assert tmp_path.joinpath(file).exists(), f"{file} shall exist"


def test_init_with_force_in_non_empty_directory(tmp_path: Path, kickstart_files: List[str]) -> None:
    tmp_path.joinpath("test").mkdir()
    result = runner.invoke(app, ["init", "--project-dir", tmp_path.as_posix()])
    assert result.exit_code == 1, "The command shall fail because the directory is not empty."

    result = runner.invoke(app, ["init", "--force", "--project-dir", tmp_path.as_posix()])
    assert result.exit_code == 0, "The command shall succeed because of the --force flag."

    for file in kickstart_files:
        assert tmp_path.joinpath(file).exists(), f"{file} shall exist"


def test_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0

    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert f"please {__version__}" in result.output
