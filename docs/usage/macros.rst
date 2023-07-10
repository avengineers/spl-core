CMake Macros
************

spl_add_source
^^^^^^^^^^^^^^

Add a source file of a component to the list of sources to be compiled.

.. code-block:: cmake

  spl_add_source(<relative path to component source> [COMPILE_OPTIONS "<option 1>" "<option 2> ..."]

This macro is intended to be used in a component's CMakeLists.txt (or included .cmake file) to add a source file to the list of files to be compiled for the current component.

The options are:

``COMPILE_OPTIONS``
  Define additional compiler options to be added to the default compiler options defined by the toolchain file.