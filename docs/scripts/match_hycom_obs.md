# Matching Simulations to Observations

`make run-match-hycom-obs`
## Summary

This scripts reads data from a folder and matches simulated points from a given provider to the observations locations.

## Configuration

The configuration file for this script is `config/match_hycom_obs.toml` (based on [`config/default/match_hycom_obs.toml`]({{repo_blob}}/config/default/match_hycom_obs.toml)). All the parameters and their functionality are listed below:
### **Input/Output**
??? question "LOADING_DIR"

    Directory from which to load data.

    **default**: `"bgc_data"`

    Expected type: `str`

??? question "SAVING_DIR"

    Directory in which to save reuslting DataFrames.

    **default**: `"output"`

    Expected type: `str`

??? question "SIM_PROVIDER"

    Name of the Simulated points provider.

    **default**: `"HYCOM"`

    Expected type: `str`

??? question "TO_INTERPOLATE"

    Labels of the variables to interpolate.

    **default**: `["TEMP","PSAL"]`

    Expected type: list[str]

??? question "INTERPOLATION_KIND"

    Kind of interpolation for scipy.interpolate.interp1d.

    **default**: `"linear"`

    Expected type: str
