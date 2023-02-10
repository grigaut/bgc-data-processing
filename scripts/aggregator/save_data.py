import sys
from time import time

import pandas as pd
from bgc_data_processing import CONFIG, data_providers, lists_reader
from bgc_data_processing.base import Storer


def get_args(sys_argv: list) -> tuple[list[str], list[str], int]:
    years = sys_argv[1].split(",")
    if len(sys_argv) > 2:
        list_src = sys_argv[2].split(",")
    else:
        list_src = sorted(list(data_providers.LOADERS.keys()))
    if len(sys_argv) > 3:
        try:
            verbose = int(sys_argv[3])
        except ValueError:
            verbose = 0
    else:
        verbose = 1
    return years, list_src, verbose


if __name__ == "__main__":
    # Script arguments
    SAVE_INTERMEDIARY = True
    YEARS, LIST_SRC, VERBOSE = get_args(sys.argv)

    drngs = []
    aggr_date_names = []
    full_year_rows = []
    # cycle dates parsing
    for year in YEARS:
        # Collect cycle dates
        cycle_file = f"{CONFIG['LOADING']['LIST_DIR']}/ran_cycle_{year}.txt"
        drng = lists_reader.parse_cycle_file(
            filepath=cycle_file,
            start=4,
            end=3,
        )
        aggr_date_names.append(lists_reader.get_first_date(filepath=cycle_file))
        drngs.append(drng)
    DRNG = pd.concat(drngs, ignore_index=True)
    str_start = pd.to_datetime(DRNG["start_date"]).dt.strftime("%Y%m%d")
    str_end = pd.to_datetime(DRNG["end_date"]).dt.strftime("%Y%m%d")
    dates_str = str_start + "-" + str_end
    aggr_date_names = pd.concat(aggr_date_names).astype(str)
    if VERBOSE > 0:
        txt = f"Processing BGC data from {', '.join(YEARS)} provided by {', '.join(LIST_SRC)}"
        print("\n\t" + "-" * len(txt))
        print("\t" + txt)
        print("\t" + "-" * len(txt) + "\n")
    data_dict = {}
    # Iterate over data sources
    t0 = time()
    for data_src in LIST_SRC:
        if VERBOSE > 0:
            print("Loading data : {}".format(data_src))
        dset_loader = data_providers.LOADERS[data_src]
        dset_loader.set_date_boundaries(
            date_min=DRNG.values.min(),
            date_max=DRNG.values.max(),
        )
        dset_loader.set_latitude_boundaries(
            latitude_min=50,
            latitude_max=89,
        )
        dset_loader.set_longitude_boundaries(
            longitude_min=-40,
            longitude_max=40,
        )
        dset_loader.set_verbose(VERBOSE)
        # -------------------------------
        # LOADING DATA
        # -------------------------------
        df = dset_loader()
        if SAVE_INTERMEDIARY:
            # -------------------------------
            # SLICING DATA
            # -------------------------------
            if VERBOSE > 0:
                print("Slicing data : {}".format(data_src))
            slices_index = DRNG.apply(
                df.slice_on_dates,
                axis=1,
            )
            # -------------------------------
            # SAVING SLICES
            # -------------------------------
            if VERBOSE > 0:
                print("saving slices : {}".format(data_src))
            to_save = pd.concat(
                [dates_str, slices_index], keys=["dates", "slice"], axis=1
            )
            make_name = (
                lambda x: f"{CONFIG['SAVING']['FILES_DIR']}/{data_src}/nutrients_{data_src}_{x['dates']}.csv"
            )
            to_save.apply(
                lambda x: x["slice"].save(make_name(x)),
                axis=1,
            )
            if VERBOSE > 0:
                print(
                    "\n-------Loading, Slicing, Saving completed for {}-------\n".format(
                        data_src
                    )
                )
            else:
                if VERBOSE > 0:
                    print(
                        "\n-----------Loading completed for {}-----------\n".format(
                            data_src
                        )
                    )
        category = dset_loader.category
        if category not in data_dict.keys():
            data_dict[category] = []
        data_dict[category].append(df)
    for category, data in data_dict.items():
        # -------------------------------
        # AGGREGATING DATA
        # -------------------------------
        if VERBOSE > 0:
            print("Aggregating data")
        df: Storer = sum(data)
        # -------------------------------
        # SLICING AGGREGATED DATA
        # -------------------------------
        slices_index = DRNG.apply(
            df.slice_on_dates,
            axis=1,
        )
        # -------------------------------
        # SAVING SLICES OF AGGREGATED DATA
        # -------------------------------
        if VERBOSE > 0:
            print("Saving aggregated data")
        to_save = pd.concat(
            [aggr_date_names, slices_index], keys=["dates", "slice"], axis=1
        )
        make_name = (
            lambda x: f"{CONFIG['SAVING']['FILES_DIR']}/bgc_{category}_{x['dates']}.txt"
        )
        to_save.apply(
            lambda x: x["slice"].save(make_name(x)),
            axis=1,
        )
    if VERBOSE > 0:
        print("\n" + "\t" + "-" * len(txt))
        print("\t" + " " * (len(txt) // 2) + "DONE")
        print("\t" + "-" * len(txt) + "\n")
    print(time() - t0)
