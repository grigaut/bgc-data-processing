"""Match Observation data to their equivalent in a simulation dataset."""
from pathlib import Path

from bgc_data_processing import (
    DEFAULT_VARS,
    data_classes,
    features,
    interpolation,
    selectors,
)
from bgc_data_processing.data_providers import hycom
from bgc_data_processing.parsers import ConfigParser

CONFIG_FOLDER = Path("config")

if __name__ == "__main__":
    config_filepath = CONFIG_FOLDER.joinpath(Path(__file__).stem)
    CONFIG = ConfigParser(
        filepath=config_filepath.with_suffix(".toml"),
        check_types=False,
        dates_vars_keys=[],
        dirs_vars_keys=["SAVING_DIR"],
        existing_directory="raise",
    )
    # Configuration parameters
    LOADING_DIR: Path = Path(CONFIG["LOADING_DIR"])
    SIM_PROVIDER: str = CONFIG["SIM_PROVIDER"]
    TO_INTERPOLATE: list[str] = CONFIG["TO_INTERPOLATE"]
    INTERPOLATION_KIND: str = CONFIG["INTERPOLATION_KIND"]
    # Default variables
    LATITUDE_TEMPLATE = DEFAULT_VARS["latitude"]
    SALINITY_TEMPLATE = DEFAULT_VARS["salinity"]
    TEMPERATURE_TEMPLATE = DEFAULT_VARS["temperature"]
    DEPTH_TEMPLATE = DEFAULT_VARS["depth"]

    filepaths_txt = list(LOADING_DIR.glob("*.txt"))
    filepaths_csv = list(LOADING_DIR.glob("*.csv"))
    filepaths = filepaths_txt + filepaths_csv

    observations = data_classes.Storer.from_files(
        filepaths,
        providers_column_label=DEFAULT_VARS["provider"].label,
        expocode_column_label=DEFAULT_VARS["expocode"].label,
        date_column_label=DEFAULT_VARS["date"].label,
        year_column_label=DEFAULT_VARS["year"].label,
        month_column_label=DEFAULT_VARS["month"].label,
        day_column_label=DEFAULT_VARS["day"].label,
        hour_column_label=DEFAULT_VARS["hour"].label,
        latitude_column_label=DEFAULT_VARS["latitude"].label,
        longitude_column_label=DEFAULT_VARS["longitude"].label,
        depth_column_label=DEFAULT_VARS["depth"].label,
        category="in_situ",
        unit_row_index=1,
        delim_whitespace=True,
        verbose=1,
    )
    selector = selectors.Selector(
        reference=observations,
        strategy=selectors.NearestNeighborStrategy(metric="haversine"),
        loader=hycom.loader,
    )

    simulations = selector()

    interpolator = interpolation.Interpolator(
        base=simulations,
        x_column_name=DEPTH_TEMPLATE.label,
        y_columns_name=TO_INTERPOLATE,
        kind=INTERPOLATION_KIND,
    )
    interpolated = interpolator.interpolate_storer(
        observations,
    )
    # Add pressure
    obs_pres_var, obs_pres_data = features.compute_pressure(
        observations,
        DEPTH_TEMPLATE.label,
        LATITUDE_TEMPLATE.label,
    )
    observations.add_feature(obs_pres_var, obs_pres_data)
    sim_pres_var, sim_pres_data = features.compute_pressure(
        interpolated,
        DEPTH_TEMPLATE.label,
        LATITUDE_TEMPLATE.label,
    )
    interpolated.add_feature(sim_pres_var, sim_pres_data)
    # Add potential temperature
    obs_ptemp_var, obs_ptemp_data = features.compute_potential_temperature(
        storer=observations,
        salinity_field=SALINITY_TEMPLATE.label,
        temperature_field=TEMPERATURE_TEMPLATE.label,
        pressure_field=obs_pres_var.label,
    )
    observations.add_feature(obs_ptemp_var, obs_ptemp_data)
    interpolated.add_feature(
        obs_ptemp_var,
        interpolated.data[TEMPERATURE_TEMPLATE.label],
    )
    save_vars = [
        var.label
        for var in observations.variables
        if var.name != observations.variables.date_var_name
    ]
    observations.variables.set_saving_order(
        var_names=save_vars,
    )
    interpolated.variables.set_saving_order(
        var_names=save_vars,
    )
    observations_save = observations.slice_using_index(interpolated.data.index)

    SAVING_DIR = Path(CONFIG["SAVING_DIR"])

    observations_save.save(SAVING_DIR.joinpath("observations.txt"))
    interpolated.save(SAVING_DIR.joinpath("simulations.txt"))
