import os
import re
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from bgc_data_processing.base import BaseLoader

if TYPE_CHECKING:
    from bgc_data_processing.variables import Var, VariablesStorer


class CSVLoader(BaseLoader):
    """BaseLoader subclass to use with csv files.

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
        """Reading function for csv files, modified to use self._read_params when loading the file.

        Parameters
        ----------
        filepath : str
            CSV filepath.

        Returns
        -------
        pd.DataFrame
            Raw data from the csv file.
        """
        return pd.read_csv(filepath, **self._read_params)

    def _find_columns_to_keep(self, df: pd.DataFrame) -> list:
        """Selects columns to keep in the dataframe.

        Notes
        -----
        This methods handles the fact that variables can have multiple aliases
        (if the column name for the variable is different in different files).
        For multi-aliases variables, this methods only returns the first specified alias
        appearing in the data file.

        Parameters
        ----------
        df : pd.DataFrame
            Dataframe to select columns from

        Returns
        -------
        list
            Columns to keep when formatting.
        """
        columns_to_keep = []
        for var in self._variables.in_dset:
            for alias in var.alias:
                if alias in df.columns:
                    columns_to_keep.append(alias)
                    break
        return columns_to_keep

    def _find_flag_columns(self, df: pd.DataFrame) -> list["Var"]:
        """Selects columns to keep in the dataframe.

        Notes
        -----
        This methods handles the fact that variables can have multiple aliases
        (if the column name for the variable is different in different files).
        For multi-aliases variables, this methods only returns the first specified alias
        appearing in the data file.

        Parameters
        ----------
        df : pd.DataFrame
            Dataframe to select columns from

        Returns
        -------
        list
            Columns to keep when formatting.
        """
        columns_to_keep = []
        for var in self._variables.in_dset:
            if var.flag_alias in df.columns:
                columns_to_keep.append(var)
                break
        return columns_to_keep

    def _format(self, df: pd.DataFrame) -> pd.DataFrame:
        """Formatting function for csv files, modified to drop useless columns,
        rename columns and add missing columns (variables in self._variables but not in csv file).

        Parameters
        ----------
        df : pd.DataFrame
            Dataframe to format.

        Returns
        -------
        pd.DataFrame
            Formatted Dataframe.
        """
        names_mapping = self._variables.name_mapping
        units_mapping = self._variables.unit_mapping
        # Drop useless columns
        columns_keep = self._find_columns_to_keep(df)
        slice = df.filter(columns_keep, axis=1)
        # Rename columns using pre-determined alias
        slice.rename(columns=names_mapping, inplace=True)
        # Check flags :
        flags_vars = self._find_flag_columns(df)
        slice_flags = df.filter([v.flag_alias for v in flags_vars], axis=1)
        slice_flags.rename(
            columns={v.flag_alias: v.label for v in flags_vars}, inplace=True
        )
        for var in flags_vars:
            slice[var.label].where(
                slice_flags[var.label].isin(var.correct_flag),
                np.nan,
                inplace=True,
            )
        slice[self._variables.labels["PROVIDER"]] = self._provider
        if self._variables.labels["DATE"] in slice.columns:
            # Convert Date column to datetime (if existing)
            raw_date_col = slice.pop(self._variables.labels["DATE"]).astype(str)
            dates = pd.to_datetime(raw_date_col, infer_datetime_format=True)
            slice.insert(0, self._variables.labels["DAY"], dates.dt.day)
            slice.insert(0, self._variables.labels["MONTH"], dates.dt.month)
            slice.insert(0, self._variables.labels["YEAR"], dates.dt.year)
        else:
            dates = pd.to_datetime(
                slice[
                    [
                        self._variables.labels["YEAR"],
                        self._variables.labels["MONTH"],
                        self._variables.labels["DAY"],
                    ]
                ]
            )
        slice.loc[:, self._variables.labels["DATE"]] = dates
        # Check if columns are missing => fill them with np.nan values
        missing_cols = [col for col in units_mapping.keys() if col not in slice.columns]
        if missing_cols:
            slice = slice.reindex(columns=list(slice.columns) + missing_cols)
        return slice

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
                # if the value is nan (to keep the "nan" values flagged at previous line)
                nan_values = df[var.label].isnull()
                # removing these rows
                df = df.loc[~(alpha_values & (~nan_values)), :]
            df[var.label] = df[var.label].astype(var.type)
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
        df_rm = self.remove_nan_rows(df_blon)
        return df_rm
