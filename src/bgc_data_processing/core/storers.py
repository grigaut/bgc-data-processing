"""Data storing objects."""


import datetime as dt
from copy import deepcopy
from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd

from bgc_data_processing.exceptions import (
    DifferentSliceOriginError,
    IncompatibleCategoriesError,
    IncompatibleVariableSetsError,
)
from bgc_data_processing.verbose import with_verbose

if TYPE_CHECKING:
    from bgc_data_processing.core.filtering import Constraints
    from bgc_data_processing.core.variables.sets import StoringVariablesSet
    from bgc_data_processing.core.variables.vars import (
        NotExistingVar,
    )


class Storer:
    """Storing data class, to keep track of metadata.

    Parameters
    ----------
    data : pd.DataFrame
        Dataframe to store.
    category: str
        Data category.
    providers : list
        Names of the data providers.
    variables : StoringVariablesSet
        Variables storer of object to keep track of the variables in the Dataframe.
    """

    def __init__(
        self,
        data: pd.DataFrame,
        category: str,
        providers: list,
        variables: "StoringVariablesSet",
    ) -> None:
        self._data = data
        self._category = category
        self._providers = providers
        self._variables = deepcopy(variables)

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
    def variables(self) -> "StoringVariablesSet":
        """Getter for self._variables.

        Returns
        -------
        StoringVariablesSet
            Variables storer.
        """
        return self._variables

    def __repr__(self) -> str:
        """Representation of self.

        Returns
        -------
        str
            Representation of self.data.
        """
        return repr(self.data)

    def __eq__(self, __o: object) -> bool:
        """Test equality with other object.

        Parameters
        ----------
        __o : object
            Object to test equality with.

        Returns
        -------
        bool
            True if is same object only.
        """
        return self is __o

    def __radd__(self, other: Any) -> "Storer":
        """Perform right addition.

        Parameters
        ----------
        other : Any
            Object to add.

        Returns
        -------
        Storer
            Concatenation of both storer's dataframes.
        """
        if other == 0:
            return self
        return self.__add__(other)

    def __add__(self, other: object) -> "Storer":
        """Perform left addition.

        Parameters
        ----------
        other : Any
            Object to add.

        Returns
        -------
        Storer
            Concatenation of both storer's dataframes.

        Raises
        ------
        TypeError
            If other is not a storer.
        IncompatibleVariableSetsError
            If both storers have a different variable set.
        IncompatibleCategoriesError
            If both storers have different categories.
        """
        if not isinstance(other, Storer):
            error_msg = f"Can't add CSVStorer object to {type(other)}"
            raise TypeError(error_msg)
        # Assert variables are the same
        if self.variables != other.variables:
            error_msg = "Variables or categories are not compatible"
            raise IncompatibleVariableSetsError(error_msg)
        # Assert categories are the same
        if self.category != other.category:
            error_msg = "Categories are not compatible"
            raise IncompatibleCategoriesError(error_msg)

        concat_data = pd.concat([self._data, other.data], ignore_index=True)
        concat_providers = list(set(self.providers + other.providers))
        # Return Storer with similar variables
        return Storer(
            data=concat_data,
            category=self.category,
            providers=concat_providers,
            variables=self.variables,
        )

    def remove_duplicates(self, priority_list: list | None = None) -> None:
        """Update self._data to remove duplicates in data.

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
        """Remove duplicates among a common providers.

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
                subset_group.append(self._variables.get(name).label)
        # Select dupliacted rows
        is_duplicated = df.duplicated(subset=subset_group, keep=False)
        duplicates = df.filter(items=df[is_duplicated].index, axis=0)
        # Drop dupliacted rows from dataframe
        dropped = df.drop(df[is_duplicated].index, axis=0)
        # Group duplicates and average them
        grouped = (
            duplicates.groupby(subset_group, dropna=False)
            .mean(numeric_only=True)
            .reset_index()
        )
        # Concatenate dataframe with droppped duplicates and duplicates averaged
        return pd.concat([dropped, grouped], ignore_index=True, axis=0)

    def _remove_duplicates_between_providers(
        self,
        df: pd.DataFrame,
        priority_list: list | None,
    ) -> pd.DataFrame:
        """Remove duplicates among a common providers.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to remove duplicated data from.
        priority_list : list | None
            Providers priority order, first has priority over others and so on.

        Returns
        -------
        pd.DataFrame
            DataFrame without duplicates.
        """
        if self._variables.has_provider:
            provider_var_name = self._variables.provider_var_name
            provider_label = self._variables.get(provider_var_name).label
            providers = df[provider_label].unique()
        else:
            return df
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
                subset.append(self._variables.get(name).label)
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

    @staticmethod
    @with_verbose(
        trigger_threshold=1,
        message="Slicing data for date range: {_start_date}-{_end_date}.",
    )
    def slice_verbose(_start_date: dt.date, _end_date: dt.date) -> None:
        """Invoke Verbose for slicing.

        Parameters
        ----------
        start_date : dt.date
            Start date.
        end_date : dt.date
            End date.
        """
        return

    def slice_on_dates(
        self,
        drng: pd.Series,
    ) -> "Slice":
        """Slice the Dataframe using the date column.

        Only returns indexes to use for slicing.

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
        start_date: dt.datetime = drng["start_date"]
        end_date: dt.datetime = drng["end_date"]
        self.slice_verbose(_start_date=start_date.date(), _end_date=end_date.date())
        dates_col = self._data[self._variables.get(self._variables.date_var_name).label]
        # slice
        after_start = dates_col >= start_date
        before_end = dates_col <= end_date
        slice_index = dates_col.loc[after_start & before_end].index.values.tolist()
        return Slice(
            storer=self,
            slice_index=slice_index,
        )

    def add_feature(
        self,
        variable: "NotExistingVar",
        data: pd.Series,
    ) -> None:
        """Add a new feature to the storer.

        Parameters
        ----------
        variable : NotExistingVar
            Variable corresponding to the feature.
        data : pd.Series
            Feature data.
        """
        self.variables.add_var(variable)
        self._data[variable.name] = data

    def pop(self, variable_name: str) -> pd.Series:
        """Remove and return the data for a given variable.

        Parameters
        ----------
        variable_name : str
            Name of the variable to remove.

        Returns
        -------
        pd.Series
            Data of the corresponding variable.
        """
        var = self.variables.pop(variable_name)
        return self._data.pop(var.name)

    @classmethod
    def from_constraints(
        cls,
        storer: "Storer",
        constraints: "Constraints",
    ) -> "Storer":
        """Create a new storer object from an existing storer and constraints.

        Parameters
        ----------
        storer : Storer
            Storer to modify with constraints.
        constraints : Constraints
            Constraints to use to modify the storer.

        Returns
        -------
        Storer
            New storer respecting the constraints.
        """
        data = constraints.apply_constraints_to_dataframe(dataframe=storer.data)
        return Storer(
            data=data,
            category=storer.category,
            providers=storer.providers,
            variables=storer.variables,
        )

    def slice_using_index(self, index: pd.Index) -> "Storer":
        """Slice Storer using.

        Parameters
        ----------
        index : pd.Index
            Index values to keep.

        Returns
        -------
        Storer
            Corresponding storer.
        """
        return Storer(
            data=self._data.loc[index, :],
            category=self._category,
            providers=self._providers,
            variables=self._variables,
        )


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
        """Slice storing object, instance of Storer to inherit of the saving method.

        Parameters
        ----------
        storer : Storer
            Storer to slice.
        slice_index : list
            Indexes to keep from the Storer dataframe.
        """
        self.slice_index = slice_index
        self.storer = storer
        super().__init__(
            data=storer.data,
            category=storer.category,
            providers=storer.providers,
            variables=storer.variables,
        )

    @property
    def providers(self) -> list:
        """Getter for self.storer._providers.

        Returns
        -------
        list
            Providers of the dataframe which the slice comes from.
        """
        return self.storer.providers

    @property
    def variables(self) -> list:
        """Getter for self.storer._variables.

        Returns
        -------
        list
            Variables of the dataframe which the slice comes from.
        """
        return self.storer.variables

    @property
    def data(self) -> pd.DataFrame:
        """Getter for self.storer._data.

        Returns
        -------
        pd.DataFrame
            The dataframe which the slice comes from.
        """
        return self.storer.data.loc[self.slice_index, :]

    def __repr__(self) -> str:
        """Represent self as a string.

        Returns
        -------
        str
            str(slice.index)
        """
        return str(self.slice_index)

    def __add__(self, __o: object) -> "Slice":
        """Perform left addition.

        Parameters
        ----------
        __o : object
            Object to add.

        Returns
        -------
        Slice
            Concatenation of both slices.

        Raises
        ------
        DifferentSliceOriginError
            If the slices don't originate from same storer.
        """
        if self.storer != __o.storer:
            error_msg = "Addition can only be performed with slice from same CSVStorer"
            raise DifferentSliceOriginError(error_msg)
        new_index = list(set(self.slice_index).union(set(__o.slice_index)))
        return Slice(self.storer, new_index)
