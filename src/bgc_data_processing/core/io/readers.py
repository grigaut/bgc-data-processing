"""Read generated files."""

from copy import deepcopy
from pathlib import Path

import pandas as pd

from bgc_data_processing.core.storers import Storer
from bgc_data_processing.core.variables.sets import SourceVariableSet
from bgc_data_processing.core.variables.vars import BaseVar, ParsedVar


def read_files(
    filepath: Path | str | list[Path] | list[str],
    providers_column_label: str = "PROVIDER",
    expocode_column_label: str = "EXPOCODE",
    date_column_label: str = "DATE",
    year_column_label: str = "YEAR",
    month_column_label: str = "MONTH",
    day_column_label: str = "DAY",
    hour_column_label: str = "HOUR",
    latitude_column_label: str = "LATITUDE",
    longitude_column_label: str = "LONGITUDE",
    depth_column_label: str = "DEPH",
    variables_reference: list[BaseVar] = [],
    category: str = "in_situ",
    unit_row_index: int = 1,
    delim_whitespace: bool = True,
    verbose: int = 1,
) -> "Storer":
    """Build Storer reading data from csv or txt files.

    Parameters
    ----------
    filepath : Path | str | list[Path] | list[str]
        Path to the file to read.
    providers_column_label : str, optional
        Provider column in the dataframe., by default "PROVIDER"
    expocode_column_label : str, optional
        Expocode column in the dataframe., by default "EXPOCODE"
    date_column_label : str, optional
        Date column in the dataframe., by default "DATE"
    year_column_label : str, optional
        Year column in the dataframe., by default "YEAR"
    month_column_label : str, optional
        Month column in the dataframe., by default "MONTH"
    day_column_label : str, optional
        Day column in the dataframe., by default "DAY"
    hour_column_label : str, optional
        Hour column in the dataframe., by default "HOUR"
    latitude_column_label : str, optional
        Latitude column in the dataframe., by default "LATITUDE"
    longitude_column_label : str, optional
        Longitude column in the dataframe., by default "LONGITUDE"
    depth_column_label : str, optional
        Depth column in the dataframe., by default "DEPH"
    variables_reference: list[BaseVar]
        List of variable to use as reference. If a variable label is a column name,
         this variable will be used for the output storer., by default []
    category : str, optional
        Category of the loaded file., by default "in_situ"
    unit_row_index : int, optional
        Index of the row with the units, None if there's no unit row., by default 1
    delim_whitespace : bool, optional
        Whether to use whitespace as delimiters., by default True
    verbose : int, optional
        Controls the verbose, by default 1

    Returns
    -------
    Storer
        Storer aggregating the data from all the files

    Raises
    ------
    TypeError
        If filepath argument is not an instance of string or list.

    Examples
    --------
    Loading from a single file:
    >>> filepath = "path/to/file"
    >>> storer = read_files(filepath, providers="providers_column_name")

    Loading from multiple files:
    >>> filepaths = [
    ...     "path/to/file1",
    ...     "path/to/file2",
    ... ]
    >>> storer = read_files(
    ...     filepaths,
    ... )
    """
    if isinstance(filepath, list):
        storers = []
        for path in filepath:
            storer = read_files(
                filepath=path,
                providers_column_label=providers_column_label,
                expocode_column_label=expocode_column_label,
                date_column_label=date_column_label,
                year_column_label=year_column_label,
                month_column_label=month_column_label,
                day_column_label=day_column_label,
                hour_column_label=hour_column_label,
                latitude_column_label=latitude_column_label,
                longitude_column_label=longitude_column_label,
                depth_column_label=depth_column_label,
                variables_reference=variables_reference,
                category=category,
                unit_row_index=unit_row_index,
                delim_whitespace=delim_whitespace,
                verbose=verbose,
            )

            storers.append(storer)
        return sum(storers)
    if isinstance(filepath, Path):
        path = filepath
    elif isinstance(filepath, str):
        path = Path(filepath)
    else:
        error_msg = f"Can't read filepaths from {filepath}. "
        "Accepted types are Path or str."
        raise TypeError(error_msg)
    reader = Reader(
        filepath=path,
        providers_column_label=providers_column_label,
        expocode_column_label=expocode_column_label,
        date_column_label=date_column_label,
        year_column_label=year_column_label,
        month_column_label=month_column_label,
        day_column_label=day_column_label,
        hour_column_label=hour_column_label,
        latitude_column_label=latitude_column_label,
        longitude_column_label=longitude_column_label,
        depth_column_label=depth_column_label,
        variables_reference=variables_reference,
        category=category,
        unit_row_index=unit_row_index,
        delim_whitespace=delim_whitespace,
        verbose=verbose,
    )
    return reader.get_storer()


class Reader:
    """Reading routine to parse csv files.

    Parameters
    ----------
    filepath : Path | str
        Path to the file to read.
    providers_column_label : str, optional
        Provider column in the dataframe., by default "PROVIDER"
    expocode_column_label : str, optional
        Expocode column in the dataframe., by default "EXPOCODE"
    date_column_label : str, optional
        Date column in the dataframe., by default "DATE"
    year_column_label : str, optional
        Year column in the dataframe., by default "YEAR"
    month_column_label : str, optional
        Month column in the dataframe., by default "MONTH"
    day_column_label : str, optional
        Day column in the dataframe., by default "DAY"
    hour_column_label : str, optional
        Hour column in the dataframe., by default "HOUR"
    latitude_column_label : str, optional
        Latitude column in the dataframe., by default "LATITUDE"
    longitude_column_label : str, optional
        Longitude column in the dataframe., by default "LONGITUDE"
    depth_column_label : str, optional
        Depth column in the dataframe., by default "DEPH"
    variables_reference: list[BaseVar]
        List of variable to use as reference. If a variable label is a column name,
         this variable will be used for the output storer., by default []
    category : str, optional
        Category of the loaded file., by default "in_situ"
    unit_row_index : int, optional
        Index of the row with the units, None if there's no unit row., by default 1
    delim_whitespace : bool, optional
        Whether to use whitespace as delimiters., by default True
    verbose : int, optional
        Controls the verbose, by default 1

    Examples
    --------
    Loading from a file:
    >>> filepath = "path/to/file"
    >>> reader = Reader(filepath, providers="providers_column_name")

    Getting the storer:
    >>> storer = reader.get_storer()
    """

    def __init__(
        self,
        filepath: Path | str,
        providers_column_label: str = "PROVIDER",
        expocode_column_label: str = "EXPOCODE",
        date_column_label: str = "DATE",
        year_column_label: str = "YEAR",
        month_column_label: str = "MONTH",
        day_column_label: str = "DAY",
        hour_column_label: str = "HOUR",
        latitude_column_label: str = "LATITUDE",
        longitude_column_label: str = "LONGITUDE",
        depth_column_label: str = "DEPH",
        variables_reference: list[BaseVar] = [],
        category: str = "in_situ",
        unit_row_index: int = 1,
        delim_whitespace: bool = True,
        verbose: int = 1,
    ):
        self._verbose = verbose
        self._reference_vars = {var.label: var for var in variables_reference}

        raw_df, unit_row = self._read(Path(filepath), unit_row_index, delim_whitespace)
        if self._verbose > 1:
            print("\tParsing file variables.")
        mandatory_vars = {
            providers_column_label: "provider",
            expocode_column_label: "expocode",
            date_column_label: "date",
            year_column_label: "year",
            month_column_label: "month",
            day_column_label: "day",
            hour_column_label: "hour",
            latitude_column_label: "latitude",
            longitude_column_label: "longitude",
            depth_column_label: "depth",
        }
        self._category = category
        if providers_column_label is not None:
            self._providers = raw_df[providers_column_label].unique().tolist()
        else:
            self._providers = ["????"]
        self._data = self._add_date_columns(
            raw_df,
            year_column_label,
            month_column_label,
            day_column_label,
            date_column_label,
        )
        self._variables = self._get_variables(raw_df, unit_row, mandatory_vars)

    def _read(
        self,
        filepath: Path,
        unit_row_index: int,
        delim_whitespace: bool,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Read the filepath and extract the unit row.

        Parameters
        ----------
        filepath : Path
            Path to the file to read.
        unit_row_index : int
            Index of the row with the units, None if there's no unit row.
        delim_whitespace : bool
            Whether to use whitespace as delimiters.

        Returns
        -------
        tuple[pd.DataFrame, pd.DataFrame]
            Dataframe, unit row
        """
        if unit_row_index is None:
            skiprows = None
            unit_row = None
        else:
            skiprows = [unit_row_index]
            unit_row = pd.read_csv(
                filepath,
                delim_whitespace=delim_whitespace,
                skiprows=lambda x: x not in [*skiprows, 0],
            )
        if self._verbose > 0:
            print(f"Reading data from {filepath}")
        raw_df = pd.read_csv(
            filepath,
            delim_whitespace=delim_whitespace,
            skiprows=skiprows,
        )
        return raw_df, unit_row

    def _get_variables(
        self,
        raw_df: pd.DataFrame,
        unit_row: pd.DataFrame,
        mandatory_vars: dict,
    ) -> "SourceVariableSet":
        """Parse variables from the csv data.

        Parameters
        ----------
        raw_df : pd.DataFrame
            Dataframe to parse.
        unit_row : pd.DataFrame
            Unit row to use as reference for variables' units.
        mandatory_vars: dict
            Mapping between column name and parameter for mandatory variables.

        Returns
        -------
        SourceVariableSet
            Collection of variables.
        """
        variables = {}
        for column in raw_df.columns:
            if self._verbose > 2:
                print(f"\t\tParsing column {column}.")
            if unit_row is None or column not in unit_row.columns:
                unit = "[]"
            else:
                unit = unit_row[column].values[0]

            default_var = ParsedVar(
                name=column.upper(),
                unit=unit,
                var_type=raw_df.dtypes[column].name,
            )
            var = deepcopy(self._reference_vars.get(column, default_var))
            if column in mandatory_vars:
                variables[mandatory_vars[column]] = var
            else:
                variables[column.lower()] = var
        for param in mandatory_vars.values():
            if param not in variables.keys():
                variables[param] = None
        return SourceVariableSet(**variables)

    def _make_date_column(
        self,
        raw_df: pd.DataFrame,
        year_col: str,
        month_col: str,
        day_col: str,
    ) -> pd.Series:
        """Make date column (datetime) from year, month, day columns if existing.

        Parameters
        ----------
        raw_df : pd.DataFrame
            Dataframe
        year_col: str
            Year column name.
        month_col: str
            Month column name.
        day_col: str
            Day column name.

        Returns
        -------
        pd.Series
            Date column.
        """
        return pd.to_datetime(raw_df[[year_col, month_col, day_col]])

    def _add_date_columns(
        self,
        raw_df: pd.DataFrame,
        year_col: str,
        month_col: str,
        day_col: str,
        date_col: str,
    ) -> pd.DataFrame:
        """Add missing columns to the dataframe.

        Parameters
        ----------
        raw_df : pd.DataFrame
            Dataframe to modify
        year_col: str
            Year column name.
        month_col: str
            Month column name.
        day_col: str
            Day column name.
        date_col: str
            Date column name.

        Returns
        -------
        pd.DataFrame
            Dataframe with new columns
        """
        if self._verbose > 2:
            print("\t\tParsing date.")
        if date_col in raw_df.columns:
            return raw_df
        missing_col = self._make_date_column(raw_df, year_col, month_col, day_col)
        raw_df.insert(0, date_col, missing_col)
        return raw_df

    def get_storer(self) -> "Storer":
        """Return the Storer storing the data loaded.

        Returns
        -------
        Storer
            Contains the data from the csv.
        """
        return Storer(
            data=self._data,
            category=self._category,
            providers=self._providers,
            variables=self._variables.storing_variables,
            verbose=self._verbose,
        )
