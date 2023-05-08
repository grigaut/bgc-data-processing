# Data Saving

`make run-save-data`
## Summary

This scripts loads data from differents providers, aggregate the data to a standardized format and save the data in `.txt` files.

## Configuration

The configuration file for this script is `config/save_data.toml` (based on [`config/default_save_data.toml`]({{repo_blob}}/config/default/save_data.toml)). All the parameters and their functionality are listed below:
### **Input/Output**

??? question "SAVING_DIR"

    Directory in which to save the dataframes

    **default**: "bgc_data"

    Expected type: `str`
### **Data Selection**
??? question "PROVIDERS"

    List of providers to use data from

    **default**: ["GLODAP_2022", "CMEMS", "ARGO", "NMDC", "CLIVAR", "IMR", "ICES"]

    Expected type: `list[str]`
??? question "VARIABLES"

    Variables to include in the output file. The name or the variables are the ones defined in `config/variables.toml`, in the `NAME` field.

    **default**: ["PROVIDER", "EXPOCODE", "YEAR", "MONTH", "DAY", "HOUR", "LONGITUDE", "LATITUDE", "DEPH", "TEMP", "PSAL", "DOXY", "PHOS", "NTRA", "SLCA", "CPHL"]

    Expected type: `list[str]`

??? question "DATE_MIN"

    Beginning of the data to load (included).

    **default**: "20070101"

    Expected type: `str` (respecting the `YYYYMMDD` format)

??? question "DATE_MAX"

    End of the data to load (included).

    **default**: "20071231"

    Expected type: `str` (respecting the `YYYYMMDD` format)

??? question "INTERVAL"

    : str: horizontal resolution of the plot
    # If set to 'day': will group datapoint by day
    # If set to 'week': will group datapoints by their week number
    # If set to 'month': will group datapoints by month
    # If set to 'year': will grou datapoints by year
    # If set to 'custom': will group datapoints based on a custom interval
    **default**: "month"

??? question "CUSTOM_INTERVAL"

    : int: if INTERVAL is 'custom', length of the custom interval (in days)
    **default**: 8

??? question "LATITUDE_MIN"

    : int | float: minimum latitude boundary (included)
    **default**: 50

??? question "LATITUDE_MAX"
    : int | float: maximum latitude boundary (included)
    **default**: 90

??? question "LONGITUDE_MIN"
    : int | float: minimum longitude boundary (included)
    **default**: -180

??? question "LONGITUDE_MAX"
    : int | float: maximum longitude boundary (included)
    **default**: 180

??? question "DEPTH_MIN"
    : int | float: minimum depth boundary (included)
    **default**: nan

??? question "DEPTH_MAX"
    : int | float: maximum depth boundary (included)
    **default**: 0

??? question "EXPOCODES_TO_LOAD"
    : list[str]: precise expocode to load alone.
    If empty, no discrimination on expocode will be conducted
    **default**: []

??? question "PRIORITY"
    : list[str]: providers priority list to use when removing duplicates
    **default**: ["GLODAP_2022", "CMEMS", "ARGO", "NMDC", "CLIVAR", "IMR", "ICES"]
### **Others**
??? question "VERBOSE"
    : int: verbose value, the higher, the more informations.
    # If set to 0 or below: no information displayed
    # If set to 1: minimal informations displayed
    # If set to 2: very complete informations displayed
    # if set to 3 or higher: exhaustive informations displayed
    **default**: 2

Source code: [:octicons-file-code-16:]({{repo_blob}}/scripts/save_data.py)
