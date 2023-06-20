"""Base Loaders."""


from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

from bgc_data_processing.data_structures.io.savers import StorerSaver
from bgc_data_processing.data_structures.storers import Storer

if TYPE_CHECKING:
    from bgc_data_processing.data_structures.filtering import Constraints
    from bgc_data_processing.data_structures.variables import VariablesStorer
    from bgc_data_processing.utils.dateranges import DateRangeGenerator
    from bgc_data_processing.utils.patterns import FileNamePattern


class BaseLoader(ABC):
    """Base class to load data.

    Parameters
    ----------
    provider_name : str
        Data provider name.
    dirin : Path
        Directory to browse for files to load.
    category: str
        Category provider belongs to.
    exclude: list[str]
        Filenames to exclude from loading.
    files_pattern : FileNamePattern
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
        dirin: Path,
        category: str,
        exclude: list[str],
        files_pattern: "FileNamePattern",
        variables: "VariablesStorer",
    ) -> None:
        self._provider = provider_name
        self._dirin = dirin
        self._category = category
        self._exclude = exclude
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

    @property
    def dirin(self) -> Path:
        """Input directory.

        Returns
        -------
        str
            Input directory
        """
        return self._dirin

    @property
    def files_pattern(self) -> "FileNamePattern":
        """Files pattern.

        Returns
        -------
        FileNamePattern
            Files pattern.
        """
        return self._files_pattern

    @property
    def excluded_filenames(self) -> list[str]:
        """Filenames to exclude from loading."""
        return self._exclude

    @abstractmethod
    def __call__(self, constraints: "Constraints") -> "Storer":
        """Load all files for the loader.

        Parameters
        ----------
        constraints: Constraints
            Constraint slicer.

        Returns
        -------
        Storer
            Storer for the loaded data.
        """
        ...

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
        keep_path = str(filepath) not in self._exclude
        keep_name = filepath.name not in self._exclude

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

    def load_and_save(
        self,
        saving_directory: Path,
        dateranges_gen: "DateRangeGenerator",
        constraints: "Constraints",
    ):
        """Save data in files as soon as the data is loaded to relieve memory.

        Parameters
        ----------
        saving_directory : Path
            Path to the directory to save in.
        dateranges_gen : DateRangeGenerator
            Generator to use to retrieve dateranges.
        constraints : Constraints
            Contraints ot apply on data.
        """
        date_label = self._variables.get(self._variables.date_var_name).label
        date_constraint = constraints.get_constraint_parameters(date_label)
        pattern_matcher = self._files_pattern.build_from_constraint(date_constraint)
        pattern_matcher.validate = self.is_file_valid
        filepaths = pattern_matcher.select_matching_filepath(
            research_directory=self._dirin,
        )
        for filepath in filepaths:
            data = self.load(filepath=filepath, constraints=constraints)
            storer = Storer(
                data=data,
                category=self.category,
                providers=[self.provider],
                variables=self.variables,
                verbose=self.verbose,
            )
            saver = StorerSaver(storer)
            saver.save_from_daterange(
                dateranges_gen=dateranges_gen,
                saving_directory=saving_directory,
            )
