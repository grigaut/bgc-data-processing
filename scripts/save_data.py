"""Data aggregation and saving script."""

import datetime as dt
from pathlib import Path
from time import time

import bgc_data_processing as bgc_dp

CONFIG_FOLDER = Path("config")

if __name__ == "__main__":
    config_filepath = CONFIG_FOLDER.joinpath(Path(__file__).stem)
    CONFIG = bgc_dp.parsers.ConfigParser(
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
    VERBOSE = CONFIG["VERBOSE"]
    PRIORITY = CONFIG["PRIORITY"]

    bgc_dp.set_verbose_level(VERBOSE)

    # Dates parsing
    dates_generator = bgc_dp.dateranges.DateRangeGenerator(
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
            print(f"Loading data: {data_src}")
        datasource = bgc_dp.providers.PROVIDERS[data_src]
        variables = datasource.variables
        # Constraint slicer
        constraints = bgc_dp.Constraints()
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
        # Loading data
        datasource.saving_order = VARIABLES
        datasource.load_and_save(
            SAVING_DIR,
            dates_generator,
            constraints,
        )
    for file in SAVING_DIR.glob("*.txt"):
        if VERBOSE > 0:
            print(f"Removing duplicates from: {file}")
        storer = bgc_dp.io.read_files(
            filepath=file,
            providers_column_label=bgc_dp.defaults.VARS["provider"].label,
            expocode_column_label=bgc_dp.defaults.VARS["expocode"].label,
            date_column_label=bgc_dp.defaults.VARS["date"].label,
            year_column_label=bgc_dp.defaults.VARS["year"].label,
            month_column_label=bgc_dp.defaults.VARS["month"].label,
            day_column_label=bgc_dp.defaults.VARS["day"].label,
            hour_column_label=bgc_dp.defaults.VARS["hour"].label,
            latitude_column_label=bgc_dp.defaults.VARS["latitude"].label,
            longitude_column_label=bgc_dp.defaults.VARS["longitude"].label,
            depth_column_label=bgc_dp.defaults.VARS["depth"].label,
            variables_reference=bgc_dp.defaults.VARS.to_list(),
            category="_",
            unit_row_index=1,
            delim_whitespace=True,
        )
        file.unlink()
        storer.remove_duplicates(PRIORITY)
        bgc_dp.io.save_storer(storer, filepath=file, saving_order=VARIABLES)
    if VERBOSE > 0:
        print("\n\t" + "-" * len(txt))
        print("\t" + " " * (len(txt) // 2) + "DONE")
        print("\t" + "-" * len(txt) + "\n")
    print(time() - t0)
