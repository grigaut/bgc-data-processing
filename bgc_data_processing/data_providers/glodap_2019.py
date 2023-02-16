"""Specific parameters to load GLODAPv2.2019-provided data"""


from bgc_data_processing import CONFIG, DEFAULT_VARS, csv_tools, variables

loader = csv_tools.CSVLoader(
    provider_name="GLODAP_2019",
    dirin=CONFIG["LOADING"]["GLODAP_2019"]["PATH"],
    category=CONFIG["LOADING"]["GLODAP_2019"]["CATEGORY"],
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
        DEFAULT_VARS["salinity"].in_file_as(("SALNTY", "salinityf", [2])),
        DEFAULT_VARS["oxygen"]
        .in_file_as(("OXYGEN", "oxygenf", [2]))
        .correct_with(lambda x: x / 32),
        DEFAULT_VARS["phosphate"]
        .in_file_as(("PHSPHT", "phosphatef", [2]))
        .remove_when_all_nan(),
        DEFAULT_VARS["nitrate"]
        .in_file_as(("NITRAT", "nitratef", [2]))
        .remove_when_all_nan(),
        DEFAULT_VARS["silicate"]
        .in_file_as(("SILCAT", "silicatef", [2]))
        .remove_when_all_nan(),
        DEFAULT_VARS["chlorophyll"].not_in_file().remove_when_all_nan(),
    ),
    read_params={
        "low_memory": False,
        "index_col": False,
        "skiprows": [1],
    },
)
