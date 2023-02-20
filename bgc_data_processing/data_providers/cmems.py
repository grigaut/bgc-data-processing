"""Specific parameters to load Argo-provided data"""

from bgc_data_processing import CONFIG, DEFAULT_VARS, netcdf_tools, variables

loader = netcdf_tools.NetCDFLoader(
    provider_name="CMEMS",
    dirin=CONFIG["LOADING"]["CMEMS"]["PATH"],
    category=CONFIG["LOADING"]["CMEMS"]["CATEGORY"],
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
        .in_file_as("DEPH", "PRES")
        .remove_when_nan()
        .correct_with(lambda x: -x),
        DEFAULT_VARS["temperature"].in_file_as("TEMP"),
        DEFAULT_VARS["salinity"].in_file_as("PSAL"),
        DEFAULT_VARS["oxygen"].in_file_as("DOX1"),
        DEFAULT_VARS["phosphate"]
        .in_file_as(("PHOS", "PHOS_QC", [1]))
        .remove_when_all_nan(),
        DEFAULT_VARS["nitrate"]
        .in_file_as(("NTRA", "NTRA_QC", [1]))
        .remove_when_all_nan(),
        DEFAULT_VARS["silicate"]
        .in_file_as(("SLCA", "SLCA_QC", [1]))
        .remove_when_all_nan(),
        DEFAULT_VARS["chlorophyll"]
        .in_file_as(("CPHL", "CPHL_QC", [1]))
        .remove_when_all_nan(),
    ),
)
