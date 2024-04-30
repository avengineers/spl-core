.. _use-project-creator:

Generate SPL Example Project
============================

Download SPL Core
-----------------

You can either install the SPL Core from the Python Package Index (PyPI)

.. code-block:: powershell

    pip install spl-core

or clone the repository from GitHub and install its dependencies:

.. code-block:: powershell

    git clone https://github.com/avengineers/spl-core
    cd spl-core
    .\build.ps1 -install

SPL Core has a command-line interface called ``please``.

.. note::
    If you have cloned the SPL Core repository you find the ``please`` script in the ``.venv/Scripts`` directory.

Make sure the installation was successful by running the following command:

.. code-block:: powershell

    please --help


Initialize a new SPL Project
----------------------------

Generate the example project:

.. code-block:: powershell

    please init --project-dir C:\tmp\MyProject

This will create a new SPL project in the directory ``C:\tmp\MyProject``.

Before you can build the project, you need to install its dependencies.
Change to the project directory and run the following command:

.. code-block:: powershell

    .\build.ps1 -install

Now you can build the project:

.. code-block:: powershell

    .\build.ps1 -build

Select one of the variants to build, e.g., ``EnglishVariant``.
The created executable can be found in the directory ``build\EnglishVariant\prod\my_main.exe``.

Run the executable in the terminal will output:

.. code-block::

    Hello, World!


Generated Project
-----------------


PowerShell Build Script
^^^^^^^^^^^^^^^^^^^^^^^

The ``build.ps1`` PowerShell script acts as a centralized tool to streamline several tasks related to the project, such as installing dependencies, running, and testing the project. It can be viewed as a build automation script that ensures consistency in development and deployment activities.

You can provide several parameters to customize the script's behavior:

* ``install`` : Install all dependencies required to build.
* ``build`` : Build the target.
* ``clean`` : Clean build, wipe out all build artifacts.
* ``buildKit`` : Build kit to be used.
* ``target`` : Target to be built.
* ``variants`` : Variants (of the product) to be built (List of strings, leave empty to be asked or "all" for automatic build of all variants)
* ``filter`` : filter for selftests; define in pytest syntax: https://docs.pytest.org/en/6.2.x/usage.html; e.g. "EnglishVariant or test_EnglishVariant.py"
* ``ninjaArgs`` : Additional build arguments for Ninja (e.g., "-d explain -d keepdepfile" for debugging purposes)
* ``reconfigure`` : Delete CMake cache and reconfigure.

The following is a flowchart describing the script's operation:

.. mermaid::

    flowchart TD

        Start(Start Script)
        Install{Install?}
        Build{Build?}
        Clean{Clean?}
        HandleClean[Remove All Build Artifacts]
        End(End Script)
        PressKey[Press Any Key to Continue]

        CheckTargetSelftests{Target 'selftests'?}
        HandleSelfTests[Execute Selftests]
        HandleVariants[Detect Variants]
        CleanVariant{Clean?}
        HandleVariantClean[Remove Variant Build Artifacts]
        ReconfigureCheck{Reconfigure?}
        HandleReconfigure[Remove Variant CMake Files]
        CMakeConfigure[Configure & Generate CMake]
        CMakeBuild[Build with CMake]

        Start --> Install
        Install -->|Yes| Bootstrap(Invoke Bootstrap)

        subgraph "BOOTSTRAP"
            Bootstrap-->GitConfig(Git-Config)
        end
        GitConfig-->Build

        Install -->|No| Build
        Build -->|No| PressKey
        Build -->|Yes| CheckTargetSelftests

        subgraph "BUILD"
            CheckTargetSelftests -->|Yes| Clean
            Clean -->|Yes| HandleClean
            Clean -->|No| HandleSelfTests
            HandleClean --> HandleSelfTests
            CheckTargetSelftests -->|No| HandleVariants
            HandleVariants --> CleanVariant
            CleanVariant -->|Yes| HandleVariantClean
            CleanVariant -->|No| ReconfigureCheck
            HandleVariantClean --> ReconfigureCheck
            ReconfigureCheck -->|Yes| HandleReconfigure
            ReconfigureCheck -->|No| CMakeConfigure
            HandleReconfigure --> CMakeConfigure
            CMakeConfigure --> CMakeBuild
        end

        HandleSelfTests --> PressKey
        CMakeBuild --> PressKey
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

        C:/Users/<username>/scoop/apps

.. note::

    For more information about ``scoop`` and how to import dependencies from a ``scoopfile.json`` file, please refer to the `scoop documentation <https://github.com/ScoopInstaller/Scoop>`_.
