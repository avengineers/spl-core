# How to Start Working on a {ref}`Variant <glossary_variant>`

In this guide, we will show you how to configure a new variant of your SPL.
We will cover the most common use cases for variant configuration, including feature selection, component inclusion, and build customization.
Some of these steps are also explained in the {ref}`"Hello World" Tutorial <hello_world>`.
However, this guide will provide a more detailed explanation of the variant specific configuration.

```{attention}
As a precondition to this guide, you should have a project with at least one component set up and configured.
If you haven't done this yet, please refer to the guide on how to {ref}`start working on a component <start_new_component>`.
```

## Variant directory structure

Inside your project root create a new directory for your variant. The name of this directory should be the name of the variant.
This will result in the following exemplary structure:

```
<project root>
└── variants
    ├── var1
    │
    ├── var2
    │
    └── ...
```

## Select your components - `parts.cmake`

The `parts.cmake` file contains the list of components which are part of your variant.
You have to manually create this file inside the variant directory:

```
<project root>
└── variants
    └── var1
        ├── parts.cmake
        └── ...
```

Add the following lines to the `parts.cmake` file to include the components you want to have as a part of your variant:

```cmake
spl_add_component(src/comp1)
spl_add_component(src/comp2)
```

This {ref}`SPL Core specific macro <cmake-macro-spl-add-component>` is responsible for automatically including the components during the build process.

At last you have to include `parts.cmake` in the `CMakeLists.txt` file of your project root.
You can achieve this by adding the following line to the `CMakeLists.txt` file after the inclusion of `spl.cmake`:

```cmake
# Fetch and make spl-core available
FetchContent_Declare(
  spl-core
  GIT_REPOSITORY https://github.com/avengineers/spl-core.git
  GIT_TAG develop
)
FetchContent_MakeAvailable(spl-core)
include(${spl-core_SOURCE_DIR}/src/spl_core/spl.cmake)

# Include the variant specific parts
include(${CMAKE_SOURCE_DIR}/variants/${VARIANT}/parts.cmake)
```

## Select your features - `KConfig` and `config.txt`

Think of `KConfig` as a tool to define possible features, while `config.txt` reflects the actual selection of those.
For more details, see the [official Kconfig documentation](https://www.kernel.org/doc/html/latest/kbuild/kconfig-language.html).

The `config.txt` file contains then a list of features which are part of your variant. This file is automatically created using `KConfig`.
However, there are still some steps you have to take care of.

Create a `KConfig` model file in the root of your project.:

```
<project root>
├── variants
│   └── ...
├── src
│   └── ...
├── KConfig
└── ...
```

Add the following lines to include the `KConfig` files of your components:

```kconfig
menu "Features"
    source "src/comp1/KConfig"
    source "src/comp2/KConfig"
    ...
endmenu
```

Use `KConfig`'s graphical user interface to create the corresponding `config.txt` file for your variant.
You can start it by running the following command:

```powershell
guiconfig
```

See the {ref}`corresponding section from the "Hello World" tutorial <make_main_component_configurable>` to see how to install it and how to create the `config.txt` file.

The generated `config.txt` now holds all the features you selected for your variant. Please note that this file is not meant to be edited manually.

## Additional CMake configurations - `config.cmake`

In addition, for optional variant specific configurations like target architecture and toolchain, you can create a `config.cmake` file inside your variant directory:

```
<project root>
└── variants
    └── var1
        ├── parts.cmake
        ├── config.txt
        ├── config.cmake
        └── ...
```

You have to include this file in the `CMakeLists.txt` file of your project root.
You can achieve this by adding the following lines to the `CMakeLists.txt` file before the `project()` macro is called for the first time:

```cmake
# Include variant specific configurations
include(${CMAKE_SOURCE_DIR}/variants/${VARIANT}/config.cmake)

if(BUILD_KIT STREQUAL prod)
    project(${VARIANT} C ASM)
else()
    # C++ project due to GTest usage
    project(${VARIANT} C ASM CXX)
endif()
```

Inside the `config.cmake` file you can set a bunch of different options using official CMake syntax.
Refer to the [official CMake documentation](https://cmake.org/cmake/help/latest/index.html) for more information.
Here is a selection of some examples:

- Build-kit and -type specific settings:

```cmake
if(BUILD_KIT STREQUAL prod)
    if(CMAKE_BUILD_TYPE STREQUAL "Debug")
        message(STATUS "Configuring Debug build")
    endif()
endif()
```

- Variant specific settings:

```cmake
set(VARIANT_C_FLAGS ${CCFLAGS})
set(VARIANT_LINKER_FILE ${LDFILE})
set(VARIANT_LINK_FLAGS ${LDFLAGS})
```

- CMake settings:

```cmake
set(CMAKE_C_FLAGS_DEBUG "-O0 -g")
set(CMAKE_C_FLAGS_RELEASE "-O3")
set(CMAKE_C_FLAGS ${VARIANT_C_FLAGS})
```

- Link options:

```cmake
add_link_options(-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard -Wl,-Map=${BUILD_OUT_PATH}/${PROJECT_NAME}.map -T${VARIANT_LINKER_FILE})
```

- CMake toolchain file:

```cmake
set(CMAKE_TOOLCHAIN_FILE ${CMAKE_SOURCE_DIR}/tools/some_compiler/toolchain.cmake)
```

```{note}
This `toolchain.cmake` file is generally used to set compiler specific options and flags using CMake syntax.
Having a dedicated toolchain file allows for consistent and reproducible builds across different environments and simplifies the configuration process by centralizing compiler and linker settings.
While each compiler should have its own toolchain file, you can easily configure your different variants to use different compilers by simply setting the corresponding `toolchain.cmake` file.
```
