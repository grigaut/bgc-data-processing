"""Specific parameters to load Argo-provided data."""


from pathlib import Path

from bgc_data_processing import units
from bgc_data_processing.core.variables.sets import SourceVariableSet
from bgc_data_processing.core.variables.vars import FeatureVar
from bgc_data_processing.data_sources import DataSource
from bgc_data_processing.defaults import PROVIDERS_CONFIG, VARS
from bgc_data_processing.features import ChlorophyllFromDiatomFlagellate
from bgc_data_processing.utils.patterns import FileNamePattern

loader = DataSource(
    provider_name="HYCOM",
    data_format="abfiles",
    dirin=Path(PROVIDERS_CONFIG["HYCOM"]["PATH"]),
    data_category=PROVIDERS_CONFIG["HYCOM"]["CATEGORY"],
    excluded_files=PROVIDERS_CONFIG["HYCOM"]["EXCLUDE"],
    files_pattern=FileNamePattern("archm.{years}_[0-9]*_[0-9]*.a"),
    variable_ensemble=SourceVariableSet(
        provider=VARS["provider"].not_in_file().set_default("HYCOM"),
        expocode=VARS["expocode"].not_in_file(),
        date=VARS["date"].not_in_file(),
        year=VARS["year"].not_in_file(),
        month=VARS["month"].not_in_file(),
        day=VARS["day"].not_in_file(),
        hour=VARS["hour"].not_in_file(),
        longitude=VARS["longitude"].in_file_as("plon"),
        latitude=VARS["latitude"].in_file_as("plat"),
        depth=VARS["depth"].in_file_as("thknss"),
        temperature=VARS["temperature"].in_file_as("temp"),
        salinity=VARS["salinity"].in_file_as("salin"),
        oxygen=VARS["oxygen"].in_file_as("ECO_oxy"),
        phosphate=VARS["phosphate"]
        .in_file_as("ECO_pho")
        .correct_with(units.convert_phosphate_mgc_by_m3_to_umol_by_l),
        nitrate=VARS["nitrate"]
        .in_file_as("ECO_no3")
        .correct_with(units.convert_nitrate_mgc_by_m3_to_umol_by_l),
        silicate=VARS["silicate"]
        .in_file_as("ECO_sil")
        .correct_with(units.convert_silicate_mgc_by_m3_to_umol_by_l),
        chlorophyll=FeatureVar(
            ChlorophyllFromDiatomFlagellate.copy_var_infos_from_template(
                template=VARS["chlorophyll"],
                diatom_variable=VARS["diatom"].in_file_as("ECO_diac"),
                flagellate_variable=VARS["flagellate"].in_file_as("ECO_flac"),
            ),
        ),
    ),
    grid_basename=PROVIDERS_CONFIG["HYCOM"]["REGIONAL_GRID_BASENAME"],
)
