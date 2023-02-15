"""Specific parameters to load CLIVAR-provided data"""


from bgc_data_processing import CONFIG, DEFAULT_VARS, csv_tools, variables

loader = csv_tools.CSVLoader(
    provider_name="CLIVAR",
    dirin=CONFIG["LOADING"]["CLIVAR"]["PATH"],
    category=CONFIG["LOADING"]["CLIVAR"]["CATEGORY"],
    files_pattern="clivar_({years})[0-9][0-9][0-9][0-9]_.*.csv",
    variables=variables.VariablesStorer(
        DEFAULT_VARS["provider"].not_here(),
        DEFAULT_VARS["expocode"].here_as("EXPOCODE"),
        DEFAULT_VARS["date"].here_as("DATE"),
        DEFAULT_VARS["year"].not_here(),
        DEFAULT_VARS["month"].not_here(),
        DEFAULT_VARS["day"].not_here(),
        DEFAULT_VARS["longitude"].here_as("LONGITUDE"),
        DEFAULT_VARS["latitude"].here_as("LATITUDE"),
        DEFAULT_VARS["depth"].here_as("CTDPRS").correct_with(lambda x: -x),
        DEFAULT_VARS["temperature"].here_as("CTDTMP"),
        DEFAULT_VARS["salinity"].here_as("CTDSAL"),
        DEFAULT_VARS["oxygen"].here_as("OXYGEN").correct_with(lambda x: x / 32),
        DEFAULT_VARS["phosphate"].here_as("PHSPHT").remove_when_all_nan(),
        DEFAULT_VARS["nitrate"].here_as("NITRAT").remove_when_all_nan(),
        DEFAULT_VARS["silicate"].here_as("SILCAT").remove_when_all_nan(),
        DEFAULT_VARS["chlorophyll"].not_here(),
    ),
    read_params={
        "low_memory": False,
        "skiprows": [1],
    },
)
