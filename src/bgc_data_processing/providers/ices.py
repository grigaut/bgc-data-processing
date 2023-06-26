"""Specific parameters to load ICES-provided data."""

from pathlib import Path

from bgc_data_processing import units
from bgc_data_processing.core.sources import DataSource
from bgc_data_processing.core.variables.sets import SourceVariableSet
from bgc_data_processing.defaults import PROVIDERS_CONFIG, VARS
from bgc_data_processing.utils.patterns import FileNamePattern

loader = DataSource(
    provider_name="ICES",
    data_format="csv",
    dirin=Path(PROVIDERS_CONFIG["ICES"]["PATH"]),
    data_category=PROVIDERS_CONFIG["ICES"]["CATEGORY"],
    excluded_files=PROVIDERS_CONFIG["ICES"]["EXCLUDE"],
    files_pattern=FileNamePattern("ices_{years}.csv"),
    variable_ensemble=SourceVariableSet(
        provider=VARS["provider"].not_in_file(),
        expocode=VARS["expocode"].in_file_as("Cruise"),
        date=VARS["date"].in_file_as("DATE"),
        year=VARS["year"].not_in_file(),
        month=VARS["month"].not_in_file(),
        day=VARS["day"].not_in_file(),
        hour=VARS["hour"].not_in_file(),
        longitude=VARS["longitude"].in_file_as("LONGITUDE"),
        latitude=VARS["latitude"].in_file_as("LATITUDE"),
        depth=VARS["depth"]
        .in_file_as("DEPTH")
        .remove_when_nan()
        .correct_with(lambda x: -x),
        temperature=VARS["temperature"].in_file_as("CTDTMP"),
        salinity=VARS["salinity"].in_file_as("CTDSAL"),
        oxygen=VARS["oxygen"]
        .in_file_as("DOXY")
        .correct_with(units.convert_doxy_ml_by_l_to_mmol_by_m3),
        phosphate=VARS["phosphate"].in_file_as("PHOS").remove_when_all_nan(),
        nitrate=VARS["nitrate"].in_file_as("NTRA").remove_when_all_nan(),
        silicate=VARS["silicate"].in_file_as("SLCA").remove_when_all_nan(),
        chlorophyll=VARS["chlorophyll"].in_file_as("CPHL").remove_when_all_nan(),
    ),
    read_params={
        "low_memory": False,
        "skiprows": [1],
    },
)
