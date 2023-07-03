# bgc-data-processing
bgc_data_processing is a set of scripts to prepare csv files with BGC variables for EnKF prepobs.
## Getting started
### Requirements
Having conda installed is necessary to use this project.
More informations on how to download conda can be found [here](https://conda.io/projects/conda/en/latest/user-guide/install/index.html).
### Documentation
This project has a more exhaustive documentation which has been created using [mkdocs](https://www.mkdocs.org/).

The following command (executed at root level) will load the documentation:

``` bash
make view-docs
```

If `make` is not installed, one must manually create the environment with the following commands before displaying the documentation:

``` bash
conda env create --file environment.yml --prefix ./.venv
conda activate ./.venv
poetry install --group docs
mkdocs serve
```

The documentation should then be available at the following url: `localhost:8000`
## Running the Scripts

To run a script from the [scripts](/scripts/) folder and named `script_1.py`, one can use the following command:

### Using make
``` bash
make run-script-1
```

make will install the correct environment and run the script

Any `.py` file loctaed in the [scripts](/scripts/) folder can be run with a make rule starting by `run-` and ending with the name of the file (without the `.py` extension) and where all underscores ('_') ar replaced by hyphens ('-').
*These rules are created dynamically so if a new script is added, there is no modification to apply to [Makefile](/Makefile) to use the corresponding rule*

### Without make
*Virtual environment must have been installed*
``` bash
conda activate ./.venv
```

Activate virtual environment

``` bash
poetry install --without dev,docs
```

Install all required libraries

``` bash
python scripts/script_1.py
```

Run script.
## Configuration files
Each scripts has an associated configuration to set up all necessary parameters. By default, these configuration don't exists but can be created from a 'default configuration' existing in [config/default](/config/default/). If these copy don't exist, the following command will create the file:

### Using make
``` bash
make copy-default-config
```
### Without make
Manually copy/paste all scripts from [config/default](/config/default/) into [config](/config/). Or use the following command:
``` bash
for name in config/default/*.toml; do cp config/default/$(basename ${name}) config/_$(basename ${name}) ; done
```

Before running any script, one has to verify that all parameters indicated in the configuration are relevant. For example, one has to fill in all `PATH` parameters in the [`providers.toml`](/config/default/providers.toml) configuration file to indicate where the providers data can be find.

## Make rules cheatsheet

### Installation
<details close>
<summary> <code>make all</code> </summary>
Create the environment, install all libraries and copy the configuration files (if needed).
</details>

<details close>
<summary> <code>make copy-default-config</code> </summary>
Copy default configuration files to the config folder if default files have been modified or if the configuration file doesn't exist.
</details>

<details close>
<summary> <code>make pre-commit</code> </summary>
Install git pre-commit hooks to ensure that the code meets editing standards before committing to github.
</details>

<details close>
<summary> <code>make install-dev</code> </summary>
Install the environment as <code>make all</code> would do and install git hooks to ensure that the code meets editing standards before committing to github.
</details>

### Cleaning
<details close>
<summary> <code>make clean</code> </summary>
'Clean' the repository environment: remove virtual environment folder and git hooks.
</details>

<details close>
<summary> <code>make clean-dirs</code> </summary>
'Clean' the outputs: remove all bgc_fig and bgc_data directories.
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

## License :
[MIT](https://choosealicense.com/licenses/mit/)
