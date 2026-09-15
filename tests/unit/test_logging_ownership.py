"""
Guards the rule of ADR 0004: an application configures logging, a library only logs.

loguru's logger is one global object per process and ``setup_logger`` replaces
every sink on it. A module that calls it while spl-core acts as a library would
silently overrule whatever the consumer set up.
"""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[2]

SEARCH_ROOTS = (
    REPO_ROOT / "src" / "spl_core",
    # spl-core's own pypeline steps. `pypeline` calls `setup_logger` in its
    # entry point, so it owns that process and a step must not configure too.
    REPO_ROOT / "steps",
)

ALLOWED = {
    # spl-core is the application here: it owns the `please` process.
    Path("src") / "spl_core" / "main.py",
    # Acts for the consumer's pytest session and steps aside on request.
    Path("src") / "spl_core" / "test_utils" / "pytest_plugin.py",
}


@pytest.mark.unit
def test_only_the_owner_of_a_process_configures_the_logger():
    offenders = sorted(str(path.relative_to(REPO_ROOT)) for root in SEARCH_ROOTS for path in root.rglob("*.py") if "setup_logger" in path.read_text(encoding="utf-8") and path.relative_to(REPO_ROOT) not in ALLOWED)

    assert not offenders, f"these modules must not configure the logger, see ADR 0004: {offenders}"
