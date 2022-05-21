# Import new Dimension Projects

The following steps must be performed in order to import a GNU Make project into a SPL variant.

1. Cloning SPL (this repository)
2. for each project to import
   1. Take a GNU Make project
   2. Run `build.bat --import` to import a project as a new variant in SPL
   3. optional: small adaptions to variant.cmake and toolchain.cmake might be required
   4. Git commit
3. Git Push

## Import Instruction

The import mode of `build.bat` requires 2 commandline parameters:

`build.bat --import --source <path to make project> --variant <name of variant>`

* source: Location of GNU Make project containing a Makefile
* variant: Variant name (<platform>/<subsystem>, e.g. spl/my_variant)

`build.bat --import --source C:\Repos\make\my_project_dir --variant spl/my_variant

This call will import variant and sources into SPL root folder. If it is the first import into this directory, it will create the root files and add all variant and source files, based on the input of ':\Repos\make\my_project_dir'. The new variant will be called 'spl/my_variant'. You will find the variant files under `/variants/spl/my_variant/` and the source files under `/legacy/spl/my_variant/`.

> **_NOTE:_** The source files are imported as legacy. After the import they are still in the same structure as they used to be in the original project. From CMake perspective they are considered as one SW-component. Modularization must be done manually afterwards (component by component). But they are already build with the new toolchain.

If you have an imported project already, it will add a new variant and its sources, keeping the root files. You must make sure to use a new variant name in such a case, otherwise you will overwrite the existing imported project.

## Manual Adaptions

It might occur that you will see changes on Git.

Changes in `toolchain.cmake` file: There might be project specific compiler flags that are used in Make which are not part of the generic compile flags. In such case the line

```cmake
set(COMPILE_C_FLAGS -myflag)
```

or similar could have additional entries like `-DSOME_FEATURE`. If that's the case, discard the change of this line and instead add

```cmake
set(VARIANT_ADDITIONAL_COMPILE_C_FLAGS -DSOME_FEATURE)
```

To the new created `config.cmake`.

## CI

Add the imported project into selftests under /test/test_*.py
