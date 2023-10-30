📚 Internals
************

SPL Project Structure
---------------------

.. mermaid::

   classDiagram
      class SPL {
         +variants: Variant[]
         +components: Component[]
      }
      class Variant {
         +name: string
         +configuration: Configuration
      }
      class Component {
         +name: string
         +sources: Source[]
         +test_sources: TestSource[]
         +prod_sources: ProductiveSource[]
      }
      class Source {
         +path: string
      }
      SPL "1" o-- "1..*" Variant
      SPL "1" o-- "1..*" Component
      Variant --> Component: configures
      Component "1" *-- "1..*" TestSource
      Component "1" *-- "1..*" ProductiveSource
      TestSource <|-- Source
      ProductiveSource <|-- Source


Supported Build Targets
-----------------------

SPL Core reuses the concept of build kits from the VS Code extension *CMake Tools*. Currently, two build kits
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

   Build kit 'test' shall provide a build target '<component>_report', that creates a report of a SW component containing
   the documentation, test specification and all test results.
   Precondition of this build target is the existence of a conf.py and index.rst inside the root folder of a component.

.. req:: Creation of Sphinx Output
   :status: open

   Call of sphinx-build takes care of the dependencies and makes incremental builds.
   SPL Core shall always start the docs target for generating the documentation and let sphinx-build handle the dependencies.

.. req:: Configurable Sphinx Output
   :status: open

   The documentation shall be configurable. One should be able to generate the variant specific documentation, i.e.,
   only the variant specific components and their features shall be part of the documentation.

.. req:: Project Documentation
   :status: open

   The project's index.rst file shall be static but changeable and configurable.

Dependencies of Build Targets
-----------------------------

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


Folder Structure for Report Creation
------------------------------------

::

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


Sphinx Build Configuration
--------------------------

Sphnix build required configuration file(conf.py) and main rst(index.rst) file are located in same folder.
Because of this:

  * we need conf.py and index.rst files in the root directory
  * the index.rst file dynamically includes the target index.rst
  * the conf.py file needs to read a configuration file (config.json) to be able to find all the relevant files for the current CMake docs target 


conf.py
^^^^^^^

  * conf.py is a static file and we do not know the path of config.json file, we need to get the path to it as an environment variable
  * we should check, if environment variable(SPHINX_BUILD_CONFIGURATION_FILE) exists just load the content and store into the html_context(https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-html_context)
  
index.rst
^^^^^^^^^

This file just includes the target index.rst depending on the ``docs`` CMake target.


Component Docs CMake Target
---------------------------

A component docs target ``<component>_docs`` will be created automatically if there is an index.rst file in the component ``doc`` directory.
Only the files included in the ``doc`` folder are part of the report. Therefore, there will be no traceability to IDs from ``src`` or ``test``.

Execution steps: 

* we need to create config.json
* we need to create an index.rst file which includes
    * component detailed design rst file
* we need to call sphinx-build "pipenv run sphinx-build -b html . build/<Variant>/test/src/<Component>/docs/html"
    * source directory is always a projet root directory and output directory is build/<Variant>/test/src/<Component>/docs/


Component Reports CMake Target
------------------------------

* this target depends on ``unittests`` target
* we need to create config.json file
* we need to create an index.rst file, which includes
    * component detailed design rst file
    * component test results rst file
    * component doxygen rst file
* we need to create a test_results.rst file to include the componenet junit test results.
* we need to copy Doxyfile from the docs folder and then we have to update the paths where Doxyfile should find the sources
* we need to call sphinx-build "pipenv run sphinx-build -b html . build/<Variant>/test/src/<Component>/reports/html"
    * source directory is always a projet root directory and output directory is build/<Variant>/test/src/<Component>/reports/
