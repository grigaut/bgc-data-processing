"""Compute metrics over simulated and observed data."""

from pathlib import Path

import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np
from bgc_data_processing import DEFAULT_VARS, data_structures, parsers
from cartopy import feature

CONFIG_FOLDER = Path("config")

if __name__ == "__main__":
    config_filepath = CONFIG_FOLDER.joinpath(Path(__file__).stem)

    CONFIG = parsers.ConfigParser(
        filepath=config_filepath.with_suffix(".toml"),
        check_types=False,
        dates_vars_keys=[],
        dirs_vars_keys=[],
        existing_directory="raise",
    )

    OBSERVATIONS_FILE: Path = Path(CONFIG["OBSERVATIONS_FILE"])
    SIMULATIONS_FILE: Path = Path(CONFIG["SIMULATIONS_FILE"])
    VARIABLES_TO_COMPARE: list[str] = CONFIG["VARIABLES_TO_COMPARE"]
    SHOW_MAP: bool = CONFIG["SHOW_MAP"]

    obs = data_structures.read_files(
        OBSERVATIONS_FILE,
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
        verbose=1,
    )

    sims = data_structures.read_files(
        SIMULATIONS_FILE,
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
        verbose=1,
    )

    selected_obs = obs.data[
        [obs.variables.get(name).label for name in VARIABLES_TO_COMPARE]
    ]
    selected_sims = sims.data[
        [sims.variables.get(name).label for name in VARIABLES_TO_COMPARE]
    ]

    nan_sim = selected_sims.isna().all(axis=1)

    diff_2 = np.power(selected_obs[~nan_sim] - selected_sims[~nan_sim], 2)

    print("\n---------------- RMSE ----------------")

    print(np.sqrt(np.mean(diff_2, axis=0)))

    print("--------------------------------------\n")

    if SHOW_MAP:

        colors = ["red", "green", "blue", "pink", "yellow"]

        ax = plt.axes(projection=ccrs.Orthographic(0, 90))

        sim_lat = sims.data[~nan_sim][DEFAULT_VARS["latitude"].label]
        sim_lon = sims.data[~nan_sim][DEFAULT_VARS["longitude"].label]

        obs_lat = obs.data[~nan_sim][DEFAULT_VARS["latitude"].label]
        obs_lon = obs.data[~nan_sim][DEFAULT_VARS["longitude"].label]

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
