"""Plotting objects."""


import warnings
from typing import TYPE_CHECKING, Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from cartopy import crs, feature

from bgc_data_processing.base import BasePlot
from bgc_data_processing.data_classes import Storer
from bgc_data_processing.dateranges import DateRangeGenerator

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

    _lat_bin: int | float = 1
    _lon_bin: int | float = 1
    _depth_density: bool = True

    def __init__(
        self,
        storer: "Storer",
    ) -> None:
        super().__init__(storer=storer)
        depth_var_name = self._variables.depth_var_name
        depth_var_label = self._variables.get(depth_var_name).label
        self._data = storer.data.sort_values(depth_var_label, ascending=False)
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
            self._variables.provider_var_name,
            self._variables.expocode_var_name,
            self._variables.year_var_name,
            self._variables.month_var_name,
            self._variables.day_var_name,
            self._variables.hour_var_name,
            self._variables.latitude_var_name,
            self._variables.longitude_var_name,
        ]:
            if var_name in variables.keys():
                columns.append(variables.get(var_name).label)
        return columns

    def _group(
        self,
        var_key: str,
        lat_key: str,
        lon_key: str,
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
        depth_label = self._variables.get(self._variables.depth_var_name).label
        depth_min_cond = self._data[depth_label] >= self._depth_min
        depth_max_cond = self._data[depth_label] <= self._depth_max
        data = self._data[depth_min_cond & depth_max_cond].copy()
        if var_key == "all":
            data["all"] = 1
        else:
            data[var_key] = (~data[var_key].isna()).astype(int)
        data = data[data[var_key] == 1]
        group = data[self._grouping_columns + [var_key]].groupby(self._grouping_columns)
        if self._depth_density:
            var_series: pd.Series = group.sum()
        else:
            var_series: pd.Series = group.first()
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

    def set_bins_size(
        self,
        bins_size: int | float | Iterable[int | float],
    ) -> None:
        """Set the bin sizes.

        Parameters
        ----------
        bins_size : int | float | Iterable[int  |  float]
            Bins size, if tuple, first for latitude, second for longitude.
            If float or int, size is applied for both latitude and longitude.
            Unit is supposed to be degree.
        """
        if isinstance(bins_size, Iterable):
            self._lat_bin = bins_size[0]
            self._lon_bin = bins_size[1]
        else:
            self._lat_bin = bins_size
            self._lon_bin = bins_size

    def set_density_type(self, consider_depth: bool) -> None:
        """Set the self._depth_density value.

        Parameters
        ----------
        consider_depth : bool
            Whether to consider all value in the water for density mapping.
        """
        self._depth_density = consider_depth

    def _mesh(
        self,
        df: pd.DataFrame,
        label: str,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Returns the X,Y and Z 2D array to use with plt.pcolormesh.

        Parameters
        ----------
        df: pd.DataFrame
            Grouped dataframe to mesh.
        label : str
            Name of the column with the variable to mesh.

        Returns
        -------
        tuple[np.ndarray]
            Longitude values, Latitude values and variable values.
            Each one is 2 dimensionnal.
        """
        lat = self._variables.get(self._variables.latitude_var_name).label
        lon = self._variables.get(self._variables.longitude_var_name).label
        if self._verbose > 2:
            print("\t\tCreating latitude array")
        lat_cut, lat_points = self._geo_linspace(
            column=df[lat],
            bin_size=self._lat_bin,
            cut_name="lat_cut",
        )
        if self._verbose > 2:
            print("\t\tCreating longitude array")
        lon_cut, lon_points = self._geo_linspace(
            column=df[lon],
            bin_size=self._lon_bin,
            cut_name="lon_cut",
        )
        # Bining
        bins_concat = pd.concat([lat_cut, lon_cut, df[label]], axis=1)
        # Meshing
        lons, lats = np.meshgrid(lon_points, lat_points)
        if self._verbose > 2:
            print("\t\tPivotting data to 2D table")
        vals = bins_concat.pivot_table(
            values=label,
            index="lat_cut",
            columns="lon_cut",
            aggfunc="sum",
        )
        all_indexes = [index for index in range(lons.shape[0])]
        all_columns = [colum for colum in range(lats.shape[1])]
        vals: pd.DataFrame = vals.reindex(all_indexes, axis=0)
        vals: pd.DataFrame = vals.reindex(all_columns, axis=1)

        return lons, lats, vals.values

    def _build(
        self,
        variable_name: str,
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
        if variable_name == "all":
            label = "all"
        else:
            label = self._variables.get(variable_name).label
        df = self._group(
            var_key=label,
            lat_key=self._variables.get(self._variables.latitude_var_name).label,
            lon_key=self._variables.get(self._variables.longitude_var_name).label,
        )
        if self._verbose > 1:
            print("\tCreating figure")
        fig = plt.figure(figsize=[10, 10])
        provs = ", ".join(self._storer.providers)
        suptitle = f"{variable_name} - {provs} ({self._storer.category})"
        plt.suptitle(suptitle)
        ax = plt.subplot(1, 1, 1, projection=crs.Orthographic(0, 90))
        ax.gridlines(draw_labels=True)
        ax.add_feature(feature.LAND, zorder=4)
        ax.add_feature(feature.OCEAN, zorder=1)
        extent = [self._lon_min, self._lon_max, self._lat_min, self._lat_max]
        ax.set_extent(extent, crs.PlateCarree())
        if not df.empty:
            X1, Y1, Z1 = self._mesh(
                df=df,
                label=label,
            )
            if X1.shape == (1, 1) or Y1.shape == (1, 1) or Z1.shape == (1, 1):
                warnings.warn(
                    "Not enough data to display, try decreasing the bin size"
                    " or representing more data sources"
                )
            cbar = ax.pcolor(
                X1,
                Y1,
                Z1,
                transform=crs.PlateCarree(),
                **kwargs,
            )
            fig.colorbar(cbar, label=label, shrink=0.75)
        label = f"{variable_name} total data points count"

        title = f"{self._lat_bin}° x {self._lon_bin}° grid (lat x lon)"
        plt.title(title)
        return fig

    def save(
        self,
        save_path: str,
        variable_name: str,
        title: str = None,
        suptitle: str = None,
        **kwargs,
    ) -> None:
        """Plots the colormesh for the given variable.

        Parameters
        ----------
        save_path: str
            Path to save the figure at.
        variable_name : str
            Name of the variable to plot.
        title: str, optional
            Title for the figure, if set to None, automatically created.
            , by default None.
        suptitle: str, optional
            Suptitle for the figure, if set to None, automatically created.
            , by default None.
        **kwargs
            Additional arguments to pass to plt.pcolor.
        """
        super().save(
            save_path=save_path,
            variable_name=variable_name,
            title=title,
            suptitle=suptitle,
            **kwargs,
        )

    def show(
        self,
        variable_name: str,
        title: str = None,
        suptitle: str = None,
        **kwargs,
    ) -> None:
        """Plots the colormesh for the given variable.

        Parameters
        ----------
        variable_name : str
            Name of the variable to plot.
        title: str, optional
            Title for the figure, if set to None, automatically created.
            , by default None.
        suptitle: str, optional
            Suptitle for the figure, if set to None, automatically created.
            , by default None.
        **kwargs
            Additional arguments to pass to plt.pcolor.
        """
        super().show(
            variable_name=variable_name,
            title=title,
            suptitle=suptitle,
            **kwargs,
        )


class EvolutionProfile(BasePlot):
    """Class to plot the evolution of data on a given area.

    Parameters
    ----------
    storer : Storer
        Storer to map data of.
    """

    __default_interval: str = "day"
    __default_interval_length: int = 10
    __default_depth_interval: int = 100
    _interval: str = __default_interval
    _interval_length: int = __default_interval_length
    _depth_interval: int | float = __default_depth_interval

    def __init__(
        self,
        storer: "Storer",
    ) -> None:

        super().__init__(storer)

    def reset_intervals(self) -> None:
        """Reset interval parameters to the default ones."""
        self._interval = self.__default_interval
        self._interval_length = self.__default_interval_length
        self._depth_interval = self.__default_depth_interval

    def reset_parameters(self) -> None:
        """Reset all boundaries and intervals to default values."""
        self.reset_boundaries()
        self.reset_intervals()

    def set_geographic_bin(
        self,
        center_latitude: int | float,
        center_longitude: int | float,
        bins_size: int | float | Iterable[int | float],
    ) -> None:
        """Set the geographic boundaries based on a bin. The bin is considered \
            centered on the center_latitude and center_longitude center \
            and the bins_size argument defines its width and height.

        Parameters
        ----------
        center_latitude : int | float
            Latitude of the center of the bin.
        center_longitude : int | float
            Longitude of the center of the bin.
        bins_size : int | float | Iterable[int  |  float]
            Bin size, if iterable, the first coimponent is for latitude and the \
            second for longitude. If not, the value is considered for both dimensions.
        """
        if isinstance(bins_size, Iterable):
            lat_bin, lon_bin = bins_size[0], bins_size[1]
        else:
            lat_bin, lon_bin = bins_size, bins_size
        # Bin boundaries
        self._lat_min = center_latitude - lat_bin / 2
        self._lat_max = center_latitude + lat_bin / 2
        self._lon_min = center_longitude - lon_bin / 2
        self._lon_max = center_longitude + lon_bin / 2

    def set_depth_interval(self, depth_interval: int | float = "np.nan") -> None:
        """Set the depth interval value. This represent the vertical resolution \
        of the final plot.

        Parameters
        ----------
        depth_interval : int | float, optional
            Value to use (positive integer)., by default np.nan
        """
        if not np.isnan(depth_interval):
            self._depth_interval = depth_interval

    def set_date_intervals(self, interval: str, interval_length: int = None) -> None:
        """Set the date interval parameters. This represent the horizontal resolution \
        of the final plot.

        Parameters
        ----------
        interval : str
            Interval resolution, can be "day", "week", "month", "year" or "custom".
        interval_length : int, optional
            Only useful if the resolution interval is "custom". \
            Represents the interval length, in days., by default None
        """
        self._interval = interval
        if interval_length is not None:
            self._interval_length = interval_length

    def _get_cut_intervals(
        self,
    ) -> pd.IntervalIndex:
        """Create the datetime intervals to use for the cut.

        Returns
        -------
        pd.IntervalIndex
            Intervals to use for the cut.
        """
        drng_generator = DateRangeGenerator(
            start=self._date_min,
            end=self._date_max,
            interval=self._interval,
            interval_length=self._interval_length,
        )
        drng = drng_generator()
        intervals = pd.IntervalIndex.from_arrays(
            pd.to_datetime(drng[drng_generator.start_column_name]),
            pd.to_datetime(drng[drng_generator.end_column_name]),
            closed="both",
        )
        return intervals

    def _build(
        self,
        variable_name: str,
        **kwargs,
    ) -> "Figure":
        """Build the plot to display or save.

        Parameters
        ----------
        variable_name : str
            Name of the variable to plot.
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
        df = self._storer.data.copy()
        if variable_name == "all":
            df["all"] = 1
            var_col = "all"
        else:
            var_col = self._variables.get(variable_name).label
        columns = [
            self._lat_col,
            self._lon_col,
            self._depth_col,
            self._date_col,
            var_col,
        ]
        df = df[columns]
        # Boundaries boolean series
        if self._verbose > 1:
            print("\tSlicing Data based on given boundaries.")
        lat_min_cond = df[self._lat_col] >= self._lat_min
        lat_max_cond = df[self._lat_col] <= self._lat_max
        lat_cond = (lat_min_cond) & (lat_max_cond)
        lon_min_cond = df[self._lon_col] >= self._lon_min
        lon_max_cond = df[self._lon_col] <= self._lon_max
        lon_cond = (lon_min_cond) & (lon_max_cond)
        depth_min_cond = df[self._depth_col] >= self._depth_min
        depth_max_cond = df[self._depth_col] <= self._depth_max
        depth_cond = depth_min_cond & depth_max_cond
        # Slicing
        df_slice = df.loc[lat_cond & lon_cond & depth_cond, :].copy(True)
        if df_slice.empty:
            raise ValueError("Not enough data at this location to build a figure.")
        # Set 1 when the variable is not nan, otherwise 0
        var_count = (~df_slice[var_col].isna()).astype(int)
        var_count.rename("values", inplace=True)
        # Make depth groups
        depth_div = df_slice[self._depth_col] / self._depth_interval
        depth_groups = depth_div.round() * self._depth_interval
        depth_groups.rename("index", inplace=True)
        if self._verbose > 1:
            print("\tMaking date intervals.")
        intervals = self._get_cut_intervals()
        date_cut = pd.cut(df_slice[self._date_col], intervals)
        date_cut_left = pd.Series(pd.IntervalIndex(date_cut).left)
        date_cut_left.rename("columns", inplace=True)
        # Pivot
        data = pd.concat(
            [
                date_cut_left.to_frame(),
                depth_groups.to_frame(),
                var_count.to_frame(),
            ],
            axis=1,
        )
        if self._verbose > 1:
            print("\tPivotting dataframe.")
        # Aggregate using 'sum' to count non-nan values
        pivotted = data.pivot_table(
            values="values",
            index="index",
            columns="columns",
            aggfunc="sum",
        )
        to_insert = intervals[~intervals.left.isin(pivotted.columns)].left
        pivotted.loc[:, to_insert] = np.nan
        pivotted.sort_index(axis=1, inplace=True)
        # Figure
        if self._verbose > 1:
            print("\tCreating figure.")
        fig = plt.figure(figsize=[10, 5])
        suptitle = (
            "Evolution of data in the area of latitude in "
            f"[{round(self._lat_min,2)},{round(self._lat_max,2)}] and longitude in "
            f"[{round(self._lon_min,2)},{round(self._lon_max,2)}]"
        )
        plt.suptitle(suptitle)
        ax = plt.subplot(1, 1, 1)
        X, Y = np.meshgrid(pivotted.columns, pivotted.index)
        # Color mesh
        cbar = ax.pcolor(X, Y, pivotted.values, **kwargs)
        fig.colorbar(cbar, label="Number of data points", shrink=0.75)
        if self._interval == "custom":
            title = (
                f"Horizontal resolution: {self._interval_length} "
                f"day{'s' if self._interval_length > 1 else ''}. "
                f"Vertical resolution: {self._depth_interval} meters."
            )
        else:
            title = (
                f"Horizontal resolution: 1 {self._interval}. "
                f"Vertical resolution: {self._depth_interval} meters."
            )
        plt.title(title)
        return fig

    def show(
        self,
        variable_name: str,
        title: str = None,
        suptitle: str = None,
        **kwargs,
    ) -> None:
        """Plot the figure of data density evolution in a givemn area.

        Parameters
        ----------
        variable_name : str
            Name of the variable to plot.
        title : str, optional
            Specify a title to change from default., by default None
        suptitle : str, optional
            Specify a suptitle to change from default., by default None
        **kwargs
            Additional arguments to pass to plt.pcolor.
        """
        super().show(
            variable_name=variable_name,
            title=title,
            suptitle=suptitle,
            **kwargs,
        )

    def save(
        self,
        save_path: str,
        variable_name: str,
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
        title : str, optional
            Specify a title to change from default., by default None
        suptitle : str, optional
            Specify a suptitle to change from default., by default None
        **kwargs
            Additional arguments to pass to plt.pcolor.
        """
        super().save(
            save_path=save_path,
            variable_name=variable_name,
            title=title,
            suptitle=suptitle,
            **kwargs,
        )
