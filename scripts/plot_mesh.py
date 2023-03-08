import datetime as dt

from bgc_data_processing import CONFIG, data_providers
from bgc_data_processing.data_classes import Storer
from bgc_data_processing.tracers import MeshPlotter

if __name__ == "__main__":
    # Script arguments
    config_mapping = CONFIG.mapping
    DATE_MIN: dt.datetime = config_mapping["DATE_MIN"]
    DATE_MAX: dt.datetime = config_mapping["DATE_MAX"]
    LATITUDE_MIN: int | float = config_mapping["LATITUDE_MIN"]
    LATITUDE_MAX: int | float = config_mapping["LATITUDE_MAX"]
    LONGITUDE_MIN: int | float = config_mapping["LONGITUDE_MIN"]
    LONGITUDE_MAX: int | float = config_mapping["LONGITUDE_MAX"]
    BIN_SIZE: list | int | float = config_mapping["BIN_SIZE"]
    VARIABLE: str = config_mapping["VARIABLE"]
    PROVIDERS: list[str] = config_mapping["PROVIDERS"]
    DEPTH_AGGREGATION: str = config_mapping["DEPTH_AGGREGATION"]
    BIN_AGGREGATION: str = config_mapping["BIN_AGGREGATION"]
    VERBOSE: int = CONFIG.utils["VERBOSE"]

    data_dict = {}
    for data_src in PROVIDERS:
        if VERBOSE > 0:
            print("Loading data : {}".format(data_src))
        exclude = CONFIG.providers[data_src]["EXCLUDE"]
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
