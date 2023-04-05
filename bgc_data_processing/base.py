"""Base objects."""


from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import pandas as pd
import matplotlib.pyplot as plt
from bgc_data_processing.data_classes import Storer

if TYPE_CHECKING:
    from bgc_data_processing.variables import VariablesStorer
    from bgc_data_processing.data_classes import Constraints
    from matplotlib.figure import Figure


class BaseLoader(ABC):
    """Base class to load data.

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
    """

    _verbose: int = 1

    def __init__(
        self,
        provider_name: str,
        dirin: str,
        category: str,
        files_pattern: str,
        variables: "VariablesStorer",
    ) -> None:

        self._provider = provider_name
        self._dirin = dirin
        self._category = category
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
    def variables(self) -> "VariablesStorer":
        """_variables attribute getter.

        Returns
        -------
        VariablesStorer
            Variables storer.
        """
        return self._variables

    @abstractmethod
    def __call__(self, constraints: "Constraints", exclude: list = []) -> "Storer":
        """Loads all files for the loader.

        Parameters
        ----------
        constraints: Constraints
            Constraint slicer.
        exclude : list, optional
            Files not to load., by default []

        Returns
        -------
        Storer
            Storer for the loaded data.
        """
        ...

    @abstractmethod
    def _select_filepaths(self, exclude: list) -> list[str]:
        """Select filepaths matching the file pattern.

        Parameters
        ----------
        exclude : list
            Files to exclude even if their name matches the pattern.

        Returns
        -------
        list[str]
            List of the filepaths to use for loading.
        """
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

    def set_saving_order(self, var_names: str) -> None:
        """Set the saving order for the variables.

        Parameters
        ----------
        var_names : list[str]
            List of variable names => saving variables sorted.
        """
        self._variables.set_saving_order(var_names=var_names)

    def remove_nan_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """Removes rows.

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
        for label, correction_func in self._variables.corrections.items():
            correct = to_correct.pop(label).apply(correction_func)
            to_correct.insert(len(to_correct.columns), label, correct)
            # to_correct[label] = to_correct[label]  #
        return to_correct


class BasePlot(ABC):
    """Base class to plot data from a storer.

    Parameters
    ----------
    storer : Storer
        Storer to plot data of.
    constraints: Constraints
            Constraint slicer.
    """

    def __init__(self, storer: "Storer", constraints: "Constraints") -> None:
        self._storer = storer
        self._variables = storer.variables
        self._constraints = constraints
        self._verbose = storer.verbose

    @abstractmethod
    def _build_to_new_figure(self, *args, **kwargs) -> "Figure":
        """Create the figure.

        Parameters
        ----------
        *args: list
            Parameters to build the figure.
        *kwargs: dict
            Parameters to build the figure.

        Returns
        -------
        Figure
            Figure to show or save.
        """
        ...

    @abstractmethod
    def show(self, title: str = None, suptitle: str = None, *args, **kwargs) -> None:
        """Plot method.

        Parameters
        ----------
        title : str, optional
            Specify a title to change from default., by default None
        suptitle : str, optional
            Specify a suptitle to change from default., by default None
        *args: list
            Additional parameters to pass to self._build.
        *kwargs: dict
            Additional parameters to pass to self._build.
        """
        self._build_to_new_figure(
            title=title,
            suptitle=suptitle,
            *args,
            **kwargs,
        )
        plt.show()
        plt.close()

    @abstractmethod
    def save(
        self,
        save_path: str,
        title: str = None,
        suptitle: str = None,
        *args,
        **kwargs,
    ) -> None:
        """Figure saving method.

        Parameters
        ----------
        save_path : str
            Path to save the output image.
        title : str, optional
            Specify a title to change from default., by default None
        suptitle : str, optional
            Specify a suptitle to change from default., by default None
        *args: list
            Additional parameters to pass to self._build.
        *kwargs: dict
            Additional parameters to pass to self._build.
        """
        self._build_to_new_figure(
            title=title,
            suptitle=suptitle,
            *args,
            **kwargs,
        )
        plt.savefig(save_path)
