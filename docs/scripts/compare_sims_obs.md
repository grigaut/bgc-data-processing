# Simulations-Observations Comparison

`make run-compare-sims-obs`
## Summary

This scripts reads simulated and observed .

## Configuration

The configuration file for this script is `config/compare_sims_obs.toml` (based on [`config/default/compare_sims_obs.toml`]({{repo_blob}}/config/default/compare_sims_obs.toml)). All the parameters and their functionality are listed below:
### **Input/Output**

??? question "OBSERVATIONS_FILE"

    Path to the file with the observations values.

    **default**: `"output/observations.txt"`

    Expected type:  `str`

??? question "SIMULATIONS_FILE"

    Path to the file with the simulations values.

    **default**: `"output/simulations.txt"`

    Expected type:  `str`

??? question "VARIABLES_TO_COMPARE"

    Names of the variables to compare.

    **default**: `["TEMP", "PSAL", "PTEMP"]`

    Expected type:  `list[str]`

??? question "SHOW_MAP"

    Whether to show the map of all compared points or not

    **default**: `true`

    Expected type:  `bool`
