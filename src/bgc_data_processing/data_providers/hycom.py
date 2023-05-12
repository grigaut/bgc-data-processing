"""Specific parameters to load Argo-provided data."""


from pathlib import Path

from bgc_data_processing import DEFAULT_VARS, PROVIDERS_CONFIG, abfiles_tools, variables

loader = abfiles_tools.ABFileLoader(
    provider_name="HYCOM",
    dirin=Path(PROVIDERS_CONFIG["HYCOM"]["PATH"]),
    category=PROVIDERS_CONFIG["HYCOM"]["CATEGORY"],
    files_pattern="archm.{years}_[0-9]*_[0-9]*.a",
    variables=variables.VariablesStorer(
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
        oxygen=DEFAULT_VARS["oxygen"].not_in_file(),
        phosphate=DEFAULT_VARS["phosphate"].not_in_file(),
        nitrate=DEFAULT_VARS["nitrate"].not_in_file(),
        silicate=DEFAULT_VARS["silicate"].not_in_file(),
        chlorophyll=DEFAULT_VARS["chlorophyll"].not_in_file(),
    ),
    grid_basename=PROVIDERS_CONFIG["HYCOM"]["REGIONAL_GRID_BASENAME"],
)
