<a href="https://bundlephobia.com/result?p=@sherby/sherby-metadata@3.0.1">
  <img 
     alt="BundlePhobia"
     src="https://img.shields.io/bundlephobia/min/@sherby/sherby-metadata"
  />
</a>

# bgc-data-processing

bgc_data_processing is a set of scripts to prepare csv files with BGC variables for EnKF prepobs.

## Getting started

### Requirements

Having conda installed is necessary to use this projects.
More informations on how to download conda can be found [here](https://conda.io/projects/conda/en/latest/user-guide/install/index.html).

### Documentation

This project has a more exhaustive documentation which has been created using [mkdocs](https://www.mkdocs.org/).

The following command (executed at root level) will load the documentation:

``` bash
bash ./scripts/build_docs_local.sh
```

When asked about whether building or displaying the docs, enter `B` in order to build the html documentation website in the local repository or `D` to display the documentation in a web browser, available at the adress shown in the terminal (localhost:8000 by default).

## Executing

### Aggregator

The following command (executed at root level) will run the main script [save_aggregated_data.py](/scripts/aggregator/save_aggregated_data.py):

``` bash
bash ./scripts/execute_in_conda_env ./scripts/aggregator/save_aggregated_data.py <var1> <var2> <var3>
```

Where :
* `<var1>` is a string containing the years (`,` separed, no space) to process (`2007,2008` for example)

* `<var2>` is a string containing the data provider (`,` separed, no space) to consider (`IMR,ICES` for example)

* `<var13>` is an -optional- integer to specify the type of verbose to display in the terminal while executing : 

    * `0` and below => no display
    * `1` : light display => major steps only
    * `2` : medium display =>  major steps + daterange progression
    * `3` and above : heavy display => all steps

Therefore, to compute outputs for 2007 and 2009, using data priovided by IMR and CLIVAR and with a light display, run 

``` bash
bash ./scripts/execute_in_conda_env ./scripts/aggregator/save_aggregated_data.py "2007,2009" "IMR,CLIVAR" 1
```

### Mapper

The following command (executed at root level) will run the main script [plot_argo.py](/scripts/mapper/plot_argo.py):

``` bash
bash ./scripts/execute_in_conda_env ./scripts/mapper/plot_argo.py
```

## License :

[MIT](https://choosealicense.com/licenses/mit/)
