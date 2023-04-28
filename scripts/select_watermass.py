"""Select Water Mass based on salinity / potential temperature and density0 values."""

import datetime as dt
from pathlib import Path

from bgc_data_processing import features
from bgc_data_processing.data_classes import Constraints, Storer
from bgc_data_processing.parsers import ConfigParser
from bgc_data_processing.tracers import VariableBoxPlot

if __name__ == "__main__":
    CONFIG = ConfigParser(
        filepath="config/select_watermass.toml",
        dates_vars_keys=["DATE_MIN", "DATE_MAX"],
        dirs_vars_keys=["SAVING_DIR"],
        existing_directory="raise",
    )
    LOADING_DIR: Path = Path(CONFIG["LOADING_DIR"])
    SAVING_DIR: Path = Path(CONFIG["SAVING_DIR"])
    SHOW: bool = CONFIG["SHOW"]
    SAVE: bool = CONFIG["SAVE"]
    PLOT_VARIABLE: str = CONFIG["PLOT_VARIABLE"]
    BOXPLOT_PERIOD: str = CONFIG["BOXPLOT_PERIOD"]
    DATE_MIN: dt.datetime = CONFIG["DATE_MIN"]
    DATE_MAX: dt.datetime = CONFIG["DATE_MAX"]
    LATITUDE_MIN: int | float = CONFIG["LATITUDE_MIN"]
    LATITUDE_MAX: int | float = CONFIG["LATITUDE_MAX"]
    LONGITUDE_MIN: int | float = CONFIG["LONGITUDE_MIN"]
    LONGITUDE_MAX: int | float = CONFIG["LONGITUDE_MAX"]
    SALINITY_MIN: int | float = CONFIG["SALINITY_MIN"]
    SALINITY_MAX: int | float = CONFIG["SALINITY_MAX"]
    POTENTIAL_TEMPERATURE_MIN: int | float = CONFIG["POTENTIAL_TEMPERATURE_MIN"]
    POTENTIAL_TEMPERATURE_MAX: int | float = CONFIG["POTENTIAL_TEMPERATURE_MAX"]
    DENSITY0_MIN: int | float = CONFIG["DENSITY0_MIN"]
    DENSITY0_MAX: int | float = CONFIG["DENSITY0_MAX"]
    DEPTH_MIN: int | float = CONFIG["DEPTH_MIN"]
    DEPTH_MAX: int | float = CONFIG["DEPTH_MAX"]
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
    # Add relevant features to the data: Pressure / potential temperature /density0
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
    dens0_var, dens0_data = features.compute_density_p0(
        storer=storer,
        salinity_field="PSAL",
        temperature_field="TEMP",
    )
    storer.add_feature(dens0_var, dens0_data)
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
    constraints.add_boundary_constraint(
        field_label=variables.get(variables.depth_var_name).label,
        minimal_value=DEPTH_MIN,
        maximal_value=DEPTH_MAX,
    )
    constraints.add_boundary_constraint(
        field_label="PSAL",
        minimal_value=SALINITY_MIN,
        maximal_value=SALINITY_MAX,
    )
    constraints.add_boundary_constraint(
        field_label=ptemp_var.label,
        minimal_value=POTENTIAL_TEMPERATURE_MIN,
        maximal_value=POTENTIAL_TEMPERATURE_MAX,
    )
    constraints.add_boundary_constraint(
        field_label=dens0_var.label,
        minimal_value=DENSITY0_MIN,
        maximal_value=DENSITY0_MAX,
    )

    plot = VariableBoxPlot(
        storer=storer,
        constraints=constraints,
    )
    if SHOW:
        plot.show(
            variable_name=PLOT_VARIABLE,
            period=BOXPLOT_PERIOD,
        )
    if SAVE:
        filename = f"{PLOT_VARIABLE.lower()}_{BOXPLOT_PERIOD}ly_boxplot.png"
        filepath = SAVING_DIR.joinpath(filename)
        plot.save(
            variable_name=PLOT_VARIABLE,
            period=BOXPLOT_PERIOD,
            save_path=filepath,
        )
