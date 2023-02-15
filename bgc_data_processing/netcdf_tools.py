import datetime as dt
import os
import re
from typing import TYPE_CHECKING

import netCDF4 as nc
import numpy as np
import pandas as pd

from bgc_data_processing.base import BaseLoader
from bgc_data_processing.exceptions import NetCDFLoadingError

if TYPE_CHECKING:
    from bgc_data_processing.variables import Var


class NetCDFLoader(BaseLoader):
    """Class to load netCDF files"""

    _date_start: dt.datetime = dt.datetime(1950, 1, 1, 0, 0, 0)

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
        if filename[0:2] == "GL":
            return filename[9:16]
        else:
            return filename[0:7]

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
            shapes0.append(var_data.shape[0])
            if len(var_data.shape) == 2:
                shapes1.append(var_data.shape[1])
        # Assert all shape (1st dimension) are the same
        if len(set(shapes0)) != 1:
            raise NetCDFLoadingError(
                "Some variables have different size (first dimension)"
            )
        shape0 = shapes0[0]
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

    def _fill_missing(self, data_dict: dict, missing_vars: list["Var"]) -> dict:
        """Adds empty values with correct shapes for variables
        which aren't in the original data file but which were supposed to be.

        Notes
        -----
        The empty values can be 1D or 2D since
        they'll be reshaped using self._reshape_afterwards afterward.

        Parameters
        ----------
        data_dict : dict
            Dictionnary on which to add entries for missing variables.
        missing_vars : list["Var"]
            Missing variables.

        Returns
        -------
        dict
            Filled dictionnary.

        Raises
        ------
        NetCDFLoadingError
            If all the variables are missing => impossible to find the shape of the data.
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
            data_dict[var.label].fill(np.nan)
        return data_dict

    def _reshape_data(self, data_dict: dict) -> dict:
        """Reshapes the data arrays into 1 dimensionnal arrays
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
            if len(data.shape) == 1:
                # Reshape data to 2D
                data = np.tile(data.reshape((shape0, 1)), (1, shape1))
            # Flatten 2D data
            reshaped[var.label] = data.flatten()
        return reshaped

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
            found = False
            for alias in var.alias:
                if alias in nc_data.variables.keys():
                    found = True
                    values = nc_data.variables[alias][:]
                    # Convert masked_array to ndarray
                    values: np.ndarray = values.filled(np.nan)
                    data_dict[var.label] = values
                    break
            if not found:
                missing_vars.append(var)
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
        timedeltas = df.pop(self.variables.labels["DATE"])
        dates = pd.to_timedelta(timedeltas, "D") + self._date_start
        df[self.variables.labels["DATE"]] = dates
        # Add year, month and day columns
        df[self.variables.labels["YEAR"]] = dates.dt.year
        df[self.variables.labels["MONTH"]] = dates.dt.month
        df[self.variables.labels["DAY"]] = dates.dt.day
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
        if "PROVIDER" in self._variables.keys():
            df[self._variables.labels["PROVIDER"]] = self.provider
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
        if "EXPOCODE" in self._variables.keys():
            df[self._variables.labels["EXPOCODE"]] = file_id
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
            Dataframe with all wished columns (one for every variable in self._variable).
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
        df_rm = self.remove_nan_rows(df_corr)
        return df_rm
