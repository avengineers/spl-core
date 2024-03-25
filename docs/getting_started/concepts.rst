Basic Concepts and Naming Conventions
=====================================

What is a Software Product Line (SPL)?
--------------------------------------

An SPL is a software project that contains shared and configurable source code elements known as :ref:`components <what_is_a_component>`, which are used to develop several versions of a computer program, also known as :ref:`variants <what_is_a_variant>`.

Think of an SPL like an automotive factory that makes different types of cars.
Each car is special - some are race cars, some are trucks, and others might be convertibles.
But they all start from some common :ref:`components <what_is_a_component>` like wheels and engines with different configurations like size and horsepowers.
Thinking this way, making a new program is like building a new car but faster and easier because we already have the :ref:`components <what_is_a_component>` we need.

What is SPL Core?
-----------------

SPL Core is a tool chain that uses modern `CMake <https://cmake.org/>`_.
SPL Core supports the concepts and requirements of an SPL to build various software :ref:`variants <what_is_a_variant>` from a common codebase.

.. _what_is_a_variant:

What is a Variant?
------------------

A variant is a specific version of the software, consisting of a set of :ref:`features <what_is_a_feature_model>` that meet specific customer requirements.

Think of a variant like choosing different :ref:`features <what_is_a_feature_model>` for your car.
One car might be red with racing stripes and another might be a blue truck.
In computer programs, a variant is a version of the program that has something different or special about it, but it's still based on the same basic design.
It's like customizing your car or program to make it just the way you want it.

.. attention::
    In SPL Core a variant is identified by its name, which is the subpath of the variant's directory relative to the SPL's ``variants`` directory.

Here is an example of the variants directory with two variants (``my/var1`` and ``my/var2``) and some variant specific files:

.. code-block::

    <project root>
    └── variants
        └── my
            ├── var1
            │   ├── config.cmake
            │   ├── parts.cmake
            │   ├── config.txt
            │   └── ...
            └── var2
                ├── config.cmake
                ├── parts.cmake
                ├── config.txt
                └── ...


* ``config.cmake`` - variant specific CMake configuration, like the target architecture and toolchain.
* ``parts.cmake`` - contains the list of :ref:`components <what_is_a_component>` that are part of the variant.
* ``config.txt`` - this is the :ref:`feature <what_is_a_feature_model>` selection of the variant. It is a KConfig file that contains the selected :ref:`features <what_is_a_feature_model>` of the variant.

.. _what_is_a_component:

What is a Component?
--------------------

A component is a distinct, reusable SW part with defined functionality and interfaces.

Think of a component like a building block you use to build something.
In our car, components could be the wheels, seats, or steering wheel - each part has its own job, and when we put them all together, we get a car.
In computer programs, components are pieces of the program that do certain jobs.
We can configure and combine these components to build different programs.

.. attention::
    In SPL Core a component is identified by its name, which is the subpath of the component's directory relative to the SPL's root directory.

Here is an example of the source directory with two components (``src/comp1`` and ``src/comp2``):

.. code-block::

    <project root>
    └── src
    │   ├── comp1
    │   │   ├── doc
    │   │   │   └── index.rst
    │   │   ├── src
    │   │   │   ├── comp1.c
    │   │   │   └── comp1.h
    │   │   ├── test
    │   │   │   └── test_comp1.cc
    │   │   └── CMakeLists.txt
    │   ├── comp2
    │   │   ├── doc
    │   │   │   └── index.rst
    │   │   ├── src
    │   │   │   ├── comp2.c
    │   │   │   └── comp2.h
    │   │   ├── test
    │   │   │   └── test_comp2.cc
    │   │   └── CMakeLists.txt
    │   └── ...
    └── variants

* **Component Documentation**:
    * The ``doc`` directory contains the documentation of the component.
    * If a component has a ``doc/index.rst`` file, SPL Core will automatically generate a ``<component>_docs`` CMake target that can be used to build the documentation.
* **Component Implementation**:
    * The ``src`` directory contains the source code of the component.
    * The component's ``CMakeLists.txt`` defines the component relevant files using :ref:`spl_add_source <spl_add_source>`.
* **Component Testing**:
    * The ``test`` directory contains the `GTest <https://github.com/google/googletest>`_ tests of the component.
    * The component's ``CMakeLists.txt`` defines the component relevant test files using :ref:`spl_add_test_source <spl_add_test_source>`.
* **Component Definition**
    * The component's ``CMakeLists.txt`` makes the component available using :ref:`spl_create_component <spl_create_component>`.

.. _what_is_a_feature_model:

What is a Feature Model?
------------------------

A feature model represents the organization of all potential features in an SPL, showing how they relate and depend on each other.
This model guides the creation of different SPL :ref:`variants <what_is_a_variant>`, ensuring that feature combinations are viable and consistent.

Think of a feature model like a big chart showing all the different features you can choose from to customize your car.
It tells you which pieces fit together and how you can combine them to make different types of cars.
In computer programs, a feature model helps us understand all the features (like colors, sizes, or special abilities) we can choose when we're making a new version of the program.

.. attention::
    In SPL Core the feature model is implemented by using `KConfig <https://www.kernel.org/doc/html/latest/kbuild/kconfig-language.html>`_.

If a ``KConfig`` file is present in the root directory, SPL Core will automatically parse it and generate the project configuration.

The :ref:`variant <what_is_a_variant>` specific configuration file is expected in the :ref:`variant <what_is_a_variant>` directory.
If a ``config.txt`` file is present in the :ref:`variant <what_is_a_variant>` directory, SPL Core will automatically use it to override the default configuration values defined in the ``KConfig`` file.
