"""Specific parameters to load IMR-provided data."""

from pathlib import Path

from bgc_data_processing import (
    DEFAULT_VARS,
    PROVIDERS_CONFIG,
    loaders,
    units,
    variables,
)

loader = loaders.from_csv(
    provider_name="IMR",
    dirin=Path(PROVIDERS_CONFIG["IMR"]["PATH"]),
    category=PROVIDERS_CONFIG["IMR"]["CATEGORY"],
    files_pattern="imr_({years}).csv",
    variables=variables.VariablesStorer(
        provider=DEFAULT_VARS["provider"].not_in_file(),
        expocode=DEFAULT_VARS["expocode"].not_in_file(),
        date=DEFAULT_VARS["date"].not_in_file(),
        year=DEFAULT_VARS["year"].in_file_as("Year"),
        month=DEFAULT_VARS["month"].in_file_as("Month"),
        day=DEFAULT_VARS["day"].in_file_as("Day"),
        hour=DEFAULT_VARS["hour"].not_in_file(),
        longitude=DEFAULT_VARS["longitude"].in_file_as("Long"),
        latitude=DEFAULT_VARS["latitude"].in_file_as("Lati"),
        depth=DEFAULT_VARS["depth"].in_file_as("Depth").remove_when_nan(),
        temperature=DEFAULT_VARS["temperature"].in_file_as("Temp"),
        salinity=DEFAULT_VARS["salinity"].in_file_as("Saln."),
        oxygen=DEFAULT_VARS["oxygen"]
        .in_file_as("Oxygen", "Doxy")
        .correct_with(units.convert_doxy_ml_by_l_to_mmol_by_m3),
        phosphate=DEFAULT_VARS["phosphate"]
        .in_file_as("Phosphate")
        .remove_when_all_nan(),
        nitrate=DEFAULT_VARS["nitrate"].in_file_as("Nitrate").remove_when_all_nan(),
        silicate=DEFAULT_VARS["silicate"].in_file_as("Silicate").remove_when_all_nan(),
        chlorophyll=DEFAULT_VARS["chlorophyll"]
        .in_file_as("Chl.")
        .remove_when_all_nan(),
    ),
    read_params={
        "low_memory": False,
        "delim_whitespace": True,
        "skiprows": [1],
    },
)
