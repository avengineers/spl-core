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

Add a compile option to the list of sources to be compiled.

.. code-block:: cmake

  spl_add_compile_options(<relative path to list of source pattern> [COMPILE_OPTIONS "<option 1>" "<option 2> ..."])

This macro is intended to be used in a component's CMakeLists.txt (or included .cmake file) to add all file patterns to the list of files to be compiled for the current component.

The options are:

``COMPILE_OPTIONS``
  Define additional compiler options to be added to the default compiler options defined by the toolchain file.

Example:

.. code-block:: cmake

  spl_add_source(src/led_driver_main.c)
  spl_add_compile_options(src/*.c COMPILE_OPTIONS "-w")