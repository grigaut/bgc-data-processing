"""Data Source objects."""

from pathlib import Path
from typing import TYPE_CHECKING

from bgc_data_processing.data_structures.io.savers import StorerSaver
from bgc_data_processing.data_structures.storers import Storer
from bgc_data_processing.loaders.abfile_loaders import ABFileLoader
from bgc_data_processing.loaders.csv_loaders import CSVLoader
from bgc_data_processing.loaders.netcdf_loaders import (
    NetCDFLoader,
    SatelliteNetCDFLoader,
)

if TYPE_CHECKING:
    from bgc_data_processing.data_structures.filtering import Constraints
    from bgc_data_processing.data_structures.variables.sets import SourceVariableSet
    from bgc_data_processing.loaders.base import BaseLoader
    from bgc_data_processing.utils.dateranges import DateRangeGenerator
    from bgc_data_processing.utils.patterns import FileNamePattern


class DataSource:
    """Data Source.

    Parameters
    ----------
    provider_name : str
        Name of the data provider.
    data_format : str
        Data format.
    dirin : Path
        Input data directory.
    data_category : str
        Category of the data.
    excluded_files : list[str]
        Files not to load.
    files_pattern : FileNamePattern
        Pattern to match to load files.
    variable_ensemble : SourceVariableSet
        Ensembles of variables to consider.
    verbose : int, optional
        Verbose., by default 1
    """

    def __init__(
        self,
        provider_name: str,
        data_format: str,
        dirin: Path,
        data_category: str,
        excluded_files: list[str],
        files_pattern: "FileNamePattern",
        variable_ensemble: "SourceVariableSet",
        verbose: int = 1,
        **kwargs,
    ) -> None:
        self._format = data_format
        self._category = data_category
        self._vars_ensemble = variable_ensemble
        self._store_vars = variable_ensemble.storing_variables
        self._files_pattern = files_pattern
        self._dirin = dirin
        self._verbose = verbose
        self._provider = provider_name
        self._loader = self._build_loader(
            provider_name,
            excluded_files,
            **kwargs,
        )

    @property
    def dirin(self) -> Path:
        """Directory with data to load."""
        return self._dirin

    @property
    def files_pattern(self) -> "FileNamePattern":
        """Pattern to match for files in input directory."""
        return self._files_pattern

    @property
    def provider(self) -> str:
        """Name of the data provider."""
        return self._provider

    @property
    def data_format(self) -> str:
        """Name of the data format."""
        return self._format

    @property
    def data_category(self) -> str:
        """Name of the data category."""
        return self._category

    @property
    def variables(self) -> "SourceVariableSet":
        """Ensemble of all variables."""
        return self._vars_ensemble

    @property
    def loader(self) -> "BaseLoader":
        """Data loader."""
        return self._loader

    @property
    def verbose(self) -> int:
        """Verbose level."""
        return self._verbose

    @verbose.setter
    def verbose(self, verbose_value) -> None:
        assert isinstance(verbose_value, int), "self.verbose must be an instance of int"
        self._verbose = verbose_value

    @property
    def saving_order(self) -> list[str]:
        """Saving Order for variables."""
        return self._store_vars.saving_variables.save_labels

    @saving_order.setter
    def saving_order(self, var_names: list[str]) -> None:
        self._store_vars.set_saving_order(
            var_names=var_names,
        )

    def _build_loader(
        self,
        provider_name: str,
        # dirin: Path,
        excluded_files: list[str],
        **kwargs,
    ) -> "BaseLoader":
        if self._format == "csv":
            return CSVLoader(
                provider_name=provider_name,
                # dirin=dirin,
                category=self._category,
                exclude=excluded_files,
                variables=self._vars_ensemble.loading_variables,
                **kwargs,
            )
        if self._format == "netcdf" and self._category == "satellite":
            return SatelliteNetCDFLoader(
                provider_name=provider_name,
                # dirin=dirin,
                category=self._category,
                exclude=excluded_files,
                variables=self._vars_ensemble.loading_variables,
                **kwargs,
            )
        if self._format == "netcdf":
            return NetCDFLoader(
                provider_name=provider_name,
                # dirin=dirin,
                category=self._category,
                exclude=excluded_files,
                variables=self._vars_ensemble.loading_variables,
                **kwargs,
            )
        if self._format == "abfiles":
            return ABFileLoader(
                provider_name=provider_name,
                # dirin=dirin,
                category=self._category,
                exclude=excluded_files,
                variables=self._vars_ensemble.loading_variables,
                **kwargs,
            )
        raise ValueError

    def _insert_all_features(self, storer: "Storer") -> None:
        """Insert all features in a storer.

        Parameters
        ----------
        storer : Storer
            Storer to insert features in.
        """
        features = self.variables.features
        storer_vars = storer.variables.elements
        for fvar in features.iter_constructables_features(storer_vars):
            fvar.feature.insert_in_storer(storer)

    def _create_storer(self, filepath: Path, constraints: "Constraints") -> "Storer":
        """Create the storer with the data from a given filepath.

        Parameters
        ----------
        filepath : Path
            Path to the file to load data from.
        constraints : Constraints
            Constraints to apply on the storer.

        Returns
        -------
        Storer
            Storer.
        """
        data = self._loader.load(filepath=filepath, constraints=constraints)
        storer = Storer(
            data=data,
            category=self._category,
            providers=[self._loader.provider],
            variables=self._store_vars,
            verbose=self._verbose,
        )
        self._insert_all_features(storer)
        return storer

    def load_and_save(
        self,
        saving_directory: Path,
        dateranges_gen: "DateRangeGenerator",
        constraints: "Constraints",
    ) -> None:
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
        date_label = self._vars_ensemble.get(self._vars_ensemble.date_var_name).label
        date_constraint = constraints.get_constraint_parameters(date_label)
        pattern_matcher = self._files_pattern.build_from_constraint(date_constraint)
        pattern_matcher.validate = self._loader.is_file_valid
        filepaths = pattern_matcher.select_matching_filepath(
            research_directory=self._dirin,
        )
        for filepath in filepaths:
            storer = self._create_storer(filepath=filepath, constraints=constraints)
            saver = StorerSaver(storer)
            saver.save_from_daterange(
                dateranges_gen=dateranges_gen,
                saving_directory=saving_directory,
            )

    def load_all(self, constraints: "Constraints") -> "Storer":
        """Load all files for the loader.

        Parameters
        ----------
        constraints : Constraints, optional
            Constraints slicer., by default Constraints()

        Returns
        -------
        Storer
            Storer for the loaded data.
        """
        date_label = self._vars_ensemble.get(self._vars_ensemble.date_var_name).label
        date_constraint = constraints.get_constraint_parameters(date_label)
        pattern_matcher = self._files_pattern.build_from_constraint(date_constraint)
        pattern_matcher.validate = self._loader.is_file_valid
        filepaths = pattern_matcher.select_matching_filepath(
            research_directory=self._dirin,
        )
        storers = []
        for filepath in filepaths:
            storer = self._create_storer(filepath=filepath, constraints=constraints)
            storers.append(storer)
        return sum(storers)
