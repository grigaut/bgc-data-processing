"""Specific parameters to load Argo-provided data."""


from pathlib import Path

from bgc_data_processing import DEFAULT_VARS, PROVIDERS_CONFIG, units
from bgc_data_processing.data_sources import DataSource
from bgc_data_processing.data_structures.variables.ensembles import VariableSet
from bgc_data_processing.utils.patterns import FileNamePattern

loader = DataSource(
    provider_name="HYCOM",
    data_format="abfiles",
    dirin=Path(PROVIDERS_CONFIG["HYCOM"]["PATH"]),
    data_category=PROVIDERS_CONFIG["HYCOM"]["CATEGORY"],
    excluded_files=PROVIDERS_CONFIG["HYCOM"]["EXCLUDE"],
    files_pattern=FileNamePattern("archm.{years}_[0-9]*_[0-9]*.a"),
    variable_ensemble=VariableSet(
        provider=DEFAULT_VARS["provider"].not_in_file().set_default("HYCOM"),
        expocode=DEFAULT_VARS["expocode"].not_in_file(),
        date=DEFAULT_VARS["date"].not_in_file(),
        year=DEFAULT_VARS["year"].not_in_file(),
        month=DEFAULT_VARS["month"].not_in_file(),
        day=DEFAULT_VARS["day"].not_in_file(),
        hour=DEFAULT_VARS["hour"].not_in_file(),
        longitude=DEFAULT_VARS["longitude"].in_file_as("plon"),
        latitude=DEFAULT_VARS["latitude"].in_file_as("plat"),
        depth=DEFAULT_VARS["depth"].in_file_as("thknss"),
        temperature=DEFAULT_VARS["temperature"].in_file_as("temp"),
        salinity=DEFAULT_VARS["salinity"].in_file_as("salin"),
        oxygen=DEFAULT_VARS["oxygen"].in_file_as("ECO_oxy"),
        phosphate=DEFAULT_VARS["phosphate"]
        .in_file_as("ECO_pho")
        .correct_with(units.convert_phosphate_mgc_by_m3_to_umol_by_l),
        nitrate=DEFAULT_VARS["nitrate"]
        .in_file_as("ECO_no3")
        .correct_with(units.convert_nitrate_mgc_by_m3_to_umol_by_l),
        silicate=DEFAULT_VARS["silicate"]
        .in_file_as("ECO_sil")
        .correct_with(units.convert_silicate_mgc_by_m3_to_umol_by_l),
        chlorophyll=DEFAULT_VARS["chlorophyll"].not_in_file(),
    ),
    grid_basename=PROVIDERS_CONFIG["HYCOM"]["REGIONAL_GRID_BASENAME"],
)
