"""NetCDF Loaders."""

import datetime as dt
import re
from pathlib import Path
from typing import TYPE_CHECKING

import netCDF4
import numpy as np
import pandas as pd

from bgc_data_processing.data_structures.filtering import Constraints
from bgc_data_processing.data_structures.storers import Storer
from bgc_data_processing.exceptions import NetCDFLoadingError
from bgc_data_processing.loaders.base import BaseLoader

if TYPE_CHECKING:
    from bgc_data_processing.data_structures.variables import (
        ExistingVar,
        NotExistingVar,
        VariablesStorer,
    )
    from bgc_data_processing.utils.patterns import FileNamePattern


def from_netcdf(
    provider_name: str,
    dirin: Path,
    category: str,
    files_pattern: "FileNamePattern",
    variables: "VariablesStorer",
) -> "NetCDFLoader":
    """Instantiate a NetCDF Loader.

    Parameters
    ----------
    provider_name : str
        Data provider name.
    dirin : Path
        Directory to browse for files to load.
    category: str
        Category provider belongs to.
    files_pattern : FileNamePattern
        Pattern to use to parse files.
        Must contain a '{years}' in order to be completed using the .format method.
    variables : VariablesStorer
        Storer object containing all variables to consider for this data,
        both the one in the data file but and the one not represented in the file.

    Returns
    -------
    NetCDFLoader
        _description_
    """
    if category == "satellite":
        return SatelliteNetCDFLoader(
            provider_name=provider_name,
            dirin=dirin,
            category=category,
            files_pattern=files_pattern,
            variables=variables,
        )
    return NetCDFLoader(
        provider_name=provider_name,
        dirin=dirin,
        category=category,
        files_pattern=files_pattern,
        variables=variables,
    )


class NetCDFLoader(BaseLoader):
    """Loader class to use with NetCDF files.

    Parameters
    ----------
    provider_name : str
        Data provider name.
    dirin : Path
        Directory to browse for files to load.
    category: str
        Category provider belongs to.
    files_pattern : FileNamePattern
        Pattern to use to parse files.
        It must contain a '{years}' in order to be completed using the .format method.
    variables : VariablesStorer
        Storer object containing all variables to consider for this data,
        both the one in the data file but and the one not represented in the file.
    """

    _date_start: dt.datetime = dt.datetime(1950, 1, 1, 0, 0, 0)
    _date_regex: str = "[0-9][0-9][0-9][0-9]-[01][0-9]-[0-3][0-9]"
    _time_regex: str = "[0-2][0-9]:[0-5][0-9]:[0-5][0-9]"
    _date_format: str = "%Y-%m-%d"
    _time_format: str = "%H:%M:%S"
    _default_time: str = "00:00:00"

    def __init__(
        self,
        provider_name: str,
        dirin: Path,
        category: str,
        files_pattern: "FileNamePattern",
        variables: "VariablesStorer",
    ) -> None:
        super().__init__(provider_name, dirin, category, files_pattern, variables)

    def __call__(
        self,
        constraints: Constraints = Constraints(),
        exclude: list = [],
    ) -> "Storer":
        """Load all files for the loader.

        Parameters
        ----------
        constraints : Constraints, optional
            Constraints slicer., by default Constraints()
        exclude : list, optional
            Files not to load., by default []

        Returns
        -------
        Storer
            Storer for the loaded data.
        """
        date_label = self._variables.get(self._variables.date_var_name).label
        date_constraint = constraints.get_constraint_parameters(date_label)
        pattern_matcher = self._files_pattern.build_from_constraint(date_constraint)
        pattern_matcher.validate = self.is_file_valid
        filepaths = pattern_matcher.select_matching_filepath(
            research_directory=self._dirin,
            exclude=exclude,
        )
        data_list = []
        for filepath in filepaths:
            data_list.append(self.load(filepath=filepath, constraints=constraints))
        data = pd.concat(data_list, ignore_index=True, axis=0)
        return Storer(
            data=data,
            category=self.category,
            providers=[self.provider],
            variables=self.variables,
            verbose=self.verbose,
        )

    def _get_id(self, filename: str) -> str:
        """Parse the station id from the file name.

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

    def _read(self, filepath: Path) -> netCDF4.Dataset:
        """Read the file loacted at filepath.

        Parameters
        ----------
        filepath : str
            Path to the file to read.

        Returns
        -------
        netCDF4.Dataset
            File content stored in a netCDF4.Dataset object.
        """
        return netCDF4.Dataset(filepath)

    def _get_shapes(self, data_dict: dict[str, np.ndarray]) -> tuple[int]:
        """Return the data shapes of the variables.

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
                "Some variables have different size (first dimension)",
            )
        shape0 = shapes0[0] if len(set(shapes0)) == 1 else 1
        if shapes1:
            # Assert all shape (2nd dimension) are the same
            if len(set(shapes1)) != 1:
                raise NetCDFLoadingError(
                    "Some variables have different size (second dimension)",
                )
            shape1 = shapes1[0]
        else:
            shape1 = 1
        return shape0, shape1

    def _fill_missing(
        self,
        data_dict: dict,
        missing_vars: list["ExistingVar|NotExistingVar"],
    ) -> dict:
        """Add empty values with correct shapes for variables.

        Apply to variables which aren't in the original data file
        but which were supposed to be.

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
        """Reshape the data arrays into 1 dimensionnal arrays to create a Dataframe.

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
        nc_data: netCDF4.Dataset,
        variable: "ExistingVar",
    ) -> np.ndarray:
        """Filter data selecting only some flag values.

        Parameters
        ----------
        nc_data : netCDF4.Dataset
            netCDF4.Dataset to use to get data.
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
            if variable == self.variables.get(self.variables.date_var_name):
                values = self._adjust_offset(nc_data.variables[alias])
            else:
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
            return values
        return None

    def _format(self, nc_data: netCDF4.Dataset) -> pd.DataFrame:
        """Format the data from netCDF4.Dataset to pd.DataFrame.

        Parameters
        ----------
        nc_data : netCDF4.Dataset
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
                continue
            values[np.isnan(values)] = var.default
            data_dict[var.label] = values
        nc_data.close()
        # Add missing columns
        data_dict = self._fill_missing(data_dict, missing_vars)
        # Reshape all variables's data to 1D
        data_dict = self._reshape_data(data_dict)
        return pd.DataFrame(data_dict)

    def _adjust_offset(self, variable: netCDF4.Variable) -> np.ndarray:
        """Adjust the time offset for all files.

        Parameters
        ----------
        variable : netCDF4.Variable
            Date variable.

        Returns
        -------
        np.ndarray
            Adjusted values
        """
        units = variable.units
        date_search = re.search(self._date_regex, units)
        time_search = re.search(self._time_regex, units)

        if date_search is None:
            raise NetCDFLoadingError(f"Impossible to find date from time unit: {units}")
        date_slice = date_search.group(0)

        time_slice = self._default_time if time_search is None else time_search.group(0)

        date_start = dt.datetime.strptime(
            f"{date_slice} {time_slice}",
            f"{self._date_format} {self._time_format}",
        )

        data: np.ma.MaskedArray = variable[:]
        values: np.ndarray = data.filled(np.nan)
        offset_diff = date_start - self._date_start
        nans = np.isnan(values)
        values[~nans] = values[~nans] + offset_diff.total_seconds() / 86400
        return values

    def _set_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Set the dates (and year, month, day) columns in the dataframe.

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
        """Set the provider column using self._provider value.

        Parameters
        ----------
        df : pd.DataFrame
            Dataframe with wrong provider column.

        Returns
        -------
        pd.DataFrame
            Dataframe with provider column properly filled.
        """
        if self._variables.has_provider:
            provider_var_name = self._variables.provider_var_name
            df.insert(0, self._variables.get(provider_var_name).label, self.provider)
        return df

    def _set_expocode(self, df: pd.DataFrame, file_id: str) -> pd.DataFrame:
        """Set the expocode column to file_id.

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
        df.insert(0, self._variables.get(expocode_var_name).label, file_id)
        # df[self._variables.get(expocode_var_name).label] = file_id  #
        return df

    def _add_empty_cols(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add the missing columns (the one supposedly not present in the dataset).

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
                df.insert(len(df.columns), var.label, np.nan)
        return df

    def _convert_type(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert columns types to the types specified for the variables.

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
            correct_type = df.pop(var.label).astype(var.type)
            df.insert(len(df.columns), var.label, correct_type)
        return df

    def load(
        self,
        filepath: Path,
        constraints: Constraints = Constraints(),
    ) -> pd.DataFrame:
        """Load a netCDF file from filepath.

        Parameters
        ----------
        filepath: Path
            Path to the file to load.
        constraints : Constraints, optional
            Constraints slicer., by default Constraints()

        Returns
        -------
        pd.DataFrame
            DataFrame corresponding to the file.
        """
        if self._verbose > 1:
            print(f"\tLoading data from {filepath.name}")
        file_id = self._get_id(filepath.name)
        nc_data = self._read(filepath=filepath)
        df_format = self._format(nc_data)
        df_dates = self._set_dates(df_format)
        df_dates_sliced = constraints.apply_specific_constraint(
            field_label=self._variables.get(self._variables.date_var_name).label,
            df=df_dates,
        )
        df_prov = self._set_provider(df_dates_sliced)
        df_expo = self._set_expocode(df_prov, file_id)
        df_ecols = self._add_empty_cols(df_expo)
        df_types = self._convert_type(df_ecols)
        df_corr = self._correct(df_types)
        df_sliced = constraints.apply_constraints_to_dataframe(df_corr)
        return self.remove_nan_rows(df_sliced)


class SatelliteNetCDFLoader(NetCDFLoader):
    """Loader class to use with NetCDF files related to Satellite data.

    Parameters
    ----------
    provider_name : str
        Data provider name.
    dirin : Path
        Directory to browse for files to load.
    category: str
        Category provider belongs to.
    files_pattern : FileNamePattern
        Pattern to use to parse files.
        It must contain a '{years}' in order to be completed using the .format method.
    variables : VariablesStorer
        Storer object containing all variables to consider for this data,
        both the one in the data file but and the one not represented in the file.
    """

    def __init__(
        self,
        provider_name: str,
        dirin: Path,
        category: str,
        files_pattern: "FileNamePattern",
        variables: "VariablesStorer",
    ) -> None:
        super().__init__(provider_name, dirin, category, files_pattern, variables)

    def _load_dimensions_vars(
        self,
        nc_data: netCDF4.Dataset,
    ) -> np.ndarray:
        """Load dimension (latitude/longitude/time) related values.

        Parameters
        ----------
        nc_data : netCDF4.Dataset
            netCDF4.Dataset to use to get data.

        Returns
        -------
        np.ndarray
            Time, Latitude, Longitude as 3d arrays.
        """
        variables = self.variables
        latitude = variables.get(variables.latitude_var_name)
        longitude = variables.get(variables.longitude_var_name)
        date = variables.get(variables.date_var_name)

        lat_values = self._filter_flags(nc_data, latitude)
        lon_values = self._filter_flags(nc_data, longitude)
        dat_values = self._filter_flags(nc_data, date)

        dat_3d = dat_values.reshape((dat_values.shape[0], 1, 1))
        lat_3d = lat_values.reshape((1, lat_values.shape[0], 1))
        lon_3d = lon_values.reshape((1, 1, lon_values.shape[0]))

        return dat_3d, lat_3d, lon_3d

    def _set_expocode(
        self,
        df: pd.DataFrame,
        file_id: str,  # noqa: ARG002 : For compatinility only
    ) -> pd.DataFrame:
        """Set the expocode column to file_id.

        Parameters
        ----------
        df : pd.DataFrame
            Dataframe with wrong expocode column.
        file_id : str
            File id, only for compatibility.

        Returns
        -------
        pd.DataFrame
            Dataframe with expocode column properly filled.
        """
        expocode_var_name = self._variables.expocode_var_name
        df.insert(
            0,
            self._variables.get(expocode_var_name).label,
            self._variables.get(expocode_var_name).default,
        )
        return df

    def _format(self, nc_data: netCDF4.Dataset) -> pd.DataFrame:
        """Format the data from netCDF4.Dataset to pd.DataFrame.

        Parameters
        ----------
        nc_data : netCDF4.Dataset
            Data storer to format.

        Returns
        -------
        pd.DataFrame
            Dataframe with the proper columns.
        """
        data_dict = {}
        variables = self.variables
        dim_vars = [
            variables.latitude_var_name,
            variables.longitude_var_name,
            variables.date_var_name,
        ]
        dims_included = False
        missing_vars = []
        for var in variables.in_dset:
            if var.name in dim_vars:
                continue
            values = self._filter_flags(nc_data=nc_data, variable=var)
            if values is None:
                missing_vars.append(var)
                continue
            if not dims_included:
                dat_3d, lat_3d, lon_3d = self._load_dimensions_vars(nc_data=nc_data)
                dat_label = variables.get(variables.date_var_name).label
                data_dict[dat_label] = np.broadcast_to(dat_3d, values.shape).ravel()
                lat_label = variables.get(variables.latitude_var_name).label
                data_dict[lat_label] = np.broadcast_to(lat_3d, values.shape).ravel()
                lon_label = variables.get(variables.longitude_var_name).label
                data_dict[lon_label] = np.broadcast_to(lon_3d, values.shape).ravel()
                dims_included = True
            values = values.ravel()
            values[np.isnan(values)] = var.default
            data_dict[var.label] = values
        nc_data.close()
        # Add missing columns
        data_dict = self._fill_missing(data_dict, missing_vars)
        # Reshape all variables's data to 1D
        data_dict = self._reshape_data(data_dict)
        return pd.DataFrame(data_dict)
