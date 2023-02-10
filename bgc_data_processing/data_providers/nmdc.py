"""Specific parameters to load NMDC-provided data"""

from bgc_data_processing import CONFIG, DEFAULT_VARS, csv_tools, variables

loader = csv_tools.CSVLoader(
    provider_name="NMDC",
    dirin=CONFIG["LOADING"]["NMDC"],
    category=CONFIG["LOADING"]["NMDC"]["CATEGORY"],
    files_pattern="NMDC_1990-2019_all.csv",
    variables=variables.VariablesStorer(
        DEFAULT_VARS["provider"].not_here(),
        DEFAULT_VARS["expocode"].here_as("sdn_cruise"),
        DEFAULT_VARS["date"].here_as("time"),
        DEFAULT_VARS["year"].not_here(),
        DEFAULT_VARS["month"].not_here(),
        DEFAULT_VARS["day"].not_here(),
        DEFAULT_VARS["longitude"].here_as("longitude"),
        DEFAULT_VARS["latitude"].here_as("latitude"),
        DEFAULT_VARS["depth"].here_as("depth").correct_with(lambda x: -x),
        DEFAULT_VARS["temperature"].not_here(),
        DEFAULT_VARS["salinity"].not_here(),
        DEFAULT_VARS["oxygen"].here_as("dow"),
        DEFAULT_VARS["phosphate"].here_as("phosphate").remove_when_all_nan(),
        DEFAULT_VARS["nitrate"].here_as("nitrate").remove_when_all_nan(),
        DEFAULT_VARS["silicate"].here_as("silicate").remove_when_all_nan(),
        DEFAULT_VARS["chlorophyll"].here_as("chla").remove_when_all_nan(),
    ),
    read_params={
        "low_memory": False,
        "skiprows": [1],
    },
)
