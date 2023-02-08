"""Functions to select .nc file depending on different conditions."""


import datetime as dt
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from bgc_data_processing.mapper.loaders import NetCDFStorer


def select_profile_by_filename(
    nc_files: list["NetCDFStorer"],
    block_list: list,
) -> list["NetCDFStorer"]:
    """Selects files based on their names.

    Parameters
    ----------
    nc_files : list[NetCDFStorer]
        Files to sort.
    block_list : list
        Filenames to remove.

    Returns
    -------
    list[NetCDFStorer]
        Selected files.
    """
    selected = []
    for ncstorer in nc_files:
        # checking if the file can be used
        if ncstorer.get_name() not in block_list:
            selected.append(ncstorer)
    return selected


def select_profile_by_varname(
    nc_files: list["NetCDFStorer"],
    var_name: list,
) -> list["NetCDFStorer"]:
    """Selects files based on their variables names.

    Parameters
    ----------
    nc_files : list[NetCDFStorer]
        Files to sort.
    var_name : list
        Variable to look for the file.

    Returns
    -------
    list[NetCDFStorer]
        Selected files.
    """
    selected = []
    for ncstorer in nc_files:
        # open data
        variables = ncstorer.get_content().variables
        # Only consider data if cphl has been mesured
        if var_name in variables.keys():
            selected.append(ncstorer)
    return selected


def select_profiles_by_boundaries(
    nc_files: list["NetCDFStorer"],
    bb_list: dict,
) -> list["NetCDFStorer"]:
    """Selects files which values respect some space-time boundaries.

    Parameters
    ----------
    nc_files : list[NetCDFStorer]
        Files to sort.
    bb_list : list
        Boundaries dictionnary. Must contains values for the following keys :
        date_min, date_max, lat_min, lat_max, lon_min, lon_max.

    Returns
    -------
    list[NetCDFStorer]
        Selected files.
    """
    data_start_date = dt.datetime(1950, 1, 1, 0, 0, 0)
    date_min = np.datetime64(bb_list["date_min"])
    date_max = np.datetime64(bb_list["date_max"])
    lat_min = bb_list["lat_min"]
    lat_max = bb_list["lat_max"]
    lon_min = bb_list["lon_min"]
    lon_max = bb_list["lon_max"]

    selected = []
    for ncstorer in nc_files:
        # open data
        variables = ncstorer.get_content().variables
        # Read Argo data
        cphl = variables["CPHL_ADJUSTED"]  # [mg m-3]
        latitude = variables["LATITUDE"]  # [degree north]
        longitude = variables["LONGITUDE"]  # [degree east]
        day = variables["TIME"]  # [days since 1950-01-01T00:00:00Z]
        # Remove empty cphl rows from data
        msk_cphl = cphl[:].mask.all(axis=1)
        lons = np.ma.array(longitude[:], mask=msk_cphl).compressed()
        lats = np.ma.array(latitude[:], mask=msk_cphl).compressed()
        timedeltas = np.ma.array(day[:], mask=msk_cphl).compressed()
        # Convert timedeltas to datetimes using data starting date
        dates = (pd.to_timedelta(timedeltas, "D") + data_start_date).values
        # checking if there's data
        if not dates.shape[0] > 0:
            continue
        # checking if any date corresponds to boundaries
        if not ((dates > date_min).any() & (dates < date_max).any()):
            continue
        # checking if any longitude corresponds to boundaries
        if not ((lons > lon_min).any() & (lons < lon_max).any()):
            continue
        # checking if any latitudes corresponds to boundaries
        if not ((lats > lat_min).any() & (lats < lat_max).any()):
            continue
        # if all checks passed : keep profile
        selected.append(ncstorer)
    return selected


def select_profiles_by_ids(
    nc_files: list["NetCDFStorer"],
    id_list: list,
) -> list["NetCDFStorer"]:
    """Selects files which comes from precise Argo station (based on theses station IDs).

    Parameters
    ----------
    nc_files : list[NetCDFStorer]
        Files to sort.
    id_list : list
        List of stations' IDs to keep.

    Returns
    -------
    list[NetCDFStorer]
        Selected files.
    """
    selected = []
    for ncstorer in nc_files:
        # Read Argo id
        if ncstorer.get_id() in id_list:
            selected.append(ncstorer)
    return selected
