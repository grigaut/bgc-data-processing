"""Specific parameters to load IMR-provided data"""


from bgc_data_processing import CONFIG, DEFAULT_VARS, csv_tools, variables

loader = csv_tools.CSVLoader(
    provider_name="IMR",
    dirin=CONFIG["LOADING"]["IMR"]["PATH"],
    category=CONFIG["LOADING"]["IMR"]["CATEGORY"],
    files_pattern="imr_({years}).csv",
    variables=variables.VariablesStorer(
        DEFAULT_VARS["provider"].not_in_file(),
        DEFAULT_VARS["expocode"].not_in_file(),
        DEFAULT_VARS["date"].not_in_file(),
        DEFAULT_VARS["year"].in_file_as("Year"),
        DEFAULT_VARS["month"].in_file_as("Month"),
        DEFAULT_VARS["day"].in_file_as("Day"),
        DEFAULT_VARS["longitude"].in_file_as("Long"),
        DEFAULT_VARS["latitude"].in_file_as("Lati"),
        DEFAULT_VARS["depth"].in_file_as("Depth"),
        DEFAULT_VARS["temperature"].in_file_as("Temp"),
        DEFAULT_VARS["salinity"].in_file_as("Saln."),
        DEFAULT_VARS["oxygen"].in_file_as("Oxygen", "Doxy"),
        DEFAULT_VARS["phosphate"].in_file_as("Phosphate").remove_when_all_nan(),
        DEFAULT_VARS["nitrate"].in_file_as("Nitrate").remove_when_all_nan(),
        DEFAULT_VARS["silicate"].in_file_as("Silicate").remove_when_all_nan(),
        DEFAULT_VARS["chlorophyll"].in_file_as("Chl.").remove_when_all_nan(),
    ),
    read_params={
        "low_memory": False,
        "delim_whitespace": True,
        "skiprows": [1],
    },
)
