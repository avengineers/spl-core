from pathlib import Path

from py_app_dev.core.logging import logger
from pypeline.domain.pipeline import PipelineStep


class RunPytest(PipelineStep):
    def run(self) -> None:
        logger.info(f"{self.get_name()}")
        self.execution_context.create_process_executor(["poetry", "run", "pytest"]).execute()

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
