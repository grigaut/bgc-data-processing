"""Transformations / Functions to apply to data to create new features."""

from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from seawater import eos80

from bgc_data_processing.data_structures.variables import NotExistingVar

if TYPE_CHECKING:
    from bgc_data_processing.data_structures.storers import Storer


def compute_pressure(
    storer: "Storer",
    depth_field: str,
    latitude_field: str,
) -> tuple[NotExistingVar, pd.Series]:
    """Compute pressure from depth values and latitude values.

    Parameters
    ----------
    storer : Storer
        Storer to get the data from.
    depth_field : str
        Name of the depth field in the storer data.
    latitude_field : str
        Name of the latitude field in the storer data.

    Returns
    -------
    tuple[NotExistingVar, pd.Series]
        Pressure variable, pressure values.
    """
    depth = storer.data[depth_field]
    latitude = storer.data[latitude_field]
    variable = NotExistingVar(
        name="PRES",
        unit="[dbars]",
        var_type=float,
        default=np.nan,
        name_format="%-10s",
        value_format="%10.3f",
    )
    data = pd.Series(eos80.pres(np.abs(depth), latitude), index=storer.data.index)
    data.name = variable.label
    return variable, data


def compute_potential_temperature(
    storer: "Storer",
    salinity_field: str,
    temperature_field: str,
    pressure_field: str,
) -> tuple[NotExistingVar, pd.Series]:
    """Compute potential temperature from depth values and latitude values.

    Parameters
    ----------
    storer : Storer
        Storer to get the data from.
    salinity_field : str
        Name of the salinity field in the storer data.
    temperature_field : str
        Name of the temperature field in the storer data.
    pressure_field : str
        Name of the pressure field in the storer data.

    Returns
    -------
    tuple[NotExistingVar, pd.Series]
        Potential temperature variable, potenital temperature values.
    """
    salinity = storer.data[salinity_field]
    temperature = storer.data[temperature_field]
    pressure = storer.data[pressure_field]
    variable = NotExistingVar(
        name="PTEMP",
        unit="[deg_C]",
        var_type=float,
        default=np.nan,
        name_format="%-10s",
        value_format="%10.3f",
    )
    data = pd.Series(
        eos80.ptmp(salinity, temperature, pressure),
        index=storer.data.index,
    )
    data.name = variable.label
    return variable, data


def compute_sigma_t(
    storer: "Storer",
    salinity_field: str,
    temperature_field: str,
) -> tuple[NotExistingVar, pd.Series]:
    """Compute seawater's sigma-t value.

    Parameters
    ----------
    storer : Storer
        Storer to get the data from.
    salinity_field : str
        Name of the salinity field in the storer data.
    temperature_field : str
        Name of the temperature field in the storer data.

    Returns
    -------
    tuple[NotExistingVar, pd.Series]
        Sigma-t variable, sigma-t values.
    """
    salinity = storer.data[salinity_field]
    temperature = storer.data[temperature_field]
    variable = NotExistingVar(
        name="SIGT",
        unit="[kg/m3]",
        var_type=float,
        default=np.nan,
        name_format="%-10s",
        value_format="%10.3f",
    )
    data = pd.Series(
        eos80.dens0(salinity, temperature) - 1000,
        index=storer.data.index,
    )
    data.name = variable.label
    return variable, data
