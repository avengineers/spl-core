# SPL (Software Product Line) Core

_SPL Core_ is our CMake module to support multiple projects as variants of one SPL repository.

## CI (Continuous Integration)

-   [![selftests](https://github.com/avengineers/spl/actions/workflows/test.yml/badge.svg)](https://github.com/avengineers/spl/actions/workflows/test.yml)

## Installation of Dependencies

```powershell
.\build.ps1 -install
```

## Building

-   Execution of all tests
-   Building documentation

```powershell
.\build.ps1
```

## Project Creator

With the integrated project creator you can create a new SPL workspace, e.g.:

```powershell
pipenv run python src/project_creator/creator.py workspace --name MyProject --variant FLV1/SYS1 --out_dir C:\dev
```

Note: one can use the `--variant` argument several times to create a project with multiple variants.
