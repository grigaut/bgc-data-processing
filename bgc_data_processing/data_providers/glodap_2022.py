"""Specific parameters to load GLODAPv2.2022-provided data"""


from bgc_data_processing import CONFIG, DEFAULT_VARS, csv_tools, variables

loader = csv_tools.CSVLoader(
    provider_name="GLODAP_2022",
    dirin=CONFIG["LOADING"]["GLODAP_2022"]["PATH"],
    category=CONFIG["LOADING"]["GLODAP_2022"]["CATEGORY"],
    files_pattern="GLODAPv2.2022_all.csv",
    variables=variables.VariablesStorer(
        DEFAULT_VARS["provider"].not_here(),
        DEFAULT_VARS["expocode"].here_as("G2expocode"),
        DEFAULT_VARS["date"].not_here(),
        DEFAULT_VARS["year"].here_as("G2year"),
        DEFAULT_VARS["month"].here_as("G2month"),
        DEFAULT_VARS["day"].here_as("G2day"),
        DEFAULT_VARS["longitude"].here_as("G2longitude"),
        DEFAULT_VARS["latitude"].here_as("G2latitude"),
        DEFAULT_VARS["depth"].here_as("G2depth").correct_with(lambda x: -x),
        DEFAULT_VARS["temperature"].here_as("G2temperature"),
        DEFAULT_VARS["salinity"].here_as("G2salinity"),
        DEFAULT_VARS["oxygen"].here_as("G2oxygen").correct_with(lambda x: x / 32),
        DEFAULT_VARS["phosphate"].here_as("G2phosphate").remove_when_all_nan(),
        DEFAULT_VARS["nitrate"].here_as("G2nitrate").remove_when_all_nan(),
        DEFAULT_VARS["silicate"].here_as("G2silicate").remove_when_all_nan(),
        DEFAULT_VARS["chlorophyll"].not_here().remove_when_all_nan(),
    ),
    read_params={
        "low_memory": False,
        "index_col": False,
        "na_values": -9999,
    },
)
