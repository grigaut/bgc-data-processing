"""Extract Data from a given domain or polygon."""

import datetime as dt
from pathlib import Path

import bgc_data_processing as bgc_dp
import shapely

CONFIG_FOLDER = Path("config")

if __name__ == "__main__":
    config_filepath = CONFIG_FOLDER.joinpath(Path(__file__).stem)
    CONFIG = bgc_dp.parsers.ConfigParser(
        filepath=config_filepath.with_suffix(".toml"),
        check_types=True,
        dates_vars_keys=["DATE_MIN", "DATE_MAX"],
        dirs_vars_keys=["SAVING_DIR"],
        existing_directory="raise",
    )
    LOADING_DIR = Path(CONFIG["LOADING_DIR"])
    SAVING_DIR = Path(CONFIG["SAVING_DIR"])
    DATE_MIN: dt.datetime = CONFIG["DATE_MIN"]
    DATE_MAX: dt.datetime = CONFIG["DATE_MAX"]
    FROM_POLYGON: bool = CONFIG["FROM_POLYGON"]
    POLYGON_DOMAIN: str = CONFIG["POLYGON_DOMAIN"]
    LATITUDE_MIN: float = CONFIG["LATITUDE_MIN"]
    LATITUDE_MAX: float = CONFIG["LATITUDE_MAX"]
    LONGITUDE_MIN: float = CONFIG["LONGITUDE_MIN"]
    LONGITUDE_MAX: float = CONFIG["LONGITUDE_MAX"]
    VERBOSE: int = CONFIG["VERBOSE"]
    PRIORITY: list[str] = CONFIG["PRIORITY"]

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
    constraints.add_boundary_constraint(
        field_label=variables.get(variables.date_var_name).label,
        minimal_value=DATE_MIN,
        maximal_value=DATE_MAX,
    )
    if FROM_POLYGON:
        constraints.add_polygon_constraint(
            latitude_field=variables.get(variables.latitude_var_name).label,
            longitude_field=variables.get(variables.longitude_var_name).label,
            polygon=shapely.from_wkt(POLYGON_DOMAIN),
        )
    else:
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
    sliced_storer = constraints.apply_constraints_to_storer(storer)

    bgc_dp.save_storer(
        sliced_storer,
        filepath=SAVING_DIR.joinpath("extracted_domain_data.txt"),
        saving_order=[
            col
            for col in sliced_storer.data.columns
            if col != variables.get(variables.date_var_name).label
        ],
        save_aggregated_data_only=True,
    )
