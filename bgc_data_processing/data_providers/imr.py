"""Specific parameters to load IMR-provided data"""


from bgc_data_processing import CONFIG, DEFAULT_VARS, csv_tools, variables

loader = csv_tools.CSVLoader(
    provider_name="IMR",
    dirin=CONFIG["LOADING"]["IMR"]["PATH"],
    files_pattern="imr_({years}).csv",
    variables=variables.VariablesStorer(
        DEFAULT_VARS["provider"].not_here(),
        DEFAULT_VARS["expocode"].here_as("expocode"),
        DEFAULT_VARS["date"].not_here(),
        DEFAULT_VARS["year"].here_as("year"),
        DEFAULT_VARS["month"].here_as("month"),
        DEFAULT_VARS["day"].here_as("day"),
        DEFAULT_VARS["longitude"].here_as("long"),
        DEFAULT_VARS["latitude"].here_as("lati"),
        DEFAULT_VARS["depth"].here_as("depth"),
        DEFAULT_VARS["temperature"].here_as("temp"),
        DEFAULT_VARS["salinity"].here_as("saln."),
        DEFAULT_VARS["oxygen"].here_as("oxygen", "doxy"),
        DEFAULT_VARS["phosphate"].here_as("phosphate").remove_when_all_nan(),
        DEFAULT_VARS["nitrate"].here_as("nitrate").remove_when_all_nan(),
        DEFAULT_VARS["silicate"].here_as("silicate").remove_when_all_nan(),
        DEFAULT_VARS["chlorophyll"].here_as("chl.").remove_when_all_nan(),
    ),
    read_params={
        "low_memory": False,
        "delim_whitespace": True,
        "skiprows": [1],
    },
)
