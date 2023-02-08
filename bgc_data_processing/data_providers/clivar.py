"""Specific parameters to load CLIVAR-provided data"""


from bgc_data_processing import CONFIG, DEFAULT_VARS, csv_tools, variables

loader = csv_tools.CSVLoader(
    provider_name="CLIVAR",
    dirin=CONFIG["LOADING"]["CLIVAR"],
    files_pattern="clivar_({years})[0-9][0-9][0-9][0-9]_.*.csv",
    variables=variables.VariablesStorer(
        DEFAULT_VARS["provider"].not_here(),
        DEFAULT_VARS["expocode"].here_as("expocode"),
        DEFAULT_VARS["date"].here_as("date"),
        DEFAULT_VARS["year"].here_as("year"),
        DEFAULT_VARS["month"].here_as("month"),
        DEFAULT_VARS["day"].here_as("day"),
        DEFAULT_VARS["longitude"].here_as("longitude"),
        DEFAULT_VARS["latitude"].here_as("latitude"),
        DEFAULT_VARS["depth"].here_as("ctdprs").correct_with(lambda x: -x),
        DEFAULT_VARS["temperature"].here_as("ctdtmp"),
        DEFAULT_VARS["salinity"].here_as("ctdsal"),
        DEFAULT_VARS["oxygen"].here_as("oxygen").correct_with(lambda x: x / 32),
        DEFAULT_VARS["phosphate"].here_as("phspht").remove_when_all_nan(),
        DEFAULT_VARS["nitrate"].here_as("nitrat").remove_when_all_nan(),
        DEFAULT_VARS["silicate"].here_as("silcat").remove_when_all_nan(),
        DEFAULT_VARS["chlorophyll"].here_as("cphl").remove_when_all_nan(),
    ),
    read_params={
        "low_memory": False,
        "skiprows": [1],
    },
)
