import json
from dataclasses import dataclass, field
from pathlib import Path

from mashumaro.mixins.json import DataClassJSONMixin
from py_app_dev.core.logging import logger
from py_app_dev.core.subprocess import SubprocessExecutor
from pypeline.domain.pipeline import PipelineStep
from pypeline_semantic_release.check_ci_context import CIContext


@dataclass
class PR_Changes(DataClassJSONMixin):
    """Dataclass for storing PR changes."""

    ci_system: str
    target_branch: str
    current_branch: str
    commit_id: str
    changed_files: list[str]
    #: new path -> old path, for every rename git detects (pure moves included)
    renamed_files: dict[str, str] = field(default_factory=dict)


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
                changed_files, renamed_files = self._get_changed_files(ci_context.target_branch, ci_context.current_branch)
                output_file = self.get_outputs()[0]
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text(
                    json.dumps(
                        PR_Changes(
                            ci_system=ci_context.ci_system.name,
                            target_branch=ci_context.target_branch,
                            current_branch=ci_context.current_branch,
                            commit_id=self._get_commit_id(ci_context),
                            changed_files=changed_files,
                            renamed_files=renamed_files,
                        ).to_dict(),
                        indent=2,
                    )
                )
                logger.info(f"PR changes saved to {output_file}")

    def _get_changed_files(self, target_branch: str, current_branch: str) -> tuple[list[str], dict[str, str]]:
        """Get the changed files of the PR, and its renames as new path -> old path."""
        # Fetch both branches to ensure they exist locally
        logger.info(f"Fetching branches: {target_branch} and {current_branch}")

        # Fetch the target branch
        result = SubprocessExecutor(["git", "fetch", "origin", target_branch]).execute(handle_errors=False)
        if not result or result.returncode != 0:
            logger.warning(f"Failed to fetch target branch {target_branch}")
            return [], {}

        # Fetch the current branch
        result = SubprocessExecutor(["git", "fetch", "origin", current_branch]).execute(handle_errors=False)
        if not result or result.returncode != 0:
            logger.warning(f"Failed to fetch current branch {current_branch}")
            return [], {}

        # Try different git diff approaches in order of preference
        diff_commands = [
            ["git", "diff", "--name-status", "-M", f"origin/{target_branch}...origin/{current_branch}"],
            ["git", "diff", "--name-status", "-M", f"origin/{target_branch}", f"origin/{current_branch}"],
            ["git", "diff", "--name-status", "-M", f"{target_branch}...{current_branch}"],
            ["git", "diff", "--name-status", "-M", f"{target_branch}", f"{current_branch}"],
        ]

        for cmd in diff_commands:
            try:
                logger.info(f"Trying command: {' '.join(cmd)}")
                result = SubprocessExecutor(cmd).execute(handle_errors=False)

                if result and result.returncode == 0:
                    if result.stdout.strip():
                        changed_files: list[str] = []
                        renamed_files: dict[str, str] = {}
                        for line in result.stdout.splitlines():
                            # Every status line has a tab; lines without one are git warnings (stderr is merged into stdout)
                            if "\t" not in line:
                                continue
                            fields = line.split("\t")
                            changed_files.append(fields[-1])
                            if fields[0].startswith("R"):
                                renamed_files[fields[-1]] = fields[1]
                        logger.info(f"Found {len(changed_files)} changed files, {len(renamed_files)} renamed")
                        return changed_files, renamed_files
                    else:
                        logger.warning("No changed files found")
                        return [], {}
            except Exception as e:
                logger.warning(f"Command failed: {' '.join(cmd)} - {e}")
                continue
        return [], {}

    def get_inputs(self) -> list[Path]:
        return []

    def get_outputs(self) -> list[Path]:
        return [self.output_dir.joinpath("pr_changes.json")]

    def get_name(self) -> str:
        return self.__class__.__name__

    def update_execution_context(self) -> None:
        pass

    def get_needs_dependency_management(self) -> bool:
        """Always run: the step is cheap, and a cached result can name the wrong target branch or the wrong changed files."""
        return False

    def _get_commit_id(self, ci_context: CIContext | None = None) -> str:
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
