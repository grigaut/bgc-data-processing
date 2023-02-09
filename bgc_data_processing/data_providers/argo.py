"""Specific parameters to load Argo-provided data"""

import numpy as np
from bgc_data_processing import CONFIG, DEFAULT_VARS, netcdf_tools, variables

loader = netcdf_tools.NetCDFLoader(
    provider_name="ARGO",
    dirin=CONFIG["LOADING"]["ARGO"]["PATH"],
    files_pattern=".*.nc",
    variables=variables.VariablesStorer(
        # DEFAULT_VARS["provider"].not_here(),
        DEFAULT_VARS["expocode"].not_here(),
        DEFAULT_VARS["date"].here_as("TIME"),
        DEFAULT_VARS["year"].not_here(),
        DEFAULT_VARS["month"].not_here(),
        DEFAULT_VARS["day"].not_here(),
        DEFAULT_VARS["longitude"].here_as("LONGITUDE"),
        DEFAULT_VARS["latitude"].here_as("LATITUDE"),
        DEFAULT_VARS["depth"]
        .here_as("PRES_ADJUSTED")
        .remove_when_nan()
        .correct_with(lambda x: -x),
        DEFAULT_VARS["temperature"].here_as("TEMP_ADJUSTED", "TEMP"),
        DEFAULT_VARS["salinity"].here_as("PSAL_ADJUSTED", "PSAl"),
        DEFAULT_VARS["oxygen"].here_as("DOX2_ADJUSTED", "DOX2"),
        DEFAULT_VARS["phosphate"].not_here(),
        DEFAULT_VARS["nitrate"].not_here(),
        DEFAULT_VARS["silicate"].not_here(),
        DEFAULT_VARS["chlorophyll"]
        .here_as("CPHL_ADJUSTED", "CPHL")
        .remove_when_all_nan()
        .correct_with(lambda x: np.nan if x < 0.01 else x),
    ),
)
