# Data Extraction

`make run-extract-data`

## Summary

This script extract data from an already loaded dataset and saves it into a given folder.

## Configuration

The configuration file for this script is `config/extract_data.toml` (based on [`config/default/extract_data.toml`]({{repo_blob}}/config/default/extract_data.toml)). All the parameters and their functionality are listed below:

### **Input/Output**
??? question "LOADING_DIR"
    Directory from which to load data.

    **default**: `"bgc_data"`

    Expected type: `str`

??? question "SAVING_DIR"
    Directory in which to save extracted data.

    **default**: `"output"`

    Expected type: `str`
### **Data Selection**
??? question "FROM_POLYGON"
    If true, the extracted data is the data within POLYGON_DOMAIN, otherwise, the data within the [LONGITUDE_MIN, LONGITUDE_MAX] and [LATITUDE_MIN, LATITUDE_MAX] boundaries.

    **default**: `false`

    Expected type: `bool`

??? question "DATE_MIN"
    Beginning of the data to load (included).

    **default**: `"20070101"`

    Expected type: `str` (respecting the `YYYYMMDD` format)

??? question "DATE_MAX"
    End of the data to load (included).

    **default**: `"20071231"`

    Expected type: `str` (respecting the `YYYYMMDD` format)

??? question "LATITUDE_MIN"
    Minimum latitude boundary for the loaded data (included).
    Only used if `FROM_POLYGON` is set to `false`.

    **default**: `60`

    Expected type: `int`or `float`

??? question "LATITUDE_MAX"
    Maximum latitude boundary for the loaded data (included).
    Only used if `FROM_POLYGON` is set to `false`.

    **default**: `80`

    Expected type: `int`or `float`

??? question "LONGITUDE_MIN"
    Minimum longitude boundary for the loaded data (included).
    Only used if `FROM_POLYGON` is set to `false`.

    **default**: `-50`

    Expected type: `int`or `float`

??? question "LONGITUDE_MAX"
    Maximum longitude boundary for the loaded data (included).    Only used if `FROM_POLYGON` is set to `false`.

    **default**: `50`

    Expected type: `int`or `float`

??? question "POLYGON_DOMAIN"
    Polygon to use for data extraction. Only used if `FROM_POLYGON` is set to `true`.

    **default**: `"POLYGON((-50 60, 50 60, 50 80, -50 80, -50 60))"`

??? question "PRIORITY"
    Providers priority list to use when removing duplicates.

    **default**: `["GLODAP_2022", "CMEMS", "ARGO", "NMDC", "CLIVAR", "IMR", "ICES"]`

    Expected type: `list[str]`
### **Others**
??? question "VERBOSE"
    Verbose value, the higher, the more informations. If set to 0 or below: no information displayed. If set to 1: minimal informations displayed. If set to 2: very complete informations displayed. If set to 3 or higher: exhaustive informations displayed.

    **default**: `2`

    Expected type: `int`
## Script Output
When executed, this script will create a file in the `SAVING_DIR` folder with the extracted data.

This is an example of what this data could look like:

![Data Extraction output example]({{fix_url("assets/plots/saved_data.png")}}){width=750px}

Source code: [:octicons-file-code-16:]({{repo_blob}}/scripts/extract_data.py)
