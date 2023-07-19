Design
######

Supported Build Targets
***********************

SPL Core reuses the concept of build kits from the VS Code extension *CMake Tools*. Currently two build kits
are defined and supported:

* *prod*: compilation and linking of an executable for a specific target device.
* *test*: compilation, linking and execution of SW component tests, creation of documentation and reports.

Build kit *prod*
^^^^^^^^^^^^^^^^

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
   least a conf.py.

.. req:: Support Documentation
   :status: open

   Build kit 'test' shall provide a build target 'docs', that creates the documentation of all SW components.

.. req:: Support Creation of a Component Report
   :status: open

   Build kit 'test' shall provide a build target '<component>_reports', that creates a report of a SW component containing
   the documentation, test specification and all test results.
   Precondition of this build target is the existence of a conf.py and index.rst inside the root folder of a component.

.. req:: Creation of Sphinx Output
   :status: open

   Call of sphinx-build takes care of the dependencies and makes incremental builds.
   spl-core shall always start the docs target for generating the documentation and let sphinx-build handle the dependencies.

.. req:: Configurable Sphinx Output
   :status: open

   The documentation shall be configurable. One should be able to generate the variant specific documentation, i.e.,
   only the variant specific components and their features shall be part of the documentation.

.. req:: Project Documentation
   :status: open

   The project's index.rst shall be static but changable and configurable.

Dependencies of build targets
*****************************

The build targets

* docs
* reports

are just virtual targets generating several documents, one for each component.

On the other hand the build targets

* doc
* report

are real targets generating exactly one document including all components.

.. mermaid::

   graph TB
       unittests --> component_unittests["&lt;component&gt;_unittests"]
       docs --> component_docs["&lt;component&gt;_docs"]
       reports --> component_report["&lt;component&gt;_reports"]
       doc
       report


Folder structure for report creation
************************************

<project root>
  build/
    <Variant>/
      test/
        src/
          <Component>/
            doc/
              html/
                index.html (<Component>_DetailedDesign)
            test/
              html/
                index.html (<Component>_UnitTestResults-UnitTestSpecification)
            report/
              html/
                index.html (SWE.4-Report for <Component>, contains DD + Test Results + Test Spec)
            junit.xml
  src/
    App/
      <Component>/
        doc/
          conf.py
          index.rst
        src/
          <Component>.c  
        test/
          <Component>_test.cc
          index.rst
        conf.py
        index.rst
  