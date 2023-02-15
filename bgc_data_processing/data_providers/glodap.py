"""Specific parameters to load GLODAPv2-provided data"""


from bgc_data_processing import CONFIG, DEFAULT_VARS, csv_tools, variables

loader = csv_tools.CSVLoader(
    provider_name="GLODAPv2",
    dirin=CONFIG["LOADING"]["GLODAPv2"]["PATH"],
    category=CONFIG["LOADING"]["GLODAPv2"]["CATEGORY"],
    files_pattern="glodapv2_({years}).csv",
    variables=variables.VariablesStorer(
        DEFAULT_VARS["provider"].not_in_file(),
        DEFAULT_VARS["expocode"].in_file_as("cruise"),
        DEFAULT_VARS["date"].not_in_file(),
        DEFAULT_VARS["year"].in_file_as("YEAR"),
        DEFAULT_VARS["month"].in_file_as("MONTH"),
        DEFAULT_VARS["day"].in_file_as("DAY"),
        DEFAULT_VARS["longitude"].in_file_as("LONGITUDE"),
        DEFAULT_VARS["latitude"].in_file_as("LATITUDE"),
        DEFAULT_VARS["depth"].in_file_as("DEPTH").correct_with(lambda x: -x),
        DEFAULT_VARS["temperature"].in_file_as("THETA"),
        DEFAULT_VARS["salinity"].in_file_as("SALNTY"),
        DEFAULT_VARS["oxygen"].in_file_as("OXYGEN").correct_with(lambda x: x / 32),
        DEFAULT_VARS["phosphate"].in_file_as("PHSPHT").remove_when_all_nan(),
        DEFAULT_VARS["nitrate"].in_file_as("NITRAT").remove_when_all_nan(),
        DEFAULT_VARS["silicate"].in_file_as("SILCAT").remove_when_all_nan(),
        DEFAULT_VARS["chlorophyll"].not_in_file().remove_when_all_nan(),
    ),
    read_params={
        "low_memory": False,
        "index_col": False,
        "skiprows": [1],
    },
)
