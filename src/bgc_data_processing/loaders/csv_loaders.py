"""CSV Loaders."""

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from pandas.errors import EmptyDataError

from bgc_data_processing.data_classes import Constraints, Storer
from bgc_data_processing.loaders.base import BaseLoader

if TYPE_CHECKING:
    from bgc_data_processing.variables import ExistingVar, VariablesStorer


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
        date_constraint = constraints.get_constraint_parameters(date_label)
        filepaths = self._select_filepaths(
            research_dir=self._dirin,
            pattern=self._pattern(date_constraint=date_constraint),
            exclude=exclude,
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
