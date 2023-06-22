"""Specific parameters to load Argo-provided data."""

from pathlib import Path

import numpy as np

from bgc_data_processing import (
    DEFAULT_VARS,
    PROVIDERS_CONFIG,
    units,
)
from bgc_data_processing.data_sources import DataSource
from bgc_data_processing.data_structures.variables.ensembles import VariableEnsemble
from bgc_data_processing.utils.patterns import FileNamePattern

loader = DataSource(
    provider_name="ARGO",
    data_format="netcdf",
    dirin=Path(PROVIDERS_CONFIG["ARGO"]["PATH"]),
    data_category=PROVIDERS_CONFIG["ARGO"]["CATEGORY"],
    excluded_files=PROVIDERS_CONFIG["ARGO"]["EXCLUDE"],
    files_pattern=FileNamePattern(".*.nc"),
    variable_ensemble=VariableEnsemble(
        provider=DEFAULT_VARS["provider"].not_in_file(),
        expocode=DEFAULT_VARS["expocode"].not_in_file(),
        date=DEFAULT_VARS["date"].in_file_as("TIME"),
        year=DEFAULT_VARS["year"].not_in_file(),
        month=DEFAULT_VARS["month"].not_in_file(),
        day=DEFAULT_VARS["day"].not_in_file(),
        hour=DEFAULT_VARS["hour"].not_in_file(),
        longitude=DEFAULT_VARS["longitude"].in_file_as("LONGITUDE"),
        latitude=DEFAULT_VARS["latitude"].in_file_as("LATITUDE"),
        depth=DEFAULT_VARS["depth"]
        .in_file_as("PRES_ADJUSTED")
        .remove_when_nan()
        .correct_with(lambda x: -np.abs(x)),
        temperature=DEFAULT_VARS["temperature"].in_file_as(
            ("TEMP_ADJUSTED", "TEMP_ADJUSTED_QC", [1]),
            ("TEMP", "TEMP_QC", [1]),
        ),
        salinity=DEFAULT_VARS["salinity"].in_file_as(
            ("PSAL_ADJUSTED", "PSAL_ADJUSTED_QC", [1]),
            ("PSAl", "PSAl_QC", [1]),
        ),
        oxygen=DEFAULT_VARS["oxygen"]
        .in_file_as("DOX2_ADJUSTED", "DOX2")
        .correct_with(units.convert_umol_by_kg_to_mmol_by_m3),
        phosphate=DEFAULT_VARS["phosphate"].not_in_file(),
        nitrate=DEFAULT_VARS["nitrate"].not_in_file(),
        silicate=DEFAULT_VARS["silicate"].not_in_file(),
        chlorophyll=DEFAULT_VARS["chlorophyll"]
        .in_file_as(
            ("CPHL_ADJUSTED", "CPHL_ADJUSTED_QC", [1]),
            ("CPHL", "CPHL_QC", [1]),
        )
        .remove_when_all_nan()
        .correct_with(lambda x: np.nan if x < 0.01 else x),
    ),
)
