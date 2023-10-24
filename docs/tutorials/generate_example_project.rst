Generate SPL Example Project
****************************

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
