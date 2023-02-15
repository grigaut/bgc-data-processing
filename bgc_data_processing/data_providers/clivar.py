"""Specific parameters to load CLIVAR-provided data"""


from bgc_data_processing import CONFIG, DEFAULT_VARS, csv_tools, variables

loader = csv_tools.CSVLoader(
    provider_name="CLIVAR",
    dirin=CONFIG["LOADING"]["CLIVAR"]["PATH"],
    category=CONFIG["LOADING"]["CLIVAR"]["CATEGORY"],
    files_pattern="clivar_({years})[0-9][0-9][0-9][0-9]_.*.csv",
    variables=variables.VariablesStorer(
        DEFAULT_VARS["provider"].not_in_file(),
        DEFAULT_VARS["expocode"].in_file_as("EXPOCODE"),
        DEFAULT_VARS["date"].in_file_as("DATE"),
        DEFAULT_VARS["year"].not_in_file(),
        DEFAULT_VARS["month"].not_in_file(),
        DEFAULT_VARS["day"].not_in_file(),
        DEFAULT_VARS["longitude"].in_file_as("LONGITUDE"),
        DEFAULT_VARS["latitude"].in_file_as("LATITUDE"),
        DEFAULT_VARS["depth"].in_file_as("CTDPRS").correct_with(lambda x: -x),
        DEFAULT_VARS["temperature"].in_file_as("CTDTMP"),
        DEFAULT_VARS["salinity"].in_file_as("SALNTY").with_flag("SALNTY_FLAG_W", [2]),
        DEFAULT_VARS["oxygen"]
        .in_file_as("OXYGEN")
        .with_flag("OXYGEN_FLAG_W", [2])
        .correct_with(lambda x: x / 32),
        DEFAULT_VARS["phosphate"]
        .in_file_as("PHSPHT")
        .with_flag("PHSPHT_FLAG_W", [2])
        .remove_when_all_nan(),
        DEFAULT_VARS["nitrate"]
        .in_file_as("NITRAT")
        .with_flag("NITRAT_FLAG_W", [2])
        .remove_when_all_nan(),
        DEFAULT_VARS["silicate"]
        .in_file_as("SILCAT")
        .with_flag("SILCAT_FLAG_W", [2])
        .remove_when_all_nan(),
        DEFAULT_VARS["chlorophyll"].not_in_file(),
    ),
    read_params={
        "low_memory": False,
        "skiprows": [1],
    },
)
