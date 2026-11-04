# Release & RC Integration Testing with SPLED

spl-core is consumed by real SPL repositories. Its own CI runs only the unit
test suite; it cannot exercise a full variant build/coverage run of a real SPL
(for one, no `build.sh` lives here — see
{doc}`decisions/0002-build-wrapper-lives-in-the-spl`). End-to-end validation of
changes that affect consumers therefore happens **inside a real SPL (SPLED),
against a spl-core release candidate**, before the official release.

## Why

Unit tests in spl-core assert *how a command is constructed* (e.g. the
`build.bat` / `build.sh` argument list), not that a real SPL build succeeds. A
green spl-core unit suite is necessary but not sufficient. The integration gate
is running the candidate in SPLED.

## Process

1. **Change in spl-core** — implement on a feature branch, unit tests green.
2. **Cut a release candidate** — the branch produces a prerelease version, e.g.
   `8.6.0-rc.1` (non-`develop` branches build RCs; see *Branching & Release
   Strategy* in `AGENTS.md`).
3. **Point SPLED at the RC** — on a SPLED branch (the matching consumer PR), pin
   the spl-core dependency to that RC.
4. **Run SPLED integration tests** — SPLED's CI runs the full variant
   self-tests and coverage against the RC. This is the real integration gate.
5. **On green: release spl-core** — merge the spl-core PR to `develop`;
   python-semantic-release publishes the official (non-RC) version.
6. **Bump SPLED to the official version** — update the SPLED PR to pin the new
   official spl-core release (instead of the RC) and merge it to SPLED `develop`.
7. **Result** — SPLED `develop` always tracks the newest official spl-core, and
   every consumer-facing spl-core change was proven against a real SPL before it
   shipped.

```{mermaid}
graph TD
    A[spl-core feature branch<br/>unit tests green] --> B[Cut RC<br/>e.g. 8.6.0-rc.1]
    B --> C[SPLED branch pins the RC]
    C --> D[SPLED CI:<br/>full variant self-tests + coverage]
    D -->|red| A
    D -->|green| E[Merge spl-core PR to develop<br/>official release]
    E --> F[SPLED PR pins official version]
    F --> G[Merge SPLED PR to develop<br/>develop tracks newest spl-core]
```

## Rules

- Consumer-facing changes (anything touching `SplBuild`, `gcov_maid`, the
  CMake modules, the kickstart template, or the build-wrapper contract) are
  validated against a SPLED RC before the official spl-core release — never
  released blind on the strength of spl-core unit tests alone.
- SPLED never pins a spl-core RC on its `develop` branch. RCs live only on the
  SPLED integration branch; `develop` gets the official version.

## When the computed version was released before

PyPI never takes a file name twice, also not after a release was deleted. When
python-semantic-release computes a version that was released and deleted before,
it stops with "has already been released", and nothing is published.

Make the release by hand instead: run the CI workflow on `develop` with
`force_level` set to `patch`, `minor` or `major`. python-semantic-release then
counts from the highest version tag in the repository, release candidates
included, and makes a full release of that level. Check the version first with
`semantic-release --noop version --minor --print` in a clean checkout of
`develop`.
