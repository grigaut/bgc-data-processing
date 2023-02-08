"""Tools to read Depth profiles and Chlorophyll measures"""


import datetime as dt
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from bgc_data_processing.mapper.loaders import NetCDFStorer


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


def read_cphl_data(
    nc_files: list["NetCDFStorer"],
    gotm_depth: np.ndarray,
) -> pd.DataFrame:
    """Reads chlorophyll values from netCDF files.

    Parameters
    ----------
    nc_files : list[NetCDFStorer]
        List of NetCDF files (wrapped in the NetCDFStorer class)
    gotm_depth : np.ndarray
        Depth profile.

    Returns
    -------
    pd.DataFrame
        Chlorophyll values (potentially interpolated)
    """
    data = []
    for nc_obj in nc_files:
        variables = nc_obj.get_content().variables
        tmp_cphl = variables["CPHL_ADJUSTED"][:, :]  # [mg m-3]
        tmp_pres = variables["PRES"][:, :]  # [dbar]
        tmp_lats = variables["LATITUDE"][:]  # [degree north]
        tmp_lons = variables["LONGITUDE"][:]  # [degree east]
        tmp_days = variables["TIME"][:]  # [days since 1950-01-01T00:00:00Z]

        # Remove empty cphl rows from data
        msk_cphl = tmp_cphl[:].mask.all(axis=1)
        lons = np.ma.array(tmp_lons[:].data, mask=msk_cphl).compressed()
        lats = np.ma.array(tmp_lats[:].data, mask=msk_cphl).compressed()
        days = np.ma.array(tmp_days[:].data, mask=msk_cphl).compressed()

        msk_1D = [
            not elem for elem in msk_cphl
        ]  # Need to flip the mask for cphl and dep
        cphl = tmp_cphl[msk_1D]
        pres = tmp_pres[msk_1D]
        nb_tim = np.shape(cphl)[0]
        nb_dep = np.shape(gotm_depth)[0]

        date_df, cphl_interp_df = interp_cphl(
            nb_tim=nb_tim,
            nb_dep=nb_dep,
            gotm_depth=gotm_depth,
            day=days,
            pres=pres,
            cphl=cphl,
        )
        # Tile variables
        lon_df = np.tile(lons, (nb_dep, 1)).T.flatten()
        lat_df = np.tile(lats, (nb_dep, 1)).T.flatten()
        day_df = np.tile(days, (nb_dep, 1)).T.flatten()
        date_df = date_df.flatten()
        dep_df = np.tile(gotm_depth, (1, nb_tim)).T.flatten()

        df_cphl_i = pd.DataFrame(
            {
                "Argo": nc_obj.get_id(),
                "Latitude": lat_df,
                "Longitude": lon_df,
                "Day": day_df,
                "Date": date_df,
                "Depth level": dep_df,
                "CPHL": cphl_interp_df,
            }
        )

        if nc_obj.get_id() == "6903570":
            df_cphl_i.drop(
                df_cphl_i[df_cphl_i.Date > np.datetime64("2021-04")].index,
                inplace=True,
            )

        data.append(df_cphl_i)
    df = pd.concat(data, ignore_index=True)
    df.loc[df["CPHL"] < 0.05, "CPHL"] = 0.05
    return df
