"""Module contains tools for loading fron differents files."""

import datetime as dt
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any, overload

import netCDF4
import numpy as np
import pandas as pd
from abfile import ABFileArchv, ABFileGrid
from pandas.errors import EmptyDataError

from bgc_data_processing.data_classes import Constraints, Storer
from bgc_data_processing.exceptions import NetCDFLoadingError
from bgc_data_processing.variables import ExistingVar, NotExistingVar

if TYPE_CHECKING:
    from bgc_data_processing.variables import VariablesStorer


def from_netcdf(
    provider_name: str,
    dirin: Path,
    category: str,
    files_pattern: str,
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
    files_pattern : str
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
    return NetCDFLoader(
        provider_name=provider_name,
        dirin=dirin,
        category=category,
        files_pattern=files_pattern,
        variables=variables,
    )


def from_csv(
    provider_name: str,
    dirin: Path,
    category: str,
    files_pattern: str,
    variables: "VariablesStorer",
    read_params: dict = {},
) -> "CSVLoader":
    """Instanciate a CSV Loader.

    Parameters
    ----------
    provider_name : str
        Data provider name.
    dirin : Path
        Directory to browse for files to load.
    category: str
        Category provider belongs to.
    files_pattern : str
        Pattern to use to parse files.
        Must contain a '{years}' in order to be completed using the .format method.
    variables : VariablesStorer
        Storer object containing all variables to consider for this data,
        both the one in the data file but and the one not represented in the file.
    read_params : dict, optional
        Additional parameter to pass to pandas.read_csv., by default {}

    Returns
    -------
    CSVLoader
        _description_
    """
    return CSVLoader(
        provider_name=provider_name,
        dirin=dirin,
        category=category,
        files_pattern=files_pattern,
        variables=variables,
        read_params=read_params,
    )


def from_abfile(
    provider_name: str,
    dirin: Path,
    category: str,
    files_pattern: str,
    variables: "VariablesStorer",
    grid_basename: str,
) -> "ABFileLoader":
    """Instanciate a abfile Loader.

    Parameters
    ----------
    provider_name : str
        Data provider name.
    dirin : Path
        Directory to browse for files to load.
    category: str
        Category provider belongs to.
    files_pattern : str
        Pattern to use to parse files.
        Must contain a '{years}' in order to be completed using the .format method.
    variables : VariablesStorer
        Storer object containing all variables to consider for this data,
        both the one in the data file but and the one not represented in the file.
    grid_basename: str
        Basename of the ab grid grid file for the loader.
        => files are considered to be loaded over the same grid.

    Returns
    -------
    ABFileLoader
        _description_
    """
    return ABFileLoader(
        provider_name=provider_name,
        dirin=dirin,
        category=category,
        files_pattern=files_pattern,
        variables=variables,
        grid_basename=grid_basename,
    )


class BaseLoader(ABC):
    """Base class to load data.

    Parameters
    ----------
    provider_name : str
        Data provider name.
    dirin : Path
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
        dirin: Path,
        category: str,
        files_pattern: str,
        variables: "VariablesStorer",
    ) -> None:
        """Initiate base class to load data.

        Parameters
        ----------
        provider_name : str
            Data provider name.
        dirin : Path
            Directory to browse for files to load.
        category: str
            Category provider belongs to.
        files_pattern : str
            Pattern to use to parse files.
            Must contain a '{years}' in order to be completed using the .format method.
        variables : VariablesStorer
            Storer object containing all variables to consider for this data,
            both the one in the data file but and the one not represented in the file.
        """
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

    @property
    def dirin(self) -> Path:
        """Input directory.

        Returns
        -------
        str
            Input directory
        """
        return self._dirin

    @property
    def files_pattern(self) -> str:
        """Files pattern.

        Returns
        -------
        str
            Files pattern.
        """
        return self._files_pattern

    @abstractmethod
    def __call__(self, constraints: "Constraints", exclude: list = []) -> "Storer":
        """Load all files for the loader.

        Parameters
        ----------
        constraints: Constraints
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
        """Load data.

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
        """Remove rows.

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
        if vars_to_remove_when_any_nan:
            any_nans = df[vars_to_remove_when_any_nan].isna().any(axis=1)
        else:
            any_nans = pd.Series(False, index=df.index)
        if vars_to_remove_when_all_nan:
            all_nans = df[vars_to_remove_when_all_nan].isna().all(axis=1)
        else:
            all_nans = pd.Series(False, index=df.index)
        # Get indexes to drop
        indexes_to_drop = df[any_nans | all_nans].index
        return df.drop(index=indexes_to_drop)

    def _correct(self, to_correct: pd.DataFrame) -> pd.DataFrame:
        """Apply corrections functions defined in Var object to dataframe.

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
            correct = to_correct.pop(label).apply(correction_func)
            to_correct.insert(len(to_correct.columns), label, correct)
            # to_correct[label] = to_correct[label]  #
        return to_correct


class CSVLoader(BaseLoader):
    """Loader class to use with csv files.

    Parameters
    ----------
    provider_name : str
        Data provider name.
    dirin : Path
        Directory to browse for files to load.
    category: str
        Category provider belongs to.
    files_pattern : str
        Pattern to use to parse files.
        It must contain a '{years}' in order to be completed using the .format method.
    variables : VariablesStorer
        Storer object containing all variables to consider for this data,
        both the one in the data file but and the one not represented in the file.
    read_params : dict, optional
        Additional parameter to pass to pandas.read_csv., by default {}
    """

    def __init__(
        self,
        provider_name: str,
        dirin: Path,
        category: str,
        files_pattern: str,
        variables: "VariablesStorer",
        read_params: dict = {},
    ) -> None:
        self._read_params = read_params
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
        filepaths = self._select_filepaths(
            exclude=exclude,
            date_constraint=constraints.get_constraint_parameters(date_label),
        )
        data_list = []
        for filepath in filepaths:
            data_list.append(self.load(filepath=filepath, constraints=constraints))
        if data_list:
            data = pd.concat(data_list, ignore_index=True, axis=0)
        else:
            data = pd.DataFrame(columns=list(self._variables.labels.values()))
        return Storer(
            data=data,
            category=self.category,
            providers=[self.provider],
            variables=self.variables,
            verbose=self.verbose,
        )

    def _pattern(self, date_constraint: dict) -> str:
        """Return files pattern for given years for this provider.

        Returns
        -------
        str
            Pattern.
        date_constraint: dict
            Date-related constraint dictionnary.
        """
        if not date_constraint:
            years_str = "...."
        else:
            boundary_in = "boundary" in date_constraint
            superset_in = "superset" in date_constraint
            if boundary_in and superset_in and date_constraint["superset"]:
                b_min = date_constraint["boundary"]["min"]
                b_max = date_constraint["boundary"]["max"]
                s_min = min(date_constraint["superset"])
                s_max = max(date_constraint["superset"])
                year_min = min(b_min, s_min).year
                year_max = max(b_max, s_max).year
                years_str = "|".join([str(i) for i in range(year_min, year_max + 1)])
            elif not boundary_in:
                year_min = min(date_constraint["superset"]).year
                year_max = max(date_constraint["superset"]).year
                years_str = "|".join([str(i) for i in range(year_min, year_max + 1)])
            elif not superset_in:
                year_min = date_constraint["boundary"]["min"].year
                year_max = date_constraint["boundary"]["max"].year
                years_str = "|".join([str(i) for i in range(year_min, year_max + 1)])
            else:
                raise KeyError("Date constraint dictionnary has invalid keys")
        return self._files_pattern.format(years=years_str)

    def _select_filepaths(
        self,
        exclude: list,
        date_constraint: dict = {},
    ) -> list[Path]:
        """Select filepaths to use when loading the data.

        exclude: list
            List of files to exclude when loading.
        date_constraint: dict, optionnal
            Date-related constraint dictionnary., by default {}

        Returns
        -------
        list[Path]
            List of filepath to use when loading the data.
        """
        regex = re.compile(self._pattern(date_constraint=date_constraint))
        files = filter(regex.match, [x.name for x in self._dirin.glob("*.*")])
        full_paths = []
        for filename in files:
            if filename not in exclude:
                full_paths.append(self._dirin.joinpath(filename))
        return sorted(full_paths)

    def _read(self, filepath: Path) -> pd.DataFrame:
        """Read csv files, using self._read_params when loading files.

        Parameters
        ----------
        filepath : Path
            CSV filepath.

        Returns
        -------
        pd.DataFrame
            Raw data from the csv file.
        """
        try:
            file = pd.read_csv(filepath, **self._read_params)
        except EmptyDataError:
            file = pd.DataFrame(columns=[x.label for x in self._variables.in_dset])
        return file

    def _filter_flags(self, df: pd.DataFrame, var: "ExistingVar") -> pd.Series:
        """Filter data selecting only some flag values.

        Parameters
        ----------
        df : pd.DataFrame
            Dataframe to use to get the data.
        var : ExistingVar
            Variable to get the values of.

        Returns
        -------
        pd.Series
            Filtered values from the dataframe for the given variable.
        """
        for alias, flag_alias, correct_flags in var.aliases:
            if alias not in df.columns:
                continue
            if (flag_alias is not None) and (flag_alias in df.columns):
                corrects = df[flag_alias].isin(correct_flags)
                values = df[alias].where(corrects, np.nan)
                return values
            return df[alias]
        return None

    def _format(self, df: pd.DataFrame) -> pd.DataFrame:
        """Format csv files.

        It will drop useless columns, \
        rename columns and add missing columns (variables in self._variables \
        but not in csv file).

        Parameters
        ----------
        df : pd.DataFrame
            Dataframe to format.

        Returns
        -------
        pd.DataFrame
            Formatted Dataframe.
        """
        # units_mapping = self._variables.unit_mapping
        # Check flags :
        data = {}
        for var in self._variables.in_dset:
            values = self._filter_flags(df=df, var=var)
            if values is not None:
                data[var.label] = values
        clean_df = pd.DataFrame(data)
        if self._variables.has_provider:
            provider_var_name = self._variables.provider_var_name
            clean_df[self._variables.get(provider_var_name).label] = self._provider
        if self._variables.get(self._variables.date_var_name).label in clean_df.columns:
            # Convert Date column to datetime (if existing)
            date_label = self._variables.get(self._variables.date_var_name).label
            raw_date_col = clean_df.pop(date_label).astype(str)
            dates = pd.to_datetime(raw_date_col, infer_datetime_format=True)
            if self._variables.has_hour:
                hour_label = self._variables.get(self._variables.hour_var_name).label
                clean_df.insert(0, hour_label, dates.dt.hour)
            day_label = self._variables.get(self._variables.day_var_name).label
            clean_df.insert(0, day_label, dates.dt.day)
            month_label = self._variables.get(self._variables.month_var_name).label
            clean_df.insert(0, month_label, dates.dt.month)
            year_label = self._variables.get(self._variables.year_var_name).label
            clean_df.insert(0, year_label, dates.dt.year)
        else:
            dates = pd.to_datetime(
                clean_df[
                    [
                        self._variables.get(self._variables.year_var_name).label,
                        self._variables.get(self._variables.month_var_name).label,
                        self._variables.get(self._variables.day_var_name).label,
                    ]
                ],
            )
        date_var_label = self._variables.get(self._variables.date_var_name).label
        clean_df.loc[:, date_var_label] = dates
        for var in self._variables:
            if var.label in clean_df.columns:
                clean_df.loc[pd.isna(clean_df[var.label]), var.label] = var.default
            else:
                clean_df[var.label] = var.default
        return clean_df

    def _convert_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Type converting function, modified to behave with csv files.

        Parameters
        ----------
        df : pd.DataFrame
            Dataframe to convert.

        Returns
        -------
        pd.DataFrame
            Type converted Dataframe.
        """
        # Checking for outliers : change "<0,05" into "0,05" (example)
        wrong_format_columns = df.apply(
            lambda x: x.astype(str).str.contains("<").sum() > 0,
            axis=0,
        )
        if wrong_format_columns.any():
            correction_func = (
                lambda x: float(str(x)[1:]) if str(x)[0] == "<" else float(x)
            )
            corrected = df.loc[:, wrong_format_columns].applymap(correction_func)
            df.loc[:, wrong_format_columns] = corrected
        # Modify type :
        for var in self._variables:
            if var.type is not str:
                # if there are letters in the values
                alpha_values = df[var.label].astype(str).str.isalpha()
                # if the value is nan (keep the "nan" values flagged at previous line)
                nan_values = df[var.label].isnull()
                # removing these rows
                df = df.loc[~(alpha_values & (~nan_values)), :]
                df[var.label] = df[var.label].astype(var.type)
            else:
                df[var.label] = df[var.label].astype(var.type).str.strip()
        return df

    def load(
        self,
        filepath: Path,
        constraints: Constraints = Constraints(),
    ) -> pd.DataFrame:
        """Load a csv file from filepath.

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
        df_raw = self._read(filepath)
        df_form = self._format(df_raw)
        df_type = self._convert_types(df_form)
        df_corr = self._correct(df_type)
        df_sliced = constraints.apply_constraints_to_dataframe(df_corr)
        return self.remove_nan_rows(df_sliced)


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
        dirin: Path,
        category: str,
        files_pattern: str,
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
        filepaths = self._select_filepaths(exclude=exclude)
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

    def _select_filepaths(self, exclude: list) -> list[Path]:
        """Select filepaths referring to the files to load.

        exclude: list
            List of files to exclude when loading.

        Returns
        -------
        list[Path]
            List of the filepaths to the files to load.
        """
        regex = re.compile(self._files_pattern)
        files = filter(regex.match, [x.name for x in self._dirin.glob("*.*")])
        full_paths = []
        for filename in files:
            if filename not in exclude:
                full_paths.append(self._dirin.joinpath(filename))
        return sorted(full_paths)

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


class ABFileLoader(BaseLoader):
    """Loader class to use with ABFiles.

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
        Must contain a '{years}' in order to be completed using the .format method.
    variables : VariablesStorer
        Storer object containing all variables to consider for this data,
        both the one in the data file but and the one not represented in the file.
    grid_basename: str
        Basename of the ab grid grid file for the loader.
        => files are considered to be loaded over the same grid.
    """

    level_column: str = "LEVEL"
    level_key_bfile: str = "k"
    field_key_bfile: str = "field"
    # https://github.com/nansencenter/NERSC-HYCOM-CICE/blob/master/pythonlibs/modeltools/modeltools/hycom/_constants.py#LL1C1-L1C11
    pascal_by_seawater_meter: int = 9806

    def __init__(
        self,
        provider_name: str,
        dirin: Path,
        category: str,
        files_pattern: str,
        variables: "VariablesStorer",
        grid_basename: str,
    ) -> None:
        super().__init__(provider_name, dirin, category, files_pattern, variables)
        self.grid_basename = grid_basename
        self.grid_file = ABFileGrid(basename=grid_basename, action="r")
        self._index = None

    @overload
    def _set_index(self, data: pd.DataFrame) -> pd.DataFrame:
        ...

    @overload
    def _set_index(self, data: pd.Series) -> pd.Series:
        ...

    def _set_index(self, data: pd.DataFrame | pd.Series) -> pd.DataFrame | pd.Series:
        if self._index is None:
            self._index = data.index
        else:
            data.index = self._index
        return data

    def _read(self, basename: str) -> pd.DataFrame:
        """Read the ABfile using abfiles tools.

        Parameters
        ----------
        basename : str
            Basename of the file (no extension). For example, for abfiles
            'folder/file.2000_11_12.a' and 'folder/file.2000_11_12.b', basename is
            'folder/file.2000_11_12'.

        Returns
        -------
        pd.DataFrame
            DataFrame with columns for all variables (whether it is in the
            dataset or not).
        """
        file = ABFileArchv(basename=basename, action="r")
        lon = self._get_grid_field(self._variables.longitude_var_name)
        lat = self._get_grid_field(self._variables.latitude_var_name)
        all_levels = []
        # Load levels one by one
        for level in file.fieldlevels:
            level_slice = self._load_one_level(file, level=level, lon=lon, lat=lat)
            all_levels.append(level_slice)
        return pd.concat(all_levels, axis=0, ignore_index=True)

    def _get_grid_field(self, variable_name: str) -> pd.Series:
        """Retrieve a field from the grid adfiles.

        Parameters
        ----------
        variable_name : str
            Name of the variable to retrieve.

        Returns
        -------
        pd.Series
            Values for this variable.

        Raises
        ------
        KeyError
            If the variable does not exist in the dataset.
        """
        variable = self._variables.get(var_name=variable_name)
        data = None
        for alias in variable.aliases:
            name, flag_name, flag_values = alias
            if name in self.grid_file.fieldnames:
                # load data
                mask_2d: np.ma.masked_array = self.grid_file.read_field(name)
                data_2d: np.ndarray = mask_2d.filled(np.nan)
                data_1d = data_2d.flatten()
                data = self._set_index(pd.Series(data_1d, name=variable.label))
                # load flag
                if flag_name is None or flag_values is None:
                    is_valid = self._set_index(pd.Series(True, index=data.index))
                else:
                    mask_2d: np.ma.masked_array = self.grid_file.read_field(name)
                    flag_2d: np.ndarray = mask_2d.filled(np.nan)
                    flag_1d = flag_2d.flatten()
                    flag = pd.Series(flag_1d, name=variable.label)
                    is_valid = flag.isin(flag_values)
                # check flag
                data[~is_valid] = variable.default
                break
        if data is None:
            raise KeyError(
                f"Grid File doesn't have data for the variable {variable_name}",
            )
        return data

    def __call__(self, constraints: "Constraints", exclude: list = []) -> "Storer":
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
        # load date constraint
        date_label = self._variables.get(self._variables.date_var_name).label
        basenames = self._select_filepaths(
            exclude=exclude,
            date_constraint=constraints.get_constraint_parameters(date_label),
        )
        # load all files
        data_slices = []
        for basename in basenames:
            data_slices.append(self.load(basename, constraints))
        if data_slices:
            data = pd.concat(data_slices, axis=0)
        else:
            data = pd.DataFrame(columns=list(self._variables.labels.values()))
        return Storer(
            data=data,
            category=self.category,
            providers=[self.provider],
            variables=self.variables,
            verbose=self.verbose,
        )

    def _convert_types(self, wrong_types: pd.DataFrame) -> pd.DataFrame:
        """Type converting function, modified to behave with csv files.

        Parameters
        ----------
        df : pd.DataFrame
            Dataframe to convert.

        Returns
        -------
        pd.DataFrame
            Type converted Dataframe.
        """
        # Modify type :
        for var in self._variables:
            if var.type is not str:
                # if there are letters in the values
                alpha_values = wrong_types[var.label].astype(str).str.isalpha()
                # if the value is nan (keep the "nan" values flagged at previous line)
                nan_values = wrong_types[var.label].isnull()
                # removing these rows
                wrong_types = wrong_types.loc[~(alpha_values & (~nan_values)), :]
                wrong_types[var.label] = wrong_types[var.label].astype(var.type)
            else:
                stripped_str_col = wrong_types[var.label].astype(var.type).str.strip()
                wrong_types[var.label] = stripped_str_col
        return wrong_types

    def load(
        self,
        basename: Path,
        constraints: Constraints = Constraints(),
    ) -> pd.DataFrame:
        """Load a abfiles from basename.

        Parameters
        ----------
        basename: Path
            Path to the basename of the file to load.
        constraints : Constraints, optional
            Constraints slicer., by default Constraints()

        Returns
        -------
        pd.DataFrame
            DataFrame corresponding to the file.
        """
        raw_data = self._read(basename=str(basename))
        # transform thickness in depth
        with_depth = self._create_depth_column(raw_data)
        # create date columns
        with_dates = self._set_date_related_columns(with_depth, basename)
        # converts types
        typed = self._convert_types(with_dates)
        # apply corrections
        corrected = self._correct(typed)
        # apply constraints
        constrained = constraints.apply_constraints_to_dataframe(corrected)
        return self.remove_nan_rows(constrained)

    def _load_one_level(
        self,
        file: ABFileArchv,
        level: int,
        lon: pd.Series,
        lat: pd.Series,
    ) -> pd.DataFrame:
        """Load data on a single level.

        Parameters
        ----------
        file : ABFileArchv
            File to load dat from.
        level : int
            Number of the level to load data from.
        lon: pd.Series
            Longitude values series
        lat: pd.Series
            Latitude values series

        Returns
        -------
        pd.DataFrame
            Raw data from the level, for all variables of interest.
        """
        # already existing columns, from grid abfiles
        columns = [lon, lat]
        in_dset = self._variables.in_dset
        not_in_dset = [var for var in self._variables if var not in in_dset]
        for variable in in_dset:
            if variable.name == self._variables.longitude_var_name:
                continue
            if variable.name == self._variables.latitude_var_name:
                continue
            found = False
            for alias in variable.aliases:
                name, flag_name, flag_values = alias
                if name in self._get_fields_by_level(file, level):
                    # load data
                    field_df = self._load_field(file=file, field_name=name, level=level)
                    field_df = field_df.rename(variable.label)
                    # load valid indicator
                    field_valid = self._load_valid(file, level, flag_name, flag_values)
                    if field_valid is not None:
                        # select valid data
                        field_df[~field_valid] = variable.default
                    columns.append(field_df)
                    found = True
                    break
            if not found:
                not_in_dset.append(variable)
        # create missing columns
        for missing in not_in_dset:
            columns.append(self._create_missing_column(missing))
        return pd.concat(columns, axis=1)

    @overload
    def _load_valid(
        self,
        file: ABFileArchv,
        level: int,
        flag_name: None,
        flag_values: list[Any] | None,
    ) -> None:
        ...

    @overload
    def _load_valid(
        self,
        file: ABFileArchv,
        level: int,
        flag_name: str | None,
        flag_values: None,
    ) -> None:
        ...

    @overload
    def _load_valid(
        self,
        file: ABFileArchv,
        level: int,
        flag_name: None,
        flag_values: None,
    ) -> None:
        ...

    @overload
    def _load_valid(
        self,
        file: ABFileArchv,
        level: int,
        flag_name: str,
        flag_values: list[Any],
    ) -> pd.Series:
        ...

    def _load_valid(
        self,
        file: ABFileArchv,
        level: int,
        flag_name: str | None,
        flag_values: list[Any] | None,
    ) -> pd.Series | None:
        """Create series to keep valid data according to flag values.

        Parameters
        ----------
        file : ABFileArchv
            File to load dat from.
        level : int
            Number of the level to load data from.
        flag_name : str | None
            Name of the flag field.
        flag_values : list[Any] | None
            Accepted values for the flag.

        Returns
        -------
        pd.Series
            True where the data has a valid flag.
        """
        if flag_name is None or flag_values is None:
            return None
        filter_values = self._load_field(file, flag_name, level)
        return filter_values.isin(flag_values)

    def _load_field(self, file: ABFileArchv, field_name: str, level: int) -> pd.Series:
        """Load a field from an abfile.

        Parameters
        ----------
        file : ABFileArchv
            File to load dat from.
        field_name : str
            Name of the field to load.
        level : int
            Number of the level to load data from.

        Returns
        -------
        pd.Series
            Flatten values from the field.
        """
        mask_2d: np.ma.masked_array = file.read_field(fieldname=field_name, level=level)
        data_2d: np.ndarray = mask_2d.filled(np.nan)
        data_1d = data_2d.flatten()
        return self._set_index(pd.Series(data_1d))

    def _get_fields_by_level(self, file: ABFileArchv, level: int) -> dict:
        """Match level values to the list of field names for the level.

        Parameters
        ----------
        file : ABFileArchv
            File to load dat from.
        level : int
            Number of the level to load data from.

        Returns
        -------
        dict
            Mapping between level value and field names.
        """
        fields_levels = {}
        level_bfile = self.level_key_bfile
        field_bfile = self.field_key_bfile
        for field in file.fields.values():
            if field[level_bfile] not in fields_levels:
                fields_levels[field[level_bfile]] = [field[field_bfile]]
            else:
                fields_levels[field[level_bfile]].append(field[field_bfile])
        return fields_levels[level]

    def _create_depth_column(
        self,
        thickness_df: pd.DataFrame,
    ) -> pd.Series:
        """Create the depth column based on thickness values.

        Parameters
        ----------
        thickness_df : pd.DataFrame
            DataFrame with thickness values (in Pa).

        Returns
        -------
        pd.Series
            Dataframe with depth values (in m).
        """
        longitude_var = self._variables.get(self._variables.longitude_var_name)
        latitude_var = self._variables.get(self._variables.latitude_var_name)
        depth_var = self._variables.get(self._variables.depth_var_name)
        group = thickness_df[[longitude_var.label, latitude_var.label, depth_var.label]]
        pres_pascal = group.groupby(
            [longitude_var.label, latitude_var.label],
            dropna=False,
        ).cumsum()
        pres_sum = pres_pascal[depth_var.label]
        half_thickness = thickness_df[depth_var.label] / 2
        depth_meters = (pres_sum - half_thickness) / self.pascal_by_seawater_meter
        thickness_df[depth_var.label] = -np.abs(depth_meters)
        return thickness_df

    def _pattern(self, date_constraint: dict) -> str:
        """Return files pattern for given years for this provider.

        Returns
        -------
        str
            Pattern.
        date_constraint: dict
            Date-related constraint dictionnary.
        """
        if not date_constraint:
            years_str = "...."
        else:
            boundary_in = "boundary" in date_constraint
            superset_in = "superset" in date_constraint
            if boundary_in and superset_in and date_constraint["superset"]:
                b_min = date_constraint["boundary"]["min"]
                b_max = date_constraint["boundary"]["max"]
                s_min = min(date_constraint["superset"])
                s_max = max(date_constraint["superset"])
                year_min = min(b_min, s_min).year
                year_max = max(b_max, s_max).year
                years_str = "|".join([str(i) for i in range(year_min, year_max + 1)])
            elif not boundary_in:
                year_min = min(date_constraint["superset"]).year
                year_max = max(date_constraint["superset"]).year
                years_str = "|".join([str(i) for i in range(year_min, year_max + 1)])
            elif not superset_in:
                year_min = date_constraint["boundary"]["min"].year
                year_max = date_constraint["boundary"]["max"].year
                years_str = "|".join([str(i) for i in range(year_min, year_max + 1)])
            else:
                raise KeyError("Date constraint dictionnary has invalid keys")
        return self._files_pattern.format(years=years_str)

    def _select_filepaths(
        self,
        exclude: list,
        date_constraint: Constraints,
    ) -> list[Path]:
        """Select filepaths to use when loading the data.

        exclude: list
            List of files to exclude when loading.
        date_constraint: dict, optionnal
            Date-related constraint dictionnary., by default {}

        Returns
        -------
        list[Path]
            List of filepath to use when loading the data.
        """
        regex = re.compile(self._pattern(date_constraint=date_constraint))
        files = filter(regex.match, [x.name for x in self._dirin.glob("*.*")])
        full_paths = []
        for filename in files:
            basename = filename[:-2]
            keep_filename = filename not in exclude
            keep_basename = basename not in exclude
            path_basename = self._dirin.joinpath(basename)
            afile_path = Path(f"{path_basename}.a")
            bfile_path = Path(f"{path_basename}.b")
            if not afile_path.is_file():
                raise FileNotFoundError(
                    f"{afile_path} does not exist.",
                )
            if not bfile_path.is_file():
                raise FileNotFoundError(
                    f"{bfile_path} does not exist.",
                )
            if keep_basename and keep_filename:
                full_paths.append(path_basename)

        return full_paths

    def _create_missing_column(
        self,
        missing_column_variable: ExistingVar | NotExistingVar,
    ) -> pd.Series:
        """Create column for missing variables using default value.

        Parameters
        ----------
        missing_column_variable : ExistingVar | NotExistingVar
            Variable corresponding to the missing column.

        Returns
        -------
        pd.Series
            Data for the missing variable.
        """
        default_value = missing_column_variable.default
        name = missing_column_variable.label
        return pd.Series(default_value, name=name, index=self._index)

    def _set_date_related_columns(
        self,
        without_dates: pd.DataFrame,
        basename: Path,
    ) -> pd.Series:
        """Set up the date, year, month, day and hour columns.

        Parameters
        ----------
        without_dates : pd.DataFrame
            DataFrame with improper dates related columns.
        basename : Path
            Basename of the file (no extension). For example, for abfiles
            'folder/file.2000_11_12.a' and 'folder/file.2000_11_12.b', basename is
            'folder/file.2000_11_12'.

        Returns
        -------
        pd.Series
            DataFrame with correct dates related columns.
        """
        date_part_basename = basename.name.split(".")[-1]

        date = dt.datetime.strptime(date_part_basename, "%Y_%j_%H")

        date_var = self._variables.get(self._variables.date_var_name)
        year_var = self._variables.get(self._variables.year_var_name)
        month_var = self._variables.get(self._variables.month_var_name)
        day_var = self._variables.get(self._variables.day_var_name)

        without_dates[date_var.label] = date.date()
        without_dates[year_var.label] = date.year
        without_dates[month_var.label] = date.month
        without_dates[day_var.label] = date.day

        hour_var = self._variables.get(self._variables.hour_var_name)
        if hour_var is not None:
            without_dates[hour_var.label] = date.hour

        return without_dates
