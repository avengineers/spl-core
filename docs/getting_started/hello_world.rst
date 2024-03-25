Tutorial: "Hello World"
=======================

This tutorial shall give you a quick start with SPL Core.

.. attention::
   This tutorial was written to be used on a Windows machine and all given command line calls shall be executed in a PowerShell terminal. Nevertheless SPL Core is usable on other OS instances as well.

At the end of this tutorial you should be able to use SPL Core as your tool chain to build different variants of a product.

For this we will follow three steps:


Step 1: Build with CMake
------------------------

First let us build a simple "Hello World" program using `CMake <https://cmake.org>`_ and `Clang <https://clang.llvm.org/>`_ (compiler).

Create Main Program
^^^^^^^^^^^^^^^^^^^

Create a new directory to use as your project's root directory, e.g., ``C:/Projects/HelloWorld``. Therefore open a PowerShell terminal and execute:

.. code-block:: powershell

   mkdir C:/Projects/HelloWorld
   cd C:/Projects/HelloWorld

.. attention::
   All further command lines of this tutorial shall be executed in this PowerShell terminal in the root directory of our "Hello World!" example.

Inside the root directory create a source directory called ``src``.

.. code-block:: powershell

   mkdir src

Inside the source directory create a new file called ``main.c``.
Add the following code to the ``main.c`` file:

.. code-block:: c
   :linenos:

   #include <stdio.h>

   int main() {
       printf("Hello World!\n");
       return 0;
   }


Create CMakeLists File
^^^^^^^^^^^^^^^^^^^^^^

Inside the root directory create a file named ``CMakeLists.txt``.

.. note::
   If you like to know more about CMakeLists files please refer to the official `documentation <https://cmake.org/cmake/help/book/mastering-cmake/chapter/Writing%20CMakeLists%20Files.html>`_.

Add to the ``CMakeLists.txt`` the following contents:

.. code-block:: cmake
   :linenos:

   cmake_minimum_required(VERSION 3.24.0)
   cmake_policy(VERSION 3.24)

   set(CMAKE_C_COMPILER clang)
   project(HelloWorld C)

   add_executable(helloworld src/main.c)


Install the Necessary Build Tools
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For this tutorial, we will use the Scoop package manager to install the necessary software on Windows.
You can verify that Scoop is installed in your PC by typing ``scoop`` in the terminal.
In case you do not have Scoop installed, you can get it from its `official site <https://scoop.sh>`_.

.. note::

   If you face any installation problems, please check your proxy settings.

.. attention::
   All further command lines of this tutorial shall be executed in a PowerShell terminal and in the root directory of our "Hello World!" example.

Next, install the ``mingw-winlibs-llvm-ucrt`` package, which contains Clang, CMake and `Ninja <https://ninja-build.org/>`_ (build system) by executing the following command:

.. code-block:: powershell

   scoop install mingw-winlibs-llvm-ucrt


Configure the project
^^^^^^^^^^^^^^^^^^^^^

Using CMake, you can generate build files for various build systems. For this tutorial, we will use Ninja.

Run the CMake configuration command:

.. code-block:: powershell

   cmake -B build -G "Ninja"

We used the ``-B`` option to specify the build directory, and the ``-G`` option to specify generator of the build system.
(If you are interested, you can use ``cmake --help`` to see a list of available command line options.)


Build the Project
^^^^^^^^^^^^^^^^^

With the build files generated, you can now build the project using CMake:

.. code-block:: powershell

   cmake --build "build"

After building, you can run the executable named ``helloworld.exe``:

.. code-block:: powershell

   .\build\helloworld.exe

You shall see "Hello World!" as command line output.


Step 2: Build with SPL Core
---------------------------

Now we will convert our example project to an SPL and build it with SPL Core.

Create the ``main`` Component
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Let us create a directory for the main component:

.. code-block:: powershell

   mkdir src/main

Create a component's CMakeLists file ``src/main/CMakeLists.txt`` to create the ``main`` component.

Write the following lines in the ``src/main/CMakeLists.txt`` file:

.. code-block:: cmake
   :linenos:

   spl_add_source(src/main.c)
   spl_create_component()

.. note::

   Check the SPL :ref:`cmake-macro-reference-label` to understand why it is necessary to add spl_add_source(src/main.c) and spl_create_component().

Create a component's source directory:

.. code-block:: powershell

   mkdir src/main/src

Move the existing ``main.c`` to the component's source directory:

.. code-block:: powershell

   mv src/main.c src/main/src/main.c

Create an SPL Variant
^^^^^^^^^^^^^^^^^^^^^

For this we have to create a variant ``lang/en`` as sub directory of the ``variants`` directory:

.. code-block:: powershell

   mkdir variants/lang/en

Create a new file called ``variants/lang/en/parts.cmake`` to define the variant relevant components.

Write the following line in the ``variants/lang/en/parts.cmake`` file to add the component ``src/main``:

.. code-block:: cmake
   :linenos:

   spl_add_component(src/main)

Build the variant
^^^^^^^^^^^^^^^^^

To configure and build the variant ``lang/en``, we need to fetch SPL Core and all external dependencies into the modules directory.

For this purpose, we replace the content of the ``CMakeLists.txt`` file located in the root directory with the following:

.. code-block:: cmake
   :linenos:

   cmake_minimum_required(VERSION 3.24.0)
   cmake_policy(VERSION 3.24)

   set(CMAKE_C_COMPILER clang)
   project(${VARIANT} C)

   # configure the current variant to be build
   set(BUILD_KIT prod CACHE STRING "Target Group to build.")
   set(LINKER_OUTPUT_FILE helloworld.exe)

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

To generate the build files for our variant execute:

.. code-block:: powershell

   cmake -B "build/lang/en/prod" -G "Ninja" -DVARIANT="lang/en"

.. attention::

   The ``VARIANT`` is usually provided by the user with the ``-DVARIANT=`` argument when calling ``CMake``.

To build the variant execute:

.. code-block:: powershell

   cmake --build "build/lang/en/prod"

After building, you can run the executable named ``helloworld.exe``:

.. code-block:: powershell

   .\build\lang\en\prod\helloworld.exe

You shall see "Hello World!" as command line output.


Step 3: Configure and Build Several Variants
--------------------------------------------

As mentioned in the beginning of this tutorial, the main reason to use SPL Core is to build multiple variants of a product.

We define a new variant ``lang/de`` by creating a new directory ``variants/lang/de`` and creating a ``parts.cmake`` file in this new directory.

.. code-block:: powershell

   mkdir variants/lang/de

Write the following line in the ``variants/lang/de/parts.cmake`` file:

.. code-block:: cmake
   :linenos:

   spl_add_component(src/main)


Make the ``main`` Component Configurable
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We now need to make the ``main`` component configurable and define configurations for the two variants ``variants/lang/en`` and ``variants/lang/de``.

To make the ``main`` component configurable, we need to create a `KConfig <https://www.kernel.org/doc/html/latest/kbuild/kconfig-language.html#kconfig-syntax>`_ model file in the ``src/main/`` directory:

.. code-block:: KConfig
   :linenos:

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

To make our example project configurable, we need to create a ``KConfig`` model file in the root directory and add the following code:

.. code-block:: KConfig
   :linenos:

   source "src/main/KConfig"

SPL Core will automatically read the project ``KConfig`` model and generate a header file ``autoconf.h`` from it to be usable inside the C sources.

The ``kconfiglib`` Python package is used to parse the ``KConfig`` configuration files.

If you do not have Python already installed, please execute the following command:

.. code-block:: powershell

   scoop install python

Install the ``kconfiglib`` package:

.. code-block:: powershell

   pip install kconfiglib

Now one can open the graphical user interface of ``kconfiglib`` by executing:

.. code-block:: powershell

   guiconfig

Select the language "German (DE)", hit the button ``Save as...`` and save the file as ``config.txt`` in the ``variants/lang/de`` directory.

Select the language "English (EN)", hit the button ``Save as...`` and save the file as ``config.txt`` in the ``variants/lang/en`` directory.

After that close the guiconfig window.

By including the ``autoconf.h`` we can use the variants' configurations.

Add the following code to the ``src/main/src/main.c`` file:

.. code-block:: C
   :linenos:

   #include <stdio.h>
   #include "autoconf.h"

   int main() {
   #if defined(CONFIG_MY_COMPONENT_LANG_DE) && CONFIG_MY_COMPONENT_LANG_DE == 1
       printf("Hallo Welt!\n");
   #else
       printf("Hello World!\n");
   #endif
       return 0;
   }


To generate the build files including ``autoconf.h`` for variant ``lang/de`` execute:

.. code-block:: powershell

   cmake -B "build/lang/de/prod" -G "Ninja" -DVARIANT="lang/de"

To build the variant ``lang/de`` execute:

.. code-block:: powershell

   cmake --build "build/lang/de/prod"

Now execute ``helloworld.exe`` of variant ``lang/de``:

.. code-block:: powershell

   .\build\lang\de\prod\helloworld.exe

The message shall be printed in German:

.. code-block:: console

   Hallo Welt!

To generate the build files including ``autoconf.h`` for variant ``lang/en`` execute:

.. code-block:: powershell

   cmake -B "build/lang/en/prod" -G "Ninja" -DVARIANT="lang/en"

To build the ``lang/en`` variant execute:

.. code-block:: powershell

   cmake --build "build/lang/en/prod"

Now execute ``helloworld.exe`` of variant ``lang/en``:

.. code-block:: powershell

   .\build\lang\en\prod\helloworld.exe

The message shall be printed in English:

.. code-block:: console

   Hello World!

We finally created a "Hello World" example showing the principles of an SPL with variants and configurable components.
