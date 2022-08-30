# Software Product Line Core

In this repository we construct the &lt;SPL-core&gt; functionality that can be integrated into CMake projects.

## CI (Continuous Integration)

* [![selftests](https://github.com/avengineers/spl/actions/workflows/test.yml/badge.svg)](https://github.com/avengineers/spl/actions/workflows/test.yml)

## Preparation

You can add SPL to your CMake project by running:

```powershell
Invoke-Expression "& { $(Invoke-RestMethod https://raw.githubusercontent.com/avengineers/SPL/develop/install.ps1) } v1.0.9"
```

This call will download the installer script of a given version (for latest-greatest use "develop") and execute it. It will take care of downloading all mandatory dependencies. The same command can be used to up- or downgrade the version.

Our SPL works best with VSCode and some extensions. Make sure to install 'optional' tools as well by running a powershell command from your project root:

```powershell
.\build\spl-core\powershell\spl.ps1 -install -installOptional
```

In VS Code you need to install the following extensions. Hit `Ctrl+Shift+x` to search and install them.
  * CMake Tools
  * C/C++ Extension Pack

### Additional Files

There are some recommended files that should be placed in the root of your project to make it easier to use. See SPLDemo as reference:
* https://github.com/avengineers/SPLDemo/blob/develop/CMakeLists.txt (to include the `SPL` and see how the basic project structure looks like)
* https://github.com/avengineers/SPLDemo/blob/develop/build.bat (to make SPL calls easier, by simply passing all arguments; in case SPL is not downloaded it will do this for the user)
* https://github.com/avengineers/SPLDemo/blob/develop/install-spl.ps1 (activating auto download of SPL will require something similar to this)
* https://github.com/avengineers/SPLDemo/blob/develop/dependencies.json (define other dependencies to download)

## Configuration

There are multiple configurations available that you have to consider for your SPL usage.

### .vscode/cmake-variants.json

lorem ipsum
### .vscode/settings.json

lorem ipsum

### dependencies.json

lorem ipsum

### tools/splExtensions/powershell/setup scripts

lorem ipsum

## TDD (Test Driven Development) and Unit Testing

In order to develop software using TDD, you need to [write and run unit tests](doc/unitTesting.md).

## Debugging

In case your unit tests are not sufficient enough and a bug was found that is not covered by an automated test, you can also debug your software. By stepping through your software units code line-by-line, you can see its behavior on your PC. [see details here](doc/debugging.md)

## Build Binaries

In order to build the project's binaries you have two options: Visual Studio Code or command line interface, preference: Visual Studio Code. [see details here](doc/build.md)
