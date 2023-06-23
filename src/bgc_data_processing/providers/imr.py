"""Specific parameters to load IMR-provided data."""

from pathlib import Path

from bgc_data_processing import (
    units,
)
from bgc_data_processing.core.variables.sets import SourceVariableSet
from bgc_data_processing.data_sources import DataSource
from bgc_data_processing.defaults import PROVIDERS_CONFIG, VARS
from bgc_data_processing.utils.patterns import FileNamePattern

loader = DataSource(
    provider_name="IMR",
    data_format="csv",
    dirin=Path(PROVIDERS_CONFIG["IMR"]["PATH"]),
    data_category=PROVIDERS_CONFIG["IMR"]["CATEGORY"],
    excluded_files=PROVIDERS_CONFIG["IMR"]["EXCLUDE"],
    files_pattern=FileNamePattern("imr_{years}.csv"),
    variable_ensemble=SourceVariableSet(
        provider=VARS["provider"].not_in_file(),
        expocode=VARS["expocode"].not_in_file(),
        date=VARS["date"].not_in_file(),
        year=VARS["year"].in_file_as("Year"),
        month=VARS["month"].in_file_as("Month"),
        day=VARS["day"].in_file_as("Day"),
        hour=VARS["hour"].not_in_file(),
        longitude=VARS["longitude"].in_file_as("Long"),
        latitude=VARS["latitude"].in_file_as("Lati"),
        depth=VARS["depth"].in_file_as("Depth").remove_when_nan(),
        temperature=VARS["temperature"].in_file_as("Temp"),
        salinity=VARS["salinity"].in_file_as("Saln."),
        oxygen=VARS["oxygen"]
        .in_file_as("Oxygen", "Doxy")
        .correct_with(units.convert_doxy_ml_by_l_to_mmol_by_m3),
        phosphate=VARS["phosphate"].in_file_as("Phosphate").remove_when_all_nan(),
        nitrate=VARS["nitrate"].in_file_as("Nitrate").remove_when_all_nan(),
        silicate=VARS["silicate"].in_file_as("Silicate").remove_when_all_nan(),
        chlorophyll=VARS["chlorophyll"].in_file_as("Chl.").remove_when_all_nan(),
    ),
    read_params={
        "low_memory": False,
        "delim_whitespace": True,
        "skiprows": [1],
    },
)
