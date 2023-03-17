"""Specific parameters to load GLODAPv2.2019-provided data."""


from bgc_data_processing import DEFAULT_VARS, PROVIDERS_CONFIG, csv_tools, variables

loader = csv_tools.CSVLoader(
    provider_name="GLODAP_2019",
    dirin=PROVIDERS_CONFIG["GLODAP_2019"]["PATH"],
    category=PROVIDERS_CONFIG["GLODAP_2019"]["CATEGORY"],
    files_pattern="glodapv2_({years}).csv",
    variables=variables.VariablesStorer(
        provider=DEFAULT_VARS["provider"].not_in_file(),
        expocode=DEFAULT_VARS["expocode"].in_file_as("cruise"),
        date=DEFAULT_VARS["date"].not_in_file(),
        year=DEFAULT_VARS["year"].in_file_as("YEAR"),
        month=DEFAULT_VARS["month"].in_file_as("MONTH"),
        day=DEFAULT_VARS["day"].in_file_as("DAY"),
        hour=DEFAULT_VARS["hour"].in_file_as("hour"),
        longitude=DEFAULT_VARS["longitude"].in_file_as("LONGITUDE"),
        latitude=DEFAULT_VARS["latitude"].in_file_as("LATITUDE"),
        depth=DEFAULT_VARS["depth"]
        .in_file_as("DEPTH")
        .remove_when_nan()
        .correct_with(lambda x: -x),
        temperature=DEFAULT_VARS["temperature"].in_file_as("THETA"),
        salinity=DEFAULT_VARS["salinity"].in_file_as(("SALNTY", "salinityf", [2])),
        oxygen=DEFAULT_VARS["oxygen"]
        .in_file_as(("OXYGEN", "oxygenf", [2]))
        .correct_with(lambda x: x / 32),
        phosphate=DEFAULT_VARS["phosphate"]
        .in_file_as(("PHSPHT", "phosphatef", [2]))
        .remove_when_all_nan(),
        nitrate=DEFAULT_VARS["nitrate"]
        .in_file_as(("NITRAT", "nitratef", [2]))
        .remove_when_all_nan(),
        silicate=DEFAULT_VARS["silicate"]
        .in_file_as(("SILCAT", "silicatef", [2]))
        .remove_when_all_nan(),
        chlorophyll=DEFAULT_VARS["chlorophyll"].not_in_file().remove_when_all_nan(),
    ),
    read_params={
        "low_memory": False,
        "index_col": False,
        "skiprows": [1],
    },
)
