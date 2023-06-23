"""Match Observation data to their equivalent in a simulation dataset."""
from pathlib import Path

import bgc_data_processing as bgc_dp

CONFIG_FOLDER = Path("config")

if __name__ == "__main__":
    config_filepath = CONFIG_FOLDER.joinpath(Path(__file__).stem)
    CONFIG = bgc_dp.parsers.ConfigParser(
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
    LATITUDE_TEMPLATE = bgc_dp.defaults.DEFAULT_VARS["latitude"]
    SALINITY_TEMPLATE = bgc_dp.defaults.DEFAULT_VARS["salinity"]
    TEMPERATURE_TEMPLATE = bgc_dp.defaults.DEFAULT_VARS["temperature"]
    DEPTH_TEMPLATE = bgc_dp.defaults.DEFAULT_VARS["depth"]

    filepaths_txt = list(LOADING_DIR.glob("*.txt"))
    filepaths_csv = list(LOADING_DIR.glob("*.csv"))
    filepaths = filepaths_txt + filepaths_csv

    observations = bgc_dp.read_files(
        filepaths,
        providers_column_label=bgc_dp.defaults.DEFAULT_VARS["provider"].label,
        expocode_column_label=bgc_dp.defaults.DEFAULT_VARS["expocode"].label,
        date_column_label=bgc_dp.defaults.DEFAULT_VARS["date"].label,
        year_column_label=bgc_dp.defaults.DEFAULT_VARS["year"].label,
        month_column_label=bgc_dp.defaults.DEFAULT_VARS["month"].label,
        day_column_label=bgc_dp.defaults.DEFAULT_VARS["day"].label,
        hour_column_label=bgc_dp.defaults.DEFAULT_VARS["hour"].label,
        latitude_column_label=bgc_dp.defaults.DEFAULT_VARS["latitude"].label,
        longitude_column_label=bgc_dp.defaults.DEFAULT_VARS["longitude"].label,
        depth_column_label=bgc_dp.defaults.DEFAULT_VARS["depth"].label,
        category="in_situ",
        unit_row_index=1,
        delim_whitespace=True,
        verbose=1,
    )
    selector = bgc_dp.SelectiveDataSource.from_data_source(
        reference=observations,
        strategy=bgc_dp.comparison.NearestNeighborStrategy(metric="haversine"),
        dsource=bgc_dp.providers.PROVIDERS["HYCOM"],
    )

    simulations = selector.load_all(bgc_dp.Constraints())

    interpolator = bgc_dp.comparison.Interpolator(
        base=simulations,
        x_column_name=DEPTH_TEMPLATE.label,
        y_columns_name=TO_INTERPOLATE,
        kind=INTERPOLATION_KIND,
    )
    interpolated = interpolator.interpolate_storer(
        observations,
    )
    # Add pressure
    pres_feat = bgc_dp.features.Pressure(DEPTH_TEMPLATE, LATITUDE_TEMPLATE)
    pres_feat.insert_in_storer(observations)
    pres_feat.insert_in_storer(interpolated)
    # Add potential temperature
    ptemp_feat = bgc_dp.features.PotentialTemperature(
        SALINITY_TEMPLATE,
        TEMPERATURE_TEMPLATE,
        pres_feat.variable,
    )
    ptemp_feat.insert_in_storer(observations)
    ptemp_feat.insert_in_storer(interpolated)
    save_vars = [
        var.label
        for var in observations.variables
        if var.name != observations.variables.date_var_name
    ]
    observations_save = observations.slice_using_index(interpolated.data.index)

    SAVING_DIR = Path(CONFIG["SAVING_DIR"])

    obs_saver = bgc_dp.savers.StorerSaver(observations_save)
    obs_saver.saving_order = save_vars
    obs_saver.save_all_storer(SAVING_DIR.joinpath("observations.txt"))

    int_saver = bgc_dp.savers.StorerSaver(interpolated)
    int_saver.saving_order = save_vars
    int_saver.save_all_storer(SAVING_DIR.joinpath("simulations.txt"))
