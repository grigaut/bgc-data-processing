"""Create an Evolution Profile from files in a directory."""

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
    VARIABLE: str = CONFIG["VARIABLE"]
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
    INTERVAL: str = CONFIG["INTERVAL"]
    CUSTOM_INTERVAL: int = CONFIG["CUSTOM_INTERVAL"]
    DEPTH_INTERVAL: int = CONFIG["DEPTH_INTERVAL"]
    PRIORITY: list[str] = CONFIG["PRIORITY"]
    EXPOCODES_TO_LOAD: list[str] = CONFIG["EXPOCODES_TO_LOAD"]
    VERBOSE: int = CONFIG["VERBOSE"]
    bgc_dp.set_verbose_level(VERBOSE)

    storer = bgc_dp.read_files(
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
        variables_reference=bgc_dp.defaults.VARS.to_list(),
        category="in_situ",
        unit_row_index=1,
        delim_whitespace=True,
    )
    storer.remove_duplicates(PRIORITY)
    variables = storer.variables
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
    profile = bgc_dp.tracers.EvolutionProfile(storer, constraints=constraints)
    profile.set_date_intervals(INTERVAL, CUSTOM_INTERVAL)
    profile.set_depth_interval(DEPTH_INTERVAL)
    if SHOW:
        profile.show(VARIABLE)
    if SAVE:
        date_min_str = DATE_MIN.strftime("%Y%m%d")
        date_max_str = DATE_MAX.strftime("%Y%m%d")
        save_name = f"profile_{VARIABLE}_{date_min_str}_{date_max_str}.png"
        profile.save(
            save_path=f"{CONFIG['SAVING_DIR']}/{save_name}",
            variable_name=VARIABLE,
        )
