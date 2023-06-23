"""Specific parameters to load Argo-provided data."""

from pathlib import Path

import numpy as np

from bgc_data_processing import (
    units,
)
from bgc_data_processing.core.variables.sets import SourceVariableSet
from bgc_data_processing.data_sources import DataSource
from bgc_data_processing.defaults import PROVIDERS_CONFIG, VARS
from bgc_data_processing.utils.patterns import FileNamePattern

loader = DataSource(
    provider_name="ARGO",
    data_format="netcdf",
    dirin=Path(PROVIDERS_CONFIG["ARGO"]["PATH"]),
    data_category=PROVIDERS_CONFIG["ARGO"]["CATEGORY"],
    excluded_files=PROVIDERS_CONFIG["ARGO"]["EXCLUDE"],
    files_pattern=FileNamePattern(".*.nc"),
    variable_ensemble=SourceVariableSet(
        provider=VARS["provider"].not_in_file(),
        expocode=VARS["expocode"].not_in_file(),
        date=VARS["date"].in_file_as("TIME"),
        year=VARS["year"].not_in_file(),
        month=VARS["month"].not_in_file(),
        day=VARS["day"].not_in_file(),
        hour=VARS["hour"].not_in_file(),
        longitude=VARS["longitude"].in_file_as("LONGITUDE"),
        latitude=VARS["latitude"].in_file_as("LATITUDE"),
        depth=VARS["depth"]
        .in_file_as("PRES_ADJUSTED")
        .remove_when_nan()
        .correct_with(lambda x: -np.abs(x)),
        temperature=VARS["temperature"].in_file_as(
            ("TEMP_ADJUSTED", "TEMP_ADJUSTED_QC", [1]),
            ("TEMP", "TEMP_QC", [1]),
        ),
        salinity=VARS["salinity"].in_file_as(
            ("PSAL_ADJUSTED", "PSAL_ADJUSTED_QC", [1]),
            ("PSAl", "PSAl_QC", [1]),
        ),
        oxygen=VARS["oxygen"]
        .in_file_as("DOX2_ADJUSTED", "DOX2")
        .correct_with(units.convert_umol_by_kg_to_mmol_by_m3),
        phosphate=VARS["phosphate"].not_in_file(),
        nitrate=VARS["nitrate"].not_in_file(),
        silicate=VARS["silicate"].not_in_file(),
        chlorophyll=VARS["chlorophyll"]
        .in_file_as(
            ("CPHL_ADJUSTED", "CPHL_ADJUSTED_QC", [1]),
            ("CPHL", "CPHL_QC", [1]),
        )
        .remove_when_all_nan()
        .correct_with(lambda x: np.nan if x < 0.01 else x),
    ),
)
