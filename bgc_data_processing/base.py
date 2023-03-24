"""Base objects."""


import datetime as dt
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from bgc_data_processing.data_classes import Storer

if TYPE_CHECKING:
    from bgc_data_processing.variables import VariablesStorer
    from bgc_data_processing.data_classes import DataSlicer
    from matplotlib.figure import Figure


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
    def __call__(self, constraints: "DataSlicer", exclude: list = []) -> "Storer":
        """Loads all files for the loader.

        Parameters
        ----------
        constraints: DataSlicer
            Constraint slicer.
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

    __default_depth_max: int | str = 0

    def __init__(self, storer: "Storer") -> None:
        self._storer = storer
        self._variables = storer.variables
        self._verbose = storer.verbose
        lats_info = self._get_default_infos(self._variables.latitude_var_name)
        self._lat_col, self._lat_min, self._lat_max = lats_info
        lons_info = self._get_default_infos(self._variables.longitude_var_name)
        self._lon_col, self._lon_min, self._lon_max = lons_info
        dates_info = self._get_default_infos(self._variables.date_var_name)
        self._date_col, self._date_min, self._date_max = dates_info
        depths_info = self._get_default_infos(self._variables.depth_var_name)
        self._depth_col, self._depth_min, _ = depths_info
        self._depth_max = self.__default_depth_max

    def _get_default_infos(self, variable: str) -> tuple[Any]:
        """Return default information for a variable.

        Parameters
        ----------
        variable : str
            The name of the variable.

        Returns
        -------
        tuple[Any]
            Name of the corresponding column, minimum value, maximum value.
        """
        column_name = self._variables.get(variable).label
        min_value, max_value = self._get_default_boundaries(column_name)
        return column_name, min_value, max_value

    def _get_default_boundaries(self, column_name: str) -> tuple[Any, Any]:
        """Return minimum and maximum values for a given column name.

        Parameters
        ----------
        column_name : str
            Column to get the minimum and maximum of.

        Returns
        -------
        tuple[Any, Any]
            Minimum value, maximum value.
        """
        min_value = self._storer._data[column_name].min()
        max_value = self._storer._data[column_name].max()
        return min_value, max_value

    def reset_boundaries(self) -> None:
        """Reset boundaries extremum to the defaults ones \
        (minimum and maximum observed in the data)."""
        self._date_min, self._date_max = self._get_default_boundaries(self._date_col)
        self._depth_min, _ = self._get_default_boundaries(self._depth_col)
        self._depth_max == self.__default_depth_max
        self._lat_min, self._lat_max = self._get_default_boundaries(self._lat_col)
        self._lon_min, self._lon_max = self._get_default_boundaries(self._lon_col)

    def set_geographic_boundaries(
        self,
        latitude_min: int | float = np.nan,
        latitude_max: int | float = np.nan,
        longitude_min: int | float = np.nan,
        longitude_max: int | float = np.nan,
    ) -> None:
        """Set the geographic boundaries from latitude and longitude minimum / maximum.

        Parameters
        ----------
        latitude_min : int | float, optional
            Minimum value for latitude., by default np.nan
        latitude_max : int | float, optional
            Maximum value for latitude., by default np.nan
        longitude_min : int | float, optional
            Minimum value for longitude., by default np.nan
        longitude_max : int | float, optional
            Maximum value for longitude., by default np.nan
        """
        if not np.isnan(latitude_min):
            self._lat_min = latitude_min
        if not np.isnan(latitude_max):
            self._lat_max = latitude_max
        if not np.isnan(longitude_min):
            self._lon_min = longitude_min
        if not np.isnan(longitude_max):
            self._lon_max = longitude_max

    def set_dates_boundaries(
        self,
        date_min: dt.datetime = np.nan,
        date_max: dt.datetime = np.nan,
    ) -> None:
        """Set the date boundaries.

        Parameters
        ----------
        date_min : dt.datetime, optional
            Minimum date (included)., by default np.nan
        date_max : dt.datetime, optional
            Maximum date (included)., by default np.nan
        """
        if not (isinstance(date_min, float) and (not np.isnan(date_min))):
            self._date_min = date_min
        if not (isinstance(date_max, float) and not np.isnan(date_max)):
            self._date_max = date_max

    def set_depth_boundaries(
        self,
        depth_min: int | float = np.nan,
        depth_max: int | float = np.nan,
    ) -> None:
        """Set the depth boundaries.

        Parameters
        ----------
        depth_min : int | float, optional
            Minimum depth (included)., by default np.nan
        depth_max : int | float, optional
            Maximum depth (included)., by default np.nan
        """
        if not np.isnan(depth_min):
            self._depth_min = depth_min
        if not np.isnan(depth_max):
            self._depth_max = depth_max

    @abstractmethod
    def _build(self, *args, **kwargs) -> "Figure":
        """Create the figure.

        Parameters
        ----------
        *args: list
            Parameters to build the figure.
        *kwargs: dict
            Parameters to build the figure.

        Returns
        -------
        Figure
            Figure to show or save.
        """
        ...

    @abstractmethod
    def show(self, title: str = None, suptitle: str = None, *args, **kwargs) -> None:
        """Plot method.

        Parameters
        ----------
        title : str, optional
            Specify a title to change from default., by default None
        suptitle : str, optional
            Specify a suptitle to change from default., by default None
        *args: list
            Additional parameters to pass to self._build.
        *kwargs: dict
            Additional parameters to pass to self._build.
        """
        _ = self._build(*args, **kwargs)
        if title is not None:
            plt.title(title)
        if suptitle is not None:
            plt.suptitle(suptitle)
        plt.show()
        plt.close()

    @abstractmethod
    def save(
        self,
        save_path: str,
        title: str = None,
        suptitle: str = None,
        *args,
        **kwargs,
    ) -> None:
        """Figure saving method.

        Parameters
        ----------
        save_path : str
            Path to save the output image.
        title : str, optional
            Specify a title to change from default., by default None
        suptitle : str, optional
            Specify a suptitle to change from default., by default None
        *args: list
            Additional parameters to pass to self._build.
        *kwargs: dict
            Additional parameters to pass to self._build.
        """
        _ = self._build(
            *args,
            **kwargs,
        )

        if title is not None:
            plt.title(title)
        if suptitle is not None:
            plt.suptitle(suptitle)
        plt.savefig(save_path)
