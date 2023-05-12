# Variable vs Pressure Plot

`make run-plot-var-pressure`
## Summary

This scripts reads data from a folder and show a given variable value against pressure value, for different water masses.

## Configuration

The configuration file for this script is `config/plot_var_pressure.toml` (based on [`config/default_plot_var_pressure.toml`]({{repo_blob}}/config/default/plot_var_pressure.toml)). All the parameters and their functionality are listed below:
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
??? question "PLOT_VARIABLE"

    Variable to plot the value of.

    **default**: `"NTRA"`

    Expected type: `str`

??? question "DATE_MIN"

    First date to map (included).

    **default**: `"20070101"`

    Expected type: `str` (must match the `YYYYMMDD`format)

??? question "DATE_MAX"

    Last date to map (included).

    **default**: `"20121231"`

    Expected type: `str` (must match the `YYYYMMDD`format)

??? question "LATITUDE_MIN"

    Minimum latitude boundary for the loaded data (included).

    **default**: `50`

    Expected type: `int or float`

??? question "LATITUDE_MAX"

    Maximum latitude boundary for the loaded data (included).

    **default**: `90`

    Expected type: `int or float`

??? question "LONGITUDE_MIN"

    Minimum longitude boundary for the loaded data (included).

    **default**: `-180`

    Expected type: `int or float`

??? question "LONGITUDE_MAX"

    Maximum longitude boundary for the loaded data (included).

    **default**: `180`

    Expected type: `int or float`

??? question "WATER_MASS_ACRONYMS"

    List of the acronyms of the water masses to load. The acronyms are the ones defined in `config/water_masses.toml`, in the `ACRONYM` field.

    **default**: `["ALL", "AW", "MAW"]`

    Expected type: `list[str]`

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
When executed, this script display a value vs pressure view of a given variable, for different given water masses.

This is an example of what this plot could look like:

![var vs pressure output example]({{fix_url("assets/plots/wm_comparison.png")}}){width=750px}

Source code: [:octicons-file-code-16:]({{repo_blob}}/scripts/plot_var_pressure.py)
