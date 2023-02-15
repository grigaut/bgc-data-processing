"""Specific parameters to load IMR-provided data"""


from bgc_data_processing import CONFIG, DEFAULT_VARS, csv_tools, variables

loader = csv_tools.CSVLoader(
    provider_name="IMR",
    dirin=CONFIG["LOADING"]["IMR"]["PATH"],
    category=CONFIG["LOADING"]["IMR"]["CATEGORY"],
    files_pattern="imr_({years}).csv",
    variables=variables.VariablesStorer(
        DEFAULT_VARS["provider"].not_here(),
        DEFAULT_VARS["expocode"].not_here(),
        DEFAULT_VARS["date"].not_here(),
        DEFAULT_VARS["year"].here_as("Year"),
        DEFAULT_VARS["month"].here_as("Month"),
        DEFAULT_VARS["day"].here_as("Day"),
        DEFAULT_VARS["longitude"].here_as("Long"),
        DEFAULT_VARS["latitude"].here_as("Lati"),
        DEFAULT_VARS["depth"].here_as("Depth"),
        DEFAULT_VARS["temperature"].here_as("Temp"),
        DEFAULT_VARS["salinity"].here_as("Saln."),
        DEFAULT_VARS["oxygen"].here_as("Oxygen", "Doxy"),
        DEFAULT_VARS["phosphate"].here_as("Phosphate").remove_when_all_nan(),
        DEFAULT_VARS["nitrate"].here_as("Nitrate").remove_when_all_nan(),
        DEFAULT_VARS["silicate"].here_as("Silicate").remove_when_all_nan(),
        DEFAULT_VARS["chlorophyll"].here_as("Chl.").remove_when_all_nan(),
    ),
    read_params={
        "low_memory": False,
        "delim_whitespace": True,
        "skiprows": [1],
    },
)
