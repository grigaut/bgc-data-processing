"""Base objects."""


import datetime as dt
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from bgc_data_processing.data_classes import Storer
    from bgc_data_processing.variables import VariablesStorer


class BaseLoader(ABC):
    """Base class to load data.

    Parameters
    ----------
    provider_name : str
        Data provider name.
    dirin : str
        Directory to browse for files to load.
    category: str
        Category provider belongs to.
    files_pattern : str
        Pattern to use to parse files.
        It must contain a '{years}' in order to be completed using the .format method.
    variables : VariablesStorer
        Storer object containing all variables to consider for this data,
        both the one in the data file but and the one not represented in the file.
    """

    _verbose: int = 1
    _lon_min: int | float = np.nan
    _lon_max: int | float = np.nan
    _lat_min: int | float = np.nan
    _lat_max: int | float = np.nan
    _depth_min: int | float = np.nan
    _depth_max: int | float = np.nan
    _date_min: dt.datetime | dt.date = np.nan
    _date_max: dt.datetime | dt.date = np.nan

    def __init__(
        self,
        provider_name: str,
        dirin: str,
        category: str,
        files_pattern: str,
        variables: "VariablesStorer",
    ) -> None:

        self._provider = provider_name
        self._dirin = dirin
        self._category = category
        self._files_pattern = files_pattern
        self._variables = variables

    @property
    def provider(self) -> str:
        """_provider attribute getter.

        Returns
        -------
        str
            data provider name.
        """
        return self._provider

    @property
    def category(self) -> str:
        """Returns the category of the provider.

        Returns
        -------
        str
            Category provider belongs to.
        """
        return self._category

    @property
    def verbose(self) -> int:
        """_verbose attribute getter.

        Returns
        -------
        int
            Verbose value.
        """
        return self._verbose

    @property
    def variables(self) -> "VariablesStorer":
        """_variables attribute getter.

        Returns
        -------
        VariablesStorer
            Variables storer.
        """
        return self._variables

    @abstractmethod
    def __call__(self, exclude: list = []) -> "Storer":
        """Loads all files for the loader.

        Parameters
        ----------
        exclude : list, optional
            Files not to load., by default []

        Returns
        -------
        Storer
            Storer for the loaded data.
        """
        ...

    @abstractmethod
    def _select_filepaths(self, exclude: list) -> list[str]:
        """Select filepaths matching the file pattern.

        Parameters
        ----------
        exclude : list
            Files to exclude even if their name matches the pattern.

        Returns
        -------
        list[str]
            List of the filepaths to use for loading.
        """
        ...

    @abstractmethod
    def load(self, filepath: str) -> pd.DataFrame:
        """Main method to use to load data.

        Returns
        -------
        Any
            Data object.
        """
        ...

    def set_verbose(self, verbose: int):
        """Verbose setting method.

        Parameters
        ----------
        verbose : int
            Controls the verbosity: the higher, the more messages.
        """
        assert isinstance(verbose, int), "self.verbose must be an instance of int"
        self._verbose = verbose

    def set_saving_order(self, var_names: str) -> None:
        """Set the saving order for the variables.

        Parameters
        ----------
        var_names : list[str]
            List of variable names => saving variables sorted.
        """
        self._variables.set_saving_order(var_names=var_names)

    def set_longitude_boundaries(
        self,
        longitude_min: int | float,
        longitude_max: int | float,
    ) -> None:
        """Sets boundaries for longitude variable.

        Parameters
        ----------
        longitude_min : int | float
            Minimal value for longitude (included).
        longitude_max : int | float
            Maximal value for longitude (included).
        """
        self._lon_min = longitude_min
        self._lon_max = longitude_max

    def set_latitude_boundaries(
        self,
        latitude_min: int | float,
        latitude_max: int | float,
    ) -> None:
        """Sets boundaries for latitude variable.

        Parameters
        ----------
        latitude_min : int | float
            Minimal value for latitude (included).
        latitude_max : int | float
            Maximal value for latitude (included).
        """
        self._lat_min = latitude_min
        self._lat_max = latitude_max

    def set_depth_boundaries(
        self,
        depth_min: int | float,
        depth_max: int | float,
    ) -> None:
        """Sets boundaries for depth variable.

        Parameters
        ----------
        depth_min : int | float
            Minimal value for depth (included).
        depth_max : int | float
            Maximal value for depth (included).
        """
        self._depth_min = depth_min
        self._depth_max = depth_max

    def set_date_boundaries(
        self,
        date_min: dt.datetime | dt.date = np.nan,
        date_max: dt.datetime | dt.date = np.nan,
    ) -> None:
        """Sets boundaries for date variable.

        Parameters
        ----------
        date_min : int | float
            Minimal value for date (included)., by default np.nan
        date_max : int | float
            Maximal value for date (included)., by default np.nan
        """
        if isinstance(date_min, float) and np.isnan(date_min):
            self._date_min = np.nan
        else:
            self._date_min = pd.to_datetime(date_min)
        if isinstance(date_min, float) and np.isnan(date_max):
            self._date_max = np.nan
        else:
            self._date_max = pd.to_datetime(date_max)

    def _apply_boundaries(
        self,
        df: pd.DataFrame,
        var_name: str,
        min: Any,
        max: Any,
    ) -> pd.DataFrame:
        """Applies boundaries restrictions on a dataframe.

        Parameters
        ----------
        df : pd.DataFrame
            Dataframe to reduce using boundaries values.
        var_name : str
            Variable name to consider.
        min : Any
            Minimal value to use.
        max : Any
            Maximal value to use.

        Returns
        -------
        pd.DataFrame
            Reduced DataFrame.

        Examples
        --------
        >>> df = self._apply_boundaries(not_bounded_df,
        ...     "DATE",
        ...     self._date_min,
        ...     self._date_max,
        ... )

        """
        if var_name not in self._variables.keys():
            return df
        is_min_nan = isinstance(min, float) and np.isnan(min)
        is_max_nan = isinstance(max, float) and np.isnan(max)
        if is_min_nan and is_max_nan:
            return df
        to_compare = df[self._variables.labels[var_name]]
        if is_min_nan:
            after_min = to_compare <= max
            return df.loc[after_min, :].copy()
        elif is_max_nan:
            before_max = to_compare >= min
            return df.loc[before_max, :].copy()
        else:
            after_min = to_compare >= min
            before_max = to_compare <= max
            return df.loc[after_min & before_max, :].copy()

    def remove_nan_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """Removes rows.

        Parameters
        ----------
        df : pd.DataFrame
            _description_

        Returns
        -------
        pd.DataFrame
            _description_
        """
        # Load keys
        vars_to_remove_when_any_nan = self._variables.to_remove_if_any_nan
        vars_to_remove_when_all_nan = self._variables.to_remove_if_all_nan
        # Check for nans
        any_nans = df[vars_to_remove_when_any_nan].isna().any(axis=1)
        all_nans = df[vars_to_remove_when_all_nan].isna().all(axis=1)
        # Get indexes to drop
        indexes_to_drop = df[any_nans | all_nans].index
        return df.drop(index=indexes_to_drop)

    def _correct(self, to_correct: pd.DataFrame) -> pd.DataFrame:
        """Applies corrections functions defined in Var object to dataframe.

        Parameters
        ----------
        to_correct : pd.DataFrame
            Dataframe to correct

        Returns
        -------
        pd.DataFrame
            Corrected Dataframe.
        """
        # Modify type :
        for label, correction_func in self._variables.corrections.items():
            to_correct[label] = to_correct[label].apply(correction_func)
        return to_correct


class BasePlot(ABC):
    """Base class to plot data from a storer.

    Parameters
    ----------
    storer : Storer
        Storer to plot data of.
    """

    def __init__(self, storer: "Storer") -> None:
        self._storer = storer
        self._variables = storer.variables
        self._verbose = storer.verbose

    @abstractmethod
    def plot(self) -> None:
        """Plot method."""
        ...

    @abstractmethod
    def save_fig(self) -> None:
        """Figure saving method."""
        ...
