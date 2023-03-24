"""Evolution profile plotting Script."""

import datetime as dt

from bgc_data_processing import PROVIDERS_CONFIG, data_providers, parsers
from bgc_data_processing.data_classes import DataSlicer, Storer
from bgc_data_processing.tracers import EvolutionProfile

if __name__ == "__main__":
    # Script arguments
    CONFIG = parsers.ConfigParser(
        "config/plot_profile.toml",
        check_types=True,
        dates_vars_keys=["DATE_MIN", "DATE_MAX"],
        dirs_vars_keys=["SAVING_DIR"],
        existing_directory="raise",
    )
    DATE_MIN: dt.datetime = CONFIG["DATE_MIN"]
    DATE_MAX: dt.datetime = CONFIG["DATE_MAX"]
    DEPTH_MIN: int | float = CONFIG["DEPTH_MIN"]
    DEPTH_MAX: int | float = CONFIG["DEPTH_MAX"]
    LATITUDE_CENTER: int | float = CONFIG["LATITUDE_CENTER"]
    LONGITUDE_CENTER: int | float = CONFIG["LONGITUDE_CENTER"]
    BIN_SIZE: list | int | float = CONFIG["BIN_SIZE"]
    INTERVAL: str = CONFIG["INTERVAL"]
    CUSTOM_INTERVAL: int = CONFIG["CUSTOM_INTERVAL"]
    DEPTH_INTERVAL: int = CONFIG["DEPTH_INTERVAL"]
    VARIABLE: str = CONFIG["VARIABLE"]
    PROVIDERS: list[str] = CONFIG["PROVIDERS"]
    EXPOCODES_TO_LOAD: list[str] = CONFIG["EXPOCODES_TO_LOAD"]
    PRIORITY: list[str] = CONFIG["PRIORITY"]
    SHOW: bool = CONFIG["SHOW"]
    SAVE: bool = CONFIG["SAVE"]
    VERBOSE: int = CONFIG["VERBOSE"]

    data_dict = {}
    for data_src in PROVIDERS:
        if VERBOSE > 0:
            print("Loading data : {}".format(data_src))
        exclude = PROVIDERS_CONFIG[data_src]["EXCLUDE"]
        dset_loader = data_providers.LOADERS[data_src]
        variables = dset_loader.variables
        constraints = DataSlicer()
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
            minimal_value=LATITUDE_CENTER - BIN_SIZE[0],
            maximal_value=LATITUDE_CENTER + BIN_SIZE[0],
        )
        constraints.add_boundary_constraint(
            field_label=variables.get(variables.longitude_var_name).label,
            minimal_value=LONGITUDE_CENTER - BIN_SIZE[1],
            maximal_value=LONGITUDE_CENTER + BIN_SIZE[1],
        )
        constraints.add_boundary_constraint(
            field_label=variables.get(variables.depth_var_name).label,
            minimal_value=DEPTH_MIN,
            maximal_value=DEPTH_MAX,
        )
        dset_loader.set_verbose(VERBOSE)
        storer = dset_loader(exclude=exclude, constraints=constraints)
        category = dset_loader.category
        if category not in data_dict.keys():
            data_dict[category] = []
        data_dict[category].append(storer)
    for category, data in data_dict.items():
        if VERBOSE > 0:
            print(f"Plotting {category} data")
        storer: Storer = sum(data)
        storer.remove_duplicates(priority_list=PRIORITY)
        variables = storer.variables
        profile = EvolutionProfile(storer)
        profile.set_date_intervals(INTERVAL, CUSTOM_INTERVAL)
        profile.set_depth_interval(DEPTH_INTERVAL)
        if SHOW:
            profile.show(VARIABLE)
        if SAVE:
            date_min_str = DATE_MIN.strftime("%Y%m%d")
            date_max_str = DATE_MAX.strftime("%Y%m%d")
            save_name = f"profile_{VARIABLE}_{date_min_str}_{date_max_str}.png"
            profile.save(
                save_path=f"{CONFIG['SAVING_DIR']}/{save_name}",
                variable_name=VARIABLE,
            )
