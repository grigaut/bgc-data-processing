"""Data aggregation and saving script."""

import datetime as dt
from pathlib import Path
from time import time

import pandas as pd
from bgc_data_processing import (
    PROVIDERS_CONFIG,
    data_providers,
    dateranges,
    parsers,
)
from bgc_data_processing.data_classes import Constraints, Storer

if __name__ == "__main__":
    # Script arguments
    config_filepath = Path("config/save_data.toml")
    CONFIG = parsers.ConfigParser(
        filepath=config_filepath,
        check_types=True,
        dates_vars_keys=["DATE_MIN", "DATE_MAX"],
        dirs_vars_keys=["SAVING_DIR"],
        existing_directory="raise",
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
    EXPOCODES_TO_LOAD: list[str] = CONFIG["EXPOCODES_TO_LOAD"]
    PROVIDERS = CONFIG["PROVIDERS"]
    SAVING_DIR = Path(CONFIG["SAVING_DIR"])
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
            print(f"Loading data : {data_src}")
        dset_loader = data_providers.LOADERS[data_src]
        variables = dset_loader.variables
        dset_loader.set_saving_order(
            var_names=VARIABLES,
        )
        # Constraint slicer
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
        dset_loader.set_verbose(VERBOSE)
        # Loading data
        df = dset_loader(
            constraints=constraints,
            exclude=PROVIDERS_CONFIG[data_src]["EXCLUDE"],
        )
        # Slicing data
        if VERBOSE > 0:
            print(f"Slicing data : {data_src}")
        slices_index = DRNG.apply(df.slice_on_dates, axis=1)
        # Saving slices
        if VERBOSE > 0:
            print(f"Saving slices : {data_src}")
        to_save = pd.concat([dates_str, slices_index], keys=["dates", "slice"], axis=1)

        make_name = lambda x: SAVING_DIR.joinpath(
            Path(f"{data_src}/nutrients_{data_src}_{x['dates']}.csv"),
        )

        to_save.apply(lambda x: x["slice"].save(make_name(x)), axis=1)
        if VERBOSE > 0:
            print(
                f"\n-------Loading, Slicing, Saving completed for {data_src}-------\n",
            )
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
        make_name = lambda x: SAVING_DIR.joinpath(
            Path(f"bgc_{category}_{x['dates']}.txt"),
        )
        to_save.apply(lambda x: x["slice"].save(make_name(x)), axis=1)
    if VERBOSE > 0:
        print("\n" + "\t" + "-" * len(txt))
        print("\t" + " " * (len(txt) // 2) + "DONE")
        print("\t" + "-" * len(txt) + "\n")
    print(time() - t0)
