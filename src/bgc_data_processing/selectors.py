"""Data selectors objects."""


import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors

from bgc_data_processing.abfiles_tools import ABFileLoader, SelectiveABFileLoader
from bgc_data_processing.data_classes import Constraints, Storer


class NearestNeighborStrategy:
    """Implement a closest point search using NearestNeighbor algorithm.

    Parameters
    ----------
    **model_kwargs:
        Additional arguments to pass to sklearn.neighbors.NearestNeighbors.
        The value of 'n_neighbors' while be overridden by 1.
    """

    def __init__(self, **model_kwargs) -> None:
        model_kwargs["n_neighbors"] = 1
        self.model_kwargs = model_kwargs

    def get_closest_indexes(
        self,
        simulations_lat_lon: pd.DataFrame,
        observations_lat_lon: pd.DataFrame,
    ) -> pd.Series:
        """Find closest simulation point for each observation point.

        Parameters
        ----------
        simulations_lat_lon : pd.DataFrame
            DataFrame with longitude and latitude for each simulations point.
        observations_lat_lon : pd.DataFrame
            DataFrame with longitude and latitude for each observation point.

        Returns
        -------
        pd.Series
            Index of closest point for every observation point.
        """
        model = NearestNeighbors(**self.model_kwargs)
        model.fit(X=simulations_lat_lon)
        closest = model.kneighbors(
            observations_lat_lon,
            return_distance=False,
        )
        return pd.Series(closest.flatten(), index=observations_lat_lon.index)


class Mask:
    """Mask to apply to ABFiles to filter data while loading.

    Parameters
    ----------
    mask_2d : np.ndarray
        2D array to mask layers when loading them.
    index_2d : np.ndarray
        2D array of indexes to use to reindex the filtered array.

    Raises
    ------
    ValueError
        If the mask and the index have a different shape.
    """

    def __init__(self, mask_2d: np.ndarray, index_2d: np.ndarray) -> None:
        if mask_2d.shape != index_2d.shape:
            raise ValueError("Both mask and index must have similar shapes.")
        self.mask = mask_2d
        self._index = pd.Index(index_2d[self.mask].flatten())

    @property
    def index(self) -> pd.Index:
        """Index for masked data reindexing.

        Returns
        -------
        pd.Index
            Data Index.
        """
        return self._index

    def __call__(self, data_2d: np.ndarray, **kwargs) -> pd.Series:
        """Apply mask to 2D data.

        Parameters
        ----------
        data_2d : np.ndarray
            Data to apply the mask to.
        **kwargs:
            Additional parameters to pass to pd.Series.
            The value of 'index' while be overridden by self._index.

        Returns
        -------
        pd.Series
            Masked data as a pd.Series with self._index as index.
        """
        kwargs["index"] = self._index
        return pd.Series(data_2d[self.mask].flatten(), **kwargs)


class Match:
    """Match between observation indexes and simulations indexes.

    Parameters
    ----------
    obs_closests_indexes : pd.Series
        Closest simulated point index Series.
        The index is supposed to correspond to observations' index.
    """

    index_simulated: str = "sim_index"
    index_observed: str = "obs_index"
    index_loaded: str = "load_index"

    def __init__(self, obs_closests_indexes: pd.Series) -> None:

        index_link = obs_closests_indexes.to_frame(name=self.index_simulated)
        index_link.index.name = self.index_observed
        index_link.reset_index(inplace=True)
        self.index_link = index_link

    def match(self, loaded_df: pd.DataFrame) -> pd.DataFrame:
        """Transform the DataFrame index to link it to observations' index.

        Parameters
        ----------
        loaded_df : pd.DataFrame
            DataFrame to change the index of.

        Returns
        -------
        pd.DataFrame
            Copy of loaded_df with a modified index, which correspond to
            observations' index values.
        """
        loaded_index = pd.Series(loaded_df.index, name=self.index_simulated).to_frame()
        loaded_index.index.name = self.index_loaded
        loaded_index.reset_index(inplace=True)
        loaded_copy = loaded_df.copy()
        loaded_copy.index = loaded_index.index
        merge = pd.merge(
            left=loaded_index,
            right=self.index_link,
            left_on=self.index_simulated,
            right_on=self.index_simulated,
            how="left",
        )
        reshaped = loaded_copy.loc[merge[self.index_loaded], :]
        reshaped.index = merge[self.index_observed].values
        return reshaped


class Selector:
    """Load closest datapoints from a reference dataframe.

    Parameters
    ----------
    reference : pd.DataFrame
        Reference Dataframe (observations).
    strategy : NearestNeighborStrategy
        Closer point finding strategy.
    loader : ABFileLoader
        Loader.
    """

    def __init__(
        self,
        reference: pd.DataFrame,
        strategy: NearestNeighborStrategy,
        loader: "ABFileLoader",
    ) -> None:
        self.reference = reference
        self.loader = loader
        self.strategy = strategy
        self.grid = self.loader.grid_file

    def get_coord(self, var_name: str) -> pd.Series:
        """Get a coordinate field from loader.grid_file.

        Parameters
        ----------
        var_name : str
            Name of the variable to retrieve.

        Returns
        -------
        pd.Series
            Loaded variable as pd.Series.

        Raises
        ------
        ValueError
            If the variable dosn't exist in the grid file.
        """
        var = self.loader.variables.get(var_name)
        found = False
        for alias, _, _ in var.aliases:
            if alias in self.grid.fieldnames:
                mask_2d: np.ma.masked_array = self.grid.read_field(alias)
                found = True
                break
        if not found:
            raise ValueError
        value = mask_2d.filled(np.nan)
        return pd.Series(value.flatten(), name=var.label)

    def get_x_y_indexes(self) -> tuple[pd.Series, pd.Series]:
        """Get x and y indexes.

        Returns
        -------
        tuple[pd.Series, pd.Series]
            X indexes series, Y indexes series.
        """
        y_coords, x_coords = np.meshgrid(range(self.grid.idm), range(self.grid.jdm))
        x_coords_series = pd.Series(x_coords.flatten())
        y_coords_series = pd.Series(y_coords.flatten())
        return x_coords_series, y_coords_series

    def select(
        self,
    ) -> tuple["Mask", "Match"]:
        """Select closest points in an abfile using self.strategy.

        Returns
        -------
        tuple[Mask, Match]
            Mask to use for loader, Match to link observations to simulations.
        """
        lat_series = self.get_coord(self.loader.variables.latitude_var_name)
        lon_series = self.get_coord(self.loader.variables.longitude_var_name)
        sims = pd.concat([lat_series, lon_series], axis=1)
        x_coords_series, y_coords_series = self.get_x_y_indexes()
        index = self.strategy.get_closest_indexes(
            simulations_lat_lon=sims,
            observations_lat_lon=self.reference[sims.columns],
        )
        selected_xs = x_coords_series.loc[index.values]
        selected_ys = y_coords_series.loc[index.values]
        to_keep = np.full(shape=(self.grid.jdm, self.grid.idm), fill_value=False)
        to_keep[selected_xs, selected_ys] = True
        indexes = np.array(range(self.grid.jdm * self.grid.idm))
        indexes_2d = indexes.reshape((self.grid.jdm, self.grid.idm))
        return Mask(to_keep, indexes_2d), Match(index)

    def __call__(
        self,
        constraints: "Constraints" = Constraints(),
        exclude: list[str] = [],
    ) -> "Storer":
        """Load all files for the loader.

        Parameters
        ----------
        constraints : Constraints, optional
            Constraints slicer., by default Constraints()
        exclude : list, optional
            Files not to load., by default []

        Returns
        -------
        Storer
            Storer for the loaded data.
        """
        mask, match = self.select()
        loader = SelectiveABFileLoader.from_abloader(loader=self.loader, mask=mask)
        sims = loader(constraints=constraints, exclude=exclude)
        return Storer(
            data=match.match(sims.data),
            category=sims.category,
            providers=sims.providers,
            variables=sims.variables,
            verbose=sims.verbose,
        )
