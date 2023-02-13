import datetime as dt
import time

from bgc_data_processing.mapper import (
    config,
    data_readers,
    loaders,
    plotters,
    selectors,
)

if __name__ == "__main__":
    t0 = time.time()
    IDS = ["6903554"]
    SELECT_ARGO = True
    READ_ARGO = True
    VERBOSE = 2
    BB_LIST = {
        "date_min": dt.datetime(2019, 1, 1, 0, 0, 0),
        "date_max": dt.datetime(2021, 1, 1, 0, 0, 0),
        "lat_min": 50,
        "lat_max": 89,
        "lon_min": -40,
        "lon_max": 40,
    }
    # BLOCK_LIST contains files that have been removed after visual inspection
    BLOCK_LIST = [
        "GL_PR_PF_6900798.nc",
        "GL_PR_PF_5903592.nc",
        "GL_PR_PF_5903887.nc",
        "GL_PR_PF_6900796.nc",
        "GL_PR_PF_6900797.nc",
        "GL_PR_PF_6900799.nc",
        "GL_PR_PF_6903551.nc",
        "GL_PR_PF_6903567.nc",
        "GL_PR_PF_6903574.nc",
        "GL_PR_PF_6903575.nc",
        "GL_PR_PF_6903578.nc",
        "GL_PR_PF_6903579.nc",
    ]

    # Loading and selecting files
    if VERBOSE > 0:
        print("File loading and selection")
    nc_files = loaders.load_files_from_dir(
        path=config.DIRIN_ARGO,
    )
    rm_blocked = selectors.select_profile_by_filename(
        nc_files=nc_files,
        block_list=BLOCK_LIST,
    )
    cphl_files = selectors.select_profile_by_varname(
        nc_files=rm_blocked,
        var_name="CPHL_ADJUSTED",
    )
    bb_selected = selectors.select_profiles_by_boundaries(
        nc_files=cphl_files,
        bb_list=BB_LIST,
    )
    id_selected = selectors.select_profiles_by_ids(
        nc_files=bb_selected,
        id_list=IDS,
    )
    if SELECT_ARGO:
        if VERBOSE > 0:
            print("Map figure creation and data plotting")
        # All files
        fig = plotters.create_fig(figsize=(10, 10), title="All Argo")
        ax = plotters.create_geoaxes(fig=fig, extent=(-180, 180, 50, 90))
        plotters.add_netcdf_lines(ax=ax, to_plot=nc_files, color="green")
        plotters.add_netcdf_lines(ax=ax, to_plot=id_selected, color="red", lw=2)
        plotters.create_output(fig=fig, show=True, save=True, dirout=config.DIROUT)
        # Only selected files
        fig = plotters.create_fig(figsize=(10, 10), title="Norwegian Argo")
        ax = plotters.create_geoaxes(fig=fig, extent=(-30, 30, 60, 80))
        plotters.add_netcdf_lines(ax=ax, to_plot=bb_selected, color="green")
        plotters.add_netcdf_lines(ax=ax, to_plot=id_selected, color="red", lw=2)
        plotters.create_output(fig=fig, show=True, save=True, dirout=config.DIROUT)

    if READ_ARGO:
        if VERBOSE > 0:
            print("Profile figure creation and data plotting")
        gotm_depth = data_readers.read_depth_levels(
            filepath=config.FILEIN, depth_max=config.DEPTH_MAX
        )
        df_cphl = data_readers.read_cphl_data(
            nc_files=id_selected, gotm_depth=gotm_depth
        )
        fig = plotters.create_fig(figsize=(10, 4), title="CPHL Profile")
        ax = plotters.create_profile_axes(fig=fig)
        plotters.plot_profile(ax=ax, df=df_cphl, variable="CPHL")
        plotters.create_output(fig=fig, show=True, save=True, dirout=config.DIROUT)
    print(time.time() - t0)
