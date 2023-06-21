"""Transformations to apply to data to create new features."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd
from seawater import eos80

from bgc_data_processing.data_structures.variables import (
    ExistingVar,
    NotExistingVar,
    ParsedVar,
)

if TYPE_CHECKING:
    from bgc_data_processing.data_structures.storers import Storer


class BaseFeature(ABC):
    """Base class for added features.

    Parameters
    ----------
    var_name : str
        Name of the added variable.
    var_unit : str
        Unit of the added variable.
    var_type : str
        Type of the added variable.
    var_default : Any
        Default value for the added variable.
    var_name_format : str
        Name format for the added variable.
    var_value_format : str
        Value format for the added variable.
    """

    _source_vars: list[ExistingVar | NotExistingVar | ParsedVar]

    def __init__(
        self,
        var_name: str,
        var_unit: str,
        var_type: str,
        var_default: Any,
        var_name_format: str,
        var_value_format: str,
    ) -> None:
        self._output_var = NotExistingVar(
            name=var_name,
            unit=var_unit,
            var_type=var_type,
            default=var_default,
            name_format=var_name_format,
            value_format=var_value_format,
        )

    @property
    def variable(self) -> NotExistingVar:
        """Variable which correspond to the feature."""
        return self._output_var

    @property
    def required_variables(self) -> list[ExistingVar | NotExistingVar | ParsedVar]:
        """Required variables for the feature computation."""
        return self._source_vars

    def _extract_from_storer(self, storer: "Storer") -> tuple[pd.Series]:
        """Extract the required data columns from the storer..

        Parameters
        ----------
        storer : Storer
            Storer to extract data from.

        Returns
        -------
        tuple[pd.Series]
            Tuple of required series.
        """
        return (storer.data[x.label] for x in self._source_vars)

    @abstractmethod
    def _transform(self, *args: pd.Series) -> pd.Series:
        """Compute the new variable values using all required series."""

    def insert_in_storer(self, storer: "Storer") -> None:
        """Insert the new feature in a given storer.

        Parameters
        ----------
        storer : Storer
            Storer to include data into.
        """
        data = self._transform(*self._extract_from_storer(storer=storer))
        data.index = storer.data.index
        storer.add_feature(
            variable=self.variable,
            data=data,
        )


class Pressure(BaseFeature):
    """Pressure feature.

    Parameters
    ----------
    depth_variable : ExistingVar | NotExistingVar | ParsedVar
        Variable for depth.
    latitude_variable : ExistingVar | NotExistingVar | ParsedVar
        Variable for latitude.
    var_name_format : str, optional
        Name format for the added variable., by default "%-10s"
    var_value_format : str, optional
        Value format for the added variable., by default "%10.3f"
    """

    def __init__(
        self,
        depth_variable: ExistingVar | NotExistingVar | ParsedVar,
        latitude_variable: ExistingVar | NotExistingVar | ParsedVar,
        var_name_format: str = "%-10s",
        var_value_format: str = "%10.3f",
    ) -> None:
        super().__init__(
            var_name="PRES",
            var_unit="[dbars]",
            var_type=float,
            var_default=np.nan,
            var_name_format=var_name_format,
            var_value_format=var_value_format,
        )
        self._source_vars = [depth_variable, latitude_variable]

    def _transform(self, depth: pd.Series, latitude: pd.Series) -> pd.Series:
        """Compute pressure from depth and latitude.

        Parameters
        ----------
        depth : pd.Series
            Depth (in meters).
        latitude : pd.Series
            Latitude (in degree).

        Returns
        -------
        pd.Series
            Pressure (in dbars).
        """
        pressure = pd.Series(eos80.pres(np.abs(depth), latitude))
        pressure.name = self.variable.label
        return pressure


class PotentialTemperature(BaseFeature):
    """Potential Temperature feature..

    Parameters
    ----------
    salinity_variable : ExistingVar | NotExistingVar | ParsedVar
        Variable for salinity.
    temperature_variable : ExistingVar | NotExistingVar | ParsedVar
        Variable for temperature.
    pressure_variable : ExistingVar | NotExistingVar | ParsedVar
        Variable for pressure.
    var_name_format : str, optional
        Name format for the added variable., by default "%-10s"
    var_value_format : str, optional
        Value format for the added variable., by default "%10.3f"
    """

    def __init__(
        self,
        salinity_variable: ExistingVar | NotExistingVar | ParsedVar,
        temperature_variable: ExistingVar | NotExistingVar | ParsedVar,
        pressure_variable: ExistingVar | NotExistingVar | ParsedVar,
        var_name_format: str = "%-10s",
        var_value_format: str = "%10.3f",
    ) -> None:
        super().__init__(
            var_name="PTEMP",
            var_unit="[deg_C]",
            var_type=float,
            var_default=np.nan,
            var_name_format=var_name_format,
            var_value_format=var_value_format,
        )
        self._source_vars = [salinity_variable, temperature_variable, pressure_variable]

    def _transform(
        self,
        salinity: pd.Series,
        temperature: pd.Series,
        pressure: pd.Series,
    ) -> pd.Series:
        """Compute potential temperature from salinity, temperature and pressure.

        Parameters
        ----------
        salinity : pd.Series
            Salinity (in psu).
        temperature : pd.Series
            Temperature (in Celsius degree).
        pressure : pd.Series
            Pressure (in dbars).

        Returns
        -------
        pd.Series
            Potential Temperature (in Celsisus degree).
        """
        potential_temperature = pd.Series(eos80.ptmp(salinity, temperature, pressure))
        potential_temperature.name = self.variable.label
        return potential_temperature


class SigmaT(BaseFeature):
    """Sigma T feature.

    Parameters
    ----------
    salinity_variable : ExistingVar | NotExistingVar | ParsedVar
        Variable for slainity.
    temperature_variable : ExistingVar | NotExistingVar | ParsedVar
        Variable for temperature.
    var_name_format : str, optional
        Name format for the added variable., by default "%-10s"
    var_value_format : str, optional
        Value format for the added variable., by default "%10.3f"
    """

    def __init__(
        self,
        salinity_variable: ExistingVar | NotExistingVar | ParsedVar,
        temperature_variable: ExistingVar | NotExistingVar | ParsedVar,
        var_name_format: str = "%-10s",
        var_value_format: str = "%10.3f",
    ) -> None:
        super().__init__(
            var_name="SIGT",
            var_unit="[kg/m3]",
            var_type=float,
            var_default=np.nan,
            var_name_format=var_name_format,
            var_value_format=var_value_format,
        )
        self._source_vars = [salinity_variable, temperature_variable]

    def _transform(
        self,
        salinity: pd.Series,
        temperature: pd.Series,
    ) -> pd.Series:
        """Compute sigma t from salinity and temperature.

        Parameters
        ----------
        salinity : pd.Series
            Salinity (in psu).
        temperature : pd.Series
            Temperature (in Celsius degree).

        Returns
        -------
        pd.Series
            Sigma T (in kg/m3).
        """
        sigma_t = pd.Series(eos80.dens0(salinity, temperature) - 1000)
        sigma_t.name = self.variable.label
        return sigma_t


class ChlorophyllFromDiatomFlagellate(BaseFeature):
    """Chlorophyll-a feature.

    Parameters
    ----------
    diatom_variable : ExistingVar | NotExistingVar | ParsedVar
        Variable for diatom.
    flagellate_variable : ExistingVar | NotExistingVar | ParsedVar
        Variable for flagellate.
    var_name_format : str, optional
        Name format for the added variable., by default "%-10s"
    var_value_format : str, optional
        Value format for the added variable., by default "%10.3f"
    """

    def __init__(
        self,
        diatom_variable: ExistingVar | NotExistingVar | ParsedVar,
        flagellate_variable: ExistingVar | NotExistingVar | ParsedVar,
        var_name_format: str = "%-10s",
        var_value_format: str = "%10.3f",
    ) -> None:
        super().__init__(
            var_name="SIGT",
            var_unit="[kg/m3]",
            var_type=float,
            var_default=np.nan,
            var_name_format=var_name_format,
            var_value_format=var_value_format,
        )
        self._source_vars = [diatom_variable, flagellate_variable]

    def _transform(
        self,
        diatom: pd.Series,
        flagellate: pd.Series,
    ) -> pd.Series:
        """Compute chlorophyll-a from diatom and flagellate.

        Parameters
        ----------
        diatom : pd.Series
            Diatoms (in mg/m3).
        flagellate : pd.Series
            Flagellates (in mg/m3).

        Returns
        -------
        pd.Series
            Chlorophyll-a (in kg/m3).
        """
        sigma_t = diatom + flagellate
        sigma_t.name = self.variable.label
        return sigma_t
