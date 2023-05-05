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

## Configuration files
Each scripts has an associated configuration to set up all necessary parameters. By default, these configuration don't exists but can be created from a 'default configuration' existing in [config/default](/config/default/). If these copies don't exist, the following command will create the files:

=== "With make"
    ``` bash
    make copy-default-config
    ```
=== "Without make"
    Manually copy/paste all scripts from [config/default](/config/default/) into [config](/config/). Or use the following command:
    ``` bash
    for name in config/default/*.toml; do cp config/default/$(basename ${name}) config/_$(basename ${name}) ; done
    ```

Before running any script, one has to verify that all parameters indicated in the configuration are relevant. For example, one has to fill in all `PATH` parameters in the [`providers.toml`](/config/default/providers.toml) configuration file to indicate where the providers data can be find.
## Running the Scripts

To run a script from the [scripts](/scripts/) folder and named `script_1.py`, one can use the following command:

=== "With make"
    ``` bash
    make run-script-1 # (1)!
    ```

    1. make will install the correct environment and run the script

    Any `.py` file loctaed in the [scripts](/scripts/) folder can be run with a make rule starting by `run-` and ending with the name of the file (without the `.py` extension) and where all underscores ('_') ar replaced by hyphens ('-').
    *These rules are created dynamically so if a new script is added, there is no modification to apply to [Makefile](/Makefile) to use the corresponding rule*

=== "Without make"
    *Virtual environment must have been built, see [here](#building-the-virtual-environment)*
    ``` bash
    conda activate ./.venv  # (1)!
    ```

    1. Activate virtual environment

    ``` bash
    poetry install --without dev,docs  # (1)!
    ```

    1. Install all required libraries

    ``` bash
    python scripts/script_1.py # (1)!
    ```

    1. Run script.

## Make rules cheatsheet

### Installation
**Main**
<details close>
<summary> <code>make all</code> </summary>
Create the environment, install main libraries and copy the configuration files (if needed).
</details>

<details close>
<summary> <code>make copy-default-config</code> </summary>
Copy default configuration files to the config folder if default files have been modified or if the configuration file doesn't exist.
</details>

<details close>
<summary> <code>make pre-commit</code> </summary>
Install git pre-commit hooks to ensure that the code meets editing standards before committing to github.
</details>

**Development**
<details close>
<summary> <code>make install-dev</code> </summary>
Install the environment as <code>make all</code> does with additional development libraries and installs git hooks to ensure that the code meets editing standards before committing to github.
</details>

<details close>
<summary> <code>make hooks</code> </summary>
Install git hooks to ensure that the code meets editing standards before committing to github.
</details>

### Cleaning
<details close>
<summary> <code>make clean</code> </summary>
'Clean' the repository environment: remove virtual environment folder and git hooks.
</details>

<details close>
<summary> <code>make clean-dirs</code> </summary>
'Clean' the outputs: remove both bgc_fig and bgc_data directories if existing.
</details>

### Documentation
<details close>
<summary> <code>make view-docs</code> </summary>
Create the environment, install documentation-related libraries and build the documentation website locally. The documentation is then accessible from a browser at the <code>localhost:8000</code> adress. See MkDocs documentation on <code>mkdocs serve</code> for more informations.
</details>

<details close>
<summary> <code>make build-docs</code> </summary>
Create the environment, install documentation-related libraries and build the documentation website into the 'site' folder. See MkDocs documentation on <code>mkdocs build</code> for more informations.
</details>

<details close>
<summary> <code>make deploy-docs</code> </summary>
Create the environment, install documentation-related libraries and deploy documentation to a github branch. See MkDocs documentation on <code>mkdocs deploy</code> for more informations.
</details>

### Running scripts
<details close>
<summary> <code>make run-any-script</code> </summary>
Create the environment, install scripts-running-related libraries and runs the <code>scripts/any_script.py</code> python script. 'any-script' can be replaced by anything in order to run a script. For example, calling <code>make run-another-script</code> will run the <code>scripts/another_script.py</code> python script (if it exists). To make this rule work, the following syntax must be respected:

- script must be a python script
- script must be in the `scripts/` folder
- underscores ('_') must be replaced by hyphens ('-') in the script name
- extension ('.py') must be removed from the script's name
- rule must start with the `run-` prefix

</details>
