"""Specific parameters to load GLODAPv2-provided data"""


from bgc_data_processing import CONFIG, DEFAULT_VARS, csv_tools, variables

loader = csv_tools.CSVLoader(
    provider_name="GLODAPv2",
    dirin=CONFIG["LOADING"]["GLODAPv2"]["PATH"],
    category=CONFIG["LOADING"]["GLODAPv2"]["CATEGORY"],
    files_pattern="glodapv2_({years}).csv",
    variables=variables.VariablesStorer(
        DEFAULT_VARS["provider"].not_here(),
        DEFAULT_VARS["expocode"].here_as("cruise"),
        DEFAULT_VARS["date"].not_here(),
        DEFAULT_VARS["year"].here_as("YEAR"),
        DEFAULT_VARS["month"].here_as("MONTH"),
        DEFAULT_VARS["day"].here_as("DAY"),
        DEFAULT_VARS["longitude"].here_as("LONGITUDE"),
        DEFAULT_VARS["latitude"].here_as("LATITUDE"),
        DEFAULT_VARS["depth"].here_as("DEPTH").correct_with(lambda x: -x),
        DEFAULT_VARS["temperature"].here_as("THETA"),
        DEFAULT_VARS["salinity"].here_as("SALNTY"),
        DEFAULT_VARS["oxygen"].here_as("OXYGEN").correct_with(lambda x: x / 32),
        DEFAULT_VARS["phosphate"].here_as("PHSPHT").remove_when_all_nan(),
        DEFAULT_VARS["nitrate"].here_as("NITRAT").remove_when_all_nan(),
        DEFAULT_VARS["silicate"].here_as("SILCAT").remove_when_all_nan(),
        DEFAULT_VARS["chlorophyll"].not_here().remove_when_all_nan(),
    ),
    read_params={
        "low_memory": False,
        "index_col": False,
        "skiprows": [1],
    },
)
