"""Data storing objects."""


import os
from typing import Any

import numpy as np
import pandas as pd

from bgc_data_processing.variables import ParsedVar, VariablesStorer


class Storer:
    """Storing data class, to keep track of metadata.

    Parameters
    ----------
    data : pd.DataFrame
        Dataframe to store.
    providers : list
        Names of the data providers.
    variables : VariablesStorer
        Variables storer of object to keep track of the variables in the Dataframe.
    verbose : int, optional
        Controls the verbosity: the higher, the more messages., by default 0
    """

    def __init__(
        self,
        data: pd.DataFrame,
        category: str,
        providers: list,
        variables: "VariablesStorer",
        verbose: int = 0,
    ) -> None:

        self._data = data
        self._category = category
        self._providers = providers
        self._variables = variables
        self._verbose = verbose

    @property
    def data(self) -> pd.DataFrame:
        """Getter for self._data.

        Returns
        -------
        pd.DataFrame
            Dataframe.
        """
        return self._data

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
    def providers(self) -> list:
        """Getter for self._providers.

        Returns
        -------
        list
            List of providers.
        """
        return self._providers

    @property
    def variables(self) -> "VariablesStorer":
        """Getter for self._variables.

        Returns
        -------
        VariablesStorer
            Variables storer.
        """
        return self._variables

    @property
    def verbose(self) -> int:
        """_verbose attribute getter.

        Returns
        -------
        int
            Verbose value.
        """
        return self._verbose

    def __repr__(self) -> str:
        return repr(self.data)

    def __eq__(self, __o: object) -> bool:
        return self is __o

    def __radd__(self, other: Any) -> "Storer":
        if other == 0:
            return self
        else:
            return self.__add__(other)

    def __add__(self, object: object) -> "Storer":
        if not isinstance(object, Storer):
            raise TypeError(f"Can't add CSVStorer object to {type(object)}")
        # Assert variables are the same
        if not (self.variables == object.variables):
            raise ValueError("Variables or categories are not compatible")
        # Assert categories are the same
        if not (self.category == object.category):
            raise ValueError("Categories are not compatible")

        concat_data = pd.concat([self._data, object._data], ignore_index=True)
        concat_providers = list(set(self.providers + object.providers))
        # Return Storer with similar variables
        concat_storer = Storer(
            data=concat_data,
            category=self.category,
            providers=concat_providers,
            variables=self.variables,
            verbose=min(self._verbose, object.verbose),
        )
        return concat_storer

    def remove_duplicates(self, priority_list: list = None) -> None:
        """Updates self._data to remove duplicates in data.

        Parameters
        ----------
        priority_list : list, optional
            Providers priority order, first has priority over others and so on.
            , by default None
        """
        df = self._data
        df = self._remove_duplicates_among_providers(df)
        df = self._remove_duplicates_between_providers(df, priority_list=priority_list)
        self._data = df

    def _remove_duplicates_among_providers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Removes duplicates among a common providers.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to remove duplicated data from.

        Returns
        -------
        pd.DataFrame
            DataFrame without duplicates.
        """
        grouping_vars = [
            "PROVIDER",
            "EXPOCODE",
            "DATE",
            "YEAR",
            "MONTH",
            "DAY",
            "HOUR",
            "LATITUDE",
            "LONGITUDE",
            "DEPH",
        ]
        subset_group = []
        for name in grouping_vars:
            if self._variables.has_name(name):
                subset_group.append(self._variables.labels[name])
        # Select dupliacted rows
        is_duplicated = df.duplicated(subset=subset_group, keep=False)
        duplicates = df.filter(items=df[is_duplicated].index, axis=0)
        # Drop dupliacted rows from dataframe
        dropped = df.drop(df[is_duplicated].index, axis=0)
        # Group duplicates and average them
        grouped = duplicates.groupby(subset_group).mean().reset_index()
        # Concatenate dataframe with droppped duplicates and duplicates averaged
        concat = pd.concat([dropped, grouped], ignore_index=True, axis=0)
        return concat

    def _remove_duplicates_between_providers(
        self,
        df: pd.DataFrame,
        priority_list: list,
    ) -> pd.DataFrame:
        """Removes duplicates among a common providers.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to remove duplicated data from.
        priority_list : list, optional
            Providers priority order, first has priority over others and so on.
            , by default None

        Returns
        -------
        pd.DataFrame
            DataFrame without duplicates.
        """
        provider_label = self._variables.labels["PROVIDER"]
        providers = df[provider_label].unique()
        if len(providers) == 1:
            return df
        grouping_vars = [
            "EXPOCODE",
            "YEAR",
            "MONTH",
            "DAY",
            "HOUR",
            "LATITUDE",
            "LONGITUDE",
            "DEPH",
        ]
        subset = []
        for name in grouping_vars:
            if self._variables.has_name(name):
                subset.append(self._variables.labels[name])
        # every row concerned by duplication of the variables in subset
        is_duplicated = df.duplicated(
            subset=subset,
            keep=False,
        )
        if not is_duplicated.any():
            return df
        # Sorting key function
        if priority_list is not None:
            sort_func = np.vectorize(lambda x: priority_list.index(x))
        else:
            sort_func = np.vectorize(lambda x: x)
        duplicates = df.filter(df.loc[is_duplicated, :].index, axis=0)
        duplicates.sort_values(provider_label, key=sort_func, inplace=True)
        to_dump = duplicates.duplicated(subset=subset, keep="first")
        dump_index = duplicates[to_dump].index
        return df.drop(dump_index, axis=0)

    def save(self, filepath: str) -> None:
        """Saving method to save the Dataframe.

        Parameters
        ----------
        filepath : str
            Where to save the output.
        """
        # Verbose
        if self._verbose > 1:
            print(f"\tSaving data in {filepath.split('/')[-1]}")
        # Parameters
        name_format = self.variables.name_save_format
        value_format = self.variables.value_save_format
        df = self.data.loc[:, self.variables.save_labels]
        # Get unit rows' values
        units = [self.variables.unit_mapping[col] for col in df.columns]
        dirout = os.path.dirname(filepath)
        # make directory if needed
        if not os.path.isdir(dirout):
            os.mkdir(dirout)
        # Save file
        with open(filepath, "w") as file:
            # Write variables row
            file.write(name_format % tuple(df.columns) + "\n")
            # Write unit row
            file.write(name_format % tuple(units) + "\n")
            # Write
            lines = df.apply(lambda x: value_format % tuple(x) + "\n", axis=1)
            if len(lines) != 0:
                file.writelines(lines)

    def slice_on_dates(
        self,
        drng: pd.Series,
    ) -> "Slice":
        """Slices the Dataframe using the date column. \
        Returns indexes to use for slicing.

        Parameters
        ----------
        drng : pd.Series
            Two values Series, "start_date" and "end_date".

        Returns
        -------
        list
            Indexes to use for slicing.
        """
        # Params
        start_date = drng["start_date"]
        end_date = drng["end_date"]
        dates_col = self._data[self._variables.get(self._variables.date_var_name).label]
        # Verbose
        if self._verbose > 1:
            print(
                "\tSlicing data for date range"
                f" {start_date.date()} {end_date.date()}"
            )
        # slice
        after_start = dates_col >= start_date
        before_end = dates_col <= end_date
        slice_index = dates_col.loc[after_start & before_end].index.values.tolist()
        return Slice(
            storer=self,
            slice_index=slice_index,
        )

    @classmethod
    def from_files(
        cls,
        filepath: str | list,
        providers: str | list = "PROVIDER",
        category: str = "in_situ",
        unit_row_index: int = 1,
        delim_whitespace: bool = True,
        verbose: int = 1,
    ) -> "Storer":
        """Builds Storer reading data from csv or txt files.

        Parameters
        ----------
        filepath : str
            Path to the file to read.
        providers : str | list, optional
            Provider column in the dataframe (if str) or value to attribute
            to self._providers (if list)., by default "PROVIDER"
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
        >>> storer = DStorer.from_files(filepath, providers="providers_column_name")

        Loading from multiple files:
        >>> filepaths = [
        ...     "path/to/file1",
        ...     "path/to/file2",
        ... ]
        >>> storer = MeshPlotter.from_files(
        ...     filepaths,
        ...     providers="providers_column_name",
        ... )
        """
        if isinstance(filepath, list):
            storers = []
            for path in filepath:
                reader = Reader(
                    filepath=path,
                    providers=providers,
                    category=category,
                    unit_row_index=unit_row_index,
                    delim_whitespace=delim_whitespace,
                    verbose=verbose,
                )

                storers.append(reader.get_storer())
            return sum(storers)
        elif isinstance(filepath, str):
            reader = Reader(
                filepath=filepath,
                providers=providers,
                category=category,
                unit_row_index=unit_row_index,
                delim_whitespace=delim_whitespace,
                verbose=verbose,
            )
            return reader.get_storer()
        else:
            raise TypeError(f"Can't read filepaths from {filepath}")


class Slice(Storer):
    """Slice storing object, instance of Storer to inherit of the saving method.

    Parameters
    ----------
    storer : Storer
        Storer to slice.
    slice_index : list
        Indexes to keep from the Storer dataframe.
    """

    def __init__(
        self,
        storer: Storer,
        slice_index: list,
    ) -> None:
        self._slice_index = slice_index
        self._storer = storer
        super().__init__(
            data=storer.data,
            category=storer.category,
            providers=storer.providers,
            variables=storer.variables,
            verbose=storer.verbose,
        )

    @property
    def providers(self) -> list:
        """Getter for self._storer._providers.

        Returns
        -------
        list
            Providers of the dataframe which the slice comes from.
        """
        return self._storer.providers

    @property
    def variables(self) -> list:
        """Getter for self._storer._variables.

        Returns
        -------
        list
            Variables of the dataframe which the slice comes from.
        """
        return self._storer.variables

    @property
    def data(self) -> pd.DataFrame:
        """Getter for self._storer._data.

        Returns
        -------
        pd.DataFrame
            The dataframe which the slice comes from.
        """
        return self._storer.data.loc[self._slice_index, :]

    def __repr__(self) -> str:
        return str(self._slice_index)

    def __add__(self, __o: object) -> "Slice":
        if self._storer != __o._storer:
            raise ValueError(
                "Addition can only be performed with slice from same CSVStorer"
            )
        new_index = list(set(self._slice_index).union(set(__o._slice_index)))
        return Slice(self._storer, new_index)

    @classmethod
    def slice_on_date(
        drng: pd.Series,
        storer: Storer,
    ) -> "Slice":
        """Class method to use to slice on dates.

        Parameters
        ----------
        drng : pd.Series
            Date range for the slice
        storer : Storer
            Storer to slice.

        Returns
        -------
        Slice
            Slice object corresponding to the slice.

        Examples
        --------
        >>> storer = Storer(data, providers, variables, verbose)
        >>> slice = storer.slice_on_dates(drng)

        Is equivalent to :
        >>> storer = Storer(data, providers, variables, verbose)
        >>> slice = Slicer.slice_on_dates(drng)
        """
        return storer.slice_on_dates(drng)


class Reader:
    """Reading routine to parse csv files.

    Parameters
    ----------
    filepath : str
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
        filepath: str,
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
        category: str = "in_situ",
        unit_row_index: int = 1,
        delim_whitespace: bool = True,
        verbose: int = 1,
    ):
        self._verbose = verbose

        raw_df, unit_row = self._read(filepath, unit_row_index, delim_whitespace)
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
        self._providers = raw_df[providers_column_label].unique().tolist()
        self._data = self._add_date_columns(
            raw_df,
            year_column_label,
            month_column_label,
            day_column_label,
            date_column_label,
        )
        self._variables = self._get_variables(raw_df, unit_row, mandatory_vars)

    def _read(
        self, filepath: str, unit_row_index: int, delim_whitespace: bool
    ) -> tuple[pd.DataFrame, pd.Series]:
        """Method to read the filepath and extract the unit row.

        Parameters
        ----------
        filepath : str
            Path to the file to read.
        unit_row_index : int
            Index of the row with the units, None if there's no unit row.
        delim_whitespace : bool
            Whether to use whitespace as delimiters.

        Returns
        -------
        tuple[pd.DataFrame, pd.Series]
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
                skiprows=lambda x: x not in skiprows + [0],
            )
        if self._verbose > 0:
            print(f"Reading data from {filepath}")
        raw_df = pd.read_csv(
            filepath, delim_whitespace=delim_whitespace, skiprows=skiprows
        )
        return raw_df, unit_row

    def _get_variables(
        self,
        raw_df: pd.DataFrame,
        unit_row: pd.Series,
        mandatory_vars: dict,
    ) -> "VariablesStorer":
        """Parses variables from the csv data.

        Parameters
        ----------
        raw_df : pd.DataFrame
            Dataframe to parse.
        unit_row : pd.Series
            Unit row to use as reference for variables' units.
        mandatory_vars: dict
            Mapping between column name and parameter for mandatory variables.

        Returns
        -------
        VariablesStorer
            Collection of variables.
        """
        variables = {}
        for column in raw_df.columns:
            if unit_row is None or column not in unit_row.index:
                unit = "[]"
            else:
                unit = unit_row[column].values[0]

            var = ParsedVar(
                name=column.upper(),
                unit=unit,
                var_type=raw_df.dtypes[column].name,
            )
            if column in mandatory_vars.keys():
                variables[mandatory_vars[column]] = var
            else:
                variables[column.lower()] = var
        for param in mandatory_vars.values():
            if param not in variables.keys():
                variables[param] = None
        return VariablesStorer(**variables)

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
        """Adds missing columns to the dataframe.

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
        if date_col in raw_df.columns:
            return raw_df
        missing_col = self._make_date_column(raw_df, year_col, month_col, day_col)
        raw_df.insert(0, date_col, missing_col)
        return raw_df

    def get_storer(self) -> "Storer":
        """Returns the Storer storing the data loaded.

        Returns
        -------
        Storer
            Contains the data from the csv.
        """
        return Storer(
            data=self._data,
            category=self._category,
            providers=self._providers,
            variables=self._variables,
            verbose=self._verbose,
        )
