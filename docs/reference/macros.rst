.. _cmake-macro-reference-label:

CMake Macros
============


spl_add_component
-----------------

Add a component to a variant.

.. code-block:: cmake

 spl_add_component(<component_path>)

This macro is intended to be used in the variant's parts.cmake file to add a component to the variant.

The arguments are:

``<component_path>``
 The relative path from project root to the component's directory.

Example:

Adding a component to the variant in its parts.cmake:

.. code-block:: cmake

 spl_add_component(src/led_driver)

This example adds a component located in the "src/led_driver" directory to the variant.


spl_add_named_component
-----------------------

Add a named component to a variant.

.. code-block:: cmake

 spl_add_named_component(<component_name>)

This macro is intended to be used in the variant's parts.cmake file to add a named component to the variant.

The arguments are:

``<component_name>``
 The name of a CMake variable that contains the path (either absolute or relative from project root) to the component's directory.
 The variable name becomes the name of the component in the build system.

Examples:

Adding a named component to the variant in its parts.cmake:

.. code-block:: cmake

 set(LED_DRIVER_COMPONENT src/led_driver)
 spl_add_named_component(LED_DRIVER_COMPONENT)

This example adds a named component to the variant using the variable ``LED_DRIVER_COMPONENT`` that contains the path to the component's directory.

.. code-block:: cmake

 set(LED_DRIVER_COMPONENT ${CMAKE_CURRENT_SOURCE_DIR}/some_package/src/led_driver)
 spl_add_named_component(LED_DRIVER_COMPONENT)

This example adds a named component to the variant using the variable ``LED_DRIVER_COMPONENT`` that contains the absolute path to the component's directory.


spl_add_include
---------------

Add an include directory to the project's list of include directories.

.. code-block:: cmake

 spl_add_include(<include_directory>)

This macro is intended to be used in the variant's parts.cmake file to add an include directory to the build's list of include directories,
making header files in this directory accessible to the compiler.

The arguments are:

``<include_directory>``
 The relative path to the include directory you want to add to the build's list of include directories.

Example:

Adding an include directory to the project:

.. code-block:: cmake

 spl_add_include(include/my_library)

This example adds the "include/my_library" directory to the project's list of include directories, making header files within this directory accessible to the project's source code.

.. _spl_add_source:

spl_add_source
--------------

Add a source file of a component to the list of sources to be compiled.

.. code-block:: cmake

 spl_add_source(<file_name> [COMPILE_OPTIONS "<option 1>" "<option 2>" ...])

This macro is intended to be used in a component's CMakeLists.txt (or included .cmake file) to add a source file to the list of files to be compiled for the current component.

The arguments are:

``<file_name>``
 The relative path to the component's source file.

``COMPILE_OPTIONS``
 Additional compiler options specific to this source file to be added to the default compiler options defined by the toolchain file.

Example:

Adding a source file to the component:

.. code-block:: cmake

 spl_add_source(src/led_driver_main.c)

This example adds the "led_driver_main.c" source file located in the "src" directory to the component.

Applying compile options:

.. code-block:: cmake

 spl_add_source(src/led_driver_control.c COMPILE_OPTIONS "-w")

This example adds the "led_driver_control.c" source file and applies the compile options "-w" to it.


spl_add_compile_options
-----------------------

Add compile options to a set of source files matching a specified pattern.

.. code-block:: cmake

  spl_add_compile_options(<pattern> COMPILE_OPTIONS "<option 1>" "<option 2> ...")

This macro is intended to be used in a CMakeLists.txt file to add compile options to a set of source files that match a specified pattern within the current directory and its subdirectories.

The arguments are:

``<pattern>``
  A relative path to the files you want to apply compile options to. This pattern can include wildcards such as ``*`` and ``?`` to match multiple files.

``COMPILE_OPTIONS``
  Define additional compiler options to be added to the default compiler options defined by the toolchain file.

Example:

Adding compile options to all source files matching a pattern:

.. code-block:: cmake

  spl_add_compile_options(src/*.c COMPILE_OPTIONS "-w")

This example applies the compile options ``-w`` to all the C source files in the "src" directory and its subdirectories.

Adding compile options to specific files:

.. code-block:: cmake

  spl_add_compile_options(src/led_driver_main.c COMPILE_OPTIONS "-opt")

This example applies the compile option ``-opt`` specifically to the "led_driver_main.c" file in the "src" directory.

.. _spl_add_test_source:

spl_add_test_source
-------------------

Add a test source file to the list of test source files for the component.

.. code-block:: cmake

 spl_add_test_source(<file_name>)

This macro is intended to be used in a component's CMakeLists.txt (or included .cmake file)
to add a test source file to the list of test source files for the component.

The arguments are:

``<file_name>``
 The relative path to the component's test source file.

Example:

Adding a test source file to the component:

.. code-block:: cmake

 spl_add_test_source(test/test_led_driver.cc)

This example adds the "test_led_driver.cc" source file located in the "test" directory to the component.

.. _spl_create_component:

spl_create_component
--------------------

This macro is intended to be used in a component's CMakeLists.txt (or included .cmake file)
to create a component as a library in the build system.
It must be called after adding all source and test source files to the component.

.. code-block:: cmake

  spl_create_component([LONG_NAME <name>] [LIBRARY_TYPE <type>])


The arguments are:

``LONG_NAME``
 (Optional) A human-readable name for the component. This name is used in the documentation,
 providing a clearer identifier than the default component path.

``LIBRARY_TYPE``
 (Optional) Specifies the type of library to be created.
 Acceptable values are "OBJECT" or "STATIC". If not specified,
 the default value is "OBJECT". This allows the user to choose
 between creating an object library (which is not archived) or
 a static library.

Example:

Creating a component using the `spl_create_component` macro:

.. code-block:: cmake

  spl_add_source(src/led_driver_main.c)
  spl_add_test_source(test/test_led_driver.cc)
  spl_create_component(LONG_NAME "LED Driver" LIBRARY_TYPE STATIC)

Please note that this macro performs various tasks related to the component's setup, including documentation and testing, depending on the build configuration (buildKit).
