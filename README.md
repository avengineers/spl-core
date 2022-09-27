# Software Product Line Core

In this repository we construct the &lt;SPL-core&gt; functionality that can be integrated into CMake projects.

## CI (Continuous Integration)

* [![selftests](https://github.com/avengineers/spl/actions/workflows/gate.yml/badge.svg)](https://github.com/avengineers/spl/actions/workflows/gate.yml)

## Getting started

First thing to do is to install all SPL dependencies by opening a terminal and running:

```
powershell -File install.ps1 -useCurrent
```

Now you can just create a new SPL project. We recommend using the project creator wrapper to generate a tiny SPL project.

**Example:** create a project called `MyProject` with a flavor `FLV1/SYS1` under `C:\temp`
```
.\project_creator.bat --name MyProject --variant FLV1/SYS1 --out_dir C:\temp
```

Execute `.\project_creator.bat --help` to see all available options.

Note: one can use the `--variant` argument several times to create a project with multiple variants.
