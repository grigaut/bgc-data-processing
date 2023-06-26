"""Specific parameters to load NMDC-provided data."""

from pathlib import Path

from bgc_data_processing import units
from bgc_data_processing.core.sources import DataSource
from bgc_data_processing.core.variables.sets import SourceVariableSet
from bgc_data_processing.defaults import PROVIDERS_CONFIG, VARS
from bgc_data_processing.utils.patterns import FileNamePattern

loader = DataSource(
    provider_name="NMDC",
    data_format="csv",
    dirin=Path(PROVIDERS_CONFIG["NMDC"]["PATH"]),
    data_category=PROVIDERS_CONFIG["NMDC"]["CATEGORY"],
    excluded_files=PROVIDERS_CONFIG["NMDC"]["EXCLUDE"],
    files_pattern=FileNamePattern("NMDC_1990-2019_all.csv"),
    variable_ensemble=SourceVariableSet(
        provider=VARS["provider"].not_in_file(),
        expocode=VARS["expocode"].in_file_as("SDN_CRUISE"),
        date=VARS["date"].in_file_as("Time"),
        year=VARS["year"].not_in_file(),
        month=VARS["month"].not_in_file(),
        day=VARS["day"].not_in_file(),
        hour=VARS["hour"].not_in_file(),
        longitude=VARS["longitude"].in_file_as("Longitude"),
        latitude=VARS["latitude"].in_file_as("Latitude"),
        depth=VARS["depth"]
        .in_file_as("depth")
        .remove_when_nan()
        .correct_with(lambda x: -x),
        temperature=VARS["temperature"].not_in_file(),
        salinity=VARS["salinity"].not_in_file(),
        oxygen=VARS["oxygen"]
        .in_file_as("DOW")
        .correct_with(units.convert_doxy_ml_by_l_to_mmol_by_m3),
        phosphate=VARS["phosphate"]
        .in_file_as(("Phosphate", "Phosphate_SEADATANET_QC", [1]))
        .remove_when_all_nan(),
        nitrate=VARS["nitrate"]
        .in_file_as(("Nitrate", "Nitrate_SEADATANET_QC", [1]))
        .remove_when_all_nan(),
        silicate=VARS["silicate"]
        .in_file_as(("Silicate", "Silicate_SEADATANET_QC", [1]))
        .remove_when_all_nan(),
        chlorophyll=VARS["chlorophyll"]
        .in_file_as(("ChlA", "ChlA_SEADATANET_QC", [1]))
        .remove_when_all_nan(),
    ),
    read_params={
        "low_memory": False,
        "skiprows": [1],
    },
)
