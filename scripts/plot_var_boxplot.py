"""Plot Variable boxplot."""

import datetime as dt
from math import ceil
from pathlib import Path

import matplotlib.pyplot as plt
from bgc_data_processing import DEFAULT_VARS, DEFAULT_WATER_MASSES, features
from bgc_data_processing.data_classes import Constraints, Storer
from bgc_data_processing.parsers import ConfigParser
from bgc_data_processing.tracers import VariableBoxPlot
from bgc_data_processing.water_masses import WaterMass

if __name__ == "__main__":
    config_filepath = Path("config/plot_var_boxplot.toml")
    CONFIG = ConfigParser(
        filepath=config_filepath,
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
    ACRONYMS: list[str] = CONFIG["WATER_MASS_ACRONYMS"]
    WATER_MASSES: list[WaterMass] = [DEFAULT_WATER_MASSES[acro] for acro in ACRONYMS]
    EXPOCODES_TO_LOAD: list[str] = CONFIG["EXPOCODES_TO_LOAD"]
    PRIORITY: list[str] = CONFIG["PRIORITY"]
    VERBOSE: int = CONFIG["VERBOSE"]

    SALINITY_DEFAULT = DEFAULT_VARS["salinity"]
    TEMPERATURE_DEFAULT = DEFAULT_VARS["temperature"]

    filepaths_txt = list(LOADING_DIR.glob("*.txt"))
    filepaths_csv = list(LOADING_DIR.glob("*.csv"))
    filepaths = filepaths_txt + filepaths_csv

    storer = Storer.from_files(
        filepath=filepaths,
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
    # Add relevant features to the data: Pressure / potential temperature /sigmat
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

    # plot = VariableBoxPlot(
    #     storer=storer_wm,
    #     constraints=constraints,
    # )
    # suptitle = f"{PLOT_VARIABLE} Box Plot"
    # title = f"Water Mass: '{WATER_MASS.name}' ({WATER_MASS.acronym})"
    # if SHOW:
    #     plot.show(
    #         variable_name=PLOT_VARIABLE,
    #         period=BOXPLOT_PERIOD,
    #         title=title,
    #         suptitle=suptitle,
    #     )
    # if SAVE:
    #     filename = f"{PLOT_VARIABLE.lower()}_{BOXPLOT_PERIOD}ly_boxplot.png"
    #     filepath = SAVING_DIR.joinpath(filename)
    #     plot.save(
    #         variable_name=PLOT_VARIABLE,
    #         period=BOXPLOT_PERIOD,
    #         save_path=filepath,
    #         title=title,
    #         suptitle=suptitle,
    #     )

    nb_wmasses = len(WATER_MASSES)
    figure = plt.figure(figsize=(15, 15), layout="tight")
    for i, watermass in enumerate(WATER_MASSES):
        placement = f"{ceil(nb_wmasses/min(nb_wmasses,3))}{min(nb_wmasses,3)}{i+1}"
        axes = figure.add_subplot(int(placement))
        storer_wm = watermass.extract_from_storer(
            storer=storer,
            ptemperature_name=ptemp_var.label,
            salinity_name=SALINITY_DEFAULT.label,
            sigma_t_name=sigt_var.label,
        )
        plot = VariableBoxPlot(storer_wm, constraints)
        plot.plot_to_axes(PLOT_VARIABLE, period=BOXPLOT_PERIOD, ax=axes)
        axes.set_title(f"{watermass.name} ({watermass.acronym})")
    plt.suptitle(f"{PLOT_VARIABLE} Box Plots")
    if SAVE:
        filename = f"{PLOT_VARIABLE}_boxplots.png"
        plt.savefig(SAVING_DIR.joinpath(filename))
    if SHOW:
        plt.show()
