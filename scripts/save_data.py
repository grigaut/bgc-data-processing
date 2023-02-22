from time import time

import pandas as pd
from bgc_data_processing import CONFIG, data_providers, parsers
from bgc_data_processing.data_classes import Storer

if __name__ == "__main__":
    # Script arguments
    config_aggregation = CONFIG.aggregation
    YEARS: list[int] = config_aggregation["YEARS"]
    VARIABLES: list[str] = config_aggregation["VARIABLES"]
    LATITUDE_MIN: int | float = config_aggregation["LATITUDE_MIN"]
    LATITUDE_MAX: int | float = config_aggregation["LATITUDE_MAX"]
    LONGITUDE_MIN: int | float = config_aggregation["LONGITUDE_MIN"]
    LONGITUDE_MAX: int | float = config_aggregation["LONGITUDE_MAX"]
    PROVIDERS = config_aggregation["PROVIDERS"]
    LIST_DIR = config_aggregation["LIST_DIR"]
    VERBOSE = CONFIG.utils["VERBOSE"]
    SAVING_DIR = CONFIG.utils["SAVING_DIR"]

    drngs = []
    aggr_date_names = []
    full_year_rows = []
    # cycle dates parsing
    for year in YEARS:
        # Collect cycle dates
        cycle_file = f"{LIST_DIR}/ran_cycle_{year}.txt"
        parser = parsers.RanCycleParser(filepath=cycle_file)
        drng = parser.get_daterange(start=4, end=3)
        aggr_date_names.append(parser.first_dates)
        drngs.append(drng)
    DRNG = pd.concat(drngs, ignore_index=True)
    str_start = pd.to_datetime(DRNG["start_date"]).dt.strftime("%Y%m%d")
    str_end = pd.to_datetime(DRNG["end_date"]).dt.strftime("%Y%m%d")
    dates_str = str_start + "-" + str_end
    aggr_date_names = pd.concat(aggr_date_names, ignore_index=True).astype(str)
    if VERBOSE > 0:
        years_txt = ", ".join([str(x) for x in YEARS])
        txt = f"Processing BGC data from {years_txt} provided by {', '.join(PROVIDERS)}"
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
        dset_loader.set_verbose(VERBOSE)
        # Loading data
        df = dset_loader(exclude=CONFIG.providers[data_src]["EXCLUDE"])
        # Slicing data
        if VERBOSE > 0:
            print("Slicing data : {}".format(data_src))
        slices_index = DRNG.apply(df.slice_on_dates, axis=1)
        # Saving slices
        if VERBOSE > 0:
            print("saving slices : {}".format(data_src))
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
        # Slicing aggregated data
        slices_index = DRNG.apply(
            df.slice_on_dates,
            axis=1,
        )
        # Saving aggregated data's slices
        if VERBOSE > 0:
            print("Saving aggregated data")
        to_save = pd.concat(
            [aggr_date_names, slices_index], keys=["dates", "slice"], axis=1
        )
        make_name = lambda x: f"{SAVING_DIR}/bgc_{category}_{x['dates']}.txt"
        to_save.apply(lambda x: x["slice"].save(make_name(x)), axis=1)
    if VERBOSE > 0:
        print("\n" + "\t" + "-" * len(txt))
        print("\t" + " " * (len(txt) // 2) + "DONE")
        print("\t" + "-" * len(txt) + "\n")
    print(time() - t0)
