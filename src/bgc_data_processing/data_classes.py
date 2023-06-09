"""Data storing objects."""


from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import geopandas as gpd
import numpy as np
import pandas as pd

from bgc_data_processing.variables import ParsedVar, VariablesStorer

if TYPE_CHECKING:
    from collections.abc import Callable

    from shapely import Polygon

    from bgc_data_processing.variables import NotExistingVar


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
        """Instanciate a storing data class, to keep track of metadata.

        Parameters
        ----------
        data : pd.DataFrame
            Dataframe to store.
        category: str
            Data category.
        providers : list
            Names of the data providers.
        variables : VariablesStorer
            Variables storer of object to keep track of the variables in the Dataframe.
        verbose : int, optional
            Controls the verbosity: the higher, the more messages., by default 0
        """
        self._data = data
        self._category = category
        self._providers = providers
        self._variables = variables
        self._verbose = verbose

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
        """_verbose attribute getter.

        Returns
        -------
        int
            Verbose value.
        """
        return self._verbose

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
        """
        if not isinstance(other, Storer):
            raise TypeError(f"Can't add CSVStorer object to {type(other)}")
        # Assert variables are the same
        if not (self.variables == other.variables):
            raise ValueError("Variables or categories are not compatible")
        # Assert categories are the same
        if not (self.category == other.category):
            raise ValueError("Categories are not compatible")

        concat_data = pd.concat([self._data, other.data], ignore_index=True)
        concat_providers = list(set(self.providers + other.providers))
        # Return Storer with similar variables
        return Storer(
            data=concat_data,
            category=self.category,
            providers=concat_providers,
            variables=self.variables,
            verbose=min(self._verbose, other.verbose),
        )

    def remove_duplicates(self, priority_list: list = None) -> None:
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
        grouped = duplicates.groupby(subset_group, dropna=False).mean().reset_index()
        # Concatenate dataframe with droppped duplicates and duplicates averaged
        return pd.concat([dropped, grouped], ignore_index=True, axis=0)

    def _remove_duplicates_between_providers(
        self,
        df: pd.DataFrame,
        priority_list: list,
    ) -> pd.DataFrame:
        """Remove duplicates among a common providers.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to remove duplicated data from.
        priority_list : list, optional
            Providers priority order, first has priority over others and so on.
            , by default None

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

    def save(self, filepath: Path) -> None:
        """Save the Dataframe.

        Parameters
        ----------
        filepath : Path
            Where to save the output.
        """
        # Verbose
        if self._verbose > 1:
            print(f"\tSaving data in {filepath.name}")
        # Parameters
        name_format = self.variables.name_save_format
        value_format = self.variables.value_save_format
        df = self.data.loc[:, self.variables.save_labels]
        # Get unit rows' values
        units = [self.variables.unit_mapping[col] for col in df.columns]
        dirout = filepath.parent
        # make directory if needed
        if not dirout:
            pass
        elif not dirout.is_dir():
            dirout.mkdir()
        # Save file
        with filepath.open("w") as file:
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
        start_date = drng["start_date"]
        end_date = drng["end_date"]
        dates_col = self._data[self._variables.get(self._variables.date_var_name).label]
        # Verbose
        if self._verbose > 1:
            print(
                "\tSlicing data for date range"
                f" {start_date.date()} {end_date.date()}",
            )
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

    @classmethod
    def from_files(
        cls,
        filepath: Path | str | list[Path] | list[str],
        providers_column_label: str = "PROVIDER",
        expocode_column_label: str = "EXPOCODE",
        date_column_label: str = "DATE",
        year_column_label: str = "YEAR",
        month_column_label: str = "MONTH",
        day_column_label: str = "DAY",
        hour_column_label: str = "HOUR",
        latitude_column_label: str = "LATITUDE",
        longitude_column_label: str = "LONGITUDE",
        depth_column_label: str = "DEPH",
        category: str = "in_situ",
        unit_row_index: int = 1,
        delim_whitespace: bool = True,
        verbose: int = 1,
    ) -> "Storer":
        """Build Storer reading data from csv or txt files.

        Parameters
        ----------
        filepath : Path | str | list[Path] | list[str]
            Path to the file to read.
        providers_column_label : str, optional
            Provider column in the dataframe., by default "PROVIDER"
        expocode_column_label : str, optional
            Expocode column in the dataframe., by default "EXPOCODE"
        date_column_label : str, optional
            Date column in the dataframe., by default "DATE"
        year_column_label : str, optional
            Year column in the dataframe., by default "YEAR"
        month_column_label : str, optional
            Month column in the dataframe., by default "MONTH"
        day_column_label : str, optional
            Day column in the dataframe., by default "DAY"
        hour_column_label : str, optional
            Hour column in the dataframe., by default "HOUR"
        latitude_column_label : str, optional
            Latitude column in the dataframe., by default "LATITUDE"
        longitude_column_label : str, optional
            Longitude column in the dataframe., by default "LONGITUDE"
        depth_column_label : str, optional
            Depth column in the dataframe., by default "DEPH"
        category : str, optional
            Category of the loaded file., by default "in_situ"
        unit_row_index : int, optional
            Index of the row with the units, None if there's no unit row., by default 1
        delim_whitespace : bool, optional
            Whether to use whitespace as delimiters., by default True
        verbose : int, optional
            Controls the verbose, by default 1

        Returns
        -------
        Storer
            Storer aggregating the data from all the files

        Raises
        ------
        TypeError
            If filepath argument is not an instance of string or list.

        Examples
        --------
        Loading from a single file:
        >>> filepath = "path/to/file"
        >>> storer = DStorer.from_files(filepath, providers="providers_column_name")

        Loading from multiple files:
        >>> filepaths = [
        ...     "path/to/file1",
        ...     "path/to/file2",
        ... ]
        >>> storer = DensityPlotter.from_files(
        ...     filepaths,
        ... )
        """
        if isinstance(filepath, list):
            storers = []
            for path in filepath:
                storer = Storer.from_files(
                    filepath=path,
                    providers_column_label=providers_column_label,
                    expocode_column_label=expocode_column_label,
                    date_column_label=date_column_label,
                    year_column_label=year_column_label,
                    month_column_label=month_column_label,
                    day_column_label=day_column_label,
                    hour_column_label=hour_column_label,
                    latitude_column_label=latitude_column_label,
                    longitude_column_label=longitude_column_label,
                    depth_column_label=depth_column_label,
                    category=category,
                    unit_row_index=unit_row_index,
                    delim_whitespace=delim_whitespace,
                    verbose=verbose,
                )

                storers.append(storer)
            return sum(storers)
        if isinstance(filepath, Path):
            path = filepath
        elif isinstance(filepath, str):
            path = Path(filepath)
        else:
            raise TypeError(f"Can't read filepaths from {filepath}")
        reader = Reader(
            filepath=path,
            providers_column_label=providers_column_label,
            expocode_column_label=expocode_column_label,
            date_column_label=date_column_label,
            year_column_label=year_column_label,
            month_column_label=month_column_label,
            day_column_label=day_column_label,
            hour_column_label=hour_column_label,
            latitude_column_label=latitude_column_label,
            longitude_column_label=longitude_column_label,
            depth_column_label=depth_column_label,
            category=category,
            unit_row_index=unit_row_index,
            delim_whitespace=delim_whitespace,
            verbose=verbose,
        )
        return reader.get_storer()

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
            verbose=storer.verbose,
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
            verbose=self._verbose,
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
            verbose=storer.verbose,
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
        ValueError
            Is the slices don't originate from same storer.
        """
        if self.storer != __o.storer:
            raise ValueError(
                "Addition can only be performed with slice from same CSVStorer",
            )
        new_index = list(set(self.slice_index).union(set(__o.slice_index)))
        return Slice(self.storer, new_index)


class Constraints:
    """Slicer object to slice dataframes."""

    def __init__(self) -> None:
        """Initiate slicer object to slice dataframes."""
        self.boundaries: dict[str, dict[str, int | float | datetime]] = {}
        self.supersets: dict[str, list] = {}
        self.constraints: dict[str, "Callable"] = {}
        self.polygons: list[dict[str, str | "Polygon"]] = []

    def reset(self) -> None:
        """Reset all defined constraints."""
        self.boundaries = {}
        self.supersets = {}
        self.constraints = {}

    def add_boundary_constraint(
        self,
        field_label: str,
        minimal_value: int | float | datetime = np.nan,
        maximal_value: int | float | datetime = np.nan,
    ) -> None:
        """Add a constraint of type 'boundary'.

        Parameters
        ----------
        field_label : str
            Name of the column to apply the constraint to.
        minimal_value : int | float | datetime, optional
            Minimum value for the column., by default np.nan
        maximal_value : int | float | datetime, optional
            Maximum value for the column., by default np.nan
        """
        is_min_nan = isinstance(minimal_value, float) and np.isnan(minimal_value)
        is_max_nan = isinstance(maximal_value, float) and np.isnan(maximal_value)
        if not (is_min_nan and is_max_nan):
            self.boundaries[field_label] = {
                "min": minimal_value,
                "max": maximal_value,
            }

    def add_superset_constraint(
        self,
        field_label: str,
        values_superset: list[Any] = [],
    ) -> None:
        """Add a constrainte of type 'superset'.

        Parameters
        ----------
        field_label : str
            Name of the column to apply the constraint to.
        values_superset : list[Any]
            All the values that the column can take.
            If empty, no constraint will be applied.
        """
        if values_superset:
            self.supersets[field_label] = values_superset

    def add_polygon_constraint(
        self,
        latitude_field: str,
        longitude_field: str,
        polygon: "Polygon",
    ) -> None:
        """Add a polygon constraint.

        Parameters
        ----------
        latitude_field : str
            Name of the latitude-related field.
        longitude_field : str
            Name of the longitude-related field.
        polygon : Polygon
            Polygon to use as boundary.
        """
        constraint_dict = {
            "latitude_field": latitude_field,
            "longitude_field": longitude_field,
            "polygon": polygon,
        }
        self.polygons.append(constraint_dict)

    def _apply_boundary_constraints(self, df: pd.DataFrame) -> pd.Series:
        """Evaluate all boundary constraints to a DataFrame.

        Parameters
        ----------
        df : pd.DataFrame
            Datafarme to evaluate the constraints on.

        Returns
        -------
        pd.Series
            Boolean series of the rows verifying all constraints.
        """
        series = np.empty(df.iloc[:, 0].shape, dtype=bool)
        series.fill(True)
        for label, bounds in self.boundaries.items():
            minimum = bounds["min"]
            maximum = bounds["max"]
            label_series = df[label]
            is_min_nan = isinstance(minimum, float) and np.isnan(minimum)
            is_max_nan = isinstance(maximum, float) and np.isnan(maximum)
            if is_min_nan and is_max_nan:
                continue
            if is_max_nan:
                bool_series = label_series >= minimum
            elif is_min_nan:
                bool_series = label_series <= maximum
            else:
                bool_series = (label_series >= minimum) & (label_series <= maximum)
            series = series & bool_series
        return series

    def _apply_superset_constraints(self, df: pd.DataFrame) -> pd.Series:
        """Evaluate all superset constraints to a DataFrame.

        Parameters
        ----------
        df : pd.DataFrame
            Datafarme to evaluate the constraints on.

        Returns
        -------
        pd.Series
            Boolean series of the rows verifying all constraints.
        """
        series = np.empty(df.iloc[:, 0].shape, dtype=bool)
        series.fill(True)
        for label, value_set in self.supersets.items():
            if value_set:
                label_series = df[label]
                bool_series = label_series.isin(value_set)
            series = series & bool_series
        return series

    def _apply_polygon_constraints(self, df: pd.DataFrame) -> pd.Series:
        """Evaluate all polygon constraints to a DataFrame.

        Parameters
        ----------
        df : pd.DataFrame
            Datafarme to evaluate the constraints on.

        Returns
        -------
        pd.Series
            Boolean series of the rows verifying all constraints.
        """
        series = np.empty(df.iloc[:, 0].shape, dtype=bool)
        series.fill(True)
        for constraint in self.polygons:
            longitude = constraint["longitude_field"]
            latitude = constraint["latitude_field"]
            polygon = constraint["polygon"]
            geometry = gpd.points_from_xy(
                x=df[longitude],
                y=df[latitude],
            )
            is_in_polygon = geometry.within(polygon)
            series = series & is_in_polygon
        return series

    def apply_constraints_to_storer(self, storer: Storer) -> Storer:
        """Apply all constraints to a DataFrame.

        Parameters
        ----------
        storer : pd.DataFrame
            Storer to apply the constraints to.

        Returns
        -------
        Storer
            New storer with equivalent paramters and updated data.
        """
        return Storer(
            data=self.apply_constraints_to_dataframe(storer.data),
            category=storer.category,
            providers=storer.providers,
            variables=storer.variables,
            verbose=storer.verbose,
        )

    def apply_constraints_to_dataframe(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame | None:
        """Apply all constraints to a DataFrame.

        Parameters
        ----------
        dataframe : pd.DataFrame
            DataFrame to apply the constraints to.

        Returns
        -------
        pd.DataFrame
            DataFrame whose rows verify all constraints or None if inplace=True.
        """
        bool_boundaries = self._apply_boundary_constraints(dataframe)
        bool_supersets = self._apply_superset_constraints(dataframe)
        bool_polygons = self._apply_polygon_constraints(dataframe)
        verify_all = bool_boundaries & bool_supersets & bool_polygons
        return dataframe.loc[verify_all, :]

    def apply_specific_constraint(
        self,
        field_label: str,
        df: pd.DataFrame,
    ) -> pd.DataFrame | None:
        """Only apply a single constraint.

        Parameters
        ----------
        field_label : str
            Label of the field to apply the constraint to.
        df : pd.DataFrame
            DataFrame to apply the constraints to.

        Returns
        -------
        pd.DataFrame | None
            DataFrame whose rows verify all constraints or None if inplace=True.
        """
        constraint = Constraints()
        if field_label in self.boundaries:
            constraint.add_boundary_constraint(
                field_label=field_label,
                minimal_value=self.boundaries[field_label]["min"],
                maximal_value=self.boundaries[field_label]["max"],
            )
        if field_label in self.supersets:
            constraint.add_superset_constraint(
                field_label=field_label,
                value_superset=self.supersets[field_label],
            )
        return constraint.apply_constraints_to_dataframe(dataframe=df)

    def is_constrained(self, field_name: str) -> bool:
        """Return True if 'field_name' is constrained.

        Parameters
        ----------
        field_name : str
            Field to name to test the constraint.

        Returns
        -------
        bool
            True if the field has a constraint.
        """
        in_boundaries = field_name in self.boundaries
        in_supersets = field_name in self.supersets
        return in_boundaries or in_supersets

    def get_constraint_parameters(self, field_name: str) -> dict:
        """Return the constraints on 'field_name'.

        Parameters
        ----------
        field_name : str
            Field to get the constraint of.

        Returns
        -------
        dict
            Dictionnary with keys 'boundary' and/or 'superset' if constraints exist.
        """
        constraint_params = {}
        if field_name in self.boundaries:
            constraint_params["boundary"] = self.boundaries[field_name]
        if field_name in self.supersets:
            constraint_params["superset"] = self.supersets[field_name]
        return constraint_params

    def get_extremes(
        self,
        field_name: str,
        default_min: int | float | datetime = None,
        default_max: int | float | datetime = None,
    ) -> tuple[int | float | datetime, int | float | datetime]:
        """Return extreme values as they appear in the constraints.

        Parameters
        ----------
        field_name : str
            Name of the field to get the extreme of.
        default_min : int | float | datetime, optional
            Default value for the minimum if not constraint exists., by default None
        default_max : int | float | datetime, optional
            Default value for the maximum if not constraint exists., by default None

        Returns
        -------
        tuple[int | float | datetime, int | float | datetime]
            Minimum value, maximum value
        """
        if not self.is_constrained(field_name=field_name):
            return default_min, default_max
        constraints = self.get_constraint_parameters(field_name=field_name)
        boundary_in = "boundary" in constraints
        superset_in = "superset" in constraints
        if boundary_in and superset_in and constraints["superset"]:
            b_min = constraints["boundary"]["min"]
            b_max = constraints["boundary"]["max"]
            s_min = min(constraints["superset"])
            s_max = max(constraints["superset"])
            all_min = min(b_min, s_min)
            all_max = max(b_max, s_max)
        elif not boundary_in:
            all_min = min(constraints["superset"])
            all_max = max(constraints["superset"])
        elif not superset_in:
            all_min = constraints["boundary"]["min"]
            all_max = constraints["boundary"]["max"]
        return all_min, all_max


class Reader:
    """Reading routine to parse csv files.

    Parameters
    ----------
    filepath : Path | list[Path]
        Path to the file to read.
    providers_column_label : str, optional
        Provider column in the dataframe., by default "PROVIDER"
    expocode_column_label : str, optional
        Expocode column in the dataframe., by default "EXPOCODE"
    date_column_label : str, optional
        Date column in the dataframe., by default "DATE"
    year_column_label : str, optional
        Year column in the dataframe., by default "YEAR"
    month_column_label : str, optional
        Month column in the dataframe., by default "MONTH"
    day_column_label : str, optional
        Day column in the dataframe., by default "DAY"
    hour_column_label : str, optional
        Hour column in the dataframe., by default "HOUR"
    latitude_column_label : str, optional
        Latitude column in the dataframe., by default "LATITUDE"
    longitude_column_label : str, optional
        Longitude column in the dataframe., by default "LONGITUDE"
    depth_column_label : str, optional
        Depth column in the dataframe., by default "DEPH"
    category : str, optional
        Category of the loaded file., by default "in_situ"
    unit_row_index : int, optional
        Index of the row with the units, None if there's no unit row., by default 1
    delim_whitespace : bool, optional
        Whether to use whitespace as delimiters., by default True
    verbose : int, optional
        Controls the verbose, by default 1

    Examples
    --------
    Loading from a file:
    >>> filepath = "path/to/file"
    >>> reader = Reader(filepath, providers="providers_column_name")

    Getting the storer:
    >>> storer = reader.get_storer()
    """

    def __init__(
        self,
        filepath: Path,
        providers_column_label: str = "PROVIDER",
        expocode_column_label: str = "EXPOCODE",
        date_column_label: str = "DATE",
        year_column_label: str = "YEAR",
        month_column_label: str = "MONTH",
        day_column_label: str = "DAY",
        hour_column_label: str = "HOUR",
        latitude_column_label: str = "LATITUDE",
        longitude_column_label: str = "LONGITUDE",
        depth_column_label: str = "DEPH",
        category: str = "in_situ",
        unit_row_index: int = 1,
        delim_whitespace: bool = True,
        verbose: int = 1,
    ):
        """Initiate reading routine to parse csv files.

        Parameters
        ----------
        filepath : Path
            Path to the file to read.
        providers_column_label : str, optional
            Provider column in the dataframe., by default "PROVIDER"
        expocode_column_label : str, optional
            Expocode column in the dataframe., by default "EXPOCODE"
        date_column_label : str, optional
            Date column in the dataframe., by default "DATE"
        year_column_label : str, optional
            Year column in the dataframe., by default "YEAR"
        month_column_label : str, optional
            Month column in the dataframe., by default "MONTH"
        day_column_label : str, optional
            Day column in the dataframe., by default "DAY"
        hour_column_label : str, optional
            Hour column in the dataframe., by default "HOUR"
        latitude_column_label : str, optional
            Latitude column in the dataframe., by default "LATITUDE"
        longitude_column_label : str, optional
            Longitude column in the dataframe., by default "LONGITUDE"
        depth_column_label : str, optional
            Depth column in the dataframe., by default "DEPH"
        category : str, optional
            Category of the loaded file., by default "in_situ"
        unit_row_index : int, optional
            Index of the row with the units, None if there's no unit row., by default 1
        delim_whitespace : bool, optional
            Whether to use whitespace as delimiters., by default True
        verbose : int, optional
            Controls the verbose, by default 1

        Examples
        --------
        Loading from a file:
        >>> filepath = "path/to/file"
        >>> reader = Reader(filepath, providers="providers_column_name")

        Getting the storer:
        >>> storer = reader.get_storer()
        """
        self._verbose = verbose

        raw_df, unit_row = self._read(filepath, unit_row_index, delim_whitespace)
        mandatory_vars = {
            providers_column_label: "provider",
            expocode_column_label: "expocode",
            date_column_label: "date",
            year_column_label: "year",
            month_column_label: "month",
            day_column_label: "day",
            hour_column_label: "hour",
            latitude_column_label: "latitude",
            longitude_column_label: "longitude",
            depth_column_label: "depth",
        }
        self._category = category
        if providers_column_label is not None:
            self._providers = raw_df[providers_column_label].unique().tolist()
        else:
            self._providers = ["????"]
        self._data = self._add_date_columns(
            raw_df,
            year_column_label,
            month_column_label,
            day_column_label,
            date_column_label,
        )
        self._variables = self._get_variables(raw_df, unit_row, mandatory_vars)

    def _read(
        self,
        filepath: Path,
        unit_row_index: int,
        delim_whitespace: bool,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Read the filepath and extract the unit row.

        Parameters
        ----------
        filepath : Path
            Path to the file to read.
        unit_row_index : int
            Index of the row with the units, None if there's no unit row.
        delim_whitespace : bool
            Whether to use whitespace as delimiters.

        Returns
        -------
        tuple[pd.DataFrame, pd.DataFrame]
            Dataframe, unit row
        """
        if unit_row_index is None:
            skiprows = None
            unit_row = None
        else:
            skiprows = [unit_row_index]
            unit_row = pd.read_csv(
                filepath,
                delim_whitespace=delim_whitespace,
                skiprows=lambda x: x not in [*skiprows, 0],
            )
        if self._verbose > 0:
            print(f"Reading data from {filepath}")
        raw_df = pd.read_csv(
            filepath,
            delim_whitespace=delim_whitespace,
            skiprows=skiprows,
        )
        return raw_df, unit_row

    def _get_variables(
        self,
        raw_df: pd.DataFrame,
        unit_row: pd.DataFrame,
        mandatory_vars: dict,
    ) -> "VariablesStorer":
        """Parse variables from the csv data.

        Parameters
        ----------
        raw_df : pd.DataFrame
            Dataframe to parse.
        unit_row : pd.DataFrame
            Unit row to use as reference for variables' units.
        mandatory_vars: dict
            Mapping between column name and parameter for mandatory variables.

        Returns
        -------
        VariablesStorer
            Collection of variables.
        """
        variables = {}
        for column in raw_df.columns:
            if unit_row is None or column not in unit_row.columns:
                unit = "[]"
            else:
                unit = unit_row[column].values[0]

            var = ParsedVar(
                name=column.upper(),
                unit=unit,
                var_type=raw_df.dtypes[column].name,
            )
            if column in mandatory_vars:
                variables[mandatory_vars[column]] = var
            else:
                variables[column.lower()] = var
        for param in mandatory_vars.values():
            if param not in variables.keys():
                variables[param] = None
        return VariablesStorer(**variables)

    def _make_date_column(
        self,
        raw_df: pd.DataFrame,
        year_col: str,
        month_col: str,
        day_col: str,
    ) -> pd.Series:
        """Make date column (datetime) from year, month, day columns if existing.

        Parameters
        ----------
        raw_df : pd.DataFrame
            Dataframe
        year_col: str
            Year column name.
        month_col: str
            Month column name.
        day_col: str
            Day column name.

        Returns
        -------
        pd.Series
            Date column.
        """
        return pd.to_datetime(raw_df[[year_col, month_col, day_col]])

    def _add_date_columns(
        self,
        raw_df: pd.DataFrame,
        year_col: str,
        month_col: str,
        day_col: str,
        date_col: str,
    ) -> pd.DataFrame:
        """Add missing columns to the dataframe.

        Parameters
        ----------
        raw_df : pd.DataFrame
            Dataframe to modify
        year_col: str
            Year column name.
        month_col: str
            Month column name.
        day_col: str
            Day column name.
        date_col: str
            Date column name.

        Returns
        -------
        pd.DataFrame
            Dataframe with new columns
        """
        if date_col in raw_df.columns:
            return raw_df
        missing_col = self._make_date_column(raw_df, year_col, month_col, day_col)
        raw_df.insert(0, date_col, missing_col)
        return raw_df

    def get_storer(self) -> "Storer":
        """Return the Storer storing the data loaded.

        Returns
        -------
        Storer
            Contains the data from the csv.
        """
        return Storer(
            data=self._data,
            category=self._category,
            providers=self._providers,
            variables=self._variables,
            verbose=self._verbose,
        )
