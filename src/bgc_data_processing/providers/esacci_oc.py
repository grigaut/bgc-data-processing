"""Specific parameters to load ESACCI-OC-provided data."""

from pathlib import Path

from bgc_data_processing import (
    DEFAULT_VARS,
    PROVIDERS_CONFIG,
    loaders,
)
from bgc_data_processing.data_structures.variables import VariablesStorer
from bgc_data_processing.utils.patterns import FileNamePattern

loader = loaders.from_netcdf(
    provider_name="ESACCI-OC",
    dirin=Path(PROVIDERS_CONFIG["ESACCI-OC"]["PATH"]),
    category=PROVIDERS_CONFIG["ESACCI-OC"]["CATEGORY"],
    exclude=PROVIDERS_CONFIG["ESACCI-OC"]["EXCLUDE"],
    files_pattern=FileNamePattern("{years}/.*-{years}{months}{days}-.*.nc"),
    variables=VariablesStorer(
        provider=DEFAULT_VARS["provider"].not_in_file(),
        expocode=DEFAULT_VARS["expocode"].not_in_file(),
        date=DEFAULT_VARS["date"].in_file_as("time"),
        year=DEFAULT_VARS["year"].not_in_file(),
        month=DEFAULT_VARS["month"].not_in_file(),
        day=DEFAULT_VARS["day"].not_in_file(),
        hour=DEFAULT_VARS["hour"].not_in_file(),
        longitude=DEFAULT_VARS["longitude"].in_file_as("lon"),
        latitude=DEFAULT_VARS["latitude"].in_file_as("lat"),
        depth=DEFAULT_VARS["depth"].not_in_file().set_default(0),
        temperature=DEFAULT_VARS["temperature"].not_in_file(),
        salinity=DEFAULT_VARS["salinity"].not_in_file(),
        oxygen=DEFAULT_VARS["oxygen"].not_in_file(),
        phosphate=DEFAULT_VARS["phosphate"].not_in_file(),
        nitrate=DEFAULT_VARS["nitrate"].not_in_file(),
        silicate=DEFAULT_VARS["silicate"].not_in_file(),
        chlorophyll=DEFAULT_VARS["chlorophyll"].in_file_as("chlor_a").remove_when_nan(),
    ),
)
