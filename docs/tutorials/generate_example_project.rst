Generate SPL Example Project
****************************

Run Project creator
-------------------

Clone the SPL-Core repository:

.. code-block:: powershell

    git clone https://github.com/avengineers/spl-core 


Install its dependencies:

.. code-block:: powershell

    cd spl-core
    .\build.ps1 -install


Activate the python virtual environment and use the project creator to generate the example project:

.. code-block:: powershell

    .venv\Scripts\activate
    pipenv run python src/project_creator/creator.py workspace --name MyProject --variant FLV1/SYS1 --out_dir C:\tmp

This will create a new project in the directory ``MyProject``.

Before you can build the project, you need to install the dependencies:

.. code-block:: powershell

    cd MyProject
    .\build.ps1 -install

Now you can build the project:

.. code-block:: powershell

    .\build.ps1

The created executable can be found in the directory ``.\build\FLV1\SYS1\prod\my_main.exe``.

Generated Project
-----------------


PowerShell Build Script
+++++++++++++++++++++++

The ``build.ps1`` PowerShell script acts as a centralized tool to streamline several tasks related to the project, such as installing dependencies, running, and testing the project. It can be viewed as a build automation script that ensures consistency in development and deployment activities.

You can provide several parameters to customize the script's behavior:

* ``-clean`` : Clean build, wipes out all build artifacts.
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

    GitConfig --> End
    Install -->|No| Clean

    subgraph " "
        Clean -->|Yes| CleanAction[Remove Build Artifacts]
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

  