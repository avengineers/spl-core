# Software Product Line "spl"

In this repository we construct the &lt;SoftwareProductLine&gt; spl.

The &lt;SPL&gt; spl is a tiny but fully fledged &lt;SPL&gt;: https://en.wikipedia.org/wiki/Software_product_line. It is capable of holding a set of software modules that are differently used and configured among the variants. Each variant creates its own binaries.

## CI (Continuous Integration)

* Find the latest CI results of default branch 'develop' [here](github.com).

## Preparation

The **spl**  contains [Git submodules](https://git-scm.com/book/en/v2/Git-Tools-Submodules) with the unit test framework _Unity_ and mocking framework _CMock_ in it. You don't need to take care for them, They will get checked out automatically by CMake.

Then you can install required and optional tools and install some VS Code extensions. The installer uses Scoop/PowerShell, so it will only run on Windows. The full list of external dependencies is written to `install-mandatory.list`.
* Install mandatory tools by executing `install-mandatory.bat` in the root directory of the repository.
* In case you want to use Visual Studio Code you might want to install the optional tools, too by executing `install-optional.bat` in the root directory of the repository.
  * In VS Code you need to install the following extensions. Hit `Ctrl+Shift+x` to search and install them.
    * CMake Tools
    * C/C++ Extension Pack

## TDD (Test Driven Development) and Unit Testing

In order do develop software using TDD, you need to [write and run unit tests](doc/unitTesting.md).

## Debugging

In case your unit tests are not sufficient enough and a bug was found that is not covered by an automated test, you can also debug your software. By stepping through your software units code line-by-line, you can see its behavior on your PC. [see details here](doc/Debugging.md)

## Build Binaries

In order to build the project's binaries you have two options: Visual Studio Code or command line interface, preference: Visual Studio Code. [see details here](doc/build.md)