✨ Features
************

Component Report
----------------

To support the :ref:`component <glossary_component>` development, SPL Core provides features to:

- document the component behavior - see :ref:`How to create a component detail design <how_to_component_detail_design>`
- test the component behavior - see :ref:`How to create a component test cases <how_to_component_test_cases>`
- generate component report with full traceability between documentation, code and tests - see :ref:`Component relevant CMake Targets <component_cmake_targets>`


Variant Report
--------------

To support the :ref:`variant <glossary_variant>` development, SPL Core provides features to:

TODO: add variant report description

Pypeline Steps
--------------

Spl-Core provides the step CollectPRChanges for `Pypeline <https://github.com/cuinixam/pypeline>`_ to be used in an SPL.
This step fetches the list of changed files inside a pull request (PR), which can then be used for granular quality gate checks inside an SPL.
To use this step, you need to add it to your pypeline.yaml file as follows:

.. code-block:: yaml

   ...
   - step: CheckCIContext
     module: pypeline_semantic_release.steps
   - step: CollectPRChanges
     module: spl_core.steps.collect_pr_changes
   ...

It is mandatory that the CheckCIContext step is executed before the CollectPRChanges step.
