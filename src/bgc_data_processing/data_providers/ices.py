"""Specific parameters to load ICES-provided data."""

from pathlib import Path

from bgc_data_processing import DEFAULT_VARS, PROVIDERS_CONFIG, csv_tools, variables

loader = csv_tools.CSVLoader(
    provider_name="ICES",
    dirin=Path(PROVIDERS_CONFIG["ICES"]["PATH"]),
    category=PROVIDERS_CONFIG["ICES"]["CATEGORY"],
    files_pattern="ices_({years}).csv",
    variables=variables.VariablesStorer(
        provider=DEFAULT_VARS["provider"].not_in_file(),
        expocode=DEFAULT_VARS["expocode"].in_file_as("Cruise"),
        date=DEFAULT_VARS["date"].in_file_as("DATE"),
        year=DEFAULT_VARS["year"].not_in_file(),
        month=DEFAULT_VARS["month"].not_in_file(),
        day=DEFAULT_VARS["day"].not_in_file(),
        hour=DEFAULT_VARS["hour"].not_in_file(),
        longitude=DEFAULT_VARS["longitude"].in_file_as("LONGITUDE"),
        latitude=DEFAULT_VARS["latitude"].in_file_as("LATITUDE"),
        depth=DEFAULT_VARS["depth"]
        .in_file_as("DEPTH")
        .remove_when_nan()
        .correct_with(lambda x: -x),
        temperature=DEFAULT_VARS["temperature"].in_file_as("CTDTMP"),
        salinity=DEFAULT_VARS["salinity"].in_file_as("CTDSAL"),
        oxygen=DEFAULT_VARS["oxygen"].in_file_as("DOXY"),
        phosphate=DEFAULT_VARS["phosphate"].in_file_as("PHOS").remove_when_all_nan(),
        nitrate=DEFAULT_VARS["nitrate"].in_file_as("NTRA").remove_when_all_nan(),
        silicate=DEFAULT_VARS["silicate"].in_file_as("SLCA").remove_when_all_nan(),
        chlorophyll=DEFAULT_VARS["chlorophyll"]
        .in_file_as("CPHL")
        .remove_when_all_nan(),
    ),
    read_params={
        "low_memory": False,
        "skiprows": [1],
    },
)
