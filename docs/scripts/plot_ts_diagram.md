# Temperature-Salinity Diagram

`make run-plot-ts-diagram`
## Summary

This scripts reads data from a folder and plot the Temperature-Salinity Diagram for the loaded data.

## Configuration

The configuration file for this script is `config/plot_ts_diagram.toml` (based on [`config/default_plot_ts_diagram.toml`]({{repo_blob}}/config/default/plot_ts_diagram.toml)). All the parameters and their functionality are listed below:
### **Input/Output**
??? question "LOADING_DIR"

    Directory from which to load data.

    **default**: `"bgc_data"`

    Expected type: `str`

??? question "SHOW"

    Whether to show the figure or not.

    **default**: `true`

    Expected type: `bool`

??? question "SAVE"

    Whether to save the figure or not.

    **default**: `false`

    Expected type: `bool`

??? question "SAVING_DIR"

    Directory in which to save the figure.

    **default**: `"bgc_figs"`

    Expected type: `str`
### **Data Selection**
??? question "DATE_MIN"

    First date to map (included).

    **default**: `"20070101"`

    Expected type: `str` (must match the `YYYYMMDD` format)

??? question "DATE_MAX"

    Last date to map (included).

    **default**: `"20070331"`

    Expected type: `str` (must match the `YYYYMMDD` format)

??? question "LATITUDE_MIN"

    Minimum latitude boundary to consider for the loaded data (included).

    **default**: `69`

    Expected type: `int or float`

??? question "LATITUDE_MAX"

    Maximum latitude boundary to consider for the loaded data (included).

    **default**: `76`

    Expected type: `int or float`

??? question "LONGITUDE_MIN"

    Minimum longitude boundary to consider for the loaded data (included).

    **default**: `0`

    Expected type: `int or float`

??? question "LONGITUDE_MAX"

    Maximum longitude boundary to consider for the loaded data (included).

    **default**: `40`

    Expected type: `int or float`

??? question "DEPTH_MIN"

    Minimum depth boundary to consider for the loaded data (included).

    **default**: `nan`

    Expected type: `int or float`

??? question "DEPTH_MAX"

    Maximum depth boundary to consider for the loaded data (included).

    **default**: `0`

    Expected type: `int or float`

??? question "EXPOCODES_TO_LOAD"

    Precise expocode to load alone. If empty, no discrimination on expocode will be conducted.

    **default**: `[]`

    Expected type: `list[str]`

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

When executed, this script displays the Temperature-Salinity diagram for the selected data.

This is an example of what this diagram could look like:

![ts diagram output example](../assets/plots/TS_diagram.png){width=750px}

Source code: [:octicons-file-code-16:]({{repo_blob}}/scripts/plot_ts_diagram.py)
