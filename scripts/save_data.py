"""Data aggregation and saving script."""

import datetime as dt
from time import time

import pandas as pd

from bgc_data_processing import (
    PROVIDERS_CONFIG,
    parsers,
    data_providers,
    dateranges,
)
from bgc_data_processing.data_classes import Storer

if __name__ == "__main__":
    # Script arguments
    CONFIG = parsers.ConfigParser(
        "config/save_data.toml",
        check_types=True,
        dates_vars_keys=["DATE_MIN", "DATE_MAX"],
    )
    VARIABLES: list[str] = CONFIG["VARIABLES"]
    DATE_MIN: dt.datetime = CONFIG["DATE_MIN"]
    DATE_MAX: dt.datetime = CONFIG["DATE_MAX"]
    INTERVAL: str = CONFIG["INTERVAL"]
    CUSTOM_INTERVAL: int = CONFIG["CUSTOM_INTERVAL"]
    LATITUDE_MIN: int | float = CONFIG["LATITUDE_MIN"]
    LATITUDE_MAX: int | float = CONFIG["LATITUDE_MAX"]
    LONGITUDE_MIN: int | float = CONFIG["LONGITUDE_MIN"]
    LONGITUDE_MAX: int | float = CONFIG["LONGITUDE_MAX"]
    DEPTH_MIN: int | float = CONFIG["DEPTH_MIN"]
    DEPTH_MAX: int | float = CONFIG["DEPTH_MAX"]
    PROVIDERS = CONFIG["PROVIDERS"]
    SAVING_DIR = CONFIG["SAVING_DIR"]
    PRIORITY = CONFIG["PRIORITY"]
    VERBOSE = CONFIG["VERBOSE"]

    # Dates parsing
    dates_generator = dateranges.DateRangeGenerator(
        start=DATE_MIN,
        end=DATE_MAX,
        interval=INTERVAL,
        interval_length=CUSTOM_INTERVAL,
    )
    DRNG = dates_generator()
    str_start = pd.to_datetime(DRNG["start_date"]).dt.strftime("%Y%m%d")
    str_end = pd.to_datetime(DRNG["end_date"]).dt.strftime("%Y%m%d")
    dates_str = str_start + "-" + str_end
    if VERBOSE > 0:
        txt = (
            f"Processing BGC data from {DATE_MIN.strftime('%Y%m%d')} to "
            f"{DATE_MAX.strftime('%Y%m%d')} provided by {', '.join(PROVIDERS)}"
        )
        print("\n\t" + "-" * len(txt))
        print("\t" + txt)
        print("\t" + "-" * len(txt) + "\n")
    data_dict = {}
    # Iterate over data sources
    t0 = time()
    for data_src in PROVIDERS:
        if VERBOSE > 0:
            print("Loading data : {}".format(data_src))
        dset_loader = data_providers.LOADERS[data_src]
        dset_loader.set_saving_order(
            var_names=VARIABLES,
        )
        dset_loader.set_date_boundaries(
            date_min=DRNG.values.min(),
            date_max=DRNG.values.max(),
        )
        dset_loader.set_latitude_boundaries(
            latitude_min=LATITUDE_MIN,
            latitude_max=LATITUDE_MAX,
        )
        dset_loader.set_longitude_boundaries(
            longitude_min=LONGITUDE_MIN,
            longitude_max=LONGITUDE_MAX,
        )
        dset_loader.set_depth_boundaries(
            depth_min=DEPTH_MIN,
            depth_max=DEPTH_MAX,
        )
        dset_loader.set_verbose(VERBOSE)
        # Loading data
        df = dset_loader(exclude=PROVIDERS_CONFIG[data_src]["EXCLUDE"])
        # Slicing data
        if VERBOSE > 0:
            print("Slicing data : {}".format(data_src))
        slices_index = DRNG.apply(df.slice_on_dates, axis=1)
        # Saving slices
        if VERBOSE > 0:
            print("Saving slices : {}".format(data_src))
        to_save = pd.concat([dates_str, slices_index], keys=["dates", "slice"], axis=1)
        make_name = (
            lambda x: f"{SAVING_DIR}/{data_src}/nutrients_{data_src}_{x['dates']}.csv"
        )
        to_save.apply(lambda x: x["slice"].save(make_name(x)), axis=1)
        if VERBOSE > 0:
            print(
                f"\n-------Loading, Slicing, Saving completed for {data_src}-------\n"
            )
        else:
            if VERBOSE > 0:
                print(f"\n-----------Loading completed for {data_src}-----------\n")
        category = dset_loader.category
        if category not in data_dict.keys():
            data_dict[category] = []
        data_dict[category].append(df)
    for category, data in data_dict.items():
        # Aggregating data
        if VERBOSE > 0:
            print("Aggregating data")
        df: Storer = sum(data)
        df.remove_duplicates(priority_list=PRIORITY)
        # Slicing aggregated data
        slices_index = DRNG.apply(
            df.slice_on_dates,
            axis=1,
        )
        # Saving aggregated data's slices
        if VERBOSE > 0:
            print("Saving aggregated data")
        to_save = pd.concat([str_start, slices_index], keys=["dates", "slice"], axis=1)
        make_name = lambda x: f"{SAVING_DIR}/bgc_{category}_{x['dates']}.txt"
        to_save.apply(lambda x: x["slice"].save(make_name(x)), axis=1)
    if VERBOSE > 0:
        print("\n" + "\t" + "-" * len(txt))
        print("\t" + " " * (len(txt) // 2) + "DONE")
        print("\t" + "-" * len(txt) + "\n")
    print(time() - t0)
