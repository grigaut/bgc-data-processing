"""Specific parameters to load GLODAPv2-provided data"""


from bgc_data_processing import CONFIG, DEFAULT_VARS, csv_tools, variables

loader = csv_tools.CSVLoader(
    provider_name="GLODAPv2",
    dirin=CONFIG["LOADING"]["GLODAPv2"],
    files_pattern="glodapv2_({years}).csv",
    variables=variables.VariablesStorer(
        DEFAULT_VARS["provider"].not_here(),
        DEFAULT_VARS["expocode"].here_as("expocode"),
        DEFAULT_VARS["date"].not_here(),
        DEFAULT_VARS["year"].here_as("year"),
        DEFAULT_VARS["month"].here_as("month"),
        DEFAULT_VARS["day"].here_as("day"),
        DEFAULT_VARS["longitude"].here_as("longitude"),
        DEFAULT_VARS["latitude"].here_as("latitude"),
        DEFAULT_VARS["depth"].here_as("depth").correct_with(lambda x: -x),
        DEFAULT_VARS["temperature"].here_as("theta"),
        DEFAULT_VARS["salinity"].here_as("salnty"),
        DEFAULT_VARS["oxygen"].here_as("oxygen").correct_with(lambda x: x / 32),
        DEFAULT_VARS["phosphate"].here_as("phspht").remove_when_all_nan(),
        DEFAULT_VARS["nitrate"].here_as("nitrat").remove_when_all_nan(),
        DEFAULT_VARS["silicate"].here_as("silcat").remove_when_all_nan(),
        DEFAULT_VARS["chlorophyll"].not_here().remove_when_all_nan(),
    ),
    read_params={
        "low_memory": False,
        "index_col": False,
        "skiprows": [1],
    },
)
