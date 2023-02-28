# Data aggregator

Aggregates and standardizes data from various data providers.

## Description

Biogeochemical (BGC) data comes from differents providers. They all use their own format and there can be difference in the presence of variables, the naming of variables, or the units. This aggregator aims at providing a tool which can process data from different providers and aggregate them under a standardized format.

## Configuration

In order to modify the filepaths for both input and output directories, one only has to modify the input directpries for each provider in `config.toml`.
However, it is important to keep in mind that the input directory is expected to have the following architecture.

## How it works

During the execution, for given dates and data providers the script behaves this way :

1. Loading the run cycles periods from the directory `lists` (at root level), adding the whole year as a cycle period (`01/01/2007-12/31/2007` for 2007 for example).

2.  Loading the data from the data providers on the concerned years (2006 and 2007 if the cycles extends from 28/12/2006 to 22/12/2007 for example). The informations to properly load the data are stored in the folder [data_providers](../../reference/data_providers/).

3.  Formatting the data to standardize columns names and units. Informations to modify the data are stored in the provider files in the folder [data_providers](../../reference/data_providers/)

## Details

### Correction functions
In the informations parameters from data providers in [data_providers](../../reference/data_providers/), it is possible to specify a correction funciton using the `correct_with` method of the Var objects used to represents data's variables.

### Data files patterns
In the storing class ProviderParams defined in [storers.py](../../reference/data_providers/storers/), the method `get_pattern` stores a function (defined using a lambda expression, more informations [here](https://docs.python.org/3/reference/expressions.html#lambda)). When dates specified, this function returns a pattern to look for in the data folder, the return files will correspond to the date.
To create a pattern, follow the recommandations of the re library ([here](https://docs.python.org/3/library/re.html)) to create a regex. Just leave `{years}` in the string where the years should be placed when instanciating a new object.
For example, using the one defined in [imr.py](../../reference/data_providers/imr/) (`imr_({years}).csv`) with years 2006 and 2008 will return : `imr_(2006|2007|2008).csv`. This pattern indicates that the files `imr_2006.csv`, `imr_2007.csv` and `imr_2007.csv` are the one to load in order to get the data between 2006 and 2008.
