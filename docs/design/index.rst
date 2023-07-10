Design
######

Supported Build Targets
***********************

SPL Core reuses the concept of build kits from the VS Code extension *CMake Tools*. Currently two build kits
are defined and supported:

* *prod*: compilation and linking of an executable for a specific target device.
* *test*: compilation, linking and execution of SW component tests, creation of documentation and reports.

.. req:: Build Kit Prod
   :status: done

   SPL Core shall provide a build kit called 'prod'.

.. req:: Build Kit Test
   :status: done

   SPL Core shall provide a build kit called 'test'.


Build kit *test*
^^^^^^^^^^^^^^^^

.. req:: Support Component and Unit Testing
   :status: done

   Build kit 'test' shall provide a build target '<component>_unittests', that executes all tests of a SW component
   and creates a junit.xml with the results.

.. req:: Support Testing
   :status: done

   Build kit 'test' shall provide a build target 'unittests', that executes all tests of all SW components.

.. req:: Support Creation of Documentation
   :status: open

   Build kit 'test' shall provide a build target '<component>_docs', that creates documentation of a SW component.
   Precondition of this build target is the existence of a doc folder inside the component's folder containing at
   least the two files conf.py and index.rst as input to Sphinx.

.. req:: Support Documentation
   :status: done

   Build kit 'test' shall provide a build target 'docs', that creates the documentation of all SW components.

.. req:: Support Creation of Test Report
   :status: open

   Build kit 'test' shall provide a build target '<component>_reports', that creates a test report of a SW component containing
   the documentation, test specification and all test results.
   Precondition of this build target is the existence of a conf.py and index.rst inside the test folder of a component.
