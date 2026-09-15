# Pytest Integration

SPL Core registers a pytest plugin. pytest loads it automatically because SPL
Core is installed — there is nothing to add to your project.

The plugin has one job: it configures the console logger of the pytest process.
Two ini options steer it, and both are optional.

## Why the plugin exists

`SplBuild` and `SubprocessExecutor` log every line of a build to the console.
Without a configured logger, loguru falls back to its own built-in format, which
puts the module, function and line number of the logging call in front of every
message:

```text
2026-03-24 11:18:16.429 | INFO     | py_app_dev.core.subprocess:execute:154 - -- Detecting C compiler ABI info
```

A single variant build produces thousands of these lines. The plugin installs
the same format the `please` command and the build pipeline already use:

```text
2026-03-24 11:18:16.429 | INFO     | -- Detecting C compiler ABI info
```

## Seeing the code location while debugging

The code location is the part the plugin removes. To read it — which module,
function and line wrote a message — switch it back on in your `pytest.ini`:

```ini
[pytest]
spl_log_code_location = true
```

The line keeps everything else: the plugin stays in charge, the format is still
the platform format, and the output is still written to stdout.

```text
2026-03-24 11:18:16.429 | INFO     | py_app_dev.core.subprocess:execute:154 - -- Detecting C compiler ABI info
```

## Turning it off

The plugin steps aside completely when you set this in your existing
`pytest.ini`:

```ini
[pytest]
spl_setup_logger = false
```

Then nobody configures the logger and loguru's default applies again. Use this
if your project configures loguru itself. To read the code location, prefer
`spl_log_code_location` above — it is the smaller change, and it does not move
the output to stderr.

## Changing either option for a single CI run

You do not need a commit for that. Both are ini options, so pytest accepts them
on the command line:

```text
pytest -o spl_log_code_location=true
pytest -o spl_setup_logger=false
```

Most SPL projects expose a pass-through for extra pytest arguments in their
build wrapper and in their CI job, which is the place to put it.

You can also unload the plugin entirely:

```text
pytest -p no:spl_core
```

## What the plugin does not do

- It does not touch `SplBuild`. `SplBuild` has no logging arguments, and its
  behaviour is unchanged.
- It does not define a log format of its own. It calls `setup_logger()` from
  `py_app_dev`, the same function the `please` command uses, so the platform
  keeps one console format everywhere.
- It does not write a log file.
