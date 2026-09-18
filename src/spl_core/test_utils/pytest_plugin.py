"""
Pytest plugin that gives a test session a configured console logger.

Without it nobody configures loguru in a pytest process, so its built-in default
format applies and every line a build writes carries the module, function and
line number of the logging call. The plugin installs the format the rest of the
platform uses, by calling ``setup_logger`` from ``py_app_dev`` — it defines no
format of its own.

It decides nothing. Two ini options in the project's ``pytest.ini`` steer it:
``spl_log_code_location = true`` puts the prefix back for debugging, and
``spl_setup_logger = false`` keeps the project's own logger untouched.
"""

import pytest
from py_app_dev.core.logging import logger, setup_logger

INI_SETUP_LOGGER = "spl_setup_logger"
INI_LOG_CODE_LOCATION = "spl_log_code_location"

_LOGGER_WAS_SET_UP = pytest.StashKey[bool]()


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addini(
        INI_SETUP_LOGGER,
        help="Let SPL Core configure the console logger of this test session. Set it to false if the project configures loguru itself. To read the code location, use spl_log_code_location instead.",
        type="bool",
        default=True,
    )
    parser.addini(
        INI_LOG_CODE_LOCATION,
        help="Prefix every console log line with the module, function and line number that wrote it. Off by default, because a build writes thousands of lines and the prefix is the same for almost all of them.",
        type="bool",
        default=False,
    )


def pytest_configure(config: pytest.Config) -> None:
    if not config.getini(INI_SETUP_LOGGER):
        return
    setup_logger(show_code_location=config.getini(INI_LOG_CODE_LOCATION))
    config.stash[_LOGGER_WAS_SET_UP] = True


def pytest_unconfigure(config: pytest.Config) -> None:
    # The sink is bound to the capture stream of this session. Left in place, it
    # would still be written to after the session tore that stream down.
    if config.stash.get(_LOGGER_WAS_SET_UP, False):
        logger.remove()
