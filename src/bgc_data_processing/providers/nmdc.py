"""Specific parameters to load NMDC-provided data."""

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
    provider_name="NMDC",
    data_format="csv",
    dirin=Path(PROVIDERS_CONFIG["NMDC"]["PATH"]),
    data_category=PROVIDERS_CONFIG["NMDC"]["CATEGORY"],
    excluded_files=PROVIDERS_CONFIG["NMDC"]["EXCLUDE"],
    files_pattern=FileNamePattern("NMDC_1990-2019_all.csv"),
    variable_ensemble=VariableEnsemble(
        provider=DEFAULT_VARS["provider"].not_in_file(),
        expocode=DEFAULT_VARS["expocode"].in_file_as("SDN_CRUISE"),
        date=DEFAULT_VARS["date"].in_file_as("Time"),
        year=DEFAULT_VARS["year"].not_in_file(),
        month=DEFAULT_VARS["month"].not_in_file(),
        day=DEFAULT_VARS["day"].not_in_file(),
        hour=DEFAULT_VARS["hour"].not_in_file(),
        longitude=DEFAULT_VARS["longitude"].in_file_as("Longitude"),
        latitude=DEFAULT_VARS["latitude"].in_file_as("Latitude"),
        depth=DEFAULT_VARS["depth"]
        .in_file_as("depth")
        .remove_when_nan()
        .correct_with(lambda x: -x),
        temperature=DEFAULT_VARS["temperature"].not_in_file(),
        salinity=DEFAULT_VARS["salinity"].not_in_file(),
        oxygen=DEFAULT_VARS["oxygen"]
        .in_file_as("DOW")
        .correct_with(units.convert_doxy_ml_by_l_to_mmol_by_m3),
        phosphate=DEFAULT_VARS["phosphate"]
        .in_file_as(("Phosphate", "Phosphate_SEADATANET_QC", [1]))
        .remove_when_all_nan(),
        nitrate=DEFAULT_VARS["nitrate"]
        .in_file_as(("Nitrate", "Nitrate_SEADATANET_QC", [1]))
        .remove_when_all_nan(),
        silicate=DEFAULT_VARS["silicate"]
        .in_file_as(("Silicate", "Silicate_SEADATANET_QC", [1]))
        .remove_when_all_nan(),
        chlorophyll=DEFAULT_VARS["chlorophyll"]
        .in_file_as(("ChlA", "ChlA_SEADATANET_QC", [1]))
        .remove_when_all_nan(),
    ),
    read_params={
        "low_memory": False,
        "skiprows": [1],
    },
)
