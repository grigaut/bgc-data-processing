import os
from typing import Any

import pandas as pd

from bgc_data_processing.variables import Var, VariablesStorer


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
        """Getter for self._data

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
        """Getter for self._providers

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
        """_verbose attribute getter

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
        )
        return concat_storer

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
        df = self.data.loc[:, self.variables.save_keys]
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
        """Slices the Dataframe using the date column. Returns indexes to use for slicing.

        Parameters
        ----------
        drng : pd.Series
            Two values Series, "start_date" for starting dates and "end_date" for ending date.

        Returns
        -------
        list
            Indexes to use for slicing.
        """
        # Params
        start_date = drng["start_date"]
        end_date = drng["end_date"]
        dates_col = self._data[self._variables["DATE"].key]
        # Verbose
        if self._verbose > 1:
            print("\tSlicing data for date range {} {}".format(start_date, end_date))
        # slice
        after_start = dates_col.dt.date >= start_date
        before_end = dates_col.dt.date <= end_date
        slice_index = dates_col.loc[after_start & before_end].index.values.tolist()
        return Slice(
            storer=self,
            slice_index=slice_index,
        )

    def slice_on_providers(
        self,
        providers: list[str],
    ) -> "Slice":
        """Slices the Dataframe using the provider column. Returns indexes to use for slicing.

        Parameters
        ----------
        providers : list[str]
            Providers to conserve after slicing.

        Returns
        -------
        list
            Indexes to use for slicing.
        """

        # Verbose
        if self._verbose > 1:
            print("\tSlicing data for providers {}".format(", ".join(providers)))
        # Params
        providers_col = self._data[self._variables["PROVIDER"].key]
        # Slice
        is_in_list = providers_col.isin(providers)
        slice_index = providers_col.loc[is_in_list].index.values.tolist()
        return Slice(
            data=self,
            slice_index=slice_index,
        )

    @classmethod
    def from_file(
        cls,
        filepath: str | list,
        providers: str | list = "PROVIDER",
        category: str = "in_situ",
        unit_row_index: int = 1,
        delim_whitespace: bool = True,
        verbose: int = 1,
    ) -> "Storer":
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
        if isinstance(filepath, str):
            reader = Reader(
                filepath=filepath,
                providers=providers,
                category=category,
                unit_row_index=unit_row_index,
                delim_whitespace=delim_whitespace,
                verbose=verbose,
            )
            return reader.get_storer()


class Slice(Storer):
    """Slice storing object, instance of Storer to inherit of the saving method."""

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
        """Getter for self._storer._providers

        Returns
        -------
        list
            Providers of the dataframe which the slice comes from.
        """
        return self._storer.providers

    @property
    def variables(self) -> list:
        """Getter for self._storer._variables

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
    providers : str | list, optional
        Provider column in the dataframe (if str) or value to attribute to self._providers (if list).
        , by default "PROVIDER"
    category : str, optional
        Category of the loaded file., by default "in_situ"
    unit_row_index : int, optional
        Index of the row with the units, None if there's no unit row., by default 1
    delim_whitespace : bool, optional
        Whether to use whitespace as delimiters., by default True
    verbose : int, optional
        Controls the verbose, by default 1
    """

    def __init__(
        self,
        filepath: str,
        providers: str | list = "PROVIDER",
        category: str = "in_situ",
        unit_row_index: int = 1,
        delim_whitespace: bool = True,
        verbose: int = 1,
    ):
        self._verbose = verbose
        raw_df, unit_row = self.read(filepath, unit_row_index, delim_whitespace)
        self._providers = self.get_providers(raw_df, providers)
        self._variables = self.get_variables(raw_df, unit_row)
        self._category = category
        self._data = self.add_missing_columns(raw_df)

    def read(
        self, filepath: str, unit_row_index: int, delim_whitespace: bool
    ) -> tuple[pd.DataFrame, pd.Series]:
        """Method to read the filepath and extract the unit row

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

    def get_providers(self, raw_df: pd.DataFrame, providers: str | list) -> list:
        """Gets providers for the "provider" argument and the dataframe.

        Parameters
        ----------
        raw_df : pd.DataFrame
            Loaded dataframe.
        providers : str | list
            Provider instanciating argument.

        Returns
        -------
        list
            The correct provider value to use as attribute.

        Raises
        ------
        InterruptedError
            If the provider argument is not a string or a list.
        """
        if isinstance(providers, str):
            return list(raw_df[providers].unique())
        elif isinstance(providers, list):
            return providers
        else:
            raise InterruptedError("Could no parse providers from argument")

    def get_variables(
        self,
        raw_df: pd.DataFrame,
        unit_row: pd.Series,
    ) -> "VariablesStorer":
        """Parses variables from the csv data.

        Parameters
        ----------
        raw_df : pd.DataFrame
            Dataframe to parse.
        unit_row : pd.Series
            Unit row to use as reference for variables' units.

        Returns
        -------
        VariablesStorer
            Collection of variables.
        """
        variables = []
        for i, column in enumerate(raw_df.columns):
            if unit_row is None:
                unit = "[]"
            else:
                unit = unit_row[column].values[0]
            var = Var(
                name=column.upper(),
                unit=unit,
                var_type=raw_df.dtypes[column].name,
                load_nb=i,
                save_nb=i,
            )
            variables.append(var)
        return VariablesStorer(*variables)

    def make_date_column(self, raw_df: pd.DataFrame) -> tuple[pd.Series, str]:
        """Make date column (datetime) from year, month, day columns if existing.

        Parameters
        ----------
        raw_df : pd.DataFrame
            Dataframe

        Returns
        -------
        tuple[pd.Series, str]
            Column to inser, column name to use.
        """
        year_in_vars = self._variables.has_name("YEAR")
        month_in_vars = self._variables.has_name("MONTH")
        day_in_vars = self._variables.has_name("DAY")
        if not (year_in_vars and month_in_vars and day_in_vars):
            return None, None
        year_key = self._variables["YEAR"].key
        month_key = self._variables["MONTH"].key
        day_key = self._variables["DAY"].key
        year_in = year_key in raw_df.columns
        month_in = month_key in raw_df.columns
        day_in = day_key in raw_df.columns
        if year_in and month_in and day_in:
            var = Var("DATE", "[]", "datetime64[ns]", None, None)
            self._variables.add_var(var)
            return pd.to_datetime(raw_df[[year_key, month_key, day_key]]), var.key
        else:
            return None, None

    def add_missing_columns(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """Adds missing columns to the dataframe

        Parameters
        ----------
        raw_df : pd.DataFrame
            Dataframe to modify

        Returns
        -------
        pd.DataFrame
            Dataframe with new columns
        """
        if not self._variables.has_name("DATE"):
            missing_col, name = self.make_date_column(raw_df)
            if (missing_col is not None) and (name is not None):
                raw_df.insert(0, name, missing_col)
        return raw_df

    def get_storer(self) -> "Storer":
        """Returns the Storer storing the data loaded

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
