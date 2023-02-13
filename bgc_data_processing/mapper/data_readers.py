"""Tools to read Depth profiles and Chlorophyll measures"""


import datetime as dt

import numpy as np


def read_depth_levels(
    filepath: str,
    depth_max: int | float,
) -> np.ndarray:
    """Reads depth levels from file.

    Parameters
    ----------
    filepath : str
        Filepath to depth level file.
    depth_max : int | float
        Max depth to consider.

    Returns
    -------
    np.ndarray
        Depth profile.
    """
    gotm_dep = -np.flip(np.load(filepath))  # depth [meter]
    index_max = abs(gotm_dep - depth_max).argmin()
    return gotm_dep[:index_max]  # Only depth_max first meters


def interp_cphl(
    nb_tim: int,
    nb_dep: int,
    gotm_depth: np.ndarray,
    day: np.ndarray,
    pres: np.ma.core.MaskedArray,
    cphl: np.ma.core.MaskedArray,
) -> tuple[np.ndarray]:
    """Interpolates Chlorophyll values on missing values.

    Parameters
    ----------
    nb_tim : int
        Number of Chlorophyll observation points.
    nb_dep : int
        Number of depth points.
    gotm_depth : np.ndarray
        Depth profile.
    day : np.ndarray
        Observations days.
    pres : np.ma.core.MaskedArray
        Pressure measure values, unit: bar.
    cphl : np.ma.core.MaskedArray
        Chlorophyll measure values. Some values might be missing.

    Returns
    -------
    tuple[np.ndarray]
        Observation dates, Interpolated Chlorophyll values.
    """
    start = dt.datetime(1950, 1, 1, 0, 0, 0)
    chunks_date = []
    chunks_interp = []
    for j in range(nb_tim):
        # Transform timedelta to datetime
        delta = dt.timedelta(day[j])
        offset = delta + start
        date = np.array([offset for _ in range(nb_dep)])
        chunks_date.append(date)
        # split arrays
        cphl_1d = cphl[j, :].squeeze()
        pres_1d = pres[j, :].squeeze()
        # interpolation over missing values
        cphl_1d_interp = np.interp(gotm_depth, pres_1d, cphl_1d)
        chunks_interp.append(cphl_1d_interp)
    # Concatenate all values
    date_df = np.stack(chunks_date, axis=0)
    chunks_interp = np.array(chunks_interp, dtype="float")
    # negative values are set to np.nan
    chunks_interp[chunks_interp <= 0] = np.nan
    cphl_interp = np.vstack(chunks_interp)
    cphl_interp_df = cphl_interp.flatten()

    return date_df, cphl_interp_df
