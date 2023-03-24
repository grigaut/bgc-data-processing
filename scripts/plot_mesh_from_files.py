"""Create a 2d Mesh Plot from files in a directory."""

import os
from bgc_data_processing.parsers import ConfigParser
from bgc_data_processing.data_classes import Storer, DataSlicer
from bgc_data_processing.tracers import MeshPlotter
import datetime as dt

if __name__ == "__main__":
    CONFIG = ConfigParser(
        filepath="config/plot_mesh_from_files.toml",
        dates_vars_keys=["DATE_MIN", "DATE_MAX"],
        dirs_vars_keys=["SAVING_DIR"],
        existing_directory="raise",
    )
    LOADING_DIR: str = CONFIG["LOADING_DIR"]
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
    BIN_SIZE: list | int | float = CONFIG["BIN_SIZE"]
    CONSIDER_DEPTH: bool = CONFIG["CONSIDER_DEPTH"]
    EXPOCODES_TO_LOAD: list[str] = CONFIG["EXPOCODES_TO_LOAD"]
    PRIORITY: list[str] = CONFIG["PRIORITY"]
    VERBOSE: int = CONFIG["VERBOSE"]

    filepaths = [
        f"{LOADING_DIR}/{file}"
        for file in os.listdir(LOADING_DIR)
        if file[-4:] in [".csv", ".txt"]
    ]

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
        verbose=1,
    )
    storer.remove_duplicates(PRIORITY)
    variables = storer.variables
    constraints = DataSlicer()
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
    plot = MeshPlotter(storer, constraints=constraints)
    plot.set_density_type(consider_depth=CONSIDER_DEPTH)
    plot.set_bins_size(bins_size=BIN_SIZE)
    date_min = DATE_MIN.strftime("%Y%m%d")
    date_max = DATE_MAX.strftime("%Y%m%d")
    if SHOW:
        suptitle = f"{VARIABLE} - from {LOADING_DIR}\n" f"{date_min}-{date_max}"
        plot.show(
            variable_name=VARIABLE,
            suptitle=suptitle,
        )
    if SAVE:
        save_name = f"density_map_{VARIABLE}_{date_min}_{date_max}.png"
        suptitle = f"{VARIABLE} - from {LOADING_DIR}\n" f"{date_min}-{date_max}"
        plot.save(
            save_path=f"{CONFIG['SAVING_DIR']}/{save_name}",
            variable_name=VARIABLE,
            suptitle=suptitle,
        )
