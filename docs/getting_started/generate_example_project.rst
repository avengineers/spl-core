.. _use-project-creator:

Generate SPL Example Project
============================

Run Project creator
-------------------

Clone the SPL Core repository:

.. code-block:: powershell

    git clone https://github.com/avengineers/spl-core


Install its dependencies:

.. code-block:: powershell

    cd spl-core
    .\build.ps1 -install


Activate the python virtual environment and use the project creator to generate the example project:

.. code-block:: powershell

    .venv\Scripts\activate
    pipenv run python src/project_creator/creator.py workspace --name MyProject --variant VARIANT --out_dir C:\tmp

This will create a new project in the directory ``MyProject``.

Before you can build the project, you need to install the dependencies:

.. code-block:: powershell

    cd MyProject
    .\build.ps1 -install

Now you can build the project:

.. code-block:: powershell

    .\build.ps1

The created executable can be found in the directory ``.\build\VARIANT\prod\my_main.exe``.

Generated Project
-----------------


PowerShell Build Script
^^^^^^^^^^^^^^^^^^^^^^^

The ``build.ps1`` PowerShell script acts as a centralized tool to streamline several tasks related to the project, such as installing dependencies, running, and testing the project. It can be viewed as a build automation script that ensures consistency in development and deployment activities.

You can provide several parameters to customize the script's behavior:

* ``-clean`` : Clean build wipes out all build artifacts.
* ``-install`` : Install mandatory packages.
* ``-target`` : Specifies the target to be built (default is "all").
* ``-variants`` : Specifies the variants (projects) to be built.
* ``-filter`` : Filter for selftests in pytest syntax.
* ``-ninjaArgs`` : Additional build arguments for Ninja.
* ``-reconfigure`` : Delete CMake cache and reconfigure.

The following is a flowchart describing the script's operation:

.. mermaid::

    flowchart TD

    Start(Start Script)
    Install{Install?}
    Clean{Clean?}
    CI{CI Build?}
    End(End Script)
    PressKey[Press Any Key to Continue]

    CheckTarget{Target 'selftests'?}
    HandleSelfTests[Execute Selftests]
    HandleVariants[Detect Variants]
    CleanCheck{Clean?}
    HandleClean[Remove Variant Build Artifacts]
    ReconfigureCheck{Reconfigure?}
    HandleReconfigure[Remove Variant CMake Files]
    CMakeConfigure[Configure & Generate CMake]
    CMakeBuild[Build with CMake]

    Start --> Install
    Install -->|Yes| Scoop(Install-Scoop)

    subgraph " "
        subgraph "BOOTSTRAP"
            Scoop-->Python(Install-Python-Dependency)
        end
        Python-->GitConfig(Git-Config)
    end

    GitConfig --> CI
    Install -->|No| Clean

    subgraph "CLEAN"
        Clean -->|Yes| CleanAction[Remove All Build Artifacts]
    end

    subgraph "CMAKE BUILD"
        Clean -->|No| CheckTarget
        CleanAction --> CheckTarget
        CheckTarget -->|Yes| HandleSelfTests
        CheckTarget -->|No| HandleVariants
        HandleVariants --> CleanCheck
        CleanCheck -->|Yes| HandleClean
        CleanCheck -->|No| ReconfigureCheck
        HandleClean --> ReconfigureCheck
        ReconfigureCheck -->|Yes| HandleReconfigure
        ReconfigureCheck -->|No| CMakeConfigure
        HandleReconfigure --> CMakeConfigure
        CMakeConfigure --> CMakeBuild
    end

    HandleSelfTests --> CI
    CMakeBuild --> CI
    CI -->|Yes| End
    CI -->|No| PressKey
    PressKey --> End


Python Dependencies
^^^^^^^^^^^^^^^^^^^

There are some SPL Core features which require additional Python packages (the list is not exhaustive):

* ``kconfiglib`` : used to generate the configuration header file (``autoconf.h``) from the Kconfig files.
* ``hammocking`` : used to generate the mockups for the unit tests.
* ``sphinx`` : used to generate the documentation.

These Python dependencies are defined in the ``Pipfile`` and will be automatically installed when running the ``build.ps1`` script with the ``-install`` parameter.
There will be a Python virtual environment created in the ``.venv`` directory.


Build Tools Dependencies
^^^^^^^^^^^^^^^^^^^^^^^^

The build tools dependencies (like CMake, Ninja, Compiler etc.) are defined in the ``scoopfile.json`` file and will be automatically installed when running the ``build.ps1`` script with the ``-install`` parameter.
The tools are installed in the user directory under ``scoop``.

..

        C:/Users/my_user/scoop/apps

.. note::

    For more information about ``scoop`` and how to import dependencies from a ``scoopfile.json`` file, please refer to the `scoop documentation <https://github.com/ScoopInstaller/Scoop>`_.
