"""Specific parameters to load ESACCI-OC-provided data."""

from pathlib import Path

from bgc_data_processing.core.variables.sets import SourceVariableSet
from bgc_data_processing.data_sources import DataSource
from bgc_data_processing.defaults import PROVIDERS_CONFIG, VARS
from bgc_data_processing.utils.patterns import FileNamePattern

loader = DataSource(
    provider_name="ESACCI-OC",
    data_format="netcdf",
    dirin=Path(PROVIDERS_CONFIG["ESACCI-OC"]["PATH"]),
    data_category=PROVIDERS_CONFIG["ESACCI-OC"]["CATEGORY"],
    excluded_files=PROVIDERS_CONFIG["ESACCI-OC"]["EXCLUDE"],
    files_pattern=FileNamePattern("{years}/.*-{years}{months}{days}-.*.nc"),
    variable_ensemble=SourceVariableSet(
        provider=VARS["provider"].not_in_file(),
        expocode=VARS["expocode"].not_in_file(),
        date=VARS["date"].in_file_as("time"),
        year=VARS["year"].not_in_file(),
        month=VARS["month"].not_in_file(),
        day=VARS["day"].not_in_file(),
        hour=VARS["hour"].not_in_file(),
        longitude=VARS["longitude"].in_file_as("lon"),
        latitude=VARS["latitude"].in_file_as("lat"),
        depth=VARS["depth"].not_in_file().set_default(0),
        temperature=VARS["temperature"].not_in_file(),
        salinity=VARS["salinity"].not_in_file(),
        oxygen=VARS["oxygen"].not_in_file(),
        phosphate=VARS["phosphate"].not_in_file(),
        nitrate=VARS["nitrate"].not_in_file(),
        silicate=VARS["silicate"].not_in_file(),
        chlorophyll=VARS["chlorophyll"].in_file_as("chlor_a").remove_when_nan(),
    ),
)
