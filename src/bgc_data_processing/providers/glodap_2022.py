"""Specific parameters to load GLODAPv2.2022-provided data."""

from pathlib import Path

from bgc_data_processing import (
    DEFAULT_VARS,
    PROVIDERS_CONFIG,
    loaders,
    units,
    variables,
)

loader = loaders.from_csv(
    provider_name="GLODAP_2022",
    dirin=Path(PROVIDERS_CONFIG["GLODAP_2022"]["PATH"]),
    category=PROVIDERS_CONFIG["GLODAP_2022"]["CATEGORY"],
    files_pattern="GLODAPv2.2022_all.csv",
    variables=variables.VariablesStorer(
        provider=DEFAULT_VARS["provider"].not_in_file(),
        expocode=DEFAULT_VARS["expocode"]
        .in_file_as("G2expocode")
        .correct_with(lambda x: x[:-8]),
        date=DEFAULT_VARS["date"].not_in_file(),
        year=DEFAULT_VARS["year"].in_file_as("G2year"),
        month=DEFAULT_VARS["month"].in_file_as("G2month"),
        day=DEFAULT_VARS["day"].in_file_as("G2day"),
        hour=DEFAULT_VARS["hour"].in_file_as("G2hour"),
        longitude=DEFAULT_VARS["longitude"].in_file_as("G2longitude"),
        latitude=DEFAULT_VARS["latitude"].in_file_as("G2latitude"),
        depth=DEFAULT_VARS["depth"]
        .in_file_as("G2depth")
        .remove_when_nan()
        .correct_with(lambda x: -x),
        temperature=DEFAULT_VARS["temperature"].in_file_as("G2temperature"),
        salinity=DEFAULT_VARS["salinity"].in_file_as(
            ("G2salinity", "G2salinityf", [2]),
        ),
        oxygen=DEFAULT_VARS["oxygen"]
        .in_file_as(("G2oxygen", "G2oxygenf", [2]))
        .correct_with(units.convert_umol_by_kg_to_mmol_by_m3),
        phosphate=DEFAULT_VARS["phosphate"]
        .in_file_as(("G2phosphate", "G2phosphatef", [2]))
        .remove_when_all_nan(),
        nitrate=DEFAULT_VARS["nitrate"]
        .in_file_as(("G2nitrate", "G2nitratef", [2]))
        .remove_when_all_nan(),
        silicate=DEFAULT_VARS["silicate"]
        .in_file_as(("G2silicate", "G2silicatef", [2]))
        .remove_when_all_nan(),
        chlorophyll=DEFAULT_VARS["chlorophyll"].not_in_file().remove_when_all_nan(),
    ),
    read_params={
        "low_memory": False,
        "index_col": False,
        "na_values": -9999,
    },
)
