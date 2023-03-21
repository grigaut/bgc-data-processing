"""Specific parameters to load CMEMS-provided data."""

from bgc_data_processing import DEFAULT_VARS, PROVIDERS_CONFIG, netcdf_tools, variables

loader = netcdf_tools.NetCDFLoader(
    provider_name="CMEMS",
    dirin=PROVIDERS_CONFIG["CMEMS"]["PATH"],
    category=PROVIDERS_CONFIG["CMEMS"]["CATEGORY"],
    files_pattern=".*.nc",
    variables=variables.VariablesStorer(
        provider=DEFAULT_VARS["provider"].not_in_file(),
        expocode=DEFAULT_VARS["expocode"].not_in_file(),
        date=DEFAULT_VARS["date"].in_file_as("TIME"),
        year=DEFAULT_VARS["year"].not_in_file(),
        month=DEFAULT_VARS["month"].not_in_file(),
        day=DEFAULT_VARS["day"].not_in_file(),
        hour=DEFAULT_VARS["hour"].not_in_file(),
        longitude=DEFAULT_VARS["longitude"].in_file_as("LONGITUDE"),
        latitude=DEFAULT_VARS["latitude"].in_file_as("LATITUDE"),
        depth=DEFAULT_VARS["depth"]
        .in_file_as("DEPH", "PRES")
        .remove_when_nan()
        .correct_with(lambda x: -x if x > 0 else x),
        temperature=DEFAULT_VARS["temperature"].in_file_as("TEMP"),
        salinity=DEFAULT_VARS["salinity"].in_file_as("PSAL"),
        oxygen=DEFAULT_VARS["oxygen"].in_file_as("DOX1"),
        phosphate=DEFAULT_VARS["phosphate"]
        .in_file_as(("PHOS", "PHOS_QC", [1]))
        .remove_when_all_nan(),
        nitrate=DEFAULT_VARS["nitrate"]
        .in_file_as(("NTRA", "NTRA_QC", [1]))
        .remove_when_all_nan(),
        silicate=DEFAULT_VARS["silicate"]
        .in_file_as(("SLCA", "SLCA_QC", [1]))
        .remove_when_all_nan(),
        chlorophyll=DEFAULT_VARS["chlorophyll"]
        .in_file_as(("CPHL", "CPHL_QC", [1]))
        .remove_when_all_nan(),
    ),
)
