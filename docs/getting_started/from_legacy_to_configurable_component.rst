From Legacy to Configurable Component
#####################################

When developing product variants in isolation in separate projects and make a switch to a software product line approach, it is common to have a lot of duplicated code.
We wrote a paper about this problem and how to solve it: `SPLC2022 <https://github.com/avengineers/SPLC2022/blob/develop/In%20Three%20Steps%20to%20Software%20Product%20Lines.pdf>`_.

We will focus in this example on concrete steps for migrating from multiple legacy code components to one configurable component.

Let's assume the legacy code for the variants is structured as follows:

.. code-block::

    legacy
    ├── variant1
    │   ├── component1
    │   │   ├── component1.c
    │   │   └── component1.h
    │   └── component2
    │       ├── component2.c
    │       └── component2.h
    └── variant2
        ├── component1
        │   ├── component1.c
        │   └── component1.h
        └── component2
            ├── component2.c
            └── component2.h


Create a New Component
**********************

The first step is to create a generic "legacy" component which is just a "redirect" for the variant specific legacy component.
The idea is to configure the same component for all variants.

We need to create a new component in the ``src`` folder:

.. code-block::

    src
    └── component1
        ├── src
        │   ├── component1_legacy.c
        │   └── component1_legacy.h
        ├── test
        │   └── test_component.cc
        └── CMakeLists.txt


.. code-block:: C
    :name: component_legacy.c
    :caption: component_legacy.c

    #include "component1/component1.c"

.. code-block:: C
    :name: component_legacy.h
    :caption: component_legacy.h

    #include "component1/component1.h"


.. important::

    By including the legacy code source file, we make sure the variant specific legacy code is compiled when the ``component1_legacy`` component is compiled.
    To make sure the correct legacy code is included, you need to add the legacy code folder to the include path. This can be done globally in the main ``CMakeLists.txt``:

    .. code-block:: CMake
        :caption: CMakeLists.txt

        spl_add_include(legacy/${VARIANT})


Next step is to create a test that just calls the component main method.
With this we make sure that for all variants:

* the legacy component can be compiled for testing (e.g. no target compiler specific code or assembly code)
* all external dependencies can be automatically mocked


.. code-block:: C++
    :name: test_component.cc
    :caption: test_component.cc

    /**
    * @file
    */
    #include <gtest/gtest.h>
    using namespace testing;

    extern "C" {
    #include "autoconf.h"
    #include "component_legacy.h"
    }

    // Auto-generated mockups for this component
    #include "mockup_src_component.h"


    TEST(MyComp, testMain)
    {
        CREATE_MOCK(mymock);
        // Call the component main function
        MyCompMain();
    }


Next we need to replace the legacy code with the new component.

Identify the legacy code files in the variants *legacy* ``parts.cmake`` and remove them:

.. code-block:: diff
    :caption: legacy/parts.cmake

    spl_add_source(main.c)
    - spl_add_source(component1/component1.c)
    spl_add_source(component2/component2.c)

Add the new component to the variants ``parts.cmake``:

.. code-block:: CMake
    :caption: variants/<variant>/parts.cmake

    spl_add_component(src/component1)


At this point, you should have a test running in all variants and no difference in the variants productive code.


Test Features
*************

The next step is to test the features of the legacy component in all variants.

Depending on how complex your component is and how many variants you have, this process might be very time consuming.
To be able to merge the changes back to the main branch as soon as possible, we recommend to use a configuration switch to enable/disable the feature tests for your component.

.. code-block:: KConfig
    :caption: component1/Kconfig

    config COMPONENT1_FEATURE_TEST
        bool "Enable feature tests for component1"
        default n


.. code-block:: C++
    :caption: test_component.cc

    # if CONFIG_COMPONENT1_FEATURE_TEST
    /*!
    * @rst
    *
    * .. test:: MyComp.testMyFeature
    *    :id: TS_COMP1-001
    *    :tests: SWDD_COMP1-001, SWDD_COMP1-002
    *
    * @endrst
    */
    TEST(MyComp, testMyFeature)
    {
        CREATE_MOCK(mymock);
        ...
    }
    # endif


Now you can enable the feature tests for every variant separately.
As soon as one variant is tested, you can merge the changes back to the main branch.

.. important::

    While creating the feature tests, you will already find the differences between the variants.
    This is the perfect time to start defining the configuration switches (variabily points) in
    KConfig and use them to make the tests work in all variants.


Refactoring
***********

The main goal is to refactor the legacy code to a configurable component that can be used in all variants.

To be able to enable the new component variant by variant, we need to add a configuration switch to the component KConfig file:

.. code-block:: KConfig
    :caption: component1/Kconfig

    config COMPONENT1_CONFIGURABLE_COMPONENT
        bool "Enable new component1 configurable component"
        default n

We can now use this configuration switch to enable/disable the new component files in the component ``CMakeLists.txt``:

.. code-block:: CMake
    :caption: component1/CMakeLists.txt

    if(CONFIG_COMPONENT1_CONFIGURABLE_COMPONENT)
        spl_add_source(src/component1_new.c)
    else()
        spl_add_source(src/component1_legacy.c)
    endif()


Cleanup
*******

After all variants are migrated to the new component we shall:

* cleanup the component KConfigfile: remove the configuration switches for testing the features and enabling the "new"  component.
* remove the legacy code from the repository. No ``*_legacy.*`` files should be left.
* rename the component files to just ``component1.c`` and ``component1.h``.
