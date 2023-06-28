"""Plot Variable vs Pressure Graph with respect to water masses."""

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

    bgc_dp.set_verbose_level(VERBOSE)

    ACRONYMS: list[str] = CONFIG["WATER_MASS_ACRONYMS"]
    WATER_MASSES: list[bgc_dp.WaterMass] = [
        bgc_dp.defaults.WATER_MASSES[acro] for acro in ACRONYMS
    ]

    SALINITY_DEFAULT = bgc_dp.defaults.VARS["salinity"]
    TEMPERATURE_DEFAULT = bgc_dp.defaults.VARS["temperature"]

    storer = bgc_dp.read_files(
        list(LOADING_DIR.glob("*.txt")),
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
        variables_reference=bgc_dp.defaults.VARS.to_list(),
        category="in_situ",
        unit_row_index=1,
        delim_whitespace=True,
    )
    storer.remove_duplicates(PRIORITY)
    variables = storer.variables
    # Add relevant features to the data: Pressure / potential temperature /sigma-t
    depth_field = variables.get(variables.depth_var_name).label
    latitude_field = variables.get(variables.latitude_var_name).label
    pres_feat = bgc_dp.features.Pressure(
        depth_variable=variables.get(variables.depth_var_name),
        latitude_variable=variables.get(variables.latitude_var_name),
    )
    pres_feat.insert_in_storer(storer)
    ptemp_feat = bgc_dp.features.PotentialTemperature(
        salinity_variable=SALINITY_DEFAULT,
        temperature_variable=TEMPERATURE_DEFAULT,
        pressure_variable=pres_feat.variable,
    )
    ptemp_feat.insert_in_storer(storer)
    sigmat_feat = bgc_dp.features.SigmaT(
        salinity_variable=SALINITY_DEFAULT,
        temperature_variable=TEMPERATURE_DEFAULT,
    )
    sigmat_feat.insert_in_storer(storer)
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
    plot = bgc_dp.tracers.WaterMassVariableComparison(
        storer,
        constraints,
        pres_feat.variable.name,
        ptemp_feat.variable.name,
        SALINITY_DEFAULT.name,
        sigmat_feat.variable.name,
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
