"""Specific parameters to load Argo-provided data"""

import numpy as np
from bgc_data_processing import CONFIG, DEFAULT_VARS, netcdf_tools, variables

loader = netcdf_tools.NetCDFLoader(
    provider_name="ARGO",
    dirin=CONFIG.providers["ARGO"]["PATH"],
    category=CONFIG.providers["ARGO"]["CATEGORY"],
    files_pattern=".*.nc",
    variables=variables.VariablesStorer(
        # DEFAULT_VARS["provider"].not_in_file(),
        DEFAULT_VARS["expocode"].not_in_file(),
        DEFAULT_VARS["date"].in_file_as("TIME"),
        DEFAULT_VARS["year"].not_in_file(),
        DEFAULT_VARS["month"].not_in_file(),
        DEFAULT_VARS["day"].not_in_file(),
        DEFAULT_VARS["longitude"].in_file_as("LONGITUDE"),
        DEFAULT_VARS["latitude"].in_file_as("LATITUDE"),
        DEFAULT_VARS["depth"]
        .in_file_as("PRES_ADJUSTED")
        .remove_when_nan()
        .correct_with(lambda x: -x),
        DEFAULT_VARS["temperature"].in_file_as("TEMP_ADJUSTED", "TEMP"),
        DEFAULT_VARS["salinity"].in_file_as("PSAL_ADJUSTED", "PSAl"),
        DEFAULT_VARS["oxygen"].in_file_as("DOX2_ADJUSTED", "DOX2"),
        DEFAULT_VARS["phosphate"].not_in_file(),
        DEFAULT_VARS["nitrate"].not_in_file(),
        DEFAULT_VARS["silicate"].not_in_file(),
        DEFAULT_VARS["chlorophyll"]
        .in_file_as(
            ("CPHL_ADJUSTED", "CPHL_ADJUSTED_QC", [1]),
            ("CPHL", "CPHL_QC", [1]),
        )
        .remove_when_all_nan()
        .correct_with(lambda x: np.nan if x < 0.01 else x),
    ),
)
