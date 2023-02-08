"""Specific parameters to load ICES-provided data"""


from bgc_data_processing import CONFIG, DEFAULT_VARS, csv_tools, variables

loader = csv_tools.CSVLoader(
    provider_name="ICES",
    dirin=CONFIG["LOADING"]["ICES"],
    files_pattern="ices_({years}).csv",
    variables=variables.VariablesStorer(
        DEFAULT_VARS["provider"].not_here(),
        DEFAULT_VARS["expocode"].here_as("cruise"),
        DEFAULT_VARS["date"].here_as("date"),
        DEFAULT_VARS["year"].not_here(),
        DEFAULT_VARS["month"].not_here(),
        DEFAULT_VARS["day"].not_here(),
        DEFAULT_VARS["longitude"].here_as("longitude"),
        DEFAULT_VARS["latitude"].here_as("latitude"),
        DEFAULT_VARS["depth"].here_as("depth").correct_with(lambda x: -x),
        DEFAULT_VARS["temperature"].here_as("ctdtmp"),
        DEFAULT_VARS["salinity"].here_as("ctdsal"),
        DEFAULT_VARS["oxygen"].here_as("doxy"),
        DEFAULT_VARS["phosphate"].here_as("phos").remove_when_all_nan(),
        DEFAULT_VARS["nitrate"].here_as("ntra").remove_when_all_nan(),
        DEFAULT_VARS["silicate"].here_as("slca").remove_when_all_nan(),
        DEFAULT_VARS["chlorophyll"].here_as("cphl").remove_when_all_nan(),
    ),
    read_params={
        "low_memory": False,
        "skiprows": [1],
    },
)
