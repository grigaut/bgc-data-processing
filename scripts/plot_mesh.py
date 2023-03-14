"""Data 2D mesh plotting script."""

import datetime as dt

from bgc_data_processing import PLOT_CONFIG, PROVIDERS_CONFIG, data_providers
from bgc_data_processing.data_classes import Storer
from bgc_data_processing.tracers import MeshPlotter

if __name__ == "__main__":
    # Script arguments
    DATE_MIN: dt.datetime = PLOT_CONFIG["DATE_MIN"]
    DATE_MAX: dt.datetime = PLOT_CONFIG["DATE_MAX"]
    LATITUDE_MIN: int | float = PLOT_CONFIG["LATITUDE_MIN"]
    LATITUDE_MAX: int | float = PLOT_CONFIG["LATITUDE_MAX"]
    LONGITUDE_MIN: int | float = PLOT_CONFIG["LONGITUDE_MIN"]
    LONGITUDE_MAX: int | float = PLOT_CONFIG["LONGITUDE_MAX"]
    BIN_SIZE: list | int | float = PLOT_CONFIG["BIN_SIZE"]
    VARIABLE: str = PLOT_CONFIG["VARIABLE"]
    PROVIDERS: list[str] = PLOT_CONFIG["PROVIDERS"]
    DEPTH_AGGREGATION: str = PLOT_CONFIG["DEPTH_AGGREGATION"]
    BIN_AGGREGATION: str = PLOT_CONFIG["BIN_AGGREGATION"]
    PRIORITY: list[str] = PLOT_CONFIG["PRIORITY"]
    VERBOSE: int = PLOT_CONFIG["VERBOSE"]

    data_dict = {}
    for data_src in PROVIDERS:
        if VERBOSE > 0:
            print("Loading data : {}".format(data_src))
        exclude = PROVIDERS_CONFIG[data_src]["EXCLUDE"]
        dset_loader = data_providers.LOADERS[data_src]
        dset_loader.set_date_boundaries(
            date_min=DATE_MIN,
            date_max=DATE_MAX,
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
        storer = dset_loader(exclude=exclude)
        category = dset_loader.category
        if category not in data_dict.keys():
            data_dict[category] = []
        data_dict[category].append(storer)
    for category, data in data_dict.items():
        if VERBOSE > 0:
            print(f"Plotting {category} data")
        df: Storer = sum(data)
        df.remove_duplicates(priority_list=PRIORITY)
        date_min = DATE_MIN.strftime("%Y%m%d")
        date_max = DATE_MAX.strftime("%Y%m%d")
        MeshPlotter(df).plot(
            VARIABLE,
            BIN_SIZE,
            depth_aggr=DEPTH_AGGREGATION,
            bin_aggr=BIN_AGGREGATION,
            suptitle=(
                f"{VARIABLE} - {', '.join(PROVIDERS)} ({category})\n"
                f"{date_min}-{date_max}"
            ),
            extent=(
                LONGITUDE_MIN,
                LONGITUDE_MAX,
                LATITUDE_MIN,
                LATITUDE_MAX,
            ),
        )
