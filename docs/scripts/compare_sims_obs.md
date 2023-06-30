# Simulations-Observations Comparison

`make run-compare-sims-obs`
## Summary

This scripts loads observation data over given periode and area. It then loads the closest simulation data to these obersvation and saves both value in files. Afterward, those dataframes are compared through [RMSE](https://en.wikipedia.org/wiki/Root-mean-square_deviation) and [Bias](https://en.wikipedia.org/wiki/Bias_of_an_estimator) computation. The comparison output is saved into a file.

## Configuration

The configuration file for this script is `config/compare_sims_obs.toml` (based on [`config/default/compare_sims_obs.toml`]({{repo_blob}}/config/default/compare_sims_obs.toml)). All the parameters and their functionality are listed below:
### **Input/Output**
??? question "LOADING_DIR"
    Directory from which to load data.

    **default**: `"bgc_data"`

    Expected type: `str`

??? question "SAVING_DIR"
    Directory in which to save Observations and Simulations corresponding DataFrames.

    **default**: `"output"`

    Expected type: `str`

??? question "SIM_PROVIDER"
    Name of the simualted data provider.

    **default**: `"HYCOM"`

    Expected type: `str`

??? question "RESULT_OUTPUT_FILE"
    Output filepath. In this file will be saved the result of the comparison metrics.

    **default**: `"comparison_output.txt"`

    Expected type:  `str`
### **Interpolation Parameters**
??? question "TO_INTERPOLATE"
    Names of the variables to interpolate. The names are supposed to be the ones defined in `config/variables.toml` ([`config/default/variables.toml`]({{repo_blob}}/config/default/variables.toml)) by default.)

    **default**: `["TEMP", "PSAL", "DOXY", "PHOS", "NTRA", "SLCA", "CPHL"]`

    Expected type: `list[str]`

??? question "INTERPOLATION_KIND"
    Kind of interpolation for scipy.interpolate.interp1d.

    **default**: `"linear"`

    Expected type: `str`
### **Comparison Parameters**
??? question "VARIABLES_TO_COMPARE"
    Names of the variables to compare.

    **default**: `["PTEMP", "DOXY", "PSAL", "NTRA", "SLCA", "PHOS", "CPHL"`

    Expected type:  `list[str]`
### **Data Selection**
??? question "DATE_MIN"
    Beginning of the data to load (included).

    **default**: `"20150101"`

    Expected type: `str` (respecting the `YYYYMMDD` format)

??? question "DATE_MAX"
    End of the data to load (included).

    **default**: `"20151231"`

    Expected type: `str` (respecting the `YYYYMMDD` format)

??? question "LATITUDE_MIN"
    Minimum latitude boundary for the loaded data (included).

    **default**: `50`

    Expected type: `int`or `float`

??? question "LATITUDE_MAX"
    Maximum latitude boundary for the loaded data (included).

    **default**: `90`

    Expected type: `int`or `float`

??? question "LONGITUDE_MIN"
    Minimum longitude boundary for the loaded data (included).

    **default**: `-180`

    Expected type: `int`or `float`

??? question "LONGITUDE_MAX"
    Maximum longitude boundary for the loaded data (included).

    **default**: `180`

    Expected type: `int`or `float`

??? question "DEPTH_MIN"
    Minimum depth boundary for the loaded data (included).

    **default**: `nan`

    Expected type: `int` or `float`

??? question "DEPTH_MAX"
    Maximum depth boundary for the loaded data (included).

    **default**: `0`

    Expected type: `int` or `float`
### **Others**
??? question "SHOW_MAP"
    Whether to show the map of all compared points or not

    **default**: `false`

    Expected type:  `bool`

??? question "VERBOSE"
    Verbose value, the higher, the more informations. If set to 0 or below: no information displayed. If set to 1: minimal informations displayed. If set to 2: very complete informations displayed. If set to 3 or higher: exhaustive informations displayed.

    **default**: `3`

    Expected type: `int`
## Script Output
When executed, the script will finally output a file named `RESULT_OUTPUT_FILE`.

This is an example of what this file could look like (values are only for illustration purpose and do not reprersent anything):

![output file example]({{fix_url("assets/plots/comparison_output.png")}}){width=750px}

If `SHOW_MAP` is set to `true`, a visualisation of the matched point is also displayed.

This is an example of what this image could look like:

![matching map]({{fix_url("assets/plots/comparison_match.png")}}){width=750px}
