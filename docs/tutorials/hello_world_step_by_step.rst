.. sectnum::

"Hello World" with SPL-Core
***************************

In this tutorial, you'll learn how to set up, write, and build a simple "Hello World" program using SPL-Core.

We will follow these steps:

* build a simple "Hello World" program with CMake and Clang
* build the same program with SPL-Core
* convert the program to a SPL-Core project with multiple variants

"Hello World" with CMake
========================

Create a ``main.c``
-------------------

Start by writing a simple "Hello World" program in C. Create a new file named ``main.c`` and add the following code:

.. code-block:: c

   #include <stdio.h>

   int main() {
       printf("Hello, World!\n");
       return 0;
   }


Create a Minimal CMakeLists.txt File
------------------------------------

Next, create a file named ``CMakeLists.txt`` in the same directory as your ``main.c`` file. Add the following contents:

.. code-block:: cmake

   cmake_minimum_required(VERSION 3.20)

   project(HelloWorld)

   set(CMAKE_C_COMPILER clang)

   add_executable(helloworld main.c)


Install the Necessary Build Tools
---------------------------------

For this tutorial, we'll use the Scoop package manager to install the necessary software on Windows. If you don't have Scoop installed, you can get it from its `official site <https://scoop.sh>`_.
Next, install the ``mingw-winlibs-llvm-ucrt`` package, which contains Clang, CMake and Ninja:

.. code-block:: bash

   scoop install mingw-winlibs-llvm-ucrt


Run CMake Configure to Generate Ninja Build Files
-------------------------------------------------

Using CMake, you can generate build files for various build systems. For this tutorial, we'll use Ninja.

Run the CMake configuration command:

.. code-block:: bash

   cmake -B build -G "Ninja"

We used the ``-B`` option to specify the build directory, and the ``-G`` option to specify the build system. You can use ``cmake --help`` to see a list of available generators.


Build the Project Using CMake
-----------------------------

With the build files generated, you can now build the project using CMake:

.. code-block:: bash

   cmake --build build

After building, you should see an executable named ``helloworld.exe`` in the build directory. You can run it to see the "Hello, World!" output.


"Hello World" with SPL-Core
===========================

Let us now build the same "Hello World" program using SPL-Core.

For this we will define first some structure for our project:

* ``src``: contains the source code components
* ``variants``: contains the variants of the project


Create the ``main`` Component
-----------------------------

Let us create a directory for the new component and move the ``main.c`` to it.

.. code-block:: bash

   mkdir src/main
   mv main.c src/main/main.c

Add a ``CMakeLists.txt`` file to create the ``main`` component:

.. code-block:: cmake

   spl_add_source(main.c)
   spl_create_component()


Create a SPL Variant
--------------------

Create a directory for the variant:

.. code-block:: bash

   mkdir variants/lang/en

Add a ``parts.cmake`` to define the variant relevant components:

.. code-block:: cmake

   spl_add_component(src/main)


Include SPL-Core
----------------

Update the ``CMakeLists.txt`` in the root directory to include SPL-Core:

.. code-block:: cmake

    cmake_minimum_required(VERSION 3.10)

    # configure the current variant to be build
    set(VARIANT ${FLAVOR}/${SUBSYSTEM} CACHE STRING "Variant to build.")
    set(BUILD_KIT prod CACHE STRING "Target Group to build.")
    set(LINKER_OUTPUT_FILE main.exe)

    project(${VARIANT})

    set(CMAKE_C_COMPILER clang)

    # Fetch all external dependencies into modules directory
    set(FETCHCONTENT_BASE_DIR ${CMAKE_SOURCE_DIR}/build/modules CACHE INTERNAL "")
    set(FETCHCONTENT_QUIET FALSE)
    include(FetchContent)

    # Fetch and make spl-core available
    FetchContent_Declare(
        spl-core
        GIT_REPOSITORY https://github.com/avengineers/spl-core.git
        GIT_TAG develop
    )
    FetchContent_MakeAvailable(spl-core)
    include(${spl-core_SOURCE_DIR}/cmake/spl.cmake)

    # Include the variant specific parts
    include(${CMAKE_SOURCE_DIR}/variants/${VARIANT}/parts.cmake)


Build the Project Using SPL-Core
--------------------------------

To generate the build files for our variant run:

.. code-block:: bash

   cmake -B build/lang/en -G "Ninja" -DFLAVOR=lang -DSUBSYSTEM=en

To build the project run:

.. code-block:: bash

   cmake --build build/lang/en

After building, you should see an executable named ``main.exe`` in the build directory. You can run it to see the "Hello, World!" output.

To ease building a variant let's create a powershell script ``build.ps1`` which asks the user to select one of the available variants and then builds it:

.. code:: powershell

   $variantsDirectory = Join-Path $PSScriptRoot "variants"

   # Find all 'parts.cmake' files in the 'variants' directory and its subdirectories
   $partsCMakeFiles = Get-ChildItem -Path $variantsDirectory -Filter "parts.cmake" -File -Recurse | ForEach-Object {
      # Get the relative path of the 'parts.cmake' file
      $relativePath = $_.FullName.Substring($variantsDirectory.Length)
      # Remove leading backslashes and trim
      $relativePath.TrimStart('\')
   }

   # Create an array to store the extracted subpaths
   $subpaths = @()
   foreach ($file in $partsCMakeFiles) {
      $subpath = [System.IO.Path]::GetDirectoryName($file)
      if ($subpaths -notcontains $subpath) {
         $subpaths += $subpath
      }
   }

   # Display the subpaths as a numbered list and ask the user to choose one
   Write-Host "Select a variant by entering the corresponding number:`n"
   for ($i = 0; $i -lt $subpaths.Count; $i++) {
      Write-Host ("{0}. {1}" -f ($i + 1), $subpaths[$i])
   }

   # Prompt the user for their choice
   $selectedVariant = Read-Host "Enter the number of the variant you want to select"

   # Validate user input
   if ($selectedVariant -match '^\d+$' -and $selectedVariant -ge 1 -and $selectedVariant -le $subpaths.Count) {
      $selectedVariantPath = $subpaths[$selectedVariant - 1]
      Write-Host "You selected: $selectedVariantPath"

      # Split the selected subpath into parts
      $parts = $selectedVariantPath -split "\\"

      # Store the first part in $flavor and the second part in $subsystem
      $flavor = $parts[0]
      $subsystem = $parts[1]

      cmake -B build\$selectedVariantPath -G "Ninja" -DFLAVOR="$flavor" -DSUBSYSTEM="$subsystem"
      cmake --build build\$selectedVariantPath
   } else {
      Write-Host "Invalid selection. Exiting."
      exit 1  # Exit with code 1 for invalid choice
   }


Create SPL-Core Project with Multiple Variants
==============================================

The main reason to use SPL-Core is to build a project with multiple variants. Let us now create a project with two variants: ``lang/en`` and ``lang/de``.

We define a new variant ``lang/de`` by creating a new directory ``variants/lang/de`` and adding a ``parts.cmake`` file:

.. code-block:: cmake

   spl_add_component(src/main)

We need now to make the ``main`` component configurable and define a different configuration for the two variants.

Make the ``main`` Component Configurable
----------------------------------------

To make the ``main`` component configurable, we need to add a ``KConfig`` file to the ``main`` component directory:

.. code-block:: KConfig

   menu "Main"
      choice
         prompt "Select Language"

      config MY_COMPONENT_LANG_EN
         bool "English (EN)"
         help
         Select this option for English language (EN) support.

      config MY_COMPONENT_LANG_DE
         bool "German (DE)"
         help
         Select this option for German language (DE) support.

      endchoice
   endmenu

We now need to define a project ``KConfig`` file in the root directory to include the component ``KConfig`` file:

.. code-block:: KConfig

   source "src/main/KConfig"

SPL-Core will automatically read the project ``KConfig`` file and generate a header file from it.

The ``kconfiglib`` Python package is used to parse the ``KConfig`` files.
For this we need to install Python and then install the ``kconfiglib`` package using ``pip``:

.. code-block:: bash

   scool install python
   pip install kconfiglib

Now one can open the graphical user interface of ``kconfiglib`` by running:

.. code-block:: bash

   guiconfig

Select the "German (DE)" language and save the file as ``config.txt`` in the ``variants/lang/de`` directory.

Run the ``build.ps1`` script to build the ``lang/de`` variant. A header file named ``autoconf.h`` will be generated in the ``build/lang/de/kconfig`` directory:

.. code-block:: C

   /** @file */
   #ifndef __autoconf_h__
   #define __autoconf_h__

   /** MY_COMPONENT_LANG_DE */
   #define CONFIG_MY_COMPONENT_LANG_DE 1

   #endif /* __autoconf_h__ */

Building the ``lang/en`` variant will generate a different ``autoconf.h`` file:

.. code-block:: C

   /** @file */
   #ifndef __autoconf_h__
   #define __autoconf_h__

   /** MY_COMPONENT_LANG_EN */
   #define CONFIG_MY_COMPONENT_LANG_EN 1

   #endif /* __autoconf_h__ */


We can make now the ``main.c`` file configurable by including the ``autoconf.h`` file and using the ``CONFIG_MY_COMPONENT_LANG_DE`` and ``CONFIG_MY_COMPONENT_LANG_EN`` macros:

.. code-block:: C

   #include <stdio.h>
   #include "autoconf.h"

   int main() {
   #if defined(CONFIG_MY_COMPONENT_LANG_DE) && CONFIG_MY_COMPONENT_LANG_DE == 1
       printf("Hallo Welt!\n");
   #else
       printf("Hello, World!\n");
   #endif
       return 0;
   }


.. note::

   The directory ``build/<variant>/kconfig`` is added to the include path by SPL-Core such that one can just include ``autoconf.h`` without specifying the full path.
