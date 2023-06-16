"""Extract data from storers with given conditions."""

from datetime import datetime
from typing import TYPE_CHECKING, Any

import geopandas as gpd
import numpy as np
import pandas as pd

from bgc_data_processing.data_structures.storers import Storer

if TYPE_CHECKING:
    from collections.abc import Callable

    from shapely import Polygon


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
