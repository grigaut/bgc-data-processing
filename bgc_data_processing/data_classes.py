import os
from typing import TYPE_CHECKING, Any

import pandas as pd

if TYPE_CHECKING:
    from bgc_data_processing.variables import VariablesStorer


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
