"""Base Loaders."""


import itertools
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from bgc_data_processing.data_classes import Constraints, Storer
    from bgc_data_processing.variables import VariablesStorer


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
        dirin: Path,
        category: str,
        files_pattern: str,
        variables: "VariablesStorer",
    ) -> None:
        """Initiate base class to load data.

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
        """
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
    def files_pattern(self) -> str:
        """Files pattern.

        Returns
        -------
        str
            Files pattern.
        """
        return self._files_pattern

    @abstractmethod
    def __call__(self, constraints: "Constraints", exclude: list = []) -> "Storer":
        """Load all files for the loader.

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

    def _pattern(self, date_constraint: dict) -> str:
        """Return files pattern for given years for this provider.

        Returns
        -------
        str
            Pattern.
        date_constraint: dict
            Date-related constraint dictionnary.
        """
        if not date_constraint:
            years_str = "...."
        else:
            boundary_in = "boundary" in date_constraint
            superset_in = "superset" in date_constraint
            if boundary_in and superset_in and date_constraint["superset"]:
                b_min = date_constraint["boundary"]["min"]
                b_max = date_constraint["boundary"]["max"]
                s_min = min(date_constraint["superset"])
                s_max = max(date_constraint["superset"])
                year_min = min(b_min, s_min).year
                year_max = max(b_max, s_max).year
                years_str = "|".join([str(i) for i in range(year_min, year_max + 1)])
            elif not boundary_in:
                year_min = min(date_constraint["superset"]).year
                year_max = max(date_constraint["superset"]).year
                years_str = "|".join([str(i) for i in range(year_min, year_max + 1)])
            elif not superset_in:
                year_min = date_constraint["boundary"]["min"].year
                year_max = date_constraint["boundary"]["max"].year
                years_str = "|".join([str(i) for i in range(year_min, year_max + 1)])
            else:
                raise KeyError("Date constraint dictionnary has invalid keys")
        return self._files_pattern.format(years=years_str)

    def _select_filepaths(
        self,
        research_dir: Path,
        pattern: str,
        exclude: list[str],
    ) -> list[Path]:
        """Recursive function to apply pattern on folders and file names.

        Parameters
        ----------
        research_dir : Path
            Directory on which to search for folders/files respecting pattern.
        pattern : str
            Pattern to respect (from the level of research_dir)
        exclude : list[str]
            Filenames to exclude.

        Returns
        -------
        list[Path]
            Files matching the pattern.
        """
        if "/" not in pattern:
            # Search pattern on file names
            regex = re.compile(pattern)
            files = filter(regex.match, [x.name for x in research_dir.glob("*.*")])
            fulls_paths = map(research_dir.joinpath, files)

            def valid(filepath: Path) -> bool:
                return self._is_file_valid(filepath=filepath, exclude=exclude)

            return sorted(filter(valid, fulls_paths))

        # recursion: Search pattern on folder names
        pattern_split = pattern.split("/")
        folder_regex = re.compile(pattern_split[0])
        matches = filter(folder_regex.match, [x.name for x in research_dir.glob("*")])

        # Prepare next recursive call
        def recursive_call(folder: str) -> list[Path]:
            return self._select_filepaths(
                research_dir=research_dir.joinpath(folder),
                pattern="/".join(pattern_split[1:]),
                exclude=exclude,
            )

        # apply recursive function to selected folders
        recursion_results = map(recursive_call, matches)
        # return list of all results
        return list(itertools.chain(*recursion_results))

    def _is_file_valid(self, filepath: Path, exclude: list[str]) -> bool:
        """Indicate whether a file is valid to be kept or not.

        Parameters
        ----------
        filepath : Path
            Name of the file
        exclude : list[str]
            List of filenames to exclude

        Returns
        -------
        bool
            True if the name is not to be excluded.
        """
        keep_path = str(filepath) not in exclude
        keep_name = filepath.name not in exclude

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
            # to_correct[label] = to_correct[label]  #
        return to_correct
