# Software Product Line Core

In this repository we construct the *SPL Core* functionality that can be integrated into CMake projects.

See https://github.com/avengineers/SPLDemo for an example usage.

## CI (Continuous Integration)

* [![selftests](https://github.com/avengineers/spl/actions/workflows/test.yml/badge.svg)](https://github.com/avengineers/spl/actions/workflows/test.yml)

## Getting started

First thing to do is to install all SPL dependencies and executing tests by opening a terminal and running:

```powershell
.\build.ps1
```

Now you can just create a new SPL workspace. We recommend using the workspace creator wrapper for it.

**Example:** create a workspace called `MyProject` with a flavor `FLV1/SYS1` under `C:\temp`

```powershell
.\spl.bat workspace --name MyProject --variant FLV1/SYS1 --out_dir C:\temp
```

Execute `.\spl.bat --help` to see all available options.

Note: one can use the `--variant` argument several times to create a project with multiple variants.
