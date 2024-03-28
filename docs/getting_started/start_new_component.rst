How to Start Working on a :ref:`Component <glossary_component>`
###############################################################

To support :ref:`component <glossary_component>` development, SPL Core provides features to:

- document the component behavior
- test the component behavior
- generate component report with full traceability between documentation, code and tests
- configure **all** component artifacts (content will be included/excluded based on configuration)

`Sphinx <https://www.sphinx-doc.org/>`_ is used to generate the component report.
See the project `conf.py` file for the configuration details.

.. _how_to_component_detail_design:

Detailed Design
***************

The component behavior is described in restructured text in the ``doc`` directory.

Here are the main features supporting component documentation:

* describe the component behavior in text
* create diagrams using `mermaid <https://mermaid-js.github.io/mermaid/>`_
* include/exclude content based on configuration
* use `sphinx-needs <https://www.sphinx-needs.com/>`_ to create traceability between documentation, code and tests


**Traceability**

In order to trace the documentation to the code or tests, you need to add a `sphinx-needs <https://www.sphinx-needs.com/>`_ element.

.. code-block:: rst

    .. spec:: Feature X
        :id: SWDD_COMP-001

        The component shall implement feature X.

The ``spec`` keyword is used to tag the component specification. It shall have:

* a title to very briefly describe the specification. This will be shown in traceability tables.
* an id to uniquely identify the specification. The id naming convention is ``SWDD_<COMPONENT_NAME>-<NUMBER>``.
* free text to describe the specification in more details.

**Configurability**

All the configuration features from the project KConfig file are available in the documentation to be able to tailor it.

.. code-block:: rst

    {% if config.FEATURE_Y %}
    .. spec:: Feature Y
        :id: SWDD_COMP-002

        The component shall implement feature Y.
    {% endif %}

The ``if`` statement will include the specification only if the ``FEATURE_Y`` configuration is set to ``y``.

**Diagrams**

Diagrams can be created using `mermaid <https://mermaid-js.github.io/mermaid/>`_.

*Input:*

.. code-block:: rst

    .. mermaid::

        stateDiagram-v2
            [*] --> STATE_OFF: Initial State
            STATE_OFF --> STATE_ON : Power State != OFF
            STATE_ON --> STATE_OFF : Power State == OFF

*Result:*

.. mermaid::

    stateDiagram-v2
        [*] --> STATE_OFF: Initial State
        STATE_OFF --> STATE_ON : Power State != OFF
        STATE_ON --> STATE_OFF : Power State == OFF

See the `mermaid <https://mermaid-js.github.io/mermaid/>`_ documentation for more details.


.. _doc_template:

**Template**

Here is a ``index.rst`` template for getting you started documenting a component:

.. code-block:: rst
    :linenos:

    Software Detailed Design
    ########################

    Introduction
    ************

    This component is responsible for ...

    Component Description
    *********************

    .. spec:: Feature X
        :id: SWDD_COMP-001

        The component shall implement feature X.

    Internal Behavior
    *****************

    .. spec::  State Machine
        :id: SWDD_COMP-003

        The component main method is implemented as a state machine. The state machine is shown below.

    .. mermaid::

        stateDiagram-v2
            [*] --> STATE_OFF: Initial State
            STATE_OFF --> STATE_ON : Power State != OFF
            STATE_ON --> STATE_OFF : Power State == OFF
    {% if config.FEATURE_Y %}
            STATE_ON --> STATE_Y : Y Started
            STATE_Y --> STATE_ON : Y Stopped
            STATE_Y --> STATE_OFF : Power State == OFF
    {% endif %}

.. _how_to_component_test_cases:

Test Cases
**********

The component tests are written in GTest and are located in the ``test`` directory.

Here are the main features supporting component tests:

* Test cases are written with `GoogleTest <https://google.github.io/googletest/>`_.
* Component external interfaces are automatically mocked using Google Mock.
* Include/exclude content based on configuration.
* Use `sphinx-needs <https://www.sphinx-needs.com/>`_ to create traceability between documentation, code and tests.

**Traceability**

In order to trace the test case to the design, you need to add a `sphinx-needs <https://www.sphinx-needs.com/>`_ element.

.. code-block:: C++

    /*!
    * @rst
    *
    * .. test:: MyComp.testCorrectBehavior
    *    :id: TS_COMP-001
    *    :tests: SWDD_COMP-001
    *
    * @endrst
    */
    TEST(MyComp, testCorrectBehavior)
    {
        CREATE_MOCK(mymock);
        // test code
    }

The `test` is used to tag the component test case. It shall have:

* a title required to link the test case to the test result. ❗The title must match exactly the test case name.
* an ``id`` to uniquely identify the test case. The id naming convention is ``TS_<COMPONENT_NAME>-<NUMBER>``.
* a ``tests`` tag to link the test case to the specification. One can link multiple specifications by separating them with a comma.
* free text to describe the test case in more details.


For tracing parametrized tests to test results one can use a pattern in the ``test`` title:

.. code-block:: C++

    /*!
    * @rst
    *
    * .. test:: MyCompTestSuite/MyComp.testCorrectBehavior/*
    *    :id: TS_COMP-001
    *    :tests: SWDD_COMP-001
    *
    * @endrst
    */
    TEST_P(MyComp, testCorrectBehavior)
    {
        CREATE_MOCK(mymock);
        // test code
    }

    INSTANTIATE_TEST_SUITE_P(
        MyCompTestSuite,
        MyComp,
        ::testing::Values(
            TestParam{ "Descr0", 0},
            TestParam{ "Descr1", 0},
        )
    );

This will link both test results for the parametrized test to the same test case.


**Auto mockup generation**

SPL Core is using `Hammocking <https://github.com/avengineers/hammocking>`_ to automatically create mockups for the component external interfaces.
In order to access the generated mockups, you need to include the ``mockup_<component name>.h`` in your test file.


.. code-block:: C++

    #include "mockup_src_comp.h"

.. note::

    In SPL Core the component name is the relative path to the project directory
    - see :ref:`What is a component <glossary_component>` for more details.

One must create the mockup object in every test case before being able to use it:

.. code-block:: C++

    TEST(MyComp, testCorrectBehavior)
    {
        CREATE_MOCK(mymock);
        // Make the input interface return 5
        EXPECT_CALL(mymock, ReadExternalVar()).WillOnce(Return(5));
        // Expect the output interface to be called with 10
        EXPECT_CALL(mymock, WriteOutputVar(10)).Times(1);
        MyCompMain();
    }

For more details on how to set expectations with Google Mock, see the `GMock for dummies  <https://google.github.io/googletest/gmock_for_dummies.html#setting-expectations>`_.

**Configurability**

One must include the ``autoconf.h`` file in the test file to be able to use the configuration features.

.. code-block:: C++

    #include "autoconf.h"


**Access symbols from C files**

In order to access symbols from the component C files, you have to include the headers and external symbol declarations accordingly:

.. code-block:: C++

    extern "C" {
        #include "my_comp.h"
        #include "autoconf.h"
        extern unsigned int someFunction(int a);
    }

**Template**

Here is a ``test_comp.cc`` template for getting you started testing a component:

.. code-block:: C++

    /**
    * @file
    */
    #include <gtest/gtest.h>
    using namespace testing;

    extern "C" {
    #include "comp.h"
    #include "autoconf.h"
    }

    // Auto-generated mockups for this component
    #include "mockup_src_comp.h"


    /*!
    * @rst
    *
    * .. test:: MyComp.testCorrectBehavior
    *    :id: TS_COMP-001
    *    :tests: SWDD_COMP-001
    *
    * @endrst
    */
    TEST(MyComp, testCorrectBehavior)
    {
        CREATE_MOCK(mymock);
        // Make the input interface return 5
        EXPECT_CALL(mymock, ReadExternalVar()).WillOnce(Return(5));
        // Expect the output interface to be called with 10
        EXPECT_CALL(mymock, WriteOutputVar(10)).Times(1);
        MyCompMain();
    }


Implementing the Component
**************************

The component implementation is located in the ``src`` directory.

Here are the main features supporting component implementation:

* use `sphinx-needs <https://www.sphinx-needs.com/>`_ to create traceability between documentation, code and tests
* include/exclude content based on configuration

**Traceability**

In order to trace the documentation to the code or tests, you need to add a `sphinx-needs <https://www.sphinx-needs.com/>`_ element.

.. code-block:: C

    /**
    * @rst
    * .. impl:: Some function
    *    :id: SWIMPL_COMP-001
    *    :implements: SWDD_COMP-001
    * @endrst
    */
    unsigned int someFunction(int a)
    {
        ...
    }

The ``impl`` is used to tag the component implementation. It shall have:

* a title to very briefly describe the specification. This will be shown in traceability tables.
* an id to uniquely identify the specification. The id naming convention is ``SWIMPL<_<COMPONENT_NAME>-<NUMBER>``.
* an ``implements`` tag to link the implementation to the specification. One can link multiple specifications by separating them with a comma.
* free text to describe the specification in more details.

**Template**

Here is minimal ``my_comp.c`` template for getting you started implementing a component:

.. code-block:: C

    /**
    * @file
    */
    #include "my_comp.h"
    #include "autoconf.h"


    /**
    * @rst
    * .. impl:: Some function
    *    :id: SWIMPL_COMP-001
    *    :implements: SWDD_COMP-001
    * @endrst
    */
    unsigned int someFunction(int a)
    {
        return a + 1;
    }

.. attention::

    The ``impl`` traces are parsed from the doxygen documentation.
    To make sure the doxygen documentation is generated for a source file,
    one needs to add the ``@file`` tag at the top of the file.


Add the Component to the Build
******************************

To add the component to the build, one needs to create the component build system file and then include it in the variants.

To create a component, you need to specify the productive and test sources in the component ``CMakeLists.txt`` file.

.. code-block:: CMake

    spl_add_source(src/comp.c)
    spl_add_test_source(test/test_comp.cc)
    spl_create_component()

The :ref:`spl_create_component <spl_create_component>` macro must be called at the end of the ``CMakeLists.txt`` file, after all sources have been added.

.. note::

    One must not explicitly add the ``index.rst`` file to the component.
    If a component has a ``index.rst`` file, it will be automatically added to the documentation and the component report CMake target will be created.

To add the component to variant one needs to include the component build system file in the variant ``parts.cmake`` file.

.. code-block:: CMake

    spl_add_component(src/comp)


Component Configuration
************************

The component configuration is located in the ``Kconfig`` file and must be included in the variant ``Kconfig`` file located in the project root.

.. code-block:: KConfig

    menu "Features"
        source "src/compA/KConfig"
        source "src/compB/KConfig"
    endmenu

For more details about what can be configured, see the `Kconfig documentation <https://www.kernel.org/doc/html/latest/kbuild/kconfig-language.html>`_.
