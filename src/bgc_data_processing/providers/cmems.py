"""Specific parameters to load CMEMS-provided data."""

from pathlib import Path

import numpy as np

from bgc_data_processing import (
    DEFAULT_VARS,
    PROVIDERS_CONFIG,
    loaders,
    units,
)
from bgc_data_processing.data_structures.variables import VariablesStorer
from bgc_data_processing.utils.patterns import FileNamePattern

loader = loaders.from_netcdf(
    provider_name="CMEMS",
    dirin=Path(PROVIDERS_CONFIG["CMEMS"]["PATH"]),
    category=PROVIDERS_CONFIG["CMEMS"]["CATEGORY"],
    files_pattern=FileNamePattern(".*.nc"),
    variables=VariablesStorer(
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
        .in_file_as("DEPH", "PRES")
        .remove_when_nan()
        .correct_with(lambda x: -np.abs(x)),
        temperature=DEFAULT_VARS["temperature"].in_file_as(("TEMP", "TEMP_QC", [1])),
        salinity=DEFAULT_VARS["salinity"].in_file_as(("PSAL", "PSL_QC", [1])),
        oxygen=DEFAULT_VARS["oxygen"]
        .in_file_as("DOX1")
        .correct_with(units.convert_doxy_ml_by_l_to_mmol_by_m3),
        phosphate=DEFAULT_VARS["phosphate"]
        .in_file_as(("PHOS", "PHOS_QC", [1]))
        .remove_when_all_nan(),
        nitrate=DEFAULT_VARS["nitrate"]
        .in_file_as(("NTRA", "NTRA_QC", [1]))
        .remove_when_all_nan(),
        silicate=DEFAULT_VARS["silicate"]
        .in_file_as(("SLCA", "SLCA_QC", [1]))
        .remove_when_all_nan(),
        chlorophyll=DEFAULT_VARS["chlorophyll"]
        .in_file_as(("CPHL", "CPHL_QC", [1]))
        .remove_when_all_nan(),
    ),
)
