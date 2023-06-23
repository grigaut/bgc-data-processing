"""ABfiles Loaders."""

import datetime as dt
from pathlib import Path
from typing import TYPE_CHECKING, Any, overload

import numpy as np
import pandas as pd
from abfile import ABFileArchv, ABFileGrid

from bgc_data_processing.core.filtering import Constraints
from bgc_data_processing.core.loaders.base import BaseLoader
from bgc_data_processing.core.variables.vars import (
    ExistingVar,
    NotExistingVar,
)

if TYPE_CHECKING:
    from bgc_data_processing.core.variables.sets import SourceVariableSet


class ABFileLoader(BaseLoader):
    """Loader class to use with ABFiles.

    Parameters
    ----------
    provider_name : str
        Data provider name.
    category: str
        Category provider belongs to.
    exclude: list[str]
        Filenames to exclude from loading.
    variables : SourceVariableSet
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
        category: str,
        exclude: list[str],
        variables: "SourceVariableSet",
        grid_basename: str,
    ) -> None:
        super().__init__(
            provider_name=provider_name,
            category=category,
            exclude=exclude,
            variables=variables,
        )
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

    def is_file_valid(self, filepath: Path) -> bool:
        """Check whether a file is valid or not.

        Parameters
        ----------
        filepath : Path
            File filepath.

        Returns
        -------
        bool
            True if the file can be loaded.

        Raises
        ------
        FileNotFoundError
            If the afile doesn't not exist.
        FileNotFoundError
            If the bfile doesn't not exist.
        """
        basepath = filepath.parent / filepath.name[:-2]
        keep_filepath = str(filepath) not in self.excluded_filenames
        keep_filename = filepath.name not in self.excluded_filenames
        keep_file = keep_filename and keep_filepath
        keep_basepath = str(basepath) not in self.excluded_filenames
        keep_basename = basepath.name not in self.excluded_filenames
        keep_base = keep_basename and keep_basepath
        afile_path = Path(f"{basepath}.a")
        bfile_path = Path(f"{basepath}.b")
        if not afile_path.is_file():
            raise FileNotFoundError(
                f"{afile_path} does not exist.",
            )
        if not bfile_path.is_file():
            raise FileNotFoundError(
                f"{bfile_path} does not exist.",
            )
        return keep_base and keep_file

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
