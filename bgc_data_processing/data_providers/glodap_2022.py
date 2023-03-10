"""Specific parameters to load GLODAPv2.2022-provided data."""


from bgc_data_processing import CONFIG, DEFAULT_VARS, csv_tools, variables

loader = csv_tools.CSVLoader(
    provider_name="GLODAP_2022",
    dirin=CONFIG.providers["GLODAP_2022"]["PATH"],
    category=CONFIG.providers["GLODAP_2022"]["CATEGORY"],
    files_pattern="GLODAPv2.2022_all.csv",
    variables=variables.VariablesStorer(
        DEFAULT_VARS["provider"].not_in_file(),
        DEFAULT_VARS["expocode"]
        .in_file_as("G2expocode")
        .correct_with(lambda x: x[:-8]),
        DEFAULT_VARS["date"].not_in_file(),
        DEFAULT_VARS["year"].in_file_as("G2year"),
        DEFAULT_VARS["month"].in_file_as("G2month"),
        DEFAULT_VARS["day"].in_file_as("G2day"),
        DEFAULT_VARS["hour"].in_file_as("G2hour"),
        DEFAULT_VARS["longitude"].in_file_as("G2longitude"),
        DEFAULT_VARS["latitude"].in_file_as("G2latitude"),
        DEFAULT_VARS["depth"]
        .in_file_as("G2depth")
        .remove_when_nan()
        .correct_with(lambda x: -x),
        DEFAULT_VARS["temperature"].in_file_as("G2temperature"),
        DEFAULT_VARS["salinity"].in_file_as(("G2salinity", "G2salinityf", [2])),
        DEFAULT_VARS["oxygen"]
        .in_file_as(("G2oxygen", "G2oxygenf", [2]))
        .correct_with(lambda x: x / 32),
        DEFAULT_VARS["phosphate"]
        .in_file_as(("G2phosphate", "G2phosphatef", [2]))
        .remove_when_all_nan(),
        DEFAULT_VARS["nitrate"]
        .in_file_as(("G2nitrate", "G2nitratef", [2]))
        .remove_when_all_nan(),
        DEFAULT_VARS["silicate"]
        .in_file_as(("G2silicate", "G2silicatef", [2]))
        .remove_when_all_nan(),
        DEFAULT_VARS["chlorophyll"].not_in_file().remove_when_all_nan(),
    ),
    read_params={
        "low_memory": False,
        "index_col": False,
        "na_values": -9999,
    },
)
