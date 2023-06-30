"""Plot a Temperature-Salinity Diagram from files in a directory."""

import datetime as dt
from pathlib import Path

import bgc_data_processing as bgc_dp

CONFIG_FOLDER = Path("config")

if __name__ == "__main__":
    config_filepath = CONFIG_FOLDER.joinpath(Path(__file__).stem)
    CONFIG = bgc_dp.parsers.ConfigParser(
        filepath=config_filepath.with_suffix(".toml"),
        dates_vars_keys=["DATE_MIN", "DATE_MAX"],
        dirs_vars_keys=["SAVING_DIR"],
        existing_directory="raise",
    )
    LOADING_DIR: Path = Path(CONFIG["LOADING_DIR"])
    SHOW: bool = CONFIG["SHOW"]
    SAVE: bool = CONFIG["SAVE"]
    DATE_MIN: dt.datetime = CONFIG["DATE_MIN"]
    DATE_MAX: dt.datetime = CONFIG["DATE_MAX"]
    LATITUDE_MIN: int | float = CONFIG["LATITUDE_MIN"]
    LATITUDE_MAX: int | float = CONFIG["LATITUDE_MAX"]
    LONGITUDE_MIN: int | float = CONFIG["LONGITUDE_MIN"]
    LONGITUDE_MAX: int | float = CONFIG["LONGITUDE_MAX"]
    DEPTH_MIN: int | float = CONFIG["DEPTH_MIN"]
    DEPTH_MAX: int | float = CONFIG["DEPTH_MAX"]
    EXPOCODES_TO_LOAD: list[str] = CONFIG["EXPOCODES_TO_LOAD"]
    PRIORITY: list[str] = CONFIG["PRIORITY"]
    VERBOSE: int = CONFIG["VERBOSE"]

    bgc_dp.set_verbose_level(VERBOSE)

    SALINITY_DEFAULT = bgc_dp.defaults.VARS["salinity"]
    TEMPERATURE_DEFAULT = bgc_dp.defaults.VARS["temperature"]

    storer = bgc_dp.io.read_files(
        filepath=list(LOADING_DIR.glob("*.txt")),
        providers_column_label=bgc_dp.defaults.VARS["provider"].label,
        expocode_column_label=bgc_dp.defaults.VARS["expocode"].label,
        date_column_label=bgc_dp.defaults.VARS["date"].label,
        year_column_label=bgc_dp.defaults.VARS["year"].label,
        month_column_label=bgc_dp.defaults.VARS["month"].label,
        day_column_label=bgc_dp.defaults.VARS["day"].label,
        hour_column_label=bgc_dp.defaults.VARS["hour"].label,
        latitude_column_label=bgc_dp.defaults.VARS["latitude"].label,
        longitude_column_label=bgc_dp.defaults.VARS["longitude"].label,
        depth_column_label=bgc_dp.defaults.VARS["depth"].label,
        category="in_situ",
        unit_row_index=1,
        delim_whitespace=True,
    )
    storer.remove_duplicates(PRIORITY)
    variables = storer.variables
    # Add relevant features to the data: Pressure / potential temperature
    pres_feat = bgc_dp.features.Pressure(
        depth_variable=variables.get(variables.depth_var_name),
        latitude_variable=variables.get(variables.latitude_var_name),
    )
    if not storer.variables.has_name(pres_feat.variable.name):
        pres_feat.insert_in_storer(storer)
    ptemp_feat = bgc_dp.features.PotentialTemperature(
        salinity_variable=SALINITY_DEFAULT,
        temperature_variable=TEMPERATURE_DEFAULT,
        pressure_variable=pres_feat.variable,
    )
    if not storer.variables.has_name(ptemp_feat.variable.name):
        ptemp_feat.insert_in_storer(storer)
    # Add global constraints
    constraints = bgc_dp.Constraints()
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
    constraints.add_boundary_constraint(
        field_label=variables.get(variables.depth_var_name).label,
        minimal_value=DEPTH_MIN,
        maximal_value=DEPTH_MAX,
    )
    # Create diagram
    plot = bgc_dp.tracers.TemperatureSalinityDiagram(
        storer=storer,
        constraints=constraints,
        salinity_field=SALINITY_DEFAULT.label,
        temperature_field=TEMPERATURE_DEFAULT.label,
        ptemperature_field=ptemp_feat.variable.label,
    )
    if SHOW:
        plot.show()
    if SAVE:
        filepath = Path(CONFIG["SAVING_DIR"]) / "ts_diagram.png"
        plot.save(filepath)
