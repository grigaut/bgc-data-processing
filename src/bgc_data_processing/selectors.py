"""Data selectors objects."""

from abc import ABC, abstractmethod

import numpy as np
import pandas as pd
from abfile import ABFileGrid
from sklearn.neighbors import NearestNeighbors


class BaseSelector(ABC):
    """Base Class for selectors.

    Parameters
    ----------
    reference : pd.DataFrame
        Reference data.
    reference_lat_field : str
        Name of the latitude column in reference.
    reference_lon_field : str
        Name of the longitude column in reference.
    """

    def __init__(
        self,
        reference: pd.DataFrame,
        reference_lat_field: str,
        reference_lon_field: str,
    ) -> None:

        self.reference = reference
        self.ref_lat = reference_lat_field
        self.ref_lon = reference_lon_field

    @abstractmethod
    def select_closest(self, lat: pd.Series, lon: pd.Series) -> np.ndarray:
        """Select closest points.

        Parameters
        ----------
        lat : pd.Series
            Latitude Series to find the closest of.
        lon : pd.Series
            Longitude Series to find the closest of.

        Returns
        -------
        np.ndarray
            Index of closest samples.
        """

    @abstractmethod
    def select_from_abfile(
        self,
        grid_abfile_basename: str,
        lat_field: str,
        lon_field: str,
    ) -> np.ndarray:
        """Select closest points in an abfile.

        Parameters
        ----------
        grid_abfile_basename: str
            Basename of the gridfile.
        lat_field: str
            Name of the latitude field.
        lon_field: str
            Name of the longitude field.

        Returns
        -------
        np.ndarray
            2D mask to indicate data to keep.
        """


class NearestNeighborSelector(BaseSelector):
    """Closest point selection using sklearn's nearest neighbors.

    Parameters
    ----------
    reference : pd.DataFrame
        Reference data.
    reference_lat_field : str
        Name of the latitude column in reference.
    reference_lon_field : str
        Name of the longitude column in reference.
    **kwargs:
        Additional arhuments ot pass to NearestNeighbors
    """

    def __init__(
        self,
        reference: pd.DataFrame,
        reference_lat_field: str,
        reference_lon_field: str,
        **kwargs,
    ) -> None:

        super().__init__(reference, reference_lat_field, reference_lon_field)
        self.model_kwargs = kwargs
        self.model_kwargs["n_neighbors"] = 1

    def select_from_abfile(
        self,
        grid_abfile_basename: str,
        lat_field: str,
        lon_field: str,
    ) -> np.ndarray:
        """Select closest points in an abfile.

        Parameters
        ----------
        grid_abfile_basename: str
            Basename of the gridfile.
        lat_field: str
            Name of the latitude field.
        lon_field: str
            Name of the longitude field.

        Returns
        -------
        np.ndarray
            2D mask to indicate data to keep.
        """
        grid_file = ABFileGrid(grid_abfile_basename, "r")
        lat = self.read_raw_field(grid_file, lat_field)
        lon = self.read_raw_field(grid_file, lon_field)
        y_coords, x_coords = np.meshgrid(range(lat.shape[1]), range(lat.shape[0]))
        x_coords_series = pd.Series(x_coords.flatten())
        y_coords_series = pd.Series(y_coords.flatten())
        lat_series = pd.Series(lat.flatten(), name=self.ref_lat)
        lon_series = pd.Series(lon.flatten(), name=self.ref_lon)
        index = self.select_closest(lat=lat_series, lon=lon_series)
        selected_xs = x_coords_series.loc[index]
        selected_ys = y_coords_series.loc[index]
        to_keep = np.full(shape=lat.shape, fill_value=False)
        to_keep[selected_xs, selected_ys] = True
        return to_keep

    def read_raw_field(self, file: ABFileGrid, field_name: str) -> np.ndarray:
        """Read a grid file field.

        Parameters
        ----------
        file : ABFileGrid
            File to read the field of.
        field_name : str
            Name of the field to read.

        Returns
        -------
        np.ndarray
            Data from the file.
        """
        mask_2d: np.ma.masked_array = file.read_field(field_name)
        return mask_2d.filled(np.nan)

    def select_closest(
        self,
        lat: pd.Series,
        lon: pd.Series,
    ) -> np.ndarray:
        """Select closest points.

        Parameters
        ----------
        lat : pd.Series
            Latitude Series to find the closest of.
        lon : pd.Series
            Longitude Series to find the closest of.

        Returns
        -------
        np.ndarray
            Index of closest samples.
        """
        model = NearestNeighbors(**self.model_kwargs)
        model.fit(X=pd.concat([lat, lon], axis=1))
        closest = model.kneighbors(
            self.reference,
            return_distance=False,
        )
        return closest.flatten()
