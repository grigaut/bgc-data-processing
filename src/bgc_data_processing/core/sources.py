"""Data Source objects."""

from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING, Any

from bgc_data_processing.core.io.savers import StorerSaver
from bgc_data_processing.core.loaders.abfile_loaders import ABFileLoader
from bgc_data_processing.core.loaders.csv_loaders import CSVLoader
from bgc_data_processing.core.loaders.netcdf_loaders import (
    NetCDFLoader,
    SatelliteNetCDFLoader,
)
from bgc_data_processing.core.storers import Storer
from bgc_data_processing.exceptions import UnsupportedLoadingFormatError
from bgc_data_processing.verbose import with_verbose

if TYPE_CHECKING:
    from bgc_data_processing.core.filtering import Constraints
    from bgc_data_processing.core.loaders.base import BaseLoader
    from bgc_data_processing.core.variables.sets import SourceVariableSet
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
    dirin : Path | str
        Input data directory.
    data_category : str
        Category of the data.
    excluded_files : list[str]
        Files not to load.
    files_pattern : FileNamePattern
        Pattern to match to load files.
    variable_ensemble : SourceVariableSet
        Ensembles of variables to consider.
    """

    def __init__(
        self,
        provider_name: str,
        data_format: str,
        dirin: Path | str,
        data_category: str,
        excluded_files: list[str],
        files_pattern: "FileNamePattern",
        variable_ensemble: "SourceVariableSet",
        **kwargs,
    ) -> None:
        self._format = data_format
        self._category = data_category
        self._vars_ensemble = variable_ensemble
        self._store_vars = variable_ensemble.storing_variables
        self._files_pattern = files_pattern
        self._dirin = Path(dirin)
        self._provider = provider_name
        self._read_kwargs = kwargs
        self._prov_name = provider_name
        self._excl = excluded_files
        self._loader = None

    @property
    def as_template(self) -> dict[str, Any]:
        """Create template to easily re-create a similar data source.

        Returns
        -------
        dict[str, Any]
            Arguements to create a similar data source.
        """
        base_parameters = {
            "provider_name": self._provider,
            "data_format": self._format,
            "dirin": self._dirin,
            "data_category": self._category,
            "excluded_files": self._loader.excluded_filenames,
            "files_pattern": self._files_pattern,
            "variable_ensemble": deepcopy(self._vars_ensemble),
        }
        for key, value in self._read_kwargs.items():
            base_parameters[key] = value
        return base_parameters

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
        if self._loader is None:
            self._loader = self._build_loader(
                self._prov_name,
                self._excl,
            )
        return self._loader

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
        excluded_files: list[str],
    ) -> "BaseLoader":
        """Build the loader.

        Parameters
        ----------
        provider_name : str
            Name of the Data provider.
            !!! At the moment, it is only possible to use "csv","netcdf" or "abfiles".
        excluded_files : list[str]
            Files to exclude.

        Returns
        -------
        SelectiveABFileLoader
            Selective Loader.

        Raises
        ------
        UnsupportedLoadingFormatError
            If the file format is not supported.
        """
        if self._format == "csv":
            return CSVLoader(
                provider_name=provider_name,
                category=self._category,
                exclude=excluded_files,
                variables=self._vars_ensemble.loading_variables,
                **self._read_kwargs,
            )
        if self._format == "netcdf" and self._category == "satellite":
            return SatelliteNetCDFLoader(
                provider_name=provider_name,
                category=self._category,
                exclude=excluded_files,
                variables=self._vars_ensemble.loading_variables,
                **self._read_kwargs,
            )
        if self._format == "netcdf":
            return NetCDFLoader(
                provider_name=provider_name,
                category=self._category,
                exclude=excluded_files,
                variables=self._vars_ensemble.loading_variables,
                **self._read_kwargs,
            )
        if self._format == "abfiles":
            return ABFileLoader(
                provider_name=provider_name,
                category=self._category,
                exclude=excluded_files,
                variables=self._vars_ensemble.loading_variables,
                **self._read_kwargs,
            )
        raise UnsupportedLoadingFormatError(self._format)

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

    def _remove_temporary_variables(self, storer: "Storer") -> None:
        """Remove variables which were used to construct features.

        Parameters
        ----------
        storer : Storer
            Storer to remove variables from
        """
        to_remove = [x for x in storer.variables if not self.variables.has_name(x.name)]
        for var in to_remove:
            _ = storer.pop(var.name)

    @with_verbose(trigger_threshold=0, message="Loading data from [filepath]")
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
        data = self.loader.load(filepath=filepath, constraints=constraints)
        storer = Storer(
            data=data,
            category=self._category,
            providers=[self.loader.provider],
            variables=self._store_vars,
        )
        self._insert_all_features(storer)
        self._remove_temporary_variables(storer)
        return storer

    def load_and_save(
        self,
        saving_directory: Path | str,
        dateranges_gen: "DateRangeGenerator",
        constraints: "Constraints",
    ) -> None:
        """Save data in files as soon as the data is loaded to relieve memory.

        Parameters
        ----------
        saving_directory : Path | str
            Path to the directory to save in.
        dateranges_gen : DateRangeGenerator
            Generator to use to retrieve dateranges.
        constraints : Constraints
            Contraints ot apply on data.
        """
        date_label = self._vars_ensemble.get(self._vars_ensemble.date_var_name).label
        date_constraint = constraints.get_constraint_parameters(date_label)
        pattern_matcher = self._files_pattern.build_from_constraint(date_constraint)
        pattern_matcher.validate = self.loader.is_file_valid
        filepaths = pattern_matcher.select_matching_filepath(
            research_directory=self._dirin,
        )
        for filepath in filepaths:
            storer = self._create_storer(filepath=filepath, constraints=constraints)
            saver = StorerSaver(storer)
            saver.save_from_daterange(
                dateranges_gen=dateranges_gen,
                saving_directory=Path(saving_directory),
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
        pattern_matcher.validate = self.loader.is_file_valid
        filepaths = pattern_matcher.select_matching_filepath(
            research_directory=self._dirin,
        )
        storers = []
        for filepath in filepaths:
            storer = self._create_storer(filepath=filepath, constraints=constraints)
            storers.append(storer)
        return sum(storers)
