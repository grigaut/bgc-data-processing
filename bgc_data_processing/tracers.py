from typing import TYPE_CHECKING, Callable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from cartopy import crs, feature

from bgc_data_processing.base import BasePlot
from bgc_data_processing.data_classes import Storer

if TYPE_CHECKING:
    from bgc_data_processing.variables import VariablesStorer


class GeoMesher(BasePlot):
    """Base class for tracing on earthmaps.

    Parameters
    ----------
    data : pd.DataFrame
        Data to use when plotting.
    """

    _grouping_functions = {
        # "all": lambda x: x.apply(np.array),
        "top": lambda x: x.first(),
        "bottom": lambda x: x.last(),
    }

    def __init__(
        self,
        storer: "Storer",
    ) -> None:
        super().__init__(storer=storer)
        self._data = storer.data.sort_values(
            self._variables.labels["DEPH"], ascending=False
        )
        self._grouping_columns = self._get_grouping_columns(self._variables)

    def _get_grouping_columns(self, variables: "VariablesStorer") -> list:
        """Returns a list of columns to use when grouping the data.

        Parameters
        ----------
        variables : VariablesStorer
            Dtaa variables.

        Returns
        -------
        list
            Columns to use for grouping.
        """
        columns = []
        for var_name in [
            "PROVIDER",
            "EXPOCODE",
            "YEAR",
            "MONTH",
            "DAY",
            "LONGITUDE",
            "LATITUDE",
        ]:
            if var_name in variables.keys():
                columns.append(variables.labels[var_name])
        return columns

    def _group(
        self,
        var_key: str,
        lat_key: str,
        lon_key: str,
        how: str,
    ) -> pd.DataFrame:
        """First grouping, to aggregate data points from the same measuring point.

        Parameters
        ----------
        var_key : str
            Variable to keep after grouping, it can't be one of the grouping variables.
        lat_key : str
            Latitude variable name.
        lon_key : str
            Longitude variable name.
        how : str
            Grouping function key to use with self._grouping_functions.

        Returns
        -------
        pd.DataFrame
            Grouped dataframe with 3 columns: latitude, longitude and variable to keep.
            Column names are the same as in self._data.
        """
        group = self._data.groupby(self._grouping_columns)
        var_series: pd.Series = self._grouping_functions[how](group[var_key])
        var_series.name = var_key
        return var_series.reset_index().filter([lat_key, lon_key, var_key])

    def _geo_linspace(
        self,
        column: pd.Series,
        bin_size: float,
        cut_name: str,
    ) -> tuple[pd.Series, np.ndarray]:
        """Generates evenly spaced points to use when creating the meshgrid.
        Also performs a cut on the dataframe column to bin the values.

        Parameters
        ----------
        column : pd.Series
            Column to base point generation on and to bin.
        bin_size : float
            Bin size in degree.
        cut_name : str
            Name to give to the cut.

        Returns
        -------
        tuple[pd.Series, np.ndarray]
            Bins number for the column, value for each bin.
        """
        min_val, max_val = column.min(), column.max()
        bin_nb = int((max_val - min_val) / bin_size) + 1
        bins = np.linspace(min_val, max_val, bin_nb)
        intervals_mid = (bins[1:] + bins[:-1]) / 2
        cut: pd.Series = pd.cut(column, bins=bins, include_lowest=True, labels=False)
        cut.name = cut_name
        return cut, intervals_mid

    def mesh(
        self,
        label: str,
        bins_size: float | tuple[float, float],
        group_aggr: str,
        pivot_aggr: Callable,
    ) -> tuple[np.ndarray]:
        """Returns the X,Y and Z 2D array to use with plt.pcolormesh.

        Parameters
        ----------
        label : str
            Name of the column with the variable to mesh.
        bins_size : float | tuple[float, float], optional
            Bins size, if tuple, first component if for latitude, second is for longitude.
            If float or int, size is applied for both latitude and longitude.
            Unit is supposed to be degree
        group_aggr : str, optional
            Name of the function to use to aggregate data when group by similar measuring point.
        pivot_aggr : Callable
            Function to aggregate when pivotting data.
        Returns
        -------
        tuple[np.ndarray]
            Longitude values, Latitude values and variable values. Each one is 2 dimensionnal.
        """
        lat = self._variables.labels["LATITUDE"]
        lon = self._variables.labels["LONGITUDE"]
        df = self._group(
            var_key=label,
            lat_key=lat,
            lon_key=lon,
            how=group_aggr,
        )
        if isinstance(bins_size, tuple):
            lat_bins_size = bins_size[0]
            lon_bins_size = bins_size[1]
        else:
            lat_bins_size = bins_size
            lon_bins_size = bins_size

        lat_cut, lat_points = self._geo_linspace(
            column=df[lat],
            bin_size=lat_bins_size,
            cut_name="lat_cut",
        )
        lon_cut, lon_points = self._geo_linspace(
            column=df[lon],
            bin_size=lon_bins_size,
            cut_name="lon_cut",
        )
        # Bining
        bins_concat = pd.concat([lat_cut, lon_cut, df[label]], axis=1)
        # Meshing
        lons, lats = np.meshgrid(lon_points, lat_points)
        vals = bins_concat.pivot_table(
            values=label,
            index="lat_cut",
            columns="lon_cut",
            aggfunc=pivot_aggr,
        )
        all_indexes = [index for index in range(lons.shape[0])]
        all_columns = [colum for colum in range(lats.shape[1])]
        vals: pd.DataFrame = vals.reindex(all_indexes, axis=0)
        vals: pd.DataFrame = vals.reindex(all_columns, axis=1)

        return lons, lats, vals.values

    def plot(
        self,
        variable_name: str,
        bins_size: float | tuple[float, float] = 0.5,
        group_aggr: str = "top",
        pivot_aggr: Callable = np.mean,
    ) -> None:
        """Plots the colormesh for the given variable.

        Parameters
        ----------
        variable_name : str
            Name of the variable to plot.
        bins_size : float | tuple[float, float], optional
            Bins size, if tuple, first component if for latitude, second is for longitude.
            If float or int, size is applied for both latitude and longitude.
            Unit is supposed to be degree., by default 0.5
        group_aggr : str, optional
            Name of the function to use to aggregate data when group by similar measuring point.
            , by default "top"
        pivot_aggr : Callable
            Function to aggregate when pivotting data., by default np.mean
        """
        X1, Y1, Z1 = self.mesh(
            label=self._variables.labels[variable_name],
            bins_size=bins_size,
            group_aggr=group_aggr,
            pivot_aggr=pivot_aggr,
        )
        fig = plt.figure(figsize=[10, 10])
        provs = ", ".join(self._storer.providers)
        title = f"{variable_name} - {provs} ({self._storer.category})"
        if isinstance(bins_size, tuple):
            lat, lon = bins_size[0], bins_size[1]
        else:
            lat, lon = bins_size, bins_size
        subtitle = f"{lat}° x {lon}° grid (lat x lon)"
        fig.suptitle(f"{title}\n{subtitle}")
        ax = plt.subplot(1, 1, 1, projection=crs.Orthographic(0, 90))
        fig.subplots_adjust(bottom=0.05, top=0.95, left=0.04, right=0.95, wspace=0.02)
        ax.gridlines()
        ax.add_feature(feature.LAND, zorder=4)
        ax.add_feature(feature.OCEAN, zorder=1)
        ax.set_extent([-40, 40, 50, 89], crs.PlateCarree())
        cbar = ax.pcolor(X1, Y1, Z1, transform=crs.PlateCarree())
        plt.colorbar(
            cbar,
            label=f"{variable_name} levels {self._variables[variable_name].unit}",
        )
        plt.show()
        plt.close()

    @classmethod
    def from_files(
        cls,
        filepath: str | list,
        providers: str | list = "PROVIDER",
        category: str = "in_situ",
        unit_row_index: int = 1,
        delim_whitespace: bool = True,
        verbose: int = 1,
    ) -> "GeoMesher":
        """Builds GeoMesher reading data from csv or txt files.

        Parameters
        ----------
        filepath : str
            Path to the file to read.
        providers : str | list, optional
            Provider column in the dataframe (if str) or value to attribute to self._providers (if list).
            , by default "PROVIDER"
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
        GeoMesher
            geomesher from the aggregation of the data from all the files
        """
        storer = Storer.from_files(
            filepath=filepath,
            providers=providers,
            category=category,
            unit_row_index=unit_row_index,
            delim_whitespace=delim_whitespace,
            verbose=verbose,
        )
        return cls(storer=storer)