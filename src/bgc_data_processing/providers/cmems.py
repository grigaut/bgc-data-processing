"""Specific parameters to load CMEMS-provided data."""

from pathlib import Path

import numpy as np

from bgc_data_processing import units
from bgc_data_processing.core.sources import DataSource
from bgc_data_processing.core.variables.sets import SourceVariableSet
from bgc_data_processing.defaults import PROVIDERS_CONFIG, VARS
from bgc_data_processing.utils.patterns import FileNamePattern

loader = DataSource(
    provider_name="CMEMS",
    data_format="netcdf",
    dirin=Path(PROVIDERS_CONFIG["CMEMS"]["PATH"]),
    data_category=PROVIDERS_CONFIG["CMEMS"]["CATEGORY"],
    excluded_files=PROVIDERS_CONFIG["CMEMS"]["EXCLUDE"],
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
        .in_file_as("DEPH", "PRES")
        .remove_when_nan()
        .correct_with(lambda x: -np.abs(x)),
        temperature=VARS["temperature"].in_file_as(("TEMP", "TEMP_QC", [1])),
        salinity=VARS["salinity"].in_file_as(("PSAL", "PSL_QC", [1])),
        oxygen=VARS["oxygen"]
        .in_file_as("DOX1")
        .correct_with(units.convert_doxy_ml_by_l_to_mmol_by_m3),
        phosphate=VARS["phosphate"]
        .in_file_as(("PHOS", "PHOS_QC", [1]))
        .remove_when_all_nan(),
        nitrate=VARS["nitrate"]
        .in_file_as(("NTRA", "NTRA_QC", [1]))
        .remove_when_all_nan(),
        silicate=VARS["silicate"]
        .in_file_as(("SLCA", "SLCA_QC", [1]))
        .remove_when_all_nan(),
        chlorophyll=VARS["chlorophyll"]
        .in_file_as(("CPHL", "CPHL_QC", [1]))
        .remove_when_all_nan(),
    ),
)
