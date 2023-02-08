import datetime as dt
import os
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

import pandas as pd

if TYPE_CHECKING:
    from bgc_data_processing.variables import VariablesStorer


class BaseLoader(ABC):
    """Base class to load data.

    Parameters
    ----------
    provider_name : str
        Data provider name.
    dirin : str
        Directory to browse for files to load.
    files_pattern : str
        Pattern to use to parse files.
        It must contain a '{years}' in order to be completed using the .format method.
    variables : VariablesStorer
        Storer object containing all variables to consider for this data,
        both the one in the data file but and the one not represented in the file.
    """

    _storer: "Storer" = None
    _verbose: int = 1
    _lon_min: int | float = None
    _lon_max: int | float = None
    _lat_min: int | float = None
    _lat_max: int | float = None
    _date_min: dt.datetime | dt.date = None
    _date_max: dt.datetime | dt.date = None

    def __init__(
        self,
        provider_name: str,
        dirin: str,
        files_pattern: str,
        variables: "VariablesStorer",
    ) -> None:

        self._provider = provider_name
        self._dirin = dirin
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
    def verbose(self) -> int:
        """_verbose attribute getter

        Returns
        -------
        int
            Verbose value.
        """
        return self._verbose

    @property
    def data(self) -> "Storer":
        """_storer attribute getter.

        Returns
        -------
        Storer
            Data storer.
        """
        return self._storer

    @property
    def variables(self) -> "VariablesStorer":
        """_variables attribute getter.

        Returns
        -------
        VariablesStorer
            Variables storer.
        """
        return self._variables

    def __call__(self) -> "Storer":
        filepaths = self._select_filepaths()
        data_list = []
        for filepath in filepaths:
            data_list.append(self.load(filepath=filepath))
        data = pd.concat(data_list, ignore_index=True, axis=0)
        return Storer(
            data=data,
            providers=[self.provider],
            variables=self.variables,
            verbose=self.verbose,
        )

    @abstractmethod
    def _select_filepaths(self) -> list[str]:
        ...

    @abstractmethod
    def load(self, filepath: str) -> pd.DataFrame:
        """Main method to use to load data.

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

    def set_longitude_boundaries(
        self,
        longitude_min: int | float,
        longitude_max: int | float,
    ) -> None:
        """Sets boundaries for longitude variable.

        Parameters
        ----------
        longitude_min : int | float
            Minimal value for longitude (included).
        longitude_max : int | float
            Maximal value for longitude (included).
        """
        self._lon_min = longitude_min
        self._lon_max = longitude_max

    def set_latitude_boundaries(
        self,
        latitude_min: int | float,
        latitude_max: int | float,
    ) -> None:
        """Sets boundaries for latitude variable.

        Parameters
        ----------
        latitude_min : int | float
            Minimal value for latitude (included).
        latitude_max : int | float
            Maximal value for latitude (included).
        """
        self._lat_min = latitude_min
        self._lat_max = latitude_max

    def set_date_boundaries(
        self,
        date_min: dt.datetime | dt.date,
        date_max: dt.datetime | dt.date,
    ) -> None:
        """Sets boundaries for date variable.

        Parameters
        ----------
        date_min : int | float
            Minimal value for date (included).
        date_max : int | float
            Maximal value for date (included).
        """
        self._date_min = pd.to_datetime(date_min)
        self._date_max = pd.to_datetime(date_max + dt.timedelta(days=1))

    def _apply_boundaries(
        self,
        df: pd.DataFrame,
        var_name: str,
        min: Any,
        max: Any,
    ) -> pd.DataFrame:
        """Applies boundaries restrictions on a dataframe.

        Parameters
        ----------
        df : pd.DataFrame
            Dataframe to reduce using boundaries values.
        var_name : str
            Variable name to consider.
        min : Any
            Minimal value to use.
        max : Any
            Maximal value to use.

        Returns
        -------
        pd.DataFrame
            Reduced DataFrame.

        Examples
        --------
        >>> df = self._apply_boundaries(not_bounded_df, "DATE", self._date_min, self._date_max)

        """
        if var_name not in self._variables.keys():
            return df
        if min is None and max is None:
            return df
        to_compare = df[self._variables[var_name].key]
        if min is None:
            after_date_min = to_compare <= max
            return df.loc[after_date_min, :].copy()
        elif max is None:
            before_date_max = to_compare >= min
            return df.loc[before_date_max, :].copy()
        else:
            after_date_min = to_compare >= min
            before_date_max = to_compare <= max
            return df.loc[after_date_min & before_date_max, :].copy()

    def remove_nan_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """Removes rows

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
        any_nans = df[vars_to_remove_when_any_nan].isna().any(axis=1)
        all_nans = df[vars_to_remove_when_all_nan].isna().all(axis=1)
        # Get indexes to drop
        indexes_to_drop = df[any_nans | all_nans].index
        return df.drop(index=indexes_to_drop)

    def _correct(self, to_correct: pd.DataFrame) -> pd.DataFrame:
        """Applies corrections functions defined in Var object to dataframe.

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
        for key, correction_func in self._variables.corrections.items():
            to_correct[key] = to_correct[key].apply(correction_func)
        return to_correct


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
        providers: list,
        variables: "VariablesStorer",
        verbose: int = 0,
    ) -> None:

        self._data = data
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
        if isinstance(object, Storer):
            # Assert variable from both dataframes are the same
            if self.variables == object.variables:
                concat_data = pd.concat([self._data, object._data], ignore_index=True)
                concat_providers = list(set(self.providers + object.providers))
                # Return Storer with similar variables
                concat_storer = Storer(
                    data=concat_data,
                    providers=concat_providers,
                    variables=self.variables,
                )
                return concat_storer
            else:
                raise ValueError("Variables are not compatible")
        else:
            raise TypeError(f"Can't add CSVStorer object to {type(object)}")

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
            data=self._storer._data,
            providers=self._storer._providers,
            variables=self._storer._variables,
            verbose=self._storer._verbose,
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
