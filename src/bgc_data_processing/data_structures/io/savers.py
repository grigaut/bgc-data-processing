"""Save Storers to a file."""
from copy import copy
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:

    from bgc_data_processing.data_structures.storers import Slice, Storer
    from bgc_data_processing.utils.dateranges import DateRange, DateRangeGenerator


class StorerSaver:
    """Saver for Storer objects.

    Parameters
    ----------
    storer : Storer
        Storer to save.
    save_aggregated_data_only: bool
        Whether to only save the aggregated data or not.
        If False, for every provider, a folder with the providers' data will be created.
    """

    single_filename_format: str = "nutrients_{provider}_{dates}.txt"
    aggr_filename_format: str = "bgc_{category}_{dates}.txt"
    _date_field: str = "date"
    _slice_field: str = "slice"

    def __init__(
        self,
        storer: "Storer",
        save_aggregated_data_only: bool = False,
    ) -> None:
        self._storer = storer
        self._variables = copy(storer.variables)
        self._verbose = storer.verbose
        self.save_aggregated_data_only = save_aggregated_data_only

    @property
    def saving_order(self) -> list[str]:
        """Saving Order for variables."""
        return self._variables.save_labels

    @saving_order.setter
    def saving_order(self, var_names: list[str]) -> None:
        self._variables.set_saving_order(var_names=var_names)

    def _slice_using_drng(self, dateranges: "DateRange") -> pd.DataFrame:
        """Slice the Storer using the given DateRanges.

        Parameters
        ----------
        dateranges : DateRange
            DateRange to use as slicing reference.

        Returns
        -------
        pd.DataFrame
            DataFrame with dateranges (as string) and slices.
        """
        df_dateranges = dateranges.as_dataframe()
        slices_indexes = df_dateranges.apply(self._storer.slice_on_dates, axis=1)
        return pd.concat(
            [dateranges.as_str(), slices_indexes],
            keys=[self._date_field, self._slice_field],
            axis=1,
        )

    def _make_single_filepath(self, dates_str: str, saving_directory: Path) -> Path:
        """Create the filepath in which to save the data of a single provider.

        Parameters
        ----------
        dates_str : str
            Dates of the slice to save in the file.

        Returns
        -------
        Path
            Path to the file in which to save the data.

        Raises
        ------
        ValueError
            If the storer has multiple providers.
        """
        if len(self._storer.providers) == 1:
            provider = self._storer.providers[0]
        else:
            raise ValueError("Multiple providers in the storer.")
        filename = self.single_filename_format.format(
            provider=provider,
            dates=dates_str,
        )
        return self._create_filepath(saving_directory.joinpath(provider), filename)

    def _make_aggr_filepath(self, dates_str: str, saving_directory: Path) -> Path:
        """Create the filepath in which to save the aggregated data of all providers.

        Parameters
        ----------
        dates_str : str
            Dates of the slice to save in the file.

        Returns
        -------
        Path
            Path to the file in which to save the data.
        """
        category = self._storer.category
        filename = self.aggr_filename_format.format(category=category, dates=dates_str)
        return self._create_filepath(saving_directory, filename)

    def _create_filepath(self, dir_path: Path, filename: str) -> Path:
        """Create the filepath given the file directory and filename.

        Parameters
        ----------
        dir_path : Path
            Directory in which to save the file.
        filename : str
            Filename.

        Returns
        -------
        Path
            dir_path/filename.
        """
        if not dir_path.is_dir():
            dir_path.mkdir()
        filepath = dir_path.joinpath(filename)
        if not filepath.is_file():
            filepath.open("w")
        return filepath

    def _write_header(self, filepath: Path) -> None:
        """Write a file's header with data variables names and units.

        Parameters
        ----------
        filepath : Path
            Filepath to the file to save the data in.
        """
        if filepath.is_file() and filepath.open("r").readlines():
            return
        variables = self._variables
        name_format = variables.name_save_format
        labels = [variables.get(name).label for name in variables.save_names]
        units = [variables.get(name).unit for name in variables.save_names]
        with filepath.open("w") as file:
            # Write variables row
            file.write(name_format % tuple(labels) + "\n")
            # Write unit row
            file.write(name_format % tuple(units) + "\n")

    def _write_values(self, filepath: Path, data: pd.DataFrame) -> None:
        """Write the data values within the given file.

        Parameters
        ----------
        filepath : Path
            Filepath to the file to save the data in.
        data : pd.DataFrame
            Data to save.
        """
        value_format = self._variables.value_save_format
        with filepath.open("a") as file:
            # Write
            lines = data.apply(lambda x: value_format % tuple(x) + "\n", axis=1)
            if len(lines) != 0:
                file.writelines(lines)

    def _save_data(self, filepath: Path, data_slice: "Storer") -> None:
        """Save the data of a slice within a given file.

        Parameters
        ----------
        filepath : Path
            Filepath to the file to save the data in.
        data_slice : Storer
            Data to save.
        """
        # Verbose
        if self._verbose > 1:
            print(f"\tSaving data in {filepath.name}")
        # Parameters
        data: pd.DataFrame = data_slice.data.loc[:, self._variables.save_labels]
        self._write_header(filepath)
        if not data.empty:
            self._write_values(filepath, data)

    def _save_slice(self, date_slice: pd.Series, saving_directory: Path) -> None:
        """Save a slice.

        Parameters
        ----------
        date_slice : pd.Series
            Data slice to save.
        """
        date_str: str = date_slice[self._date_field]
        data_slice: "Slice" = date_slice[self._slice_field]
        if not self.save_aggregated_data_only:
            self._save_data(
                filepath=self._make_single_filepath(date_str, saving_directory),
                data_slice=data_slice,
            )
        self._save_data(
            filepath=self._make_aggr_filepath(date_str[:-9], saving_directory),
            data_slice=data_slice,
        )

    def save_from_daterange(
        self,
        dateranges_gen: "DateRangeGenerator",
        saving_directory: Path,
    ) -> None:
        """Save the storer's data according to the given dateranges.

        Parameters
        ----------
        dateranges_gen : DateRangeGenerator
            Generator to use to retrieve dateranges.
        """
        dateranges = dateranges_gen()
        dates_slices = self._slice_using_drng(dateranges)
        dates_slices.apply(self._save_slice, axis=1, saving_directory=saving_directory)

    def save_all_storer(self, filepath: Path) -> None:
        """Save all the storer to the given file.

        Parameters
        ----------
        filepath : Path
            File in which to save the storer data.

        Raises
        ------
        FileExistsError
            If filepath points to an existing file.
        """
        if filepath.is_file():
            raise FileExistsError
        self._save_data(filepath=filepath, data_slice=self._storer)

    @classmethod
    def save(
        cls,
        storer: "Storer",
        filepath: Path,
        save_aggregated_data_only: bool = False,
    ) -> None:
        """Save all the storer to the given file.

        Parameters
        ----------
        storer : Storer
            Storer to save.
        filepath : Path
            File in which to save the storer data.
        save_aggregated_data_only: bool
            Whether to only save the aggregated data or not.
            If False, for every provider, a folder with the provider's
            data will be created.
        """
        saver = cls(storer=storer, save_aggregated_data_only=save_aggregated_data_only)
        saver.save_all_storer(filepath=filepath)
