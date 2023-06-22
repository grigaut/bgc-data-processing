"""Specific parameters to load GLODAPv2-provided data."""

from pathlib import Path

from bgc_data_processing import (
    DEFAULT_VARS,
    PROVIDERS_CONFIG,
    units,
)
from bgc_data_processing.data_sources import DataSource
from bgc_data_processing.data_structures.variables.ensembles import VariableEnsemble
from bgc_data_processing.utils.patterns import FileNamePattern

loader = DataSource(
    provider_name="GLODAPv2",
    data_format="csv",
    dirin=Path(PROVIDERS_CONFIG["GLODAPv2"]["PATH"]),
    data_category=PROVIDERS_CONFIG["GLODAPv2"]["CATEGORY"],
    excluded_files=PROVIDERS_CONFIG["GLODAPv2"]["EXCLUDE"],
    files_pattern=FileNamePattern("glodapv2_{years}.csv"),
    variable_ensemble=VariableEnsemble(
        provider=DEFAULT_VARS["provider"].not_in_file(),
        expocode=DEFAULT_VARS["expocode"].in_file_as("cruise"),
        date=DEFAULT_VARS["date"].not_in_file(),
        year=DEFAULT_VARS["year"].in_file_as("YEAR"),
        month=DEFAULT_VARS["month"].in_file_as("MONTH"),
        day=DEFAULT_VARS["day"].in_file_as("DAY"),
        hour=DEFAULT_VARS["hour"].in_file_as("hour"),
        longitude=DEFAULT_VARS["longitude"].in_file_as("LONGITUDE"),
        latitude=DEFAULT_VARS["latitude"].in_file_as("LATITUDE"),
        depth=DEFAULT_VARS["depth"]
        .in_file_as("DEPTH")
        .remove_when_nan()
        .correct_with(lambda x: -x),
        temperature=DEFAULT_VARS["temperature"].in_file_as("THETA"),
        salinity=DEFAULT_VARS["salinity"].in_file_as("SALNTY"),
        oxygen=DEFAULT_VARS["oxygen"]
        .in_file_as("OXYGEN")
        .correct_with(units.convert_umol_by_kg_to_mmol_by_m3),
        phosphate=DEFAULT_VARS["phosphate"].in_file_as("PHSPHT").remove_when_all_nan(),
        nitrate=DEFAULT_VARS["nitrate"].in_file_as("NITRAT").remove_when_all_nan(),
        silicate=DEFAULT_VARS["silicate"].in_file_as("SILCAT").remove_when_all_nan(),
        chlorophyll=DEFAULT_VARS["chlorophyll"].not_in_file().remove_when_all_nan(),
    ),
    read_params={
        "low_memory": False,
        "index_col": False,
        "skiprows": [1],
    },
)
