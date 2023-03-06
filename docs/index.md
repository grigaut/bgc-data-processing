# Getting Started

BGC-DATA-PROCESSING provides a set of modules to process and map biogeochemical data.

## Requirements

In order to execute the scripts of this project, **It is necessary to have conda installed** to be able to create and use the virtual environements needed.

??? question "How to install conda ?"

    [Conda installing guide](https://conda.io/projects/conda/en/latest/user-guide/install/index.html)

Having **GNU Make** installed can also simplify the project's setup.

??? question "How to install GNU Make ?"

    === "Ubuntu"
        [More informations on installing GNU make for ubuntu systems.](https://linuxhint.com/install-make-ubuntu/)

    === "Windows"
        [More informations on installing GNU make for windows systems.](https://linuxhint.com/install-use-make-windows/)

    === "macOS"
        [More informations on installing GNU make for macOS systems using Homebrew.](https://docs.brew.sh/Installation)

## Building the virtual environment

=== "With make"
    ``` bash
    make all
    ```
=== "Without make"
    ``` bash
    conda env create --file environment.yml --prefix ./.venv
    ```
    ``` bash
    conda activate ./.venv
    ```
    ``` bash
    poetry install
    ```

!!! info ""
    [More details on the virtual environment](/virtual_env/)

## Running the Scripts

### Data Aggregation and Saving Script

=== "With make"
    ``` bash
    make run-save # (1)!
    ```

    1. make will install the correct environment and run the scripts

=== "Without make"
    *Virtual environment must have been installed*
    ``` bash
    conda activate ./.venv  # (1)!
    ```

    1. Activate virtual environemnt

    ``` bash
    python scripts/save_data.py # (1)!
    ```

    1. Run script.

### Data Plotting Script

=== "With make"
    ``` bash
    make run-plot # (1)!
    ```

    1. make will install the correct environment and run the scripts

=== "Without make"
    *Virtual environment must have been installed*
    ``` bash
    conda activate ./.venv  # (1)!
    ```

    1. Activate virtual environemnt

    ``` bash
    python scripts/plot_mesh.py # (1)!
    ```

    1. Run script.
