[![Docstrings](./docs/assets/badges/interrogate_badge.svg)](https://github.com/grigaut/bgc-data-processing)
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
## Executing
### Using make
- **Aggregation and Saving**

    The following command (executed at root level) will run the [aggregation and saving script](/scripts/save_data.py):

    ``` bash
    make run-save
    ```
- **Mapping**

    The following command (executed at root level) will run the main script [plot_mesh.py](/scripts/plot_mesh.py):

    ``` bash
    make run-plot
    ```
### Without make
One must manually create the environment with the following commands before runnning any script:

``` bash
conda env create --file environment.yml --prefix ./.venv
conda activate ./.venv
poetry install
```

*If the environment has already been created to display the documentation, one only has to install the libraries required for the execution in the environment:*

``` bash
conda activate ./.venv
poetry install
```

Then, it is possible to execute the scripts inside the environment (use `conda activate ./.venv` to activate the environment):
- **Aggregation and Saving**

    The following command (executed at root level in the virtual environment) will run [aggregation and saving script](/scripts/save_data.py):

    ``` bash
    python scripts/save_data.py
    ```

- **Mapping**

    The following command (executed at root level in the virtual environment) will run the main script [plot_mesh.py](/scripts/plot_mesh.py):

    ``` bash
    python scripts/plot_mesh.py
    ```
## Configuration
[Aggregation](/scripts/save_data.py) and [Mapping](/scripts/plot_mesh.py) scripts can both be configured using the configuration file, [config.toml](/config.toml)
## License :
[MIT](https://choosealicense.com/licenses/mit/)
