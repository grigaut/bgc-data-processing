"""Base Loaders."""


from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from bgc_data_processing.data_structures.variables.ensembles import (
        LoadingVariablesSet,
    )


class BaseLoader(ABC):
    """Base class to load data.

    Parameters
    ----------
    provider_name : str
        Data provider name.
    category: str
        Category provider belongs to.
    exclude: list[str]
        Filenames to exclude from loading.
    variables : SourceVariableSet
        Storer object containing all variables to consider for this data,
        both the one in the data file but and the one not represented in the file.
    """

    _verbose: int = 1

    def __init__(
        self,
        provider_name: str,
        category: str,
        exclude: list[str],
        variables: "LoadingVariablesSet",
    ) -> None:
        self._provider = provider_name
        self._category = category
        self._exclude = exclude
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
    def category(self) -> str:
        """Returns the category of the provider.

        Returns
        -------
        str
            Category provider belongs to.
        """
        return self._category

    @property
    def verbose(self) -> int:
        """_verbose attribute getter.

        Returns
        -------
        int
            Verbose value.
        """
        return self._verbose

    @property
    def variables(self) -> "LoadingVariablesSet":
        """_variables attribute getter.

        Returns
        -------
        LoadingVariablesSet
            Loading variables storer.
        """
        return self._variables

    @property
    def excluded_filenames(self) -> list[str]:
        """Filenames to exclude from loading."""
        return self._exclude

    def is_file_valid(self, filepath: Path) -> bool:
        """Indicate whether a file is valid to be kept or not.

        Parameters
        ----------
        filepath : Path
            Name of the file

        Returns
        -------
        bool
            True if the name is not to be excluded.
        """
        keep_path = str(filepath) not in self.excluded_filenames
        keep_name = filepath.name not in self.excluded_filenames

        return keep_name and keep_path

    @abstractmethod
    def load(self, filepath: str) -> pd.DataFrame:
        """Load data.

        Returns
        -------
        Any
            Data object.
        """
        ...

    def remove_nan_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove rows.

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
        if vars_to_remove_when_any_nan:
            any_nans = df[vars_to_remove_when_any_nan].isna().any(axis=1)
        else:
            any_nans = pd.Series(False, index=df.index)
        if vars_to_remove_when_all_nan:
            all_nans = df[vars_to_remove_when_all_nan].isna().all(axis=1)
        else:
            all_nans = pd.Series(False, index=df.index)
        # Get indexes to drop
        indexes_to_drop = df[any_nans | all_nans].index
        return df.drop(index=indexes_to_drop)

    def _correct(self, to_correct: pd.DataFrame) -> pd.DataFrame:
        """Apply corrections functions defined in Var object to dataframe.

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
        for label, correction_func in self._variables.corrections.items():
            correct = to_correct.pop(label).apply(correction_func)
            to_correct.insert(len(to_correct.columns), label, correct)
        return to_correct
