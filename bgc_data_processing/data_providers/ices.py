"""Specific parameters to load ICES-provided data"""


from bgc_data_processing import CONFIG, DEFAULT_VARS, csv_tools, variables

loader = csv_tools.CSVLoader(
    provider_name="ICES",
    dirin=CONFIG["LOADING"]["ICES"]["PATH"],
    category=CONFIG["LOADING"]["ICES"]["CATEGORY"],
    files_pattern="ices_({years}).csv",
    variables=variables.VariablesStorer(
        DEFAULT_VARS["provider"].not_in_file(),
        DEFAULT_VARS["expocode"].in_file_as("Cruise"),
        DEFAULT_VARS["date"].in_file_as("DATE"),
        DEFAULT_VARS["year"].not_in_file(),
        DEFAULT_VARS["month"].not_in_file(),
        DEFAULT_VARS["day"].not_in_file(),
        DEFAULT_VARS["longitude"].in_file_as("LONGITUDE"),
        DEFAULT_VARS["latitude"].in_file_as("LATITUDE"),
        DEFAULT_VARS["depth"].in_file_as("DEPTH").correct_with(lambda x: -x),
        DEFAULT_VARS["temperature"].in_file_as("CTDTMP"),
        DEFAULT_VARS["salinity"].in_file_as("CTDSAL"),
        DEFAULT_VARS["oxygen"].in_file_as("DOXY"),
        DEFAULT_VARS["phosphate"].in_file_as("PHOS").remove_when_all_nan(),
        DEFAULT_VARS["nitrate"].in_file_as("NTRA").remove_when_all_nan(),
        DEFAULT_VARS["silicate"].in_file_as("SLCA").remove_when_all_nan(),
        DEFAULT_VARS["chlorophyll"].in_file_as("CPHL").remove_when_all_nan(),
    ),
    read_params={
        "low_memory": False,
        "skiprows": [1],
    },
)
