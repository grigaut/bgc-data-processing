"""Specific parameters to load ICES-provided data"""


from bgc_data_processing import CONFIG, DEFAULT_VARS, csv_tools, variables

loader = csv_tools.CSVLoader(
    provider_name="ICES",
    dirin=CONFIG["LOADING"]["ICES"]["PATH"],
    category=CONFIG["LOADING"]["ICES"]["CATEGORY"],
    files_pattern="ices_({years}).csv",
    variables=variables.VariablesStorer(
        DEFAULT_VARS["provider"].not_here(),
        DEFAULT_VARS["expocode"].here_as("Cruise"),
        DEFAULT_VARS["date"].here_as("DATE"),
        DEFAULT_VARS["year"].not_here(),
        DEFAULT_VARS["month"].not_here(),
        DEFAULT_VARS["day"].not_here(),
        DEFAULT_VARS["longitude"].here_as("LONGITUDE"),
        DEFAULT_VARS["latitude"].here_as("LATITUDE"),
        DEFAULT_VARS["depth"].here_as("DEPTH").correct_with(lambda x: -x),
        DEFAULT_VARS["temperature"].here_as("CTDTMP"),
        DEFAULT_VARS["salinity"].here_as("CTDSAL"),
        DEFAULT_VARS["oxygen"].here_as("DOXY"),
        DEFAULT_VARS["phosphate"].here_as("PHOS").remove_when_all_nan(),
        DEFAULT_VARS["nitrate"].here_as("NTRA").remove_when_all_nan(),
        DEFAULT_VARS["silicate"].here_as("SLCA").remove_when_all_nan(),
        DEFAULT_VARS["chlorophyll"].here_as("CPHL").remove_when_all_nan(),
    ),
    read_params={
        "low_memory": False,
        "skiprows": [1],
    },
)
