"""NetCDF-related objects."""


import datetime as dt
import os
import re
from typing import TYPE_CHECKING

import netCDF4 as nc
import numpy as np
import pandas as pd

from bgc_data_processing.base import BaseLoader
from bgc_data_processing.data_classes import Storer
from bgc_data_processing.exceptions import NetCDFLoadingError

if TYPE_CHECKING:
    from bgc_data_processing.variables import (
        ExistingVar,
        NotExistingVar,
        VariablesStorer,
    )


class NetCDFLoader(BaseLoader):
    """Loader class to use with csv files.

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

    _date_start: dt.datetime = dt.datetime(1950, 1, 1, 0, 0, 0)

    def __init__(
        self,
        provider_name: str,
        dirin: str,
        category: str,
        files_pattern: str,
        variables: "VariablesStorer",
    ) -> None:
        super().__init__(provider_name, dirin, category, files_pattern, variables)

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
        filepaths = self._select_filepaths(exclude=exclude)
        data_list = []
        for filepath in filepaths:
            data_list.append(self.load(filepath=filepath))
        data = pd.concat(data_list, ignore_index=True, axis=0)
        return Storer(
            data=data,
            category=self.category,
            providers=[self.provider],
            variables=self.variables,
            verbose=self.verbose,
        )

    def _select_filepaths(self, exclude: list) -> list[str]:
        """Selects filepaths referring to the files to load.

        exclude: list
            List of files to exclude when loading.

        Returns
        -------
        list[str]
            List of the filepaths to the files to load.
        """
        regex = re.compile(self._files_pattern)
        files = filter(regex.match, os.listdir(self._dirin))
        full_paths = []
        for filename in files:
            if filename not in exclude:
                full_paths.append(f"{self._dirin}/{filename}")
        return sorted(full_paths)

    def _get_id(self, filename: str) -> str:
        """Parses the station id from the file name.

        Notes
        -----
        Maybe only relevant for Argo files => to investigate.

        Parameters
        ----------
        filename : str
            File name.

        Returns
        -------
        str
            Station id.
        """
        return filename.split("_")[3].split(".")[0]

    def _read(self, filepath: str) -> nc.Dataset:
        """Reads the file loacted at filepath.

        Parameters
        ----------
        filepath : str
            Path to the file to read.

        Returns
        -------
        nc.Dataset
            File content stored in a netCDF4.Dataset object.
        """
        return nc.Dataset(filepath)

    def _get_shapes(self, data_dict: dict[str, np.ndarray]) -> tuple[int]:
        """Returns the data shapes of the variables.

        Parameters
        ----------
        data_dict : dict
            Dictionnary (variable_name : value) mapping the data.

        Returns
        -------
        tuple[int]
            First dimension, second dimension (1 if the data is only 1D).

        Raises
        ------
        NetCDFLoadingError
            If the 1st dimension if not the same among all files.
        NetCDFLoadingError
            If the 2nd dimension if not the same among all files.
        """
        shapes0 = []
        shapes1 = []
        for var in self.variables.in_dset:
            var_data = data_dict[var.label]
            if var_data.shape[0] > 1:
                shapes0.append(var_data.shape[0])
            if len(var_data.shape) == 2:
                shapes1.append(var_data.shape[1])
        # Assert all shape (1st dimension) are the same
        if len(set(shapes0)) > 1:
            raise NetCDFLoadingError(
                "Some variables have different size (first dimension)"
            )
        elif len(set(shapes0)) == 1:
            shape0 = shapes0[0]
        else:
            # if the shape list is empty => all variables have a 1st dimension of 1
            shape0 = 1
        if shapes1:
            # Assert all shape (2nd dimension) are the same
            if len(set(shapes1)) != 1:
                raise NetCDFLoadingError(
                    "Some variables have different size (second dimension)"
                )
            shape1 = shapes1[0]
        else:
            shape1 = 1
        return shape0, shape1

    def _fill_missing(
        self, data_dict: dict, missing_vars: list["ExistingVar|NotExistingVar"]
    ) -> dict:
        """Adds empty values with correct shapes for variables \
        which aren't in the original data file but which were supposed to be.

        Notes
        -----
        The empty values can be 1D or 2D since
        they'll be reshaped using self._reshape_afterwards afterward.

        Parameters
        ----------
        data_dict : dict
            Dictionnary on which to add entries for missing variables.
        missing_vars : list["ExistingVar|NotExistingVar"]
            Missing variables.

        Returns
        -------
        dict
            Filled dictionnary.

        Raises
        ------
        NetCDFLoadingError
            If all variables are missing => impossible to find the shape of the data.
        """
        if not missing_vars:
            return data_dict
        if len(missing_vars) == len(self.variables):
            raise NetCDFLoadingError("Empty data for all variables to consider")
        # Get data shape from a non missing variable
        var_ref = [var for var in self.variables.in_dset if var not in missing_vars][0]
        shape_ref = data_dict[var_ref.label].shape
        for var in missing_vars:
            # Create empty frame with nans
            data_dict[var.label] = np.empty(shape_ref)
            data_dict[var.label].fill(var.default)
        return data_dict

    def _reshape_data(self, data_dict: dict) -> dict:
        """Reshapes the data arrays into 1 dimensionnal arrays \
        in order to create a Dataframe.

        Parameters
        ----------
        data_dict : dict
            Data to reshape.

        Returns
        -------
        dict
            Reshaped data.
        """
        shape0, shape1 = self._get_shapes(data_dict)
        reshaped = {}
        for var in self.variables.in_dset:
            data = data_dict[var.label]
            if data.shape == (1,):
                # data contains a single value => from CMEMS: latitude or longitude
                data = np.tile(data, (shape0,))
            if len(data.shape) == 1:
                # Reshape data to 2D
                data = np.tile(data.reshape((shape0, 1)), (1, shape1))
            # Flatten 2D data
            reshaped[var.label] = data.flatten()
        return reshaped

    def _filter_flags(
        self,
        nc_data: nc.Dataset,
        variable: "ExistingVar",
    ) -> np.ndarray:
        """Filter data selecting only some flag values.

        Parameters
        ----------
        nc_data : nc.Dataset
            nc.Dataset to use to get data.
        variable : ExistingVar
            Variable to get the values of.

        Returns
        -------
        np.ndarray
            Filtered values from nc_data for the given variable
        """
        file_keys = nc_data.variables.keys()
        for alias, flag, correct_flags in variable.aliases:
            if alias not in file_keys:
                continue
            # Get data from file
            values = nc_data.variables[alias][:]
            # Convert masked_array to ndarray
            values: np.ndarray = values.filled(np.nan)
            if (flag is not None) and (flag in file_keys):
                # get flag values from file
                flag_values = nc_data.variables[flag][:]
                # Fill with an integer => careful not to use an integer in the flags
                flag_values: np.ndarray = flag_values.filled(-1)
                good_flags = np.empty(values.shape, dtype=bool)
                good_flags.fill(False)
                for value in correct_flags:
                    good_flags = good_flags | (flag_values == value)
                return np.where(good_flags, values, np.nan)
            else:
                return values
        return None

    def _format(self, nc_data: nc.Dataset) -> pd.DataFrame:
        """Formats the data from netCDF4.Dataset to pd.DataFrame.

        Parameters
        ----------
        nc_data : nc.Dataset
            Data storer to format.

        Returns
        -------
        pd.DataFrame
            Dataframe with the propers columns.
        """
        data_dict = {}
        missing_vars = []
        for var in self._variables.in_dset:
            values = self._filter_flags(nc_data=nc_data, variable=var)
            if values is None:
                missing_vars.append(var)
            else:
                values[np.isnan(values)] = var.default
                data_dict[var.label] = values
                # data_dict[var.label].fill(var.default)
        # Add missing columns
        data_dict = self._fill_missing(data_dict, missing_vars)
        # Reshape all variables's data to 1D
        data_dict = self._reshape_data(data_dict)
        return pd.DataFrame(data_dict)

    def _set_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Sets the dates (and year, month, day) columns in the dataframe.

        Parameters
        ----------
        df : pd.DataFrame
            Dataframe on which to set the columns.

        Returns
        -------
        pd.DataFrame
            Dataframe with date, year, month and day columns.
        """
        # Convert from timedeltas to datetime
        date_var_label = self.variables.get(self._variables.date_var_name).label
        timedeltas = df.pop(date_var_label)
        dates = pd.to_timedelta(timedeltas, "D") + self._date_start
        df[date_var_label] = dates
        # Add year, month and day columns
        df[self.variables.get(self._variables.year_var_name).label] = dates.dt.year
        df[self.variables.get(self._variables.month_var_name).label] = dates.dt.month
        df[self.variables.get(self._variables.day_var_name).label] = dates.dt.day
        if self._variables.has_hour:
            df[self.variables.get(self._variables.hour_var_name).label] = dates.dt.hour
        return df

    def _set_provider(self, df: pd.DataFrame) -> pd.DataFrame:
        """Sets the provider column using self._provider value.

        Parameters
        ----------
        df : pd.DataFrame
            Dataframe with wrong provider column.

        Returns
        -------
        pd.DataFrame
            Dataframe with provider column properly filled.
        """
        provider_var_name = self._variables.provider_var_name
        df[self._variables.get(provider_var_name).label] = self.provider
        return df

    def _set_expocode(self, df: pd.DataFrame, file_id: str) -> pd.DataFrame:
        """Sets the expocode column to file_id.

        Parameters
        ----------
        df : pd.DataFrame
            Dataframe with wrong expocode column.
        file_id : str
            File id to use as expocode value.

        Returns
        -------
        pd.DataFrame
            Dataframe with expocode column properly filled.
        """
        expocode_var_name = self._variables.expocode_var_name
        df[self._variables.get(expocode_var_name).label] = file_id
        return df

    def _add_empty_cols(self, df: pd.DataFrame) -> pd.DataFrame:
        """Adds the missing columns (the one supposedly not present in the dataset).

        Parameters
        ----------
        df : pd.DataFrame
            Dataframe on which to add columns.

        Returns
        -------
        pd.DataFrame
            Dataframe with all wished columns (for every variable in self._variable).
        """
        for var in self._variables:
            if var.label not in df.columns:
                df[var.label] = np.nan
        return df

    def _convert_type(self, df: pd.DataFrame) -> pd.DataFrame:
        """Converts columns types to the types specified for the variables.

        Parameters
        ----------
        df : pd.DataFrame
            Dataframe on which to convert types.

        Returns
        -------
        pd.DataFrame
            Dataframe with wished types.
        """
        for var in self._variables:
            df[var.label] = df[var.label].astype(var.type)
        return df

    def load(self, filepath: str) -> pd.DataFrame:
        """Loading function to load a netCDF file from filepath.

        Parameters
        ----------
        filepath: str
            Path to the file to load.

        Returns
        -------
        pd.DataFrame
            DataFrame corresponding to the file.
        """
        if self._verbose > 1:
            print("\tLoading data from {}".format(filepath.split("/")[-1]))
        file_id = self._get_id(filepath.split("/")[-1])
        nc_data = self._read(filepath=filepath)
        df_format = self._format(nc_data)
        df_dates = self._set_dates(df_format)
        df_bdates = self._apply_boundaries(
            df_dates, "DATE", self._date_min, self._date_max
        )
        df_blat = self._apply_boundaries(
            df_bdates, "LATITUDE", self._lat_min, self._lat_max
        )
        df_blon = self._apply_boundaries(
            df_blat, "LONGITUDE", self._lon_min, self._lon_max
        )
        df_prov = self._set_provider(df_blon)
        df_expo = self._set_expocode(df_prov, file_id)
        df_ecols = self._add_empty_cols(df_expo)
        df_types = self._convert_type(df_ecols)
        df_corr = self._correct(df_types)
        df_bdep = self._apply_boundaries(
            df_corr, "DEPH", self._depth_min, self._depth_max
        )
        df_rm = self.remove_nan_rows(df_bdep)
        return df_rm
