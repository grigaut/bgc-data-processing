"""Specific parameters to load ICES-provided data."""

from pathlib import Path

from bgc_data_processing import (
    DEFAULT_VARS,
    PROVIDERS_CONFIG,
    loaders,
    units,
)
from bgc_data_processing.data_structures.variables import VariablesStorer
from bgc_data_processing.utils.patterns import FileNamePattern

loader = loaders.from_csv(
    provider_name="ICES",
    dirin=Path(PROVIDERS_CONFIG["ICES"]["PATH"]),
    category=PROVIDERS_CONFIG["ICES"]["CATEGORY"],
    exclude=PROVIDERS_CONFIG["ICES"]["EXCLUDE"],
    files_pattern=FileNamePattern("ices_{years}.csv"),
    variables=VariablesStorer(
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
        oxygen=DEFAULT_VARS["oxygen"]
        .in_file_as("DOXY")
        .correct_with(units.convert_doxy_ml_by_l_to_mmol_by_m3),
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
