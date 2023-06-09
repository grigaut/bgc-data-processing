"""Plot Variable vs Pressure Graph with respect to water masses."""

import datetime as dt
from pathlib import Path

from bgc_data_processing import DEFAULT_VARS, DEFAULT_WATER_MASSES, features
from bgc_data_processing.data_classes import Constraints, Storer
from bgc_data_processing.parsers import ConfigParser
from bgc_data_processing.tracers import WaterMassVariableComparison
from bgc_data_processing.water_masses import WaterMass

CONFIG_FOLDER = Path("config")

if __name__ == "__main__":
    config_filepath = CONFIG_FOLDER.joinpath(Path(__file__).stem)
    CONFIG = ConfigParser(
        filepath=config_filepath.with_suffix(".toml"),
        dates_vars_keys=["DATE_MIN", "DATE_MAX"],
        dirs_vars_keys=["SAVING_DIR"],
        existing_directory="raise",
    )
    LOADING_DIR: Path = Path(CONFIG["LOADING_DIR"])
    SHOW: bool = CONFIG["SHOW"]
    SAVE: bool = CONFIG["SAVE"]
    PLOT_VARIABLE: str = CONFIG["PLOT_VARIABLE"]
    DATE_MIN: dt.datetime = CONFIG["DATE_MIN"]
    DATE_MAX: dt.datetime = CONFIG["DATE_MAX"]
    LATITUDE_MIN: int | float = CONFIG["LATITUDE_MIN"]
    LATITUDE_MAX: int | float = CONFIG["LATITUDE_MAX"]
    LONGITUDE_MIN: int | float = CONFIG["LONGITUDE_MIN"]
    LONGITUDE_MAX: int | float = CONFIG["LONGITUDE_MAX"]
    EXPOCODES_TO_LOAD: list[str] = CONFIG["EXPOCODES_TO_LOAD"]
    PRIORITY: list[str] = CONFIG["PRIORITY"]
    VERBOSE: int = CONFIG["VERBOSE"]

    ACRONYMS: list[str] = CONFIG["WATER_MASS_ACRONYMS"]
    WATER_MASSES: list[WaterMass] = [DEFAULT_WATER_MASSES[acro] for acro in ACRONYMS]

    SALINITY_DEFAULT = DEFAULT_VARS["salinity"]
    TEMPERATURE_DEFAULT = DEFAULT_VARS["temperature"]

    filepaths_txt = list(LOADING_DIR.glob("*.txt"))
    filepaths_csv = list(LOADING_DIR.glob("*.csv"))
    filepaths = filepaths_txt + filepaths_csv

    storer = Storer.from_files(
        filepaths,
        providers_column_label=DEFAULT_VARS["provider"].label,
        expocode_column_label=DEFAULT_VARS["expocode"].label,
        date_column_label=DEFAULT_VARS["date"].label,
        year_column_label=DEFAULT_VARS["year"].label,
        month_column_label=DEFAULT_VARS["month"].label,
        day_column_label=DEFAULT_VARS["day"].label,
        hour_column_label=DEFAULT_VARS["hour"].label,
        latitude_column_label=DEFAULT_VARS["latitude"].label,
        longitude_column_label=DEFAULT_VARS["longitude"].label,
        depth_column_label=DEFAULT_VARS["depth"].label,
        category="in_situ",
        unit_row_index=1,
        delim_whitespace=True,
        verbose=VERBOSE,
    )
    storer.remove_duplicates(PRIORITY)
    variables = storer.variables
    # Add relevant features to the data: Pressure / potential temperature /sigma-t
    depth_field = variables.get(variables.depth_var_name).label
    latitude_field = variables.get(variables.latitude_var_name).label
    pres_var, pres_data = features.compute_pressure(storer, depth_field, latitude_field)
    storer.add_feature(pres_var, pres_data)
    ptemp_var, ptemp_data = features.compute_potential_temperature(
        storer=storer,
        salinity_field=SALINITY_DEFAULT.label,
        temperature_field=TEMPERATURE_DEFAULT.label,
        pressure_field=pres_var.label,
    )
    storer.add_feature(ptemp_var, ptemp_data)
    sigt_var, sigt_data = features.compute_sigma_t(
        storer=storer,
        salinity_field=SALINITY_DEFAULT.label,
        temperature_field=TEMPERATURE_DEFAULT.label,
    )
    storer.add_feature(sigt_var, sigt_data)
    constraints = Constraints()
    constraints.add_superset_constraint(
        field_label=variables.get(variables.expocode_var_name).label,
        values_superset=EXPOCODES_TO_LOAD,
    )
    constraints.add_boundary_constraint(
        field_label=variables.get(variables.date_var_name).label,
        minimal_value=DATE_MIN,
        maximal_value=DATE_MAX,
    )
    constraints.add_boundary_constraint(
        field_label=variables.get(variables.latitude_var_name).label,
        minimal_value=LATITUDE_MIN,
        maximal_value=LATITUDE_MAX,
    )
    constraints.add_boundary_constraint(
        field_label=variables.get(variables.longitude_var_name).label,
        minimal_value=LONGITUDE_MIN,
        maximal_value=LONGITUDE_MAX,
    )
    plot = WaterMassVariableComparison(
        storer,
        constraints,
        pres_var.name,
        ptemp_var.name,
        SALINITY_DEFAULT.label,
        sigt_var.name,
    )
    if SHOW:
        plot.show(
            variable_name=PLOT_VARIABLE,
            wmasses=WATER_MASSES,
        )
    if SAVE:
        filename = f"{PLOT_VARIABLE}_pressure.png"
        plot.save(
            variable_name=PLOT_VARIABLE,
            wmasses=WATER_MASSES,
            save_path=Path(CONFIG["SAVING_DIR"]).joinpath(filename),
        )
