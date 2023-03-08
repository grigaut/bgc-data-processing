"""Specific parameters to load NMDC-provided data."""

from bgc_data_processing import CONFIG, DEFAULT_VARS, csv_tools, variables

loader = csv_tools.CSVLoader(
    provider_name="NMDC",
    dirin=CONFIG.providers["NMDC"]["PATH"],
    category=CONFIG.providers["NMDC"]["CATEGORY"],
    files_pattern="NMDC_1990-2019_all.csv",
    variables=variables.VariablesStorer(
        DEFAULT_VARS["provider"].not_in_file(),
        DEFAULT_VARS["expocode"].in_file_as("SDN_CRUISE"),
        DEFAULT_VARS["date"].in_file_as("Time"),
        DEFAULT_VARS["year"].not_in_file(),
        DEFAULT_VARS["month"].not_in_file(),
        DEFAULT_VARS["day"].not_in_file(),
        DEFAULT_VARS["longitude"].in_file_as("Longitude"),
        DEFAULT_VARS["latitude"].in_file_as("Latitude"),
        DEFAULT_VARS["depth"].in_file_as("depth").correct_with(lambda x: -x),
        DEFAULT_VARS["temperature"].not_in_file(),
        DEFAULT_VARS["salinity"].not_in_file(),
        DEFAULT_VARS["oxygen"].in_file_as("DOW"),
        DEFAULT_VARS["phosphate"]
        .in_file_as(("Phosphate", "Phosphate_SEADATANET_QC", [1]))
        .remove_when_all_nan(),
        DEFAULT_VARS["nitrate"]
        .in_file_as(("Nitrate", "Nitrate_SEADATANET_QC", [1]))
        .remove_when_all_nan(),
        DEFAULT_VARS["silicate"]
        .in_file_as(("Silicate", "Silicate_SEADATANET_QC", [1]))
        .remove_when_all_nan(),
        DEFAULT_VARS["chlorophyll"]
        .in_file_as(("ChlA", "ChlA_SEADATANET_QC", [1]))
        .remove_when_all_nan(),
    ),
    read_params={
        "low_memory": False,
        "skiprows": [1],
    },
)
