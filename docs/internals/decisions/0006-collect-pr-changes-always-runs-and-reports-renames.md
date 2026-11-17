# 0006 — CollectPRChanges always runs and reports renames

- Status: accepted
- Date: 2026-11-17
- Deciders: SPL Core maintainers

## Context

The pypeline step `CollectPRChanges` writes `pr_changes.json` for a pull request: the target
branch, the source branch, the head commit and the changed files. Quality gates in an SPL read it.
A typical gate checks only the changed files, and compares their results with the results of the
same files on the target branch (the baseline). Two defects made the file wrong.

### A stale file was reused

The py_app_dev executor skips a step when the stored `get_config()` equals the current one and all
recorded inputs and outputs still exist with the same hash. The step's config held only the head of
`origin/<source branch>`, read without a fetch. The target branch was not part of it.

Two pull requests from the same source branch and head, but with different targets, built in one
shared CI workspace. The second build skipped the step and kept the target of the first one. A gate
that read the file then compared against the wrong baseline. The same skip happens when the target
branch moves on while the source head stays the same. Without a CI context the config was always empty, so the
step never ran again once the file existed.

### A moved file lost its baseline

`changed_files` lists a renamed file under its new path only. The target branch knows the file under
its old path. A gate that looks up the baseline by path finds nothing, and every existing finding in
the file counts as new. A pull request that only moves sources into another folder then fails the
gate, although it adds no new finding.

## Decision

**The step runs on every build, and `pr_changes.json` reports every rename that git detects. The
consumer decides what a rename means.**

- `CollectPRChanges.get_needs_dependency_management()` returns `False`. The executor then calls
  `run()` directly, without a cache check. `get_config()` is removed, because it only fed the cache.
- `PR_Changes` gets `renamed_files: dict[str, str]` (new path to old path), empty by default. It holds
  all renames, pure moves (`R100`) included. `changed_files` keeps its content: the new path for a
  rename.
- The step reads `git diff --name-status -M` instead of `--name-only`, with the same fallback
  commands. `-M` is explicit, so a `diff.renames=false` setting cannot change the result. Lines
  without a tab are skipped: git warnings arrive in the same output, because stderr is merged into
  stdout.

## Alternatives considered

- **Put the target branch and the target head into `get_config()`.** `get_config()` runs before
  `run()`, so the target head would need an extra `git ls-remote` or fetch there. That is more code to
  keep a cache of a step that costs two fetches and one diff.
- **Drop pure moves from `changed_files`.** That fixes pure moves only. A file that is moved and
  edited still has an empty baseline. It also takes the decision away from the consumer.

## Consequences

- Positive: the file always matches the current pull request. A consumer can find the baseline of a
  moved file under its old path.
- Positive: old files without `renamed_files` still load. A consumer with an older spl-core ignores
  the new key, because mashumaro ignores unknown keys.
- Negative / trade-offs: the executor stores no run info for this step. Its log says "does not need
  dependency management. Executing directly." instead of "execution skipped".
- Known limit: with a narrowed fetch refspec, `git fetch origin <branch>` moves only `FETCH_HEAD`,
  and the `origin/<branch>` refs that the step reads can be old. This is unchanged.
- Follow-ups: a gate that compares results by path should read the baseline of a renamed file under
  `renamed_files[path]`. Until it does, it behaves as before. Before the release, test a release
  candidate in SPLED, as described in {doc}`../release_integration`.
