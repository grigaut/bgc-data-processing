# Virtual Environment

This project environment is build using [Anaconda](https://conda.io/projects/conda/en/latest/index.html), while the package management is done using the Python tool [Poetry](https://python-poetry.org/). The only requirement is to have anaconda installed and to be able to able to run commands using the `conda` methods in a terminal. More informations on enabling the `conda` method in Visual Studio Code [here](https://medium.com/analytics-vidhya/efficient-way-to-activate-conda-in-vscode-ef21c4c231f2).

## Conda 

The conda environment is defined by the environment.yml file. This file contains the bare minimum to build the environment :

* The Python version to use when creating the environment.
* The Poetry version to load when creating the environment.
* Any module/package which couldn't be installed using Poetry.

## Poetry

The dependencies versions are defined in the pyproject.toml file. This file contains informations on the packages/modules version to use when building the environment.


## Environment setup

1. Create the virtual environment from the file `environment.yml`:

    === "From a Bash terminal"
        ``` bash
        conda env create --file environment.yml
        ```
    === "From a Bash script"
        ``` bash
        $CONDA_EXE env create --file environment.yml
        ```
        ??? info "$CONDA_EXE" 
            Variable referring to the conda executable path. It should be already existing.

    ??? info "conda env create" 
        <https://docs.conda.io/projects/conda/en/latest/commands/create.html>

2. Activate the environment named `conda_venv`:
TODO : add line about where to find the environment's name

    === "From a Bash terminal"
        ``` bash
        conda activate $(head -n 1 environment.yml | cut -f2 -d ' ')
        ```
    === "From a Bash script"
        <sup>*Not needed.*

3. Build the environment:

    === "From a Bash terminal"
        ``` bash
        poetry install
        ```

    === "From a Bash script"
        ``` bash
        $CONDA_EXE run --no-capture-output -n conda_venv poetry install
        ```
        ??? info "$CONDA_EXE" 
            Variable referring to the conda executable path. It should be already existing.
        
        ??? info "conda run" 
            <https://docs.conda.io/projects/conda/en/latest/commands/run.html>

    ??? info "poetry install" 
        <https://python-poetry.org/docs/cli/#install>
    
    ??? tip "Installing groups"
        In the dependencies file (pyproject.toml), dependencies are organized into groups, main (nameless), dev and docs. `poetry install` will install all dependencies, regardless of their group. 

        `poetry install --only docs` will only install the 'docs' group. 

        `poetry install --without dev,docs` will install without the docs and dev groups. 

4. Run the python script `hello_world.py`:

    === "From a Bash terminal"
        ``` bash
        python hello_world.py
        ```

    === "From a Bash script"
        ``` bash
        $CONDA_EXE run --no-capture-output -n conda_venv python hello_world.py
        ```
        ??? info "$CONDA_EXE" 
            Variable referring to the conda executable path. It should be already existing.

        ??? info "conda run" 
            <https://docs.conda.io/projects/conda/en/latest/commands/run.html>

5. Updating the environment:

    === "From a Bash terminal"
        ``` bash
        poetry update
        ```

    === "From a Bash script"
        ``` bash
        $CONDA_EXE run --no-capture-output -n conda_venv poetry update
        ```
        ??? info "$CONDA_EXE" 
            Variable referring to the conda executable path. It should be already existing.
        
        ??? info "conda run" 
            <https://docs.conda.io/projects/conda/en/latest/commands/run.html>

    ??? info "poetry update" 
        <https://python-poetry.org/docs/cli/#update>

6. Deactivate the environment named `conda_venv`:

    === "From a Bash terminal"
        ``` bash
        conda deactivate
        ```
    === "From a Bash script"
        <sup>*Not needed.*