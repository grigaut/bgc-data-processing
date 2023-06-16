"""Specific parameters to load CLIVAR-provided data."""

from pathlib import Path

from bgc_data_processing import (
    DEFAULT_VARS,
    PROVIDERS_CONFIG,
    loaders,
    units,
)
from bgc_data_processing.data_structures.variables import VariablesStorer

loader = loaders.from_csv(
    provider_name="CLIVAR",
    dirin=Path(PROVIDERS_CONFIG["CLIVAR"]["PATH"]),
    category=PROVIDERS_CONFIG["CLIVAR"]["CATEGORY"],
    files_pattern="clivar_({years})[0-9][0-9][0-9][0-9]_.*.csv",
    variables=VariablesStorer(
        provider=DEFAULT_VARS["provider"].not_in_file(),
        expocode=DEFAULT_VARS["expocode"].in_file_as("EXPOCODE"),
        date=DEFAULT_VARS["date"].in_file_as("DATE"),
        year=DEFAULT_VARS["year"].not_in_file(),
        month=DEFAULT_VARS["month"].not_in_file(),
        day=DEFAULT_VARS["day"].not_in_file(),
        hour=DEFAULT_VARS["hour"].not_in_file(),
        longitude=DEFAULT_VARS["longitude"].in_file_as("LONGITUDE"),
        latitude=DEFAULT_VARS["latitude"].in_file_as("LATITUDE"),
        depth=DEFAULT_VARS["depth"]
        .in_file_as("CTDPRS")
        .remove_when_nan()
        .correct_with(lambda x: -x),
        temperature=DEFAULT_VARS["temperature"].in_file_as("CTDTMP"),
        salinity=DEFAULT_VARS["salinity"].in_file_as(("CTDSAL", "CTDSAL_FLAG_W", [2])),
        oxygen=DEFAULT_VARS["oxygen"]
        .in_file_as(("OXYGEN", "OXYGEN_FLAG_W", [2]))
        .correct_with(units.convert_umol_by_kg_to_mmol_by_m3),
        phosphate=DEFAULT_VARS["phosphate"]
        .in_file_as(("PHSPHT", "PHSPHT_FLAG_W", [2]))
        .remove_when_all_nan(),
        nitrate=DEFAULT_VARS["nitrate"]
        .in_file_as(("NITRAT", "NITRAT_FLAG_W", [2]))
        .remove_when_all_nan(),
        silicate=DEFAULT_VARS["silicate"]
        .in_file_as(("SILCAT", "SILCAT_FLAG_W", [2]))
        .remove_when_all_nan(),
        chlorophyll=DEFAULT_VARS["chlorophyll"].not_in_file(),
    ),
    read_params={
        "low_memory": False,
        "skiprows": [1],
    },
)
