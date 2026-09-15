# 0004 — A pytest plugin configures the console logger; the SPL overrides it

- Status: accepted
- Date: 2026-09-14
- Deciders: SPL Core maintainers

## Context

A variant build driven from a consumer test suite floods the console with the
code location of the logging call:

```text
2026-03-24 11:18:16.429 | INFO     | py_app_dev.core.subprocess:execute:154 - -- Detecting C compiler ABI info
```

`SubprocessExecutor.execute` logs **every** line of the build output, so a CMake
build produces thousands of such lines. The wanted line is:

```text
2026-03-24 11:18:16.429 | INFO     | -- Detecting C compiler ABI info
```

### Where the prefix comes from

Not from `py_app_dev`. Its `setup_logger()` has never put the code location on
the console — the format it installs is time, level, message. The prefix is
**loguru's own built-in default format**, which applies whenever nobody calls
`setup_logger()` at all.

loguru's logger is a single global object per process. `setup_logger()` calls
`logger.remove()` and then `logger.add()`, so it replaces every existing sink;
the last caller wins. Consequently only the owner of a process may configure it.

Three kinds of process run spl-core code, and one of them has no owner that
configures:

| Process | who calls `setup_logger()` | console |
| --- | --- | --- |
| `please` CLI | `spl_core/main.py` | clean |
| pypeline run | `pypeline`'s own entry point | clean |
| **pytest run in a consumer project** | **nobody** | **loguru default → prefix** |

### Forces

- **The SPL must keep control.** spl-core is a library in this role. A library
  that silently reconfigures global logging fights whatever the consumer set up.
- **No new configuration file.** Consumer projects already carry a long list of
  configuration files. A seventeenth one for a log format is not acceptable.
- **Zero adaptation on upgrade.** A consumer must be able to take a new spl-core
  release without editing anything of its own. This is a hard requirement.
- **Reachable from CI without a commit.** Switching the prefix back on for one
  debugging run must not require a pull request and a release.

## Decision

**spl-core ships a pytest plugin that configures the console logger for the
pytest process. It is active by default, has no policy of its own, and any
consumer can override or disable it through its existing `pytest.ini`.**

```text
SPL project   pytest.ini          says what      (optional)
spl-core      pytest plugin       forwards       (decides nothing)
py_app_dev    setup_logger(...)   executes
```

The plugin is registered as a `pytest11` entry point, so pytest finds it because
spl-core is installed. Nothing is created, imported or declared in the consumer.

When the consumer says nothing, the plugin applies `py_app_dev`'s default. It
does not invent a format of its own: it replaces *loguru's* default with the
default the platform already uses everywhere else.

Overrides, in the consumer's existing `pytest.ini`:

```ini
spl_log_code_location = true    # keep the plugin, put the prefix back
spl_setup_logger = false        # spl-core does not touch the logger at all
```

From CI without a commit, through the same options:

```text
-o spl_log_code_location=true
-o spl_setup_logger=false
```

or `-p no:spl_core` to unload the plugin entirely.

The two are not interchangeable. `spl_log_code_location` is the one to reach for
while debugging: the plugin keeps its sink, so only the prefix returns.
`spl_setup_logger = false` hands the process back to loguru's default, which
also carries the prefix but writes to stderr instead of stdout. It exists for a
consumer that configures loguru itself, not for reading a code location.

### `SplBuild` is not changed

`SplBuild` gets no new argument and calls nothing. Two reasons:

- Consumers call `SubprocessExecutor` **directly** in their test files, not only
  through `SplBuild`. A fix inside `SplBuild` would never reach those lines. The
  switch has to cover the whole pytest process.
- `SplBuild.execute()` carries `@time_it()`, which logs the START line *before*
  the method body runs. Anything called inside the body is already too late for
  that line.

### The rule this records

**An application configures logging; a library only logs.** spl-core imports
`setup_logger` in `main.py` (where it is the application) and in the pytest
plugin (where it acts on the consumer's behalf, and only until the consumer says
otherwise). Everywhere else — `kickstart/create.py`, `src/spl_core/steps/`,
`test_utils/` — it imports `logger` and nothing more. A guard test in
`tests/unit/` fails if that is ever broken.

The repository's own pipeline in `steps/` follows the same rule, and the guard
test covers it. `pypeline` calls `setup_logger()` in its entry point, so it owns
that process; a pipeline step that configured the logger as well would overrule
the runner that started it. This is why the console of a `pypeline run` is
already clean and needs no change here.

## Alternatives considered

- **The consumer calls `setup_logger()` in its `conftest.py`** — Rejected. It is
  the most explicit option and mirrors how `conf.py` configures Sphinx, but every
  consumer would have to edit a file to get the fix. That breaks the
  zero-adaptation requirement.
- **`SplBuild` configures the logger itself** — Rejected. It makes a library
  reconfigure global logging with no way for the consumer to object, and it still
  misses direct `SubprocessExecutor` calls and the `@time_it` START line.
- **A switch in the consumer's `conf.py`** — Rejected. `conf.py` is Sphinx's
  configuration file and is imported by `sphinx-build` only. It never reaches the
  pytest process, so the setting would have no effect.
- **Only raise the `py_app_dev` dependency and change nothing else** — Rejected.
  It fixes nothing here: the published `setup_logger()` already produces the
  wanted format, and the problem is that nobody calls it.

## Consequences

- Positive: consumers get the clean console by upgrading, with no edit of their
  own. The switch lives in a file they already have. spl-core owns no log format
  of its own, so the platform keeps one format everywhere.
- Negative / trade-offs: the plugin loads into **every** pytest session that has
  spl-core installed, including sessions that never touch a build. It is inert
  unless it configures, and `-p no:spl_core` unloads it, but it is one more thing
  in the session. A consumer that already configures loguru in its own
  `conftest.py` would be overridden and has to set `spl_setup_logger = false`;
  no such consumer is known today.
- Negative / trade-offs: the console format changes for existing consumers. That
  is the point of the change, but anyone parsing the console text with a pattern
  would notice. Consumers are expected to read machine-readable results from the
  JUnit XML, not from the console.
- Positive: the debugging case needs no compromise. `py_app_dev` gained
  `setup_logger(show_code_location=...)`, and the second ini option
  `spl_log_code_location` forwards that flag, so the prefix returns without
  losing the configured sink. This raises the `py_app_dev` floor to the release
  that carries the parameter.
- Follow-up: as with every consumer-facing change, this is validated in a real
  SPL before release. See {doc}`../release_integration`.
