"""Match Observation data to their equivalent in a simulation dataset."""
import datetime as dt
from pathlib import Path

import bgc_data_processing as bgc_dp
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from cartopy import feature

CONFIG_FOLDER = Path("config")

if __name__ == "__main__":
    config_filepath = CONFIG_FOLDER.joinpath(Path(__file__).stem)
    CONFIG = bgc_dp.parsers.ConfigParser(
        filepath=config_filepath.with_suffix(".toml"),
        check_types=False,
        dates_vars_keys=[],
        dirs_vars_keys=["SAVING_DIR"],
        existing_directory="raise",
    )
    LOADING_DIR: Path = Path(CONFIG["LOADING_DIR"])
    SIM_PROVIDER: str = CONFIG["SIM_PROVIDER"]
    TO_INTERPOLATE: list[str] = CONFIG["TO_INTERPOLATE"]
    INTERPOLATION_KIND: str = CONFIG["INTERPOLATION_KIND"]
    LATITUDE_TEMPLATE = bgc_dp.defaults.VARS["latitude"]
    SALINITY_TEMPLATE = bgc_dp.defaults.VARS["salinity"]
    TEMPERATURE_TEMPLATE = bgc_dp.defaults.VARS["temperature"]
    DEPTH_TEMPLATE = bgc_dp.defaults.VARS["depth"]
    RESULT_OUTPUT_FILE: Path = Path(CONFIG["RESULT_OUTPUT_FILE"])
    VARIABLES_TO_COMPARE: list[str] = CONFIG["VARIABLES_TO_COMPARE"]
    VARIABLES_TO_COMPARE: list[str] = CONFIG["VARIABLES_TO_COMPARE"]
    DATE_MIN: dt.datetime = CONFIG["DATE_MIN"]
    DATE_MAX: dt.datetime = CONFIG["DATE_MAX"]
    LATITUDE_MIN: int | float = CONFIG["LATITUDE_MIN"]
    LATITUDE_MAX: int | float = CONFIG["LATITUDE_MAX"]
    LONGITUDE_MIN: int | float = CONFIG["LONGITUDE_MIN"]
    LONGITUDE_MAX: int | float = CONFIG["LONGITUDE_MAX"]
    DEPTH_MIN: int | float = CONFIG["DEPTH_MIN"]
    DEPTH_MAX: int | float = CONFIG["DEPTH_MAX"]
    SHOW_MAP: bool = CONFIG["SHOW_MAP"]

    bgc_dp.set_verbose_level(CONFIG["VERBOSE"])

    observations = bgc_dp.io.read_files(
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
    variables = observations.variables
    constraints = bgc_dp.Constraints()
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
    observations = constraints.apply_constraints_to_storer(observations)

    selector = bgc_dp.SelectiveDataSource.from_data_source(
        reference=observations,
        strategy=bgc_dp.comparison.NearestNeighborStrategy(metric="haversine"),
        dsource=bgc_dp.providers.PROVIDERS["HYCOM"],
    )
    simulations = selector.load_all(bgc_dp.Constraints())

    interpolator = bgc_dp.comparison.Interpolator(
        base=simulations,
        x_column_name=DEPTH_TEMPLATE.label,
        y_columns_name=TO_INTERPOLATE,
        kind=INTERPOLATION_KIND,
    )
    interpolated = interpolator.interpolate_storer(
        observations,
    )
    # Add pressure
    pres_feat = bgc_dp.features.Pressure(DEPTH_TEMPLATE, LATITUDE_TEMPLATE)
    pres_feat.insert_in_storer(observations)
    pres_feat.insert_in_storer(interpolated)
    # Add potential temperature
    ptemp_feat = bgc_dp.features.PotentialTemperature(
        SALINITY_TEMPLATE,
        TEMPERATURE_TEMPLATE,
        pres_feat.variable,
    )
    ptemp_feat.insert_in_storer(observations)
    ptemp_feat.insert_in_storer(interpolated)
    save_vars = [
        var.label
        for var in observations.variables
        if var.name != observations.variables.date_var_name
    ]
    observations_save = observations.slice_using_index(interpolated.data.index)

    SAVING_DIR = Path(CONFIG["SAVING_DIR"])

    obs_saver = bgc_dp.savers.StorerSaver(observations_save)
    obs_saver.saving_order = save_vars
    obs_saver.save_all_storer(SAVING_DIR.joinpath("observations.txt"))

    int_saver = bgc_dp.savers.StorerSaver(interpolated)
    int_saver.saving_order = save_vars
    int_saver.save_all_storer(SAVING_DIR.joinpath("simulations.txt"))

    obs = bgc_dp.io.read_files(
        SAVING_DIR.joinpath("observations.txt"),
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

    sims = bgc_dp.io.read_files(
        SAVING_DIR.joinpath("simulations.txt"),
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

    rmse = bgc_dp.metrics.RMSE(VARIABLES_TO_COMPARE)
    rmse_value = rmse.evaluate_storers(obs, sims)

    bias = bgc_dp.metrics.Bias(VARIABLES_TO_COMPARE)
    bias_value = bias.evaluate_storers(obs, sims)

    concat_values = pd.concat([rmse_value, bias_value], axis=1)

    print("\n---------------- Results ----------------")

    print(concat_values)

    print("-----------------------------------------\n")

    values_format = "%-10s " + " ".join(["%10.3f" for _ in concat_values.columns])
    names_format = "%-10s " + " ".join(["%10s" for _ in concat_values.columns])
    concat_values.reset_index(names="Variable", inplace=True)
    with RESULT_OUTPUT_FILE.open("w") as file:
        file.write("---------- Boundaries ----------\n")
        file.write(f"Date:      [ {DATE_MIN}; {DATE_MAX}]\n")
        file.write(f"Longitude: [ {LONGITUDE_MIN}; {LONGITUDE_MAX}]\n")
        file.write(f"Latitude:  [ {LATITUDE_MIN}; {LATITUDE_MAX}]\n")
        file.write(f"Depth:     [ {DEPTH_MIN}; {DEPTH_MAX}]\n")
        file.write("--------------------------------\n\n")
        file.write(names_format % tuple(concat_values.columns) + "\n")
        file.writelines(
            concat_values.apply(lambda x: values_format % tuple(x) + "\n", axis=1),
        )

    if SHOW_MAP:
        selected_obs = obs.data[
            [obs.variables.get(name).label for name in VARIABLES_TO_COMPARE]
        ]
        selected_sims = sims.data[
            [sims.variables.get(name).label for name in VARIABLES_TO_COMPARE]
        ]
        nan_sim = selected_sims.isna().all(axis=1) | selected_obs.isna().all(axis=1)

        colors = ["red", "green", "blue", "pink", "yellow"]

        ax = plt.axes(projection=ccrs.Orthographic(0, 90))

        sim_lat = sims.data[~nan_sim][bgc_dp.defaults.VARS["latitude"].label]
        sim_lon = sims.data[~nan_sim][bgc_dp.defaults.VARS["longitude"].label]

        obs_lat = obs.data[~nan_sim][bgc_dp.defaults.VARS["latitude"].label]
        obs_lon = obs.data[~nan_sim][bgc_dp.defaults.VARS["longitude"].label]

        ax.set_extent(
            [
                min(np.min(obs_lon), np.min(sim_lon)) - 2,
                max(np.max(obs_lon), np.max(sim_lon)) + 2,
                min(np.min(obs_lat), np.min(sim_lat)) - 2,
                max(np.max(obs_lat), np.max(sim_lat)) + 2,
            ],
            crs=ccrs.PlateCarree(),
        )
        ax.add_feature(feature.LAND, zorder=1)
        ax.scatter(
            sim_lon,
            sim_lat,
            label="Simulations",
            c=[colors[p % len(colors)] for p in sims.data[~nan_sim].index.to_list()],
            marker="<",
            edgecolors="black",
            zorder=2,
            transform=ccrs.PlateCarree(),
        )
        ax.scatter(
            obs_lon,
            obs_lat,
            label="Observations",
            c=[colors[p % len(colors)] for p in obs.data[~nan_sim].index.to_list()],
            marker=">",
            edgecolors="black",
            zorder=2,
            transform=ccrs.PlateCarree(),
        )
        plt.legend()
        plt.show()
