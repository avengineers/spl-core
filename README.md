# SPL (Software Product Line) Core

In this repository we construct the *SPL Core* functionality that can be integrated into CMake projects.

See https://github.com/avengineers/SPLDemo for an example usage.

## CI (Continuous Integration)

* [![selftests](https://github.com/avengineers/spl/actions/workflows/test.yml/badge.svg)](https://github.com/avengineers/spl/actions/workflows/test.yml)

## Running selftests

* Installing all dependencies:
```powershell
.\build.ps1 -install
```
* Running all tests
```powershell
.\build.ps1
```

## Project Creator

With the integrated project creator you can create a new SPL workspace, e.g.:

```powershell
pipenv run python src/project_creator/creator.py workspace --name MyProject --variant FLV1/SYS1 --out_dir C:\temp
```

Note: one can use the `--variant` argument several times to create a project with multiple variants.
