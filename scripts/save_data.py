"""Data aggregation and saving script."""

import datetime as dt
from pathlib import Path
from time import time

from bgc_data_processing import (
    PROVIDERS_CONFIG,
    data_structures,
    parsers,
    providers,
    utils,
)

CONFIG_FOLDER = Path("config")

if __name__ == "__main__":
    config_filepath = CONFIG_FOLDER.joinpath(Path(__file__).stem)
    CONFIG = parsers.ConfigParser(
        filepath=config_filepath.with_suffix(".toml"),
        check_types=True,
        dates_vars_keys=["DATE_MIN", "DATE_MAX"],
        dirs_vars_keys=["SAVING_DIR"],
        existing_directory="raise",
    )
    SAVING_DIR = Path(CONFIG["SAVING_DIR"])
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
    PRIORITY = CONFIG["PRIORITY"]
    VERBOSE = CONFIG["VERBOSE"]

    # Dates parsing
    dates_generator = utils.dateranges.DateRangeGenerator(
        start=DATE_MIN,
        end=DATE_MAX,
        interval=INTERVAL,
        interval_length=CUSTOM_INTERVAL,
    )
    if VERBOSE > 0:
        txt = (
            f"Processing BGC data from {DATE_MIN.strftime('%Y%m%d')} to "
            f"{DATE_MAX.strftime('%Y%m%d')} provided by {', '.join(PROVIDERS)}"
        )
        print("\n\t" + "-" * len(txt))
        print("\t" + txt)
        print("\t" + "-" * len(txt) + "\n")
    # Iterate over data sources
    t0 = time()
    for data_src in PROVIDERS:
        if VERBOSE > 0:
            print(f"Loading data : {data_src}")
        dset_loader = providers.LOADERS[data_src]
        variables = dset_loader.variables
        dset_loader.set_saving_order(
            var_names=VARIABLES,
        )
        # Constraint slicer
        constraints = data_structures.Constraints()
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
        storer = dset_loader(
            constraints=constraints,
            exclude=PROVIDERS_CONFIG[data_src]["EXCLUDE"],
        )
        storer.remove_duplicates(PRIORITY)
        saver = data_structures.StorerSaver(storer=storer)
        saver.saving_order = VARIABLES
        saver.save_from_daterange(dates_generator, SAVING_DIR)
    if VERBOSE > 0:
        print("\n" + "\t" + "-" * len(txt))
        print("\t" + " " * (len(txt) // 2) + "DONE")
        print("\t" + "-" * len(txt) + "\n")
    print(time() - t0)
