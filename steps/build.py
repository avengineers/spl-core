import os
from pathlib import Path

from py_app_dev.core.logging import logger
from pypeline.domain.pipeline import PipelineStep

COVERAGE = ["poetry", "run", "coverage"]


class RunPytest(PipelineStep):
    """
    Run the test suite and measure coverage.

    Coverage is started by ``coverage run``, not by ``pytest --cov``. pytest
    imports the ``pytest11`` entry point of spl_core while it starts up, which is
    before any pytest plugin can begin measuring. Everything that runs at import
    time -- ``src/spl_core/__init__.py`` and the plugin module itself -- would
    therefore read as uncovered. ``coverage run`` is already measuring when
    pytest starts, so those lines are counted.

    ``COVERAGE_PROCESS_START`` lets processes the tests start measure themselves
    as well; ``coverage combine`` merges their data files into one.
    """

    def run(self) -> None:
        logger.info(f"{self.get_name()}")
        self._coverage("erase")
        # Every process started while this is set measures itself. It must not
        # outlive the test run, or the following pipeline steps leave data files
        # behind that the next `coverage combine` would merge in.
        os.environ["COVERAGE_PROCESS_START"] = str(Path("pyproject.toml").resolve())
        try:
            self._coverage("run", "-m", "pytest")
        finally:
            os.environ.pop("COVERAGE_PROCESS_START", None)
            # A failing test suite still has to produce the report CI uploads.
            self._coverage("combine")
            self._coverage("xml", "-o", "out/coverage.xml")
            self._coverage("report", "--show-missing")

    def _coverage(self, *arguments: str) -> None:
        self.execution_context.create_process_executor([*COVERAGE, *arguments]).execute()

    def get_inputs(self) -> list[Path]:
        return []

    def get_outputs(self) -> list[Path]:
        return []

    def get_name(self) -> str:
        return self.__class__.__name__

    def update_execution_context(self) -> None:
        pass


class GenerateDocs(PipelineStep):
    def run(self) -> None:
        logger.info(f"{self.get_name()}")
        self.execution_context.create_process_executor(["poetry", "run", "sphinx-build", "docs", "out/docs/html"]).execute()

    def get_inputs(self) -> list[Path]:
        return []

    def get_outputs(self) -> list[Path]:
        return []

    def get_name(self) -> str:
        return self.__class__.__name__

    def update_execution_context(self) -> None:
        pass
