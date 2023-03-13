"""Plotting objects."""


import warnings
from typing import TYPE_CHECKING, Callable, Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from cartopy import crs, feature

from bgc_data_processing.base import BasePlot
from bgc_data_processing.data_classes import Storer

if TYPE_CHECKING:
    from matplotlib.figure import Figure

    from bgc_data_processing.variables import VariablesStorer


class MeshPlotter(BasePlot):
    """Base class for tracing on earthmaps.

    Parameters
    ----------
    storer : Storer
        Data Storer containing data to plot.
    """

    depth_aggr = {
        "top": lambda x: x.first(),
        "bottom": lambda x: x.last(),
        "count": lambda x: x.count(),
    }
    bin_aggr = {
        "mean": np.mean,
        "count": lambda x: x.count(),
        "sum": np.sum,
    }

    def __init__(
        self,
        storer: "Storer",
    ) -> None:
        super().__init__(storer=storer)
        self._data = storer.data.sort_values(
            self._variables.get("DEPH").label, ascending=False
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
        how: str | Callable,
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
        how : str | Callable
            Grouping function key to use with self.depth_aggr or
            Callable function to use to group.

        Returns
        -------
        pd.DataFrame
            Grouped dataframe with 3 columns: latitude, longitude and variable to keep.
            Column names are the same as in self._data.
        """
        group = self._data.groupby(self._grouping_columns)
        if isinstance(how, str):
            group_fn = self.depth_aggr[how]
        else:
            group_fn = how
        var_series: pd.Series = group_fn(group[var_key])
        var_series.name = var_key
        return var_series.reset_index().filter([lat_key, lon_key, var_key])

    def _geo_linspace(
        self,
        column: pd.Series,
        bin_size: float,
        cut_name: str,
    ) -> tuple[pd.Series, np.ndarray]:
        """Generates evenly spaced points to use when creating the meshgrid. \
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
        bin_nb = int((max_val - min_val + 2 * bin_size) / bin_size)
        bins = np.linspace(min_val - 1, max_val + 1, bin_nb)
        if bin_nb == 1:
            intervals_mid = bins
            intervals_mid = (bins[1:] + bins[:-1]) / 2
        else:
            intervals_mid = (bins[1:] + bins[:-1]) / 2

        cut: pd.Series = pd.cut(column, bins=bins, include_lowest=True, labels=False)
        cut.name = cut_name
        return cut, intervals_mid

    def mesh(
        self,
        label: str,
        bins_size: float | tuple[float, float],
        depth_aggr: str | Callable,
        bin_aggr: str | Callable,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Returns the X,Y and Z 2D array to use with plt.pcolormesh.

        Parameters
        ----------
        label : str
            Name of the column with the variable to mesh.
        bins_size : float | tuple[float, float], optional
            Bins size, if tuple: first for latitude, second for longitude.
            If float or int, size is applied for both latitude and longitude.
            Unit is supposed to be degree
        depth_aggr : str | Callable
            Name of the function to use to aggregate data when group by
            similar measuring point or callable function to use to aggregate.
        bin_aggr : str | Callable
            Name of the function to aggregate when pivotting data or
            callable function to use to aggregate.

        Returns
        -------
        tuple[np.ndarray]
            Longitude values, Latitude values and variable values.
            Each one is 2 dimensionnal.
        """
        lat = self._variables.get("LATITUDE").label
        lon = self._variables.get("LONGITUDE").label
        df = self._group(
            var_key=label,
            lat_key=lat,
            lon_key=lon,
            how=depth_aggr,
        )
        if isinstance(bins_size, Iterable):
            lat_bins_size = bins_size[0]
            lon_bins_size = bins_size[1]
        else:
            lat_bins_size = bins_size
            lon_bins_size = bins_size
        if self._verbose > 2:
            print("\t\tCreating latitude array")
        lat_cut, lat_points = self._geo_linspace(
            column=df[lat],
            bin_size=lat_bins_size,
            cut_name="lat_cut",
        )
        if self._verbose > 2:
            print("\t\tCreating longitude array")
        lon_cut, lon_points = self._geo_linspace(
            column=df[lon],
            bin_size=lon_bins_size,
            cut_name="lon_cut",
        )
        # Bining
        bins_concat = pd.concat([lat_cut, lon_cut, df[label]], axis=1)
        # Meshing
        lons, lats = np.meshgrid(lon_points, lat_points)
        if isinstance(bin_aggr, str):
            aggfunc = self.bin_aggr[bin_aggr]
        else:
            aggfunc = bin_aggr
        if self._verbose > 2:
            print("\t\tPivotting data to 2D table")
        vals = bins_concat.pivot_table(
            values=label,
            index="lat_cut",
            columns="lon_cut",
            aggfunc=aggfunc,
        )
        all_indexes = [index for index in range(lons.shape[0])]
        all_columns = [colum for colum in range(lats.shape[1])]
        vals: pd.DataFrame = vals.reindex(all_indexes, axis=0)
        vals: pd.DataFrame = vals.reindex(all_columns, axis=1)

        return lons, lats, vals.values

    def _build_plot(
        self,
        variable_name: str,
        bins_size: float | tuple[float, float],
        depth_aggr: str | Callable,
        bin_aggr: Callable | Callable,
        extent: tuple | list,
        **kwargs,
    ) -> "Figure":
        """Plots the colormesh for the given variable.

        Parameters
        ----------
        variable_name : str
            Name of the variable to plot.
        bins_size : float | tuple[float, float]
            Bins size, if tuple, first is latitude, second is longitude.
            If float or int, size is applied for both latitude and longitude.
            Unit is supposed to be degree.
        depth_aggr : str | Callable
            Name of the function to use to aggregate data when group
            by similar measuring point (from self.depth_aggr),
             or callable function to use to aggregate.
        bin_aggr : str | Callable
            Name of the aggregation function to use when pivotting data
            (from self.bin_aggr),
            or callable function to use to aggregate.
        extent : tuple | list
            Boundaries of the map.
        **kwargs
            Additional arguments to pass to plt.pcolor.
        """
        if self._verbose > 1:
            print(f"\tMeshing {variable_name} data")
        X1, Y1, Z1 = self.mesh(
            label=self._variables.get(variable_name).label,
            bins_size=bins_size,
            depth_aggr=depth_aggr,
            bin_aggr=bin_aggr,
        )
        if X1.shape == (1, 1) or Y1.shape == (1, 1) or Z1.shape == (1, 1):
            warnings.warn(
                "Not enough data to display, try decreasing the bin size"
                " or representing more data sources"
            )
        if self._verbose > 1:
            print("\tCreating figure")
        fig = plt.figure(figsize=[10, 10])
        provs = ", ".join(self._storer.providers)
        suptitle = f"{variable_name} - {provs} ({self._storer.category})"
        plt.suptitle(suptitle)
        if isinstance(bins_size, Iterable):
            lat, lon = bins_size[0], bins_size[1]
        else:
            lat, lon = bins_size, bins_size
        ax = plt.subplot(1, 1, 1, projection=crs.Orthographic(0, 90))
        fig.subplots_adjust(bottom=0.05, top=0.95, left=0.04, right=0.95, wspace=0.02)
        ax.gridlines(draw_labels=True)
        ax.add_feature(feature.LAND, zorder=4)
        ax.add_feature(feature.OCEAN, zorder=1)
        ax.set_extent(extent, crs.PlateCarree())
        cbar = ax.pcolor(
            X1,
            Y1,
            Z1,
            transform=crs.PlateCarree(),
            **kwargs,
        )
        if bin_aggr == "count":
            label = f"{variable_name} data points count"
        elif depth_aggr == "count" and bin_aggr == "sum":
            label = f"{variable_name} total data points count"
        else:
            unit = self._variables[variable_name].unit
            label = f"{bin_aggr} {variable_name} levels {unit}"
        fig.colorbar(cbar, label=label, shrink=0.75)
        title = f"{lat}° x {lon}° grid (lat x lon)"
        plt.title(title)
        return fig

    def save_fig(
        self,
        save_path: str,
        variable_name: str,
        bins_size: float | tuple[float, float] = 0.5,
        depth_aggr: str | Callable = "top",
        bin_aggr: Callable | Callable = "count",
        title: str = None,
        suptitle: str = None,
        extent: tuple | list = (-40, 40, 50, 89),
        **kwargs,
    ) -> None:
        """Plots the colormesh for the given variable.

        Parameters
        ----------
        save_path: str
            Path to save the figure at.
        variable_name : str
            Name of the variable to plot.
        bins_size : float | tuple[float, float], optional
            Bins size, if tuple, first for latitude, second for longitude.
            If float or int, size is applied for both latitude and longitude.
            Unit is supposed to be degree., by default 0.5
        depth_aggr : str | Callable, optional
            Name of the function to use to aggregate data when group
            by similar measuring point (from self.depth_aggr),
            or callable function to use to aggregate., by default "top"
        bin_aggr : str | Callable, optional
            Name of the aggregation function to use to pivot data (from self.bin_aggr),
            or callable function to use to aggregate., by default "count"
        title: str, optional
            Title for the figure, if set to None, automatically created.
            , by default None.
        suptitle: str, optional
            Suptitle for the figure, if set to None, automatically created.
            , by default None.
        extent : tuple | list, optional
            Boundaries of the map., by default (-40, 40, 50, 89).
        **kwargs
            Additional arguments to pass to plt.pcolor.
        """
        _ = self._build_plot(
            variable_name=variable_name,
            bins_size=bins_size,
            depth_aggr=depth_aggr,
            bin_aggr=bin_aggr,
            extent=extent,
            **kwargs,
        )
        if title is not None:
            plt.title(title)
        if suptitle is not None:
            plt.suptitle(suptitle)
        plt.savefig(save_path)

    def plot(
        self,
        variable_name: str,
        bins_size: float | tuple[float, float] = 0.5,
        depth_aggr: str | Callable = "top",
        bin_aggr: Callable | Callable = "count",
        title: str = None,
        suptitle: str = None,
        extent: tuple | list = (-40, 40, 50, 89),
        **kwargs,
    ) -> None:
        """Plots the colormesh for the given variable.

        Parameters
        ----------
        variable_name : str
            Name of the variable to plot.
        bins_size : float | tuple[float, float], optional
            Bins size, if tuple, first component if for latitude, second for longitude.
            If float or int, size is applied for both latitude and longitude.
            Unit is supposed to be degree., by default 0.5
        depth_aggr : str | Callable, optional
            Name of the function to use to aggregate data when group
            by similar measuring point (from self.depth_aggr),
            or callable function to use to aggregate., by default "top"
        bin_aggr : str | Callable, optional
            Name of the aggregation function to use to pivot data (from self.bin_aggr),
            or callable function to use to aggregate., by default "count"
        title: str, optional
            Title for the figure, if set to None, automatically created.
            , by default None.
        suptitle: str, optional
            Suptitle for the figure, if set to None, automatically created.
            , by default None.
        extent : tuple | list, optional
            Boundaries of the map., by default (-40, 40, 50, 89)
        **kwargs
            Additional arguments to pass to plt.pcolor.
        """
        _ = self._build_plot(
            variable_name=variable_name,
            bins_size=bins_size,
            depth_aggr=depth_aggr,
            bin_aggr=bin_aggr,
            extent=extent,
            **kwargs,
        )

        if title is not None:
            plt.title(title)
        if suptitle is not None:
            plt.suptitle(suptitle)
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
    ) -> "MeshPlotter":
        """Builds a MeshPlotter reading data from csv or txt files.

        Parameters
        ----------
        filepath : str
            Path to the file to read.
        providers : str | list, optional
            Provider column in the dataframe (if str) or
            value to attribute to self._providers (if list).
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
        MeshPlotter
            mesh from the aggregation of the data from all the files

        Examples
        --------
        Loading from a single file:
        >>> filepath = "path/to/file"
        >>> mesh = MeshPlotter.from_files(filepath, providers="providers_column_name")

        Loading from multiple files:
        >>> filepaths = [
        ...     "path/to/file1",
        ...     "path/to/file2",
        ... ]
        >>> mesh = MeshPlotter.from_files(filepaths, providers="providers_column_name")

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


class BinEvolutionPlotter(BasePlot):
    """Class to plot the evolution of data on a given area.

    Parameters
    ----------
    storer : Storer
        Storer to map data of.
    """

    def __init__(self, storer: "Storer") -> None:
        super().__init__(storer)

    def _build_plot(
        self,
        variable_name: str,
        latitude_ref: int | float,
        longitude_ref: int | float,
        bins_size: int | float | Iterable[int | float],
        **kwargs,
    ) -> "Figure":
        """Build the plot to display or save.

        Parameters
        ----------
        variable_name : str
            Name of the variable to plot.
        latitude_ref : int | float
            Latitude to use for the center of the area.
        longitude_ref : int | float
            Longitude to use for the center of the area.
        bins_size : int | float | Iterable[int  |  float]
            Area dimension, first component is latitude and second is longitude.
        **kwargs
            Additional arguments to pass to plt.pcolor.

        Returns
        -------
        Figure
            Data evolution figure on the given area.

        Raises
        ------
        ValueError
            If there is not enough data to create a figure.
        """
        depth_col = self._variables.get("DEPH").label
        lat_col = self._variables.get("LATITUDE").label
        lon_col = self._variables.get("LONGITUDE").label
        date_col = self._variables.get("DATE").label
        var_col = self._variables.get(variable_name).label
        if isinstance(bins_size, Iterable):
            lat_bin, lon_bin = bins_size[0], bins_size[1]
        else:
            lat_bin, lon_bin = bins_size, bins_size
        # Bin boundaries
        lat_min = latitude_ref - lat_bin / 2
        lat_max = latitude_ref + lat_bin / 2
        lon_min = longitude_ref - lon_bin / 2
        lon_max = longitude_ref + lon_bin / 2
        # Slice data
        df = self._storer.data[[lat_col, lon_col, depth_col, date_col, var_col]]
        lat_cond = (df[lat_col] >= lat_min) & (df[lat_col] <= lat_max)
        lon_cond = (df[lon_col] >= lon_min) & (df[lon_col] <= lon_max)
        df_slice = df.loc[lat_cond & lon_cond, :].copy(True)
        if df_slice.empty:
            raise ValueError("Not enough data at this location to build a figure.")
        df_slice[var_col] = 1
        df_slice[depth_col] = (df_slice[depth_col] / 100).round() * 100
        # Pivot
        pivotted = df_slice.pivot_table(
            values=var_col,
            index=depth_col,
            columns=date_col,
            aggfunc="count",
        )
        # Figure
        fig = plt.figure(figsize=[10, 5])
        ax = plt.subplot(1, 1, 1)
        suptitle = f"Evolution of data around {(latitude_ref, longitude_ref)}"
        plt.suptitle(suptitle)
        X, Y = np.meshgrid(pivotted.columns, pivotted.index)
        # Color mesh
        cbar = ax.pcolor(X, Y, pivotted.values, **kwargs)
        fig.colorbar(cbar, label="Number of data points", shrink=0.75)
        title = f"{lat_bin}° x {lon_bin}° bin"
        plt.title(title)
        return fig

    def plot(
        self,
        variable_name: str,
        latitude_ref: int | float,
        longitude_ref: int | float,
        bins_size: int | float | Iterable[int | float],
        title: str = None,
        suptitle: str = None,
        **kwargs,
    ) -> None:
        """Plot the figure of data density evolution in a givemn area.

        Parameters
        ----------
        variable_name : str
            Name of the variable to plot.
        latitude_ref : int | float
            Latitude to use for the center of the area.
        longitude_ref : int | float
            Longitude to use for the center of the area.
        bins_size : int | float | Iterable[int  |  float]
            Area dimension, first component is latitude and second is longitude.
        title : str, optional
            Specify a title to change from default., by default None
        suptitle : str, optional
            Specify a suptitle to change from default., by default None
        **kwargs
            Additional arguments to pass to plt.pcolor.
        """
        _ = self._build_plot(
            variable_name=variable_name,
            latitude_ref=latitude_ref,
            longitude_ref=longitude_ref,
            bins_size=bins_size,
            **kwargs,
        )

        if title is not None:
            plt.title(title)
        if suptitle is not None:
            plt.suptitle(suptitle)
        plt.show()
        plt.close()

    def save_fig(
        self,
        save_path: str,
        variable_name: str,
        latitude_ref: int | float,
        longitude_ref: int | float,
        bins_size: int | float | Iterable[int | float],
        title: str = None,
        suptitle: str = None,
        **kwargs,
    ) -> None:
        """Save the figure of data density evolution in a givemn area.

        Parameters
        ----------
        save_path : str
            Path to save the output image.
        variable_name : str
            Name of the variable to plot.
        latitude_ref : int | float
            Latitude to use for the center of the area.
        longitude_ref : int | float
            Longitude to use for the center of the area.
        bins_size : int | float | Iterable[int  |  float]
            Area dimension, first component is latitude and second is longitude.
        title : str, optional
            Specify a title to change from default., by default None
        suptitle : str, optional
            Specify a suptitle to change from default., by default None
        **kwargs
            Additional arguments to pass to plt.pcolor.
        """
        _ = self._build_plot(
            variable_name=variable_name,
            latitude_ref=latitude_ref,
            longitude_ref=longitude_ref,
            bins_size=bins_size,
            **kwargs,
        )

        if title is not None:
            plt.title(title)
        if suptitle is not None:
            plt.suptitle(suptitle)
        plt.savefig(save_path)
