"""Specific parameters to load GLODAPv2.2019-provided data."""

from pathlib import Path

from bgc_data_processing import (
    units,
)
from bgc_data_processing.core.variables.sets import SourceVariableSet
from bgc_data_processing.data_sources import DataSource
from bgc_data_processing.defaults import PROVIDERS_CONFIG, VARS
from bgc_data_processing.utils.patterns import FileNamePattern

loader = DataSource(
    provider_name="GLODAP_2019",
    data_format="csv",
    dirin=Path(PROVIDERS_CONFIG["GLODAP_2019"]["PATH"]),
    data_category=PROVIDERS_CONFIG["GLODAP_2019"]["CATEGORY"],
    excluded_files=PROVIDERS_CONFIG["GLODAP_2019"]["EXCLUDE"],
    files_pattern=FileNamePattern("glodapv2_({years}).csv"),
    variable_ensemble=SourceVariableSet(
        provider=VARS["provider"].not_in_file(),
        expocode=VARS["expocode"].in_file_as("cruise"),
        date=VARS["date"].not_in_file(),
        year=VARS["year"].in_file_as("YEAR"),
        month=VARS["month"].in_file_as("MONTH"),
        day=VARS["day"].in_file_as("DAY"),
        hour=VARS["hour"].in_file_as("hour"),
        longitude=VARS["longitude"].in_file_as("LONGITUDE"),
        latitude=VARS["latitude"].in_file_as("LATITUDE"),
        depth=VARS["depth"]
        .in_file_as("DEPTH")
        .remove_when_nan()
        .correct_with(lambda x: -x),
        temperature=VARS["temperature"].in_file_as("THETA"),
        salinity=VARS["salinity"].in_file_as(("SALNTY", "salinityf", [2])),
        oxygen=VARS["oxygen"]
        .in_file_as(("OXYGEN", "oxygenf", [2]))
        .correct_with(units.convert_umol_by_kg_to_mmol_by_m3),
        phosphate=VARS["phosphate"]
        .in_file_as(("PHSPHT", "phosphatef", [2]))
        .remove_when_all_nan(),
        nitrate=VARS["nitrate"]
        .in_file_as(("NITRAT", "nitratef", [2]))
        .remove_when_all_nan(),
        silicate=VARS["silicate"]
        .in_file_as(("SILCAT", "silicatef", [2]))
        .remove_when_all_nan(),
        chlorophyll=VARS["chlorophyll"].not_in_file().remove_when_all_nan(),
    ),
    read_params={
        "low_memory": False,
        "index_col": False,
        "skiprows": [1],
    },
)
