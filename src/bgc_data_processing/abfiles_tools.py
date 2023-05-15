"""ABFiles-related objects."""
import datetime as dt
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any, overload

import numpy as np
import pandas as pd
from abfile import ABFileArchv, ABFileGrid

from bgc_data_processing.base import BaseLoader
from bgc_data_processing.data_classes import Constraints, Storer
from bgc_data_processing.variables import ExistingVar, NotExistingVar

if TYPE_CHECKING:
    from bgc_data_processing.variables import VariablesStorer


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
        """Loader class to use with ABFiles.

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
            TODO: accept one grid file per loaded file.
        """
        super().__init__(provider_name, dirin, category, files_pattern, variables)
        self.grid_basename = grid_basename
        self.grid_file = ABFileGrid(basename=grid_basename, action="r")
        self._index = None
        self.longitude_series = self._get_grid_field(self._variables.longitude_var_name)
        self.latitude_series = self._get_grid_field(self._variables.latitude_var_name)

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
        all_levels = []
        # Load levels one by one
        for level in file.fieldlevels:
            level_slice = self._load_one_level(file, level=level)
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

    def _load_one_level(self, file: ABFileArchv, level: int) -> pd.DataFrame:
        """Load data on a single level.

        Parameters
        ----------
        file : ABFileArchv
            File to load dat from.
        level : int
            Number of the level to load data from.

        Returns
        -------
        pd.DataFrame
            Raw data from the level, for all variables of interest.
        """
        # already existing columns, from grid abfiles
        columns = [self.longitude_series, self.latitude_series]
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
        pres_pascal = group.groupby([longitude_var.label, latitude_var.label]).cumsum()
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

        year, day_month, hour = date_part_basename.split("_")
        day = day_month[:2]
        month = day_month[2:]
        date = dt.date(int(year), int(month), int(day))

        date_var = self._variables.get(self._variables.date_var_name)
        year_var = self._variables.get(self._variables.year_var_name)
        month_var = self._variables.get(self._variables.month_var_name)
        day_var = self._variables.get(self._variables.day_var_name)

        without_dates[date_var.label] = date
        without_dates[year_var.label] = int(year)
        without_dates[month_var.label] = int(month)
        without_dates[day_var.label] = int(day)

        hour_var = self._variables.get(self._variables.hour_var_name)
        if hour_var is not None:
            without_dates[hour_var.label] = int(hour)

        return without_dates


class SelectiveABFileLoader(ABFileLoader):
    """Load ABFile only on given points.

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
    selection_mask : np.ndarray
        2d mask to use to load data.
    grid_basename: str
        Basename of the ab grid grid file for the loader.
        => files are considered to be loaded over the same grid.
    """

    def __init__(
        self,
        provider_name: str,
        dirin: Path,
        category: str,
        files_pattern: str,
        variables: "VariablesStorer",
        selection_mask: np.ndarray,
        grid_basename: str,
    ) -> None:

        self.mask = selection_mask
        super().__init__(
            provider_name,
            dirin,
            category,
            files_pattern,
            variables,
            grid_basename,
        )

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
                data_1d = data_2d[self.mask]
                data = self._set_index(pd.Series(data_1d, name=variable.label))
                # load flag
                if flag_name is None or flag_values is None:
                    is_valid = self._set_index(pd.Series(True, index=data.index))
                else:
                    mask_2d: np.ma.masked_array = self.grid_file.read_field(name)
                    flag_2d: np.ndarray = mask_2d.filled(np.nan)
                    flag_1d = flag_2d[self.mask]
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
        data_1d = data_2d[self.mask]
        return self._set_index(pd.Series(data_1d))

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
        data_1d = data_2d[self.mask]
        return self._set_index(pd.Series(data_1d))

    @classmethod
    def from_abloader(
        cls,
        loader: ABFileLoader,
        mask: np.ndarray,
    ) -> "SelectiveABFileLoader":
        """Create a Selective loader based on an existing loader.

        Parameters
        ----------
        loader : ABFileLoader
            Loader to use as reference.
        mask : np.ndarray
            Data mask to use for data selection.

        Returns
        -------
        SelectiveABFileLoader
            Selective Loader.
        """
        return SelectiveABFileLoader(
            provider_name=loader.provider,
            dirin=loader.dirin,
            category=loader.category,
            files_pattern=loader.files_pattern,
            variables=loader.variables,
            selection_mask=mask,
            grid_basename=loader.grid_basename,
        )
