"""CSV-related objects."""

import os
import re
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from pandas.errors import EmptyDataError

from bgc_data_processing.base import BaseLoader
from bgc_data_processing.data_classes import Storer

if TYPE_CHECKING:
    from bgc_data_processing.variables import ExistingVar, VariablesStorer


class CSVLoader(BaseLoader):
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
    read_params : dict, optional
        Additional parameter to pass to pandas.read_csv., by default {}
    """

    def __init__(
        self,
        provider_name: str,
        dirin: str,
        category: str,
        files_pattern: str,
        variables: "VariablesStorer",
        read_params: dict = {},
    ) -> None:

        self._read_params = read_params
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

    def _pattern(self) -> str:
        """Returns files pattern for given years for this provider.

        Returns
        -------
        str
            Pattern.
        """
        if self._date_min is None or self._date_max is None:
            years_str = "...."
        else:
            year_min = self._date_min.year
            year_max = self._date_max.year
            years_str = "|".join([str(i) for i in range(year_min, year_max + 1)])
        pattern = self._files_pattern.format(years=years_str)
        return pattern

    def _select_filepaths(self, exclude: list) -> list[str]:
        """Selects filepaths to use when loading the data.

        exclude: list
            List of files to exclude when loading.

        Returns
        -------
        list[str]
            List of filepath to use when loading the data.
        """
        regex = re.compile(self._pattern())
        files = filter(regex.match, os.listdir(self._dirin))
        full_paths = []
        for filename in files:
            if filename not in exclude:
                full_paths.append(f"{self._dirin}/{filename}")
        return sorted(full_paths)

    def _read(self, filepath: str) -> pd.DataFrame:
        """Reading function for csv files, using self._read_params when loading files.

        Parameters
        ----------
        filepath : str
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
        """Filters data selecting only some flag values.

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
            else:
                return df[alias]
        return None

    def _format(self, df: pd.DataFrame) -> pd.DataFrame:
        """Formatting function for csv files, modified to drop useless columns, \
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
                ]
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
            lambda x: x.astype(str).str.contains("<").sum() > 0, axis=0
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

    def load(self, filepath: str) -> pd.DataFrame:
        """Loading function to load a csv file from filepath.

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
        df_raw = self._read(filepath)
        df_form = self._format(df_raw)
        df_type = self._convert_types(df_form)
        df_corr = self._correct(df_type)
        df_bdate = self._apply_boundaries(
            df_corr, "DATE", self._date_min, self._date_max
        )

        df_blat = self._apply_boundaries(
            df_bdate, "LATITUDE", self._lat_min, self._lat_max
        )

        df_blon = self._apply_boundaries(
            df_blat, "LONGITUDE", self._lon_min, self._lon_max
        )
        df_bdep = self._apply_boundaries(
            df_blon, "DEPH", self._depth_min, self._depth_max
        )
        df_expo = self._select_expocodes(df_bdep)
        df_rm = self.remove_nan_rows(df_expo)
        return df_rm
