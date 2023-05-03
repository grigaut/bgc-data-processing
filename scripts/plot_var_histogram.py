"""Plot Variable Bar Plot."""

import datetime as dt
from pathlib import Path

from bgc_data_processing import DEFAULT_WATER_MASSES, features
from bgc_data_processing.data_classes import Constraints, Storer
from bgc_data_processing.parsers import ConfigParser
from bgc_data_processing.tracers import VariableHistogram
from bgc_data_processing.water_masses import WaterMass

if __name__ == "__main__":
    CONFIG = ConfigParser(
        filepath="config/plot_var_histogram.toml",
        dates_vars_keys=["DATE_MIN", "DATE_MAX"],
        dirs_vars_keys=["SAVING_DIR"],
        existing_directory="raise",
    )
    LOADING_DIR: Path = Path(CONFIG["LOADING_DIR"])
    SAVING_DIR: Path = Path(CONFIG["SAVING_DIR"])
    SHOW: bool = CONFIG["SHOW"]
    SAVE: bool = CONFIG["SAVE"]
    PLOT_VARIABLE: str = CONFIG["PLOT_VARIABLE"]
    DATE_MIN: dt.datetime = CONFIG["DATE_MIN"]
    DATE_MAX: dt.datetime = CONFIG["DATE_MAX"]
    LATITUDE_MIN: int | float = CONFIG["LATITUDE_MIN"]
    LATITUDE_MAX: int | float = CONFIG["LATITUDE_MAX"]
    LONGITUDE_MIN: int | float = CONFIG["LONGITUDE_MIN"]
    LONGITUDE_MAX: int | float = CONFIG["LONGITUDE_MAX"]
    WATER_MASS: WaterMass = DEFAULT_WATER_MASSES[CONFIG["WATER_MASS_ACRONYM"]]
    EXPOCODES_TO_LOAD: list[str] = CONFIG["EXPOCODES_TO_LOAD"]
    PRIORITY: list[str] = CONFIG["PRIORITY"]
    VERBOSE: int = CONFIG["VERBOSE"]

    filepaths_txt = list(LOADING_DIR.glob("*.txt"))
    filepaths_csv = list(LOADING_DIR.glob("*.csv"))
    filepaths = filepaths_txt + filepaths_csv

    storer = Storer.from_files(
        filepath=filepaths,
        providers_column_label="PROVIDER",
        expocode_column_label="EXPOCODE",
        date_column_label="DATE",
        year_column_label="YEAR",
        month_column_label="MONTH",
        day_column_label="DAY",
        hour_column_label="HOUR",
        latitude_column_label="LATITUDE",
        longitude_column_label="LONGITUDE",
        depth_column_label="DEPH",
        category="in_situ",
        unit_row_index=1,
        delim_whitespace=True,
        verbose=VERBOSE,
    )
    storer.remove_duplicates(PRIORITY)
    variables = storer.variables
    # Add relevant features to the data: Pressure / potential temperature /sigmat
    depth_field = variables.get(variables.depth_var_name).label
    latitude_field = variables.get(variables.latitude_var_name).label
    pres_var, pres_data = features.compute_pressure(storer, depth_field, latitude_field)
    storer.add_feature(pres_var, pres_data)
    ptemp_var, ptemp_data = features.compute_potential_temperature(
        storer=storer,
        salinity_field="PSAL",
        temperature_field="TEMP",
        pressure_field=pres_var.label,
    )
    storer.add_feature(ptemp_var, ptemp_data)
    sigt_var, sigt_data = features.compute_sigma_t(
        storer=storer,
        salinity_field="PSAL",
        temperature_field="TEMP",
    )
    storer.add_feature(sigt_var, sigt_data)
    storer_wm = WATER_MASS.extract_from_storer(
        storer=storer,
        ptemperature_name=ptemp_var.label,
        salinity_name="PSAL",
        sigma_t_name=sigt_var.label,
    )
    variables_wm = storer_wm.variables
    constraints = Constraints()
    constraints.add_superset_constraint(
        field_label=variables_wm.get(variables_wm.expocode_var_name).label,
        values_superset=EXPOCODES_TO_LOAD,
    )
    constraints.add_boundary_constraint(
        field_label=variables_wm.get(variables_wm.date_var_name).label,
        minimal_value=DATE_MIN,
        maximal_value=DATE_MAX,
    )
    constraints.add_boundary_constraint(
        field_label=variables_wm.get(variables_wm.latitude_var_name).label,
        minimal_value=LATITUDE_MIN,
        maximal_value=LATITUDE_MAX,
    )
    constraints.add_boundary_constraint(
        field_label=variables_wm.get(variables_wm.longitude_var_name).label,
        minimal_value=LONGITUDE_MIN,
        maximal_value=LONGITUDE_MAX,
    )

    plot = VariableHistogram(storer_wm, constraints)
    if SHOW:
        plot.show(PLOT_VARIABLE)
    if SAVE:
        filename = f"{PLOT_VARIABLE}_histogram.png"
        plot.save(PLOT_VARIABLE, SAVING_DIR.joinpath(filename))
