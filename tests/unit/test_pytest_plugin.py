"""
Tests for the pytest plugin that configures the console logger.

The behaviour can only be observed in a real pytest session, so most tests drive
a nested one via the ``pytester`` fixture. The nested session loads the plugin on
its own through the entry point — no flag is passed — which is exactly the
property consumers rely on: install spl-core, change nothing.

They therefore need spl-core to be installed, which ``poetry install`` does
before the suite runs.
"""

import re
import sys
import tomllib
from pathlib import Path
from typing import Any, cast

import pytest
from py_app_dev.core.logging import logger

from spl_core.test_utils import pytest_plugin

PLUGIN = "spl_core.test_utils.pytest_plugin"

MESSAGE = "hello from the build"

BUILD_OUTPUT_TEST = f"""
from py_app_dev.core.logging import logger


def test_emits_a_log_line():
    logger.info("{MESSAGE}")
"""


ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")


def sink_count() -> int:
    """Number of sinks on the global loguru logger. Only its internals know."""
    # Reached through an untyped name on purpose. mypy sees a different `logger`
    # depending on whether loguru is installed -- pre-commit runs it without --
    # so a `type: ignore` here is required in one environment and reported as
    # unused in the other.
    core: Any = logger
    return len(core._core.handlers)


def stub_config(setup_logger: bool) -> pytest.Config:
    return cast(pytest.Config, StubConfig(setup_logger))


def find_log_line(lines: list[str]) -> str:
    """Return the console line carrying the message, without loguru's colour codes."""
    matches = [ANSI_ESCAPE.sub("", line) for line in lines if MESSAGE in line]
    assert matches, f"no console line containing {MESSAGE!r}"
    return matches[0]


@pytest.fixture
def build_output_project(pytester):
    pytester.makepyfile(test_build_output=BUILD_OUTPUT_TEST)
    return pytester


@pytest.fixture
def restore_logger():
    """Give the outer session a usable logger back after a test removed its sinks."""
    yield
    logger.remove()
    logger.add(sys.stderr)


@pytest.mark.unit
def test_console_line_has_no_code_location(build_output_project):
    result = build_output_project.runpytest_subprocess("--capture=tee-sys")

    result.assert_outcomes(passed=1)
    line = find_log_line(result.outlines)
    assert "test_build_output:test_emits_a_log_line" not in line
    assert line.endswith(f"| {MESSAGE}")


@pytest.mark.unit
def test_ini_option_keeps_the_plugin_out(build_output_project):
    build_output_project.makefile(".ini", pytest="[pytest]\nspl_setup_logger = false\n")

    result = build_output_project.runpytest_subprocess("--capture=tee-sys")

    result.assert_outcomes(passed=1)
    # Nobody configures the logger, so loguru's own default applies: it carries the
    # code location and it writes to stderr instead of stdout.
    line = find_log_line(result.errlines)
    assert "test_build_output:test_emits_a_log_line" in line


@pytest.mark.unit
def test_ini_option_puts_the_code_location_back(build_output_project):
    build_output_project.makefile(".ini", pytest="[pytest]\nspl_log_code_location = true\n")

    result = build_output_project.runpytest_subprocess("--capture=tee-sys")

    result.assert_outcomes(passed=1)
    # Unlike switching the plugin off, this keeps the configured sink: the line
    # stays on stdout and only gains the code location back.
    line = find_log_line(result.outlines)
    assert "test_build_output:test_emits_a_log_line" in line


@pytest.mark.unit
def test_command_line_override_keeps_the_plugin_out(build_output_project):
    result = build_output_project.runpytest_subprocess("--capture=tee-sys", "-o", "spl_setup_logger=false")

    result.assert_outcomes(passed=1)
    line = find_log_line(result.errlines)
    assert "test_build_output:test_emits_a_log_line" in line


@pytest.mark.unit
def test_sink_is_detached_when_the_session_ends(restore_logger):
    config = stub_config(setup_logger=True)

    pytest_plugin.pytest_configure(config)
    assert sink_count() == 1, "the plugin must install exactly one sink"

    pytest_plugin.pytest_unconfigure(config)
    assert sink_count() == 0, "a sink left behind writes to a torn-down capture stream"


@pytest.mark.unit
def test_nothing_is_detached_that_was_not_installed(restore_logger):
    logger.remove()
    logger.add(sys.stderr)
    config = stub_config(setup_logger=False)

    pytest_plugin.pytest_configure(config)
    pytest_plugin.pytest_unconfigure(config)

    assert sink_count() == 1, "the sink of a project that configures itself must survive"


@pytest.mark.unit
def test_plugin_is_registered_as_an_entry_point():
    """Without this registration nothing happens on upgrade and consumers would have to act."""
    pyproject = tomllib.loads((Path(__file__).parents[2] / "pyproject.toml").read_text(encoding="utf-8"))

    entry_points = pyproject["tool"]["poetry"]["plugins"]["pytest11"]

    assert entry_points == {"spl_core": PLUGIN}


class StubConfig:
    """The parts of ``pytest.Config`` the plugin uses."""

    def __init__(self, setup_logger: bool):
        self._values = {
            pytest_plugin.INI_SETUP_LOGGER: setup_logger,
            pytest_plugin.INI_LOG_CODE_LOCATION: False,
        }
        self.stash = pytest.Stash()

    def getini(self, name: str) -> bool:
        assert name in self._values, f"the plugin read an ini option this stub does not know: {name}"
        return self._values[name]
