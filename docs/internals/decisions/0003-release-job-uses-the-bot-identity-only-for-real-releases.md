# 0003 — The release job uses the bot identity only for real releases

- Status: accepted
- Date: 2026-08-21
- Deciders: SPL Core maintainers

## Context

The `release` job in `.github/workflows/ci.yml` runs on three event types, and
`Determine Release Type` gives each a different mode:

| Event                        | Mode      | Writes to `develop`? |
| ---------------------------- | --------- | -------------------- |
| `push` to `develop`          | release   | **Yes** — version bump commit and tag |
| `workflow_dispatch`          | release   | **Yes** — release candidate |
| `pull_request`               | `--noop`  | No — reports the next version and stops |

On 2026-05-31 the `Protect develop` branch ruleset was activated. The automatic
`GITHUB_TOKEN` could no longer push the version bump, so the same day a GitHub
App identity was introduced (`6705a1d`, re-applied as `a25f45a`). That commit
added `Generate Release Bot Token` as the job's **first** step and routed
`checkout` and `Release` through the App token.

The App token requires `secrets.APP_ID` and `secrets.APP_PRIVATE_KEY`. GitHub
does not supply repository or organisation secrets to two kinds of run:

- **Fork pull requests** — secrets are never passed to forks.
- **Dependabot pull requests** — these read a separate Dependabot secret store.

Both therefore resolved the secrets to empty strings and failed on step 1,
before reaching a single useful step. Pushes to `develop` were unaffected, so
releases kept working while every fork and Dependabot pull request showed a red
`release` check. A `if: github.actor != 'dependabot[bot]'` guard was added as a
stop-gap; it silenced Dependabot but not forks, and it removed the dry run
rather than fixing it.

The underlying mistake is scope, not the App identity itself: a credential
needed by *one* operation was applied to *all* invocations of the job.

## Decision

**The bot identity is generated only for events that actually write to the
protected branch. Pull requests fall back to the automatic `GITHUB_TOKEN`.**

```yaml
- name: Generate Release Bot Token
  id: app-token
  if: github.event_name != 'pull_request'
  uses: actions/create-github-app-token@v2
  with:
      app-id: ${{ secrets.APP_ID }}
      private-key: ${{ secrets.APP_PRIVATE_KEY }}

- uses: actions/checkout@v6
  with:
      fetch-depth: 0
      repository: ${{ github.event.pull_request.head.repo.full_name || github.repository }}
      ref: ${{ github.event.inputs.target_branch || github.head_ref || github.ref_name }}
      token: ${{ steps.app-token.outputs.token || github.token }}
```

The `Release` step takes the same `${{ steps.app-token.outputs.token || github.token }}`
fallback. `Publish package distributions to GitHub Releases` keeps the plain App
token, because it is gated on `publish_release == 'true'` and so only ever runs
when the token step has run.

Three supporting points:

- **`--noop` needs no privilege.** It reads the commit history, prints the
  version it would produce, and writes nothing. Verified on PR #353: the
  `Release` step completed successfully on the automatic token.
- **`repository:` is required for forks.** `github.head_ref` is a bare branch
  name that exists in the fork, not in this repository. Without an explicit
  head repository, `checkout` looks for that branch here and fails. This was
  broken before the ruleset too; it had simply never been exercised.
- **The `if: github.actor != 'dependabot[bot]'` guard is removed.** With the
  token correctly scoped, Dependabot pull requests run the dry run like any
  other pull request.

The ruleset itself is unchanged. Its App bypass is correct — that is why pushes
to `develop` release successfully.

## Alternatives considered

- **Copy `APP_ID` and `APP_PRIVATE_KEY` into the Dependabot secret store** —
  Rejected. It fixes Dependabot but not forks, because no secret store reaches a
  fork. It also exposes the App private key to runs that install and execute
  unreviewed third-party packages, and that App can push to repositories and cut
  releases. A dependency-bump pull request is precisely the run where a
  compromised package would look for it.
- **Skip the whole `release` job on pull requests** (`if: github.event_name != 'pull_request'`
  at job level) — Rejected. It is one line and it does turn the checks green, but
  it removes a quality gate to hide a configuration error. The dry run is the
  only pre-merge signal that semantic-release can still parse the commit history
  and configuration.
- **Keep the `dependabot[bot]` actor guard** — Rejected, and reverted. It
  special-cases one bot for a problem shared by every run that lacks secrets, so
  forks stayed broken and the special case invited more special cases.
- **Split into `release-dry-run` and `release` jobs** — Deferred, not rejected.
  Two jobs would make the distinction visible in the job name instead of a step
  condition, and would confine `environment: release` to runs that genuinely
  deploy. It is the better long-term shape; it was not chosen now because it is a
  larger change than the defect required. See the follow-up below.

## Consequences

- Positive: fork, Dependabot and maintainer pull requests all run the release dry
  run again. The App private key never enters a run triggered by unreviewed code.
  `develop` stays protected and releases are untouched. No secret has to be
  duplicated into a second store.
- Negative / trade-offs: the credential now depends on `github.event_name`, so
  the job reads two ways depending on the trigger — a subtlety worth keeping the
  inline comments for. The `|| github.token` fallback is silent: if the token step
  ever fails on a release event, the job continues with a read-only token and
  fails later and less obviously than it would have.
- Follow-up: `environment: release` still applies to pull request runs. If that
  environment gains required reviewers, pull requests will queue for approval
  instead of running. Splitting the job as described above resolves this and is
  the recommended next step.
