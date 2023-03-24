"""Data 2D mesh plotting script."""

import datetime as dt

from bgc_data_processing import PROVIDERS_CONFIG, data_providers, parsers
from bgc_data_processing.data_classes import Storer, Constraints
from bgc_data_processing.tracers import MeshPlotter

if __name__ == "__main__":
    # Script arguments
    CONFIG = parsers.ConfigParser(
        "config/plot_mesh.toml",
        check_types=True,
        dates_vars_keys=["DATE_MIN", "DATE_MAX"],
        dirs_vars_keys=["SAVING_DIR"],
        existing_directory="raise",
    )
    DATE_MIN: dt.datetime = CONFIG["DATE_MIN"]
    DATE_MAX: dt.datetime = CONFIG["DATE_MAX"]
    LATITUDE_MIN: int | float = CONFIG["LATITUDE_MIN"]
    LATITUDE_MAX: int | float = CONFIG["LATITUDE_MAX"]
    LONGITUDE_MIN: int | float = CONFIG["LONGITUDE_MIN"]
    LONGITUDE_MAX: int | float = CONFIG["LONGITUDE_MAX"]
    DEPTH_MIN: int | float = CONFIG["DEPTH_MIN"]
    DEPTH_MAX: int | float = CONFIG["DEPTH_MAX"]
    BIN_SIZE: list | int | float = CONFIG["BIN_SIZE"]
    VARIABLE: str = CONFIG["VARIABLE"]
    PROVIDERS: list[str] = CONFIG["PROVIDERS"]
    PRIORITY: list[str] = CONFIG["PRIORITY"]
    CONSIDER_DEPTH: bool = CONFIG["CONSIDER_DEPTH"]
    EXPOCODES_TO_LOAD: list[str] = CONFIG["EXPOCODES_TO_LOAD"]
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
        date_min = DATE_MIN.strftime("%Y%m%d")
        date_max = DATE_MAX.strftime("%Y%m%d")
        plot = MeshPlotter(storer)
        plot.set_density_type(consider_depth=CONSIDER_DEPTH)
        plot.set_bins_size(bins_size=BIN_SIZE)
        if SHOW:
            suptitle = (
                f"{VARIABLE} - {', '.join(PROVIDERS)} ({category})\n"
                f"{date_min}-{date_max}"
            )
            plot.show(
                variable_name=VARIABLE,
                suptitle=suptitle,
            )
        if SAVE:
            save_name = f"density_map_{VARIABLE}_{date_min}_{date_max}.png"
            suptitle = (
                f"{VARIABLE} - {', '.join(PROVIDERS)} ({category})\n"
                f"{date_min}-{date_max}"
            )
            plot.save(
                save_path=f"{CONFIG['SAVING_DIR']}/{save_name}",
                variable_name=VARIABLE,
                suptitle=suptitle,
            )
