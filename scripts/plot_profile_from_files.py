"""Create an Evolution Profile from files in a directory."""

import os
from bgc_data_processing.parsers import ConfigParser
from bgc_data_processing.data_classes import Storer
from bgc_data_processing.tracers import EvolutionProfile
import datetime as dt

if __name__ == "__main__":
    CONFIG = ConfigParser(
        filepath="config/plot_profile_from_files.toml",
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
    LATITUDE_CENTER: int | float = CONFIG["LATITUDE_CENTER"]
    LONGITUDE_CENTER: int | float = CONFIG["LONGITUDE_CENTER"]
    DEPTH_MIN: int | float = CONFIG["DEPTH_MIN"]
    DEPTH_MAX: int | float = CONFIG["DEPTH_MAX"]
    BIN_SIZE: list | int | float = CONFIG["BIN_SIZE"]
    INTERVAL: str = CONFIG["INTERVAL"]
    CUSTOM_INTERVAL: int = CONFIG["CUSTOM_INTERVAL"]
    DEPTH_INTERVAL: int = CONFIG["DEPTH_INTERVAL"]
    SAVING_DIR: str = CONFIG["SAVING_DIR"]
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
    storer.remove_duplicates(priority_list=PRIORITY)
    profile = EvolutionProfile(storer)
    profile.set_dates_boundaries(DATE_MIN, DATE_MAX)
    profile.set_depth_boundaries(DEPTH_MIN, DEPTH_MAX)
    profile.set_geographic_bin(LATITUDE_CENTER, LONGITUDE_CENTER, BIN_SIZE)
    profile.set_date_intervals(INTERVAL, CUSTOM_INTERVAL)
    profile.set_depth_interval(DEPTH_INTERVAL)
    if SHOW:
        profile.show(VARIABLE)
    if SAVE:
        date_min_str = DATE_MIN.strftime("%Y%m%d")
        date_max_str = DATE_MAX.strftime("%Y%m%d")
        save_name = f"profile_{VARIABLE}_{date_min_str}_{date_max_str}.png"
        profile.save(
            save_path=f"{SAVING_DIR}/{save_name}",
            variable_name=VARIABLE,
        )
