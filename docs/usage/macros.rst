CMake Macros
************

spl_add_component
^^^^^^^^^^^^^^^^^

Add a component to a variant.

.. code-block:: cmake

  spl_add_component(<relative path from project root to the component's directory>)

This macro is intended to be used in the variant's parts.cmake file to add a component to the variant.

Example:

.. code-block:: cmake

  spl_add_component(src/led_driver)



spl_add_source
^^^^^^^^^^^^^^

Add a source file of a component to the list of sources to be compiled.

.. code-block:: cmake

  spl_add_source(<relative path to component source> [COMPILE_OPTIONS "<option 1>" "<option 2> ..."])

This macro is intended to be used in a component's CMakeLists.txt (or included .cmake file) to add a source file to the list of files to be compiled for the current component.

The options are:

``COMPILE_OPTIONS``
  Define additional compiler options to be added to the default compiler options defined by the toolchain file.

Example:

.. code-block:: cmake

  spl_add_source(src/led_driver_main.c)
  spl_add_source(src/led_driver_control.c COMPILE_OPTIONS "-w")



spl_add_compile_options
^^^^^^^^^^^^^^^^^^^^^^^

Add compile options to a set of source files matching a specified pattern.

.. code-block:: cmake

  spl_add_compile_options(<pattern> COMPILE_OPTIONS "<option 1>" "<option 2> ...")

This macro is intended to be used in a CMakeLists.txt file to add compile options to a set of source files that match a specified pattern within the current directory and its subdirectories.

The argurments are:

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