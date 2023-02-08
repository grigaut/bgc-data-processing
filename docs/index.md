# Getting Started

BGC-DATA-PROCESSING provides a set of modules to process amd map biogeochemical data.

## Execution

In order to execute the scripts of this project, **It is necessary to have conda installed** to be able to create and use the virtual environements needed.

??? question "Installing conda"

    <https://conda.io/projects/conda/en/latest/user-guide/install/index.html>

??? question "Setting up the virtual environment to run the scripts inside it"
    More informations here : [Virtual Environment](/virtual_env/)

    *Not necessary*

All the scripts are located in the `/scripts/` folder, all the following paths will be relative to this folder.

### Aggregator

* To run the main script (`/aggregator/save_aggregated_data.py`) using custom parameters, execute :

=== "Outside virtual environment"
    ``` bash
    bash ./scripts/execute_in_conda_env ./scripts/aggregator/save_aggregated_data.py <var1> <var2> <var3>
    ```
=== "Inside virtual environment"
    ``` bash
    python ./scripts/aggregator/save_aggregated_data.py <var1> <var2> <var3>
    ```

!!! info "`<var1>`"

    string containing the years (`,` separed, no space) to process (`2007,2008` for example)

!!! info "`<var2>`"

    string containing the data provider (`,` separed, no space) to consider (`IMR,ICES` for example)

!!! info "`<var13>`"

    -optional- integer to specify the type of verbose to display in the terminal while executing : 

    * `0` and below => no display
    * `1` : light display => major steps only
    * `2` : medium display =>  major steps + daterange progression
    * `3` and above : heavy display => all steps

    
Therefore, to compute outputs for 2007 and 2009, using data priovided by IMR and CLIVAR and with a light display, run 

=== "Outside virtual environment"
    ``` bash
    bash ./scripts/execute_in_conda_env ./scripts/aggregator/save_aggregated_data.py "2007,2009" "IMR,CLIVAR" 1
    ```
=== "Inside virtual environment"
    ``` bash
    python ./scripts/aggregator/save_aggregated_data.py "2007,2009" "IMR,CLIVAR" 1
    ```

### Mapper

To run the main script (`/mapper/plot_argo.py`), execute :

=== "Outside virtual environment"
    ``` bash
    bash ./scripts/execute_in_conda_env ./scripts/mapper/plot_argo.py
    ```
=== "inside virtual environment"
    ``` bash
    python ./scripts/mapper/plot_argo.py
    ```