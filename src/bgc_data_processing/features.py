"""Transformations to apply to data to create new features."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd
from seawater import eos80

from bgc_data_processing.core.variables.vars import (
    ExistingVar,
    NotExistingVar,
    ParsedVar,
    TemplateVar,
)

if TYPE_CHECKING:
    from bgc_data_processing.core.storers import Storer


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
    def transform(self, *args: pd.Series) -> pd.Series:
        """Compute the new variable values using all required series."""

    def insert_in_storer(self, storer: "Storer") -> None:
        """Insert the new feature in a given storer.

        Parameters
        ----------
        storer : Storer
            Storer to include data into.
        """
        data = self.transform(*self._extract_from_storer(storer=storer))
        data.index = storer.data.index
        storer.add_feature(
            variable=self.variable,
            data=data,
        )

    @classmethod
    def copy_var_infos_from_template(
        cls,
        template: "TemplateVar",
        **kwargs: ExistingVar | NotExistingVar | ParsedVar,
    ) -> "BaseFeature":
        """Create Feature from a variable template.

        Parameters
        ----------
        template : TemplateVar
            Template to use for the variable definition.

        Returns
        -------
        BaseFeature
            Feature.
        """
        return cls(
            **kwargs,
            var_name=template.name,
            var_unit=template.unit,
            var_type=template.type,
            var_default=template.default,
            var_name_format=template.name_format,
            var_value_format=template.value_format,
        )


class Pressure(BaseFeature):
    """Pressure feature.

    Parameters
    ----------
    depth_variable : ExistingVar | NotExistingVar | ParsedVar
        Variable for depth.
    latitude_variable : ExistingVar | NotExistingVar | ParsedVar
        Variable for latitude.
    var_name : str, optional
        Variable Name., by default "PRES"
    var_unit : str, optional
        Variable unit., by default "[dbars]"
    var_type : str, optional
        Data type., by default float
    var_default : Any, optional
        Default value., by default np.nan
    var_name_format : str, optional
        Name format for the added variable., by default "%-10s"
    var_value_format : str, optional
        Value format for the added variable., by default "%10.3f"
    """

    def __init__(
        self,
        depth_variable: ExistingVar | NotExistingVar | ParsedVar,
        latitude_variable: ExistingVar | NotExistingVar | ParsedVar,
        var_name: str = "PRES",
        var_unit: str = "[dbars]",
        var_type: str = float,
        var_default: Any = np.nan,
        var_name_format: str = "%-10s",
        var_value_format: str = "%10.3f",
    ) -> None:
        super().__init__(
            var_name=var_name,
            var_unit=var_unit,
            var_type=var_type,
            var_default=var_default,
            var_name_format=var_name_format,
            var_value_format=var_value_format,
        )
        self._source_vars = [depth_variable, latitude_variable]

    def transform(self, depth: pd.Series, latitude: pd.Series) -> pd.Series:
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
    var_name : str, optional
        Variable name., by default "PTEMP"
    var_unit : str, optional
        Variable unit., by default "[deg_C]"
    var_type : str, optional
        Data type., by default float
    var_default : Any, optional
        Default value, by default np.nan
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
        var_name: str = "PTEMP",
        var_unit: str = "[deg_C]",
        var_type: str = float,
        var_default: Any = np.nan,
        var_name_format: str = "%-10s",
        var_value_format: str = "%10.3f",
    ) -> None:
        super().__init__(
            var_name=var_name,
            var_unit=var_unit,
            var_type=var_type,
            var_default=var_default,
            var_name_format=var_name_format,
            var_value_format=var_value_format,
        )
        self._source_vars = [salinity_variable, temperature_variable, pressure_variable]

    def transform(
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
    var_name : str, optional
        Variable name., by default "SIGT"
    var_unit : str, optional
        Variable unit., by default "[kg/m3]"
    var_type : str, optional
        Data type., by default float
    var_default : Any, optional
        Default value., by default np.nan
    var_name_format : str, optional
        Name format for the added variable., by default "%-10s"
    var_value_format : str, optional
        Value format for the added variable., by default "%10.3f"
    """

    def __init__(
        self,
        salinity_variable: ExistingVar | NotExistingVar | ParsedVar,
        temperature_variable: ExistingVar | NotExistingVar | ParsedVar,
        var_name: str = "SIGT",
        var_unit: str = "[kg/m3]",
        var_type: str = float,
        var_default: Any = np.nan,
        var_name_format: str = "%-10s",
        var_value_format: str = "%10.3f",
    ) -> None:
        super().__init__(
            var_name=var_name,
            var_unit=var_unit,
            var_type=var_type,
            var_default=var_default,
            var_name_format=var_name_format,
            var_value_format=var_value_format,
        )
        self._source_vars = [salinity_variable, temperature_variable]

    def transform(
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
    var_name : str, optional
        Variable name., by default "CPHL"
    var_unit : str, optional
        Variable unit., by default "[mg/m3]"
    var_type : str, optional
        Data type., by default float
    var_default : Any, optional
        Default value., by default np.nan
    var_name_format : str, optional
        Name format for the added variable., by default "%-10s"
    var_value_format : str, optional
        Value format for the added variable., by default "%10.3f"
    """

    def __init__(
        self,
        diatom_variable: ExistingVar | NotExistingVar | ParsedVar,
        flagellate_variable: ExistingVar | NotExistingVar | ParsedVar,
        var_name: str = "CPHL",
        var_unit: str = "[mg/m3]",
        var_type: str = float,
        var_default: Any = np.nan,
        var_name_format: str = "%-10s",
        var_value_format: str = "%10.3f",
    ) -> None:
        super().__init__(
            var_name=var_name,
            var_unit=var_unit,
            var_type=var_type,
            var_default=var_default,
            var_name_format=var_name_format,
            var_value_format=var_value_format,
        )
        self._source_vars = [diatom_variable, flagellate_variable]

    def transform(
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
