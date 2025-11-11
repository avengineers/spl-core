import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from mashumaro.mixins.json import DataClassJSONMixin
from py_app_dev.core.logging import logger
from py_app_dev.core.subprocess import SubprocessExecutor
from pypeline.domain.pipeline import PipelineStep
from pypeline_semantic_release.steps import CIContext


@dataclass
class PR_Changes(DataClassJSONMixin):
    """Dataclass for storing PR changes."""

    ci_system: str
    target_branch: str
    current_branch: str
    commit_id: str
    changed_files: List[str]


class CollectPRChanges(PipelineStep):
    """Collect changed files from a pull request."""

    def run(self) -> None:
        logger.info(f"{self.get_name()}")
        ci_contexts = self.execution_context.data_registry.find_data(CIContext)
        if len(ci_contexts) > 0:
            ci_context = ci_contexts[0]
            logger.info(f"CI context: {ci_context}")
            if ci_context.is_pull_request:
                logger.info(f"Collecting PR changes between branch {ci_context.target_branch} and {ci_context.current_branch}")
                changed_files = self._get_changed_files(ci_context.target_branch, ci_context.current_branch)
                output_file = self.get_outputs()[0]
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text(
                    json.dumps(
                        PR_Changes(
                            ci_system=ci_context.ci_system.name, target_branch=ci_context.target_branch, current_branch=ci_context.current_branch, commit_id=self._get_commit_id(ci_context), changed_files=changed_files
                        ).to_dict(),
                        indent=2,
                    )
                )
                logger.info(f"PR changes saved to {output_file}")

    def _get_changed_files(self, target_branch: str, current_branch: str) -> List[str]:
        """Get list of changed files in the current branch/PR"""
        # Fetch both branches to ensure they exist locally
        logger.info(f"Fetching branches: {target_branch} and {current_branch}")

        # Fetch the target branch
        result = SubprocessExecutor(["git", "fetch", "origin", target_branch]).execute(handle_errors=False)
        if not result or result.returncode != 0:
            logger.warning(f"Failed to fetch target branch {target_branch}")
            return []

        # Fetch the current branch
        result = SubprocessExecutor(["git", "fetch", "origin", current_branch]).execute(handle_errors=False)
        if not result or result.returncode != 0:
            logger.warning(f"Failed to fetch current branch {current_branch}")
            return []

        # Try different git diff approaches in order of preference
        diff_commands = [
            ["git", "diff", "--name-only", f"origin/{target_branch}...origin/{current_branch}"],
            ["git", "diff", "--name-only", f"origin/{target_branch}", f"origin/{current_branch}"],
            ["git", "diff", "--name-only", f"{target_branch}...{current_branch}"],
            ["git", "diff", "--name-only", f"{target_branch}", f"{current_branch}"],
        ]

        for cmd in diff_commands:
            try:
                logger.info(f"Trying command: {' '.join(cmd)}")
                result = SubprocessExecutor(cmd).execute(handle_errors=False)

                if result and result.returncode == 0:
                    if result.stdout.strip():
                        files = [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]
                        logger.info(f"Found {len(files)} changed files")
                        return files
                    else:
                        logger.warning("No changed files found")
                        return []
            except Exception as e:
                logger.warning(f"Command failed: {' '.join(cmd)} - {e}")
                continue
        return []

    def get_inputs(self) -> List[Path]:
        return []

    def get_outputs(self) -> List[Path]:
        return [self.output_dir.joinpath("pr_changes.json")]

    def get_name(self) -> str:
        return self.__class__.__name__

    def update_execution_context(self) -> None:
        pass

    def get_config(self) -> dict[str, str] | None:
        """
        Get runnable configuration.

        (!) Do NOT put sensitive information in the configuration. It will be stored in a file.
        """
        return {"latest_commit": self._get_commit_id()}

    def _get_commit_id(self, ci_context: Optional[CIContext] = None) -> str:
        """Get the latest commit ID in the current branch."""
        try:
            if not ci_context:
                ci_contexts = self.execution_context.data_registry.find_data(CIContext)
                if len(ci_contexts) == 0:
                    logger.info("No CI context found.")
                    return ""
                ci_context = ci_contexts[0]
            if isinstance(ci_context, CIContext) and ci_context.is_pull_request:
                result = SubprocessExecutor(["git", "rev-parse", f"origin/{ci_context.current_branch}"]).execute(handle_errors=False)
                if result and result.returncode == 0:
                    return result.stdout.strip()
        except Exception as e:
            logger.info(f"Failed to get commit ID: {e}")
        return ""
