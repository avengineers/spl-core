# 0002 — The platform build wrapper (`build.bat` / `build.sh`) is owned by the SPL, not spl-core

- Status: accepted
- Date: 2026-07-16
- Deciders: SPL Core maintainers, Product Owner

## Context

`SplBuild.execute()` (`src/spl_core/test_utils/spl_build.py`) drives a
repository-level build wrapper script rather than calling CMake/Ninja directly.
Since it became platform-aware it invokes:

- **Windows** (`sys.platform` starts with `win`): `build.bat` with `-flag` style
  options.
- **Linux / macOS**: `bash ./build.sh` with `--flag` style options.

This raised the question: should spl-core ship a `build.sh` (e.g. in the
kickstart template, next to the `build.bat` it already scaffolds)?

The wrapper is the *project's* entry point, not spl-core's. It is
environment-specific (shell, toolchain bootstrap, PowerShell vs. POSIX sh) and
each SPL owns it after scaffolding. spl-core is consumed as a library/CMake
module; it defines *what command* it will call, not *how that command is
implemented* in a given SPL.

## Decision

**The build wrapper is owned by the SPL consumer repository. spl-core defines
only the command contract that `SplBuild.execute()` invokes; it does not ship a
`build.sh`.**

`build.sh` is intentionally absent from spl-core, including the kickstart
template. A SPL that wants to run its variant self-tests on Linux/macOS provides
its own `build.sh` peer of `build.bat` that honours the contract below. (The
kickstart template currently scaffolds only `build.bat` + `build.ps1`; that is
the Windows-first default, and a Linux-capable SPL adds `build.sh` itself.)

### Command contract

`SplBuild.execute()` builds exactly this command; the wrapper must accept it.
`additional_args` are appended verbatim (raw passthrough to the inner build
tool, e.g. `["-j", "4"]`) — do **not** re-map them.

| Semantic     | Windows (`build.bat`)      | Linux/macOS (`bash ./build.sh`) |
| ------------ | -------------------------- | ------------------------------- |
| action       | `-build`                   | `--build`                       |
| build kit    | `-buildKit <kit>`          | `--build-kit <kit>`             |
| variant      | `-variants <variant>`      | `--variant <variant>`           |
| target       | `-target <target>`         | `--target <target>`             |
| reconfigure  | `-reconfigure`             | `--reconfigure`                 |
| build type   | `-buildType <type>` (opt.) | `--build-type <type>` (opt.)    |

The wrapper is invoked from the repository root (relative `./build.sh`), and the
POSIX wrapper is run through `bash` explicitly, so it needs no execute bit and no
shebang resolution via `PATH`.

## Alternatives considered

- **Ship `build.sh` in the kickstart template** — Rejected. It would bake one
  fixed shell/bootstrap implementation into every scaffolded project, which SPLs
  then have to diverge from anyway. The wrapper is project-owned; spl-core should
  not dictate its implementation, only its interface.
- **Drive `pwsh -File build.ps1` on all platforms** — Rejected for now.
  PowerShell Core runs cross-platform and would reuse the single tested
  `build.ps1`, avoiding a second wrapper and the `-flag`/`--flag` asymmetry. It
  was not chosen because it forces a PowerShell Core dependency onto every
  Linux/macOS runner, whereas SPLs already have (or can trivially add) a POSIX
  `build.sh`. Revisit if wrapper drift between `build.bat`/`build.ps1` and each
  SPL's `build.sh` becomes a real maintenance problem.

## Consequences

- Positive: spl-core stays a build *module*, free of a POSIX wrapper it would
  have to maintain per environment. SPLs keep full control of their build entry
  point. The contract is explicit and discoverable here.
- Negative / trade-offs: the contract is hand-maintained on two sides. If a flag
  changes in spl-core, every SPL's `build.sh` must follow — nothing enforces
  this at build time. Note the intentional naming asymmetry (`-variants` plural
  on Windows vs. `--variant` singular on POSIX) so implementers don't "fix" it.
- Follow-up: because spl-core's own CI cannot exercise a real SPL build on Linux
  (no `build.sh` here), end-to-end validation happens by testing a spl-core
  **release candidate** inside a real SPL (SPLED) before the official release.
  See {doc}`../release_integration`.
