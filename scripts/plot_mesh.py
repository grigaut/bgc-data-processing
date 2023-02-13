import datetime as dt
import sys

from bgc_data_processing import CONFIG, data_providers
from bgc_data_processing.base import Storer
from bgc_data_processing.mapper.tracers import GeoMesher

BIN_SIZE = tuple(CONFIG["MAPPING"]["BINS_SIZE"])
EXCLUDE = CONFIG["MAPPING"]["EXCLUDE"]


def get_args(sys_argv: list) -> tuple[list[str], list[str], int]:
    year_min = int(sys_argv[1])
    year_max = int(sys.argv[2])
    var_name = sys.argv[3]
    if len(sys_argv) > 4:
        list_src = sys_argv[4].split(",")
    else:
        list_src = sorted(list(data_providers.LOADERS.keys()))
    if len(sys_argv) > 5:
        try:
            verbose = int(sys_argv[5])
        except ValueError:
            verbose = 0
    else:
        verbose = 1
    return year_min, year_max, var_name, list_src, verbose


if __name__ == "__main__":
    # Script arguments
    YEAR_MIN, YEAR_MAX, VAR_NAME, LIST_SRC, VERBOSE = get_args(sys.argv)
    data_dict = {}
    for data_src in LIST_SRC:
        if VERBOSE > 0:
            print("Loading data : {}".format(data_src))
        if data_src in EXCLUDE.keys():
            exclude = EXCLUDE[data_src]
        else:
            exclude = []
        dset_loader = data_providers.LOADERS[data_src]
        dset_loader.set_date_boundaries(
            date_min=dt.datetime(YEAR_MIN, 1, 1),
            date_max=dt.datetime(YEAR_MAX, 12, 31),
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
        storer = dset_loader(exclude=exclude)
        category = dset_loader.category
        if category not in data_dict.keys():
            data_dict[category] = []
        data_dict[category].append(storer)
    for category, data in data_dict.items():
        df: Storer = sum(data)
        GeoMesher(df).plot(VAR_NAME, BIN_SIZE)
