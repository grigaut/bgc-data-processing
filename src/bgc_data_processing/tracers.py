"""Plotting objects."""


import warnings
from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import TYPE_CHECKING, ClassVar

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from cartopy import crs, feature
from scipy.stats import norm
from seawater import eos80

from bgc_data_processing.data_structures.filtering import Constraints
from bgc_data_processing.utils.dateranges import DateRangeGenerator

if TYPE_CHECKING:
    from cartopy.mpl.geoaxes import GeoAxes
    from matplotlib.axes import Axes
    from matplotlib.collections import Collection, PathCollection
    from matplotlib.figure import Figure

    from bgc_data_processing.data_structures.storers import Storer
    from bgc_data_processing.data_structures.variables.sets import StoringVariablesSet
    from bgc_data_processing.water_masses import WaterMass


class BasePlot(ABC):
    """Base class to plot data from a storer.

    Parameters
    ----------
    storer : Storer
        Storer to plot data of.
    constraints: Constraints
            Constraint slicer.
    """

    def __init__(self, storer: "Storer", constraints: "Constraints") -> None:
        """Initiate Base class to plot data from a storer.

        Parameters
        ----------
        storer : Storer
            Storer to plot data of.
        constraints: Constraints
                Constraint slicer.
        """
        self._storer = constraints.apply_constraints_to_storer(storer)
        self._variables = storer.variables
        self._constraints = constraints
        self._verbose = storer.verbose

    @abstractmethod
    def _build_to_new_figure(self, *args, **kwargs) -> "Figure":
        """Create the figure.

        Parameters
        ----------
        *args: list
            Parameters to build the figure.
        *kwargs: dict
            Parameters to build the figure.

        Returns
        -------
        Figure
            Figure to show or save.
        """
        ...

    @abstractmethod
    def show(
        self,
        title: str | None = None,
        suptitle: str | None = None,
        **kwargs,
    ) -> None:
        """Plot method.

        Parameters
        ----------
        title : str, optional
            Specify a title to change from default., by default None
        suptitle : str, optional
            Specify a suptitle to change from default., by default None
        *kwargs: dict
            Additional parameters to pass to self._build_to_new_figure.
        """
        self._build_to_new_figure(
            title=title,
            suptitle=suptitle,
            **kwargs,
        )
        plt.show()
        plt.close()

    @abstractmethod
    def save(
        self,
        save_path: str,
        title: str | None = None,
        suptitle: str | None = None,
        **kwargs,
    ) -> None:
        """Figure saving method.

        Parameters
        ----------
        save_path : str
            Path to save the output image.
        title : str, optional
            Specify a title to change from default., by default None
        suptitle : str, optional
            Specify a suptitle to change from default., by default None
        *kwargs: dict
            Additional parameters to pass to self._build_to_new_figure.
        """
        self._build_to_new_figure(
            title=title,
            suptitle=suptitle,
            **kwargs,
        )
        plt.savefig(save_path)

    @abstractmethod
    def plot_to_axes(
        self,
        ax: "Axes | GeoAxes",
        *args,
        **kwargs,
    ) -> "Axes | GeoAxes":
        """Plot data to the given axes.

        Parameters
        ----------
        ax : Axes | GeoAxes
            Axes to plot the data on.
        *args: list
            Additional parameters for the axes plotting method.
        *kwargs: dict
            Additional parameters for the axes plotting method.

        Returns
        -------
        Axes | GeoAxes
            Axes were the data is plotted on.
        """


class DensityPlotter(BasePlot):
    """Base class for tracing on earthmaps.

    Parameters
    ----------
    storer : Storer
        Data Storer containing data to plot.
    constraints: Constraints
            Constraint slicer.
    """

    __default_lat_bin: int | float = 1
    __default_lon_bin: int | float = 1
    __default_depth_density: bool = True

    def __init__(
        self,
        storer: "Storer",
        constraints: "Constraints" = Constraints(),
    ) -> None:
        """Instanciate base class for tracing on earthmaps.

        Parameters
        ----------
        storer : Storer
            Data Storer containing data to plot.
        constraints: Constraints
                Constraint slicer.
        """
        super().__init__(storer=storer, constraints=constraints)
        self._lat_bin: int | float = self.__default_lat_bin
        self._lon_bin: int | float = self.__default_lon_bin
        self._depth_density: bool = self.__default_depth_density
        self._lat_map_min = np.nan
        self._lat_map_max = np.nan
        self._lon_map_min = np.nan
        self._lon_map_max = np.nan
        depth_var_name = self._variables.depth_var_name
        depth_var_label = self._variables.get(depth_var_name).label
        self._data = self._storer.data.sort_values(depth_var_label, ascending=False)
        self._grouping_columns = self._get_grouping_columns(self._variables)

    def _get_grouping_columns(self, variables: "StoringVariablesSet") -> list:
        """Return a list of columns to use when grouping the data.

        Parameters
        ----------
        variables : StoringVariablesSet
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
            if var_name is not None and var_name in variables.keys():  # noqa: SIM118
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
        data = self._data.copy()
        if var_key == "all":
            data.insert(0, var_key, 1)
        else:
            data[var_key] = (~data[var_key].isna()).astype(int)
        data = data[data[var_key] == 1]
        group = data[[*self._grouping_columns, var_key]].groupby(
            self._grouping_columns,
            dropna=False,
        )
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
        """Generate evenly spaced points to use when creating the meshgrid.

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

    def _get_map_extent(self, df: pd.DataFrame) -> list[int | float]:
        """Compute map's extents.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to plot. Its boundaries values will be used
             if map bondaries are not specified.

        Returns
        -------
        list[int | float]
            Minimal longitude, maximal longitude, minimal latitude, maximal latitude.
        """
        lat_col = self._variables.get(self._variables.latitude_var_name).label
        lon_col = self._variables.get(self._variables.longitude_var_name).label

        lat_min, lat_max = self._constraints.get_extremes(
            lat_col,
            df[lat_col].min(),
            df[lat_col].max(),
        )
        lon_min, lon_max = self._constraints.get_extremes(
            lon_col,
            df[lon_col].min(),
            df[lon_col].max(),
        )

        lat_map_min = self._lat_map_min if not np.isnan(self._lat_map_min) else lat_min
        lat_map_max = self._lat_map_max if not np.isnan(self._lat_map_max) else lat_max
        lon_map_min = self._lon_map_min if not np.isnan(self._lon_map_min) else lon_min
        lon_map_max = self._lon_map_max if not np.isnan(self._lon_map_max) else lon_max

        return [lon_map_min, lon_map_max, lat_map_min, lat_map_max]

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

    def set_map_boundaries(
        self,
        latitude_min: int | float = np.nan,
        latitude_max: int | float = np.nan,
        longitude_min: int | float = np.nan,
        longitude_max: int | float = np.nan,
    ) -> None:
        """Define the boundaries of the map.

        (different from the boundaries of the plotted data).

        Parameters
        ----------
        latitude_min : int | float, optional
            Minimum latitude, by default np.nan
        latitude_max : int | float, optional
            Maximal latitude, by default np.nan
        longitude_min : int | float, optional
            Mnimal longitude, by default np.nan
        longitude_max : int | float, optional
            Maximal longitude, by default np.nan
        """
        if not np.isnan(latitude_min):
            self._lat_map_min = latitude_min
        if not np.isnan(latitude_max):
            self._lat_map_max = latitude_max
        if not np.isnan(longitude_min):
            self._lon_map_min = longitude_min
        if not np.isnan(longitude_max):
            self._lon_map_max = longitude_max

    def _mesh(
        self,
        df: pd.DataFrame,
        label: str,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Return the X,Y and Z 2D array to use with plt.pcolormesh.

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
        all_indexes = list(range(lons.shape[0]))
        all_columns = list(range(lats.shape[1]))
        vals: pd.DataFrame = vals.reindex(all_indexes, axis=0)
        vals: pd.DataFrame = vals.reindex(all_columns, axis=1)

        return lons, lats, vals.values

    def save(
        self,
        save_path: str,
        variable_name: str,
        title: str | None = None,
        suptitle: str | None = None,
        **kwargs,
    ) -> None:
        """Plot the colormesh for the given variable.

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
        title: str | None = None,
        suptitle: str | None = None,
        **kwargs,
    ) -> None:
        """Plot the colormesh for the given variable.

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

    def _build_to_new_figure(
        self,
        variable_name: str,
        title: str,
        suptitle: str,
        **kwargs,
    ) -> "Figure":
        """Create a Figure and plot the data on the axes of the Figure.

        Parameters
        ----------
        variable_name : str
            Name of the variable to plot.
        title : str, optional
            Title for the Figure, automatically generated if None., by default None
        suptitle : str, optional
            Suptitle for the Figure, automatically generated if None., by default None
        **kwargs
            Additional arguments to pass to plt.pcolormesh.

        Returns
        -------
        Figure
            Final Figure.
        """
        fig = plt.figure(figsize=[10, 10])
        ax: "GeoAxes" = plt.subplot(1, 1, 1, projection=crs.Orthographic(0, 90))
        if suptitle is not None:
            ax.set_title(suptitle)
        ax.gridlines(draw_labels=True)
        ax.add_feature(feature.LAND, zorder=4)
        ax.add_feature(feature.OCEAN, zorder=1)
        ax, cbar = self._build_to_geoaxes(variable_name=variable_name, ax=ax, **kwargs)
        if cbar is not None:
            label = f"{variable_name} total data points count"
            fig.colorbar(cbar, label=label, shrink=0.75)
        if suptitle is None:
            provs = ", ".join(self._storer.providers)
            suptitle = f"{variable_name} - {provs} ({self._storer.category})"
        if title is None:
            title = f"{self._lat_bin}° x {self._lon_bin}° grid (lat x lon)"
        plt.suptitle(suptitle)
        ax.set_title(title)
        return fig

    def _build_to_geoaxes(
        self,
        variable_name: str,
        ax: "GeoAxes",
        **kwargs,
    ) -> tuple["GeoAxes", "Collection"]:
        """Build the plot to given axes.

        Parameters
        ----------
        variable_name : str
            Name of the variable to plot.
        ax : GeoAxes
            GeoAxes (from cartopy) to plot the data to.
        **kwargs
            Additional arguments to pass to plt.pcolormesh.

        Returns
        -------
        tuple[GeoAxes, Collection]
            Axes, Colorbar.
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
        ax.gridlines(draw_labels=True)
        ax.add_feature(feature.LAND, zorder=4)
        ax.add_feature(feature.OCEAN, zorder=1)
        extent = self._get_map_extent(df)
        ax.set_extent(extent, crs.PlateCarree())
        if not df.empty:
            lat_2d, lon_2d, vals_2d = self._mesh(
                df=df,
                label=label,
            )
            if (
                lat_2d.shape == (1, 1)
                or lon_2d.shape == (1, 1)
                or vals_2d.shape == (1, 1)
            ):
                warnings.warn(
                    "Not enough data to display, try decreasing the bin size"
                    " or representing more data sources",
                    stacklevel=2,
                )
            cbar = ax.pcolormesh(
                lat_2d,
                lon_2d,
                vals_2d,
                transform=crs.PlateCarree(),
                **kwargs,
            )
        else:
            cbar = None

        title = f"{self._lat_bin}° x {self._lon_bin}° grid (lat x lon)"
        ax.set_title(title)
        return ax, cbar

    def plot_to_axes(
        self,
        variable_name: str,
        ax: "GeoAxes",
        **kwargs,
    ) -> tuple["GeoAxes", "Collection"]:
        """Build the plot to given axes.

        Parameters
        ----------
        variable_name : str
            Name of the variable to plot.
        ax : GeoAxes
            GeoAxes (from cartopy) to plot the data to.
        **kwargs
            Additional arguments to pass to plt.pcolormesh.

        Returns
        -------
        tuple[GeoAxes, Collection]
            Axes, Colorbar.
        """
        return self._build_to_geoaxes(
            variable_name=variable_name,
            ax=ax,
            **kwargs,
        )

    def get_df(
        self,
        variable_name: str,
    ) -> pd.DataFrame:
        """Return the density of the given variable on the bins.

        Parameters
        ----------
        variable_name : str
            Name of the variable to bin.

        Returns
        -------
        pd.Dataframe
            Three columns dataframe : longitude, latitude and variable density.
             The column names are the same as in the original DataFrame.
        """
        if self._verbose > 1:
            print(f"\tMeshing {variable_name} data")
        if variable_name == "all":
            label = "all"
        else:
            label = self._variables.get(variable_name).label
        lon_label = self._variables.get(self._variables.longitude_var_name).label
        lat_label = self._variables.get(self._variables.latitude_var_name).label
        df = self._group(
            var_key=label,
            lat_key=lat_label,
            lon_key=lon_label,
        )
        if self._verbose > 1:
            print("\tCreating figure")
        if df.empty:
            return pd.DataFrame(columns=[lon_label, lat_label, label])
        longis_2d, latis_2d, values_2d = self._mesh(
            df=df,
            label=label,
        )
        # Ravel the arrays to concatenate them in a single dataframe
        lons = longis_2d.ravel()
        lats = latis_2d.ravel()
        vals = values_2d.ravel()
        data = {lon_label: lons, lat_label: lats, label: vals}
        transformed_df = pd.DataFrame.from_dict(data)
        return transformed_df[~transformed_df[label].isna()]


class EvolutionProfile(BasePlot):
    """Class to plot the evolution of data on a given area.

    Parameters
    ----------
    storer : Storer
        Storer to map data of.
    constraints: Constraints
        Constraint slicer.
    """

    __default_interval: str = "day"
    __default_interval_length: int = 10
    __default_depth_interval: int = 100
    __default_depth_max: int = 0

    def __init__(
        self,
        storer: "Storer",
        constraints: "Constraints" = Constraints(),
    ) -> None:
        """Class to plot the evolution of data on a given area.

        Parameters
        ----------
        storer : Storer
            Storer to map data of.
        constraints: Constraints
                Constraint slicer.
        """
        super().__init__(storer, constraints)
        self._interval: str = self.__default_interval
        self._interval_length: int = self.__default_interval_length
        self._depth_interval: int | float = self.__default_depth_interval
        self._depth_col = self._variables.get(self._variables.depth_var_name).label
        self._date_col = self._variables.get(self._variables.date_var_name).label

    def reset_intervals(self) -> None:
        """Reset interval parameters to the default ones."""
        self._interval = self.__default_interval
        self._interval_length = self.__default_interval_length
        self._depth_interval = self.__default_depth_interval

    def reset_parameters(self) -> None:
        """Reset all boundaries and intervals to default values."""
        self.reset_intervals()

    def set_depth_interval(
        self,
        depth_interval: int | float | list[int | float] = np.nan,
    ) -> None:
        """Set the depth interval value.

        This represents the vertical resolution of the final plot.

        Parameters
        ----------
        depth_interval : int | float | list[int|float], optional
            Depth interval values, if numeric, interval resolution, if instance of list,
            list of depth bins to use., by default np.nan
        """
        if isinstance(depth_interval, list) or (not np.isnan(depth_interval)):
            self._depth_interval = depth_interval

    def set_date_intervals(
        self,
        interval: str,
        interval_length: int | None = None,
    ) -> None:
        """Set the date interval parameters.

        This represent the horizontal resolution of the final plot.

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

    def _make_depth_intervals(self) -> pd.IntervalIndex:
        """Create the depth intervals from depth boundaries and interval resolution.

        Returns
        -------
        pd.IntervalIndex
            Interval to use when grouping data.
        """
        if self._constraints.is_constrained(self._depth_col):
            depth_min, depth_max = self._constraints.get_extremes(self._depth_col)
        else:
            depth_min = self._storer.data[self._depth_col].min()
            depth_max = self.__default_depth_max
        if np.isnan(depth_min):
            depth_min = self._storer.data[self._depth_col].min()
        if np.isnan(depth_max):
            depth_max = self.__default_depth_max
        # if bins values are given as a list
        if isinstance(self._depth_interval, list):
            intervals = np.array(self._depth_interval)
            if np.any(intervals < depth_min):
                intervals = intervals[intervals >= depth_min]
            if depth_min not in intervals:
                intervals = np.append(intervals, depth_min)
            if np.any(intervals > depth_max):
                intervals = intervals[intervals <= depth_max]
            if depth_max not in intervals:
                intervals = np.append(intervals, depth_max)
            intervals.sort()
            return pd.IntervalIndex.from_arrays(intervals[:-1], intervals[1:])

        # if only the bin value resolution is given
        return pd.interval_range(
            start=depth_min - depth_min % self._depth_interval,
            end=depth_max,
            freq=self._depth_interval,
            closed="right",
        )

    def _make_date_intervals(self) -> pd.IntervalIndex:
        """Create the datetime intervals to use for the cut.

        Returns
        -------
        pd.IntervalIndex
            Intervals to use for the date cut.
        """
        if self._constraints.is_constrained(self._date_col):
            date_min, date_max = self._constraints.get_extremes(self._date_col)
        else:
            date_min = self._storer.data[self._date_col].min()
            date_max = self._storer.data[self._date_col].max()

        drng_generator = DateRangeGenerator(
            start=date_min,
            end=date_max,
            interval=self._interval,
            interval_length=self._interval_length,
        )
        drng = drng_generator()
        return pd.IntervalIndex.from_arrays(
            pd.to_datetime(drng[drng_generator.start_column_name]),
            pd.to_datetime(drng[drng_generator.end_column_name]),
            closed="both",
        )

    def _create_cut_and_ticks(
        self,
        column_to_cut: pd.Series,
        cut_intervals: pd.IntervalIndex,
    ) -> tuple[pd.IntervalIndex, np.ndarray]:
        """Return both the cut and the ticks values to use for the Figure.

        Parameters
        ----------
        column_to_cut : pd.Series
            Column to apply the cut to.
        cut_intervals : pd.IntervalIndex
            Intervals to use for the cut.

        Returns
        -------
        tuple[pd.IntervalIndex, np.ndarray]
            _description_
        """
        cut = pd.cut(
            column_to_cut,
            bins=cut_intervals,
            include_lowest=True,
        )
        intervals_cut = pd.Series(pd.IntervalIndex(cut).left).rename(column_to_cut.name)
        last_tick = cut_intervals.right.values[-1]
        ticks = np.append(cut_intervals.left.values, last_tick)
        return intervals_cut, ticks

    def _make_full_pivotted_table(
        self,
        df: pd.DataFrame,
        depth_ticks: np.ndarray,
        date_ticks: np.ndarray,
        depth_series_name: str,
        date_series_name: str,
        values_series_name: str,
    ) -> pd.DataFrame:
        """Pivot the data and add the missing columns / index.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to pivot.
        depth_ticks : np.ndarray
            Ticks for depth.
        date_ticks : np.ndarray
            Ticks for dates.
        depth_series_name : str
            Depth column name.
        date_series_name : str
            Date column name.
        values_series_name : str
            Values column name.

        Returns
        -------
        pd.DataFrame
            Pivotted dataframe where all ticks (except last) are reprsented
            in index and columns.
        """
        pivotted = df.pivot_table(
            values=values_series_name,
            index=depth_series_name,
            columns=date_series_name,
            aggfunc="sum",
        )
        to_insert = date_ticks[:-1][~np.isin(date_ticks[:-1], pivotted.columns)]
        pivotted.loc[:, to_insert] = np.nan
        pivotted: pd.DataFrame = pivotted.reindex(depth_ticks[:-1])
        pivotted.sort_index(axis=1, inplace=True)
        pivotted.sort_index(axis=0, inplace=True)
        return pivotted

    def _build_to_axes(
        self,
        variable_name: str,
        ax: "Axes",
        **kwargs,
    ) -> tuple["Axes", "Collection"]:
        """Build the plot to given axes.

        Parameters
        ----------
        variable_name : str
            Name of the variable to plot.
        ax : Axes
            Axes to plot the data to.
        **kwargs
            Additional arguments to pass to plt.pcolormesh.

        Returns
        -------
        tuple[Axes, Collection]
            Axes, Colorbar.
        """
        if variable_name == "all":
            var_label = "all"
        else:
            var_label = self._variables.get(variable_name).label
        df = self._storer.data
        if var_label == "all":
            df.insert(0, var_label, 1)
        # Set 1 when the variable is not nan, otherwise 0
        var_count = (~df[var_label].isna()).astype(int)
        var_count.reset_index(drop=True, inplace=True)
        # Make cuts
        if self._verbose > 1:
            print("\tMaking date intervals.")
        depth_cut, depth_ticks = self._create_cut_and_ticks(
            column_to_cut=df[self._depth_col],
            cut_intervals=self._make_depth_intervals(),
        )
        date_cut, date_ticks = self._create_cut_and_ticks(
            column_to_cut=df[self._date_col],
            cut_intervals=self._make_date_intervals(),
        )
        # Pivot
        data = pd.concat(
            [
                date_cut,
                depth_cut,
                var_count,
            ],
            axis=1,
        )
        if self._verbose > 1:
            print("\tPivotting dataframe.")
        # Aggregate using 'sum' to count non-nan values
        df_pivot = self._make_full_pivotted_table(
            df=data,
            depth_ticks=depth_ticks,
            date_ticks=date_ticks,
            depth_series_name=depth_cut.name,
            date_series_name=date_cut.name,
            values_series_name=var_count.name,
        )
        # Figure
        if self._verbose > 1:
            print("\tCreating figure.")

        date, depth = np.meshgrid((date_ticks), (depth_ticks))
        # Color mesh
        cbar = ax.pcolormesh(date, depth, df_pivot.values, **kwargs)

        return ax, cbar

    def _build_to_new_figure(
        self,
        variable_name: str,
        title: str | None = None,
        suptitle: str | None = None,
        **kwargs,
    ) -> "Figure":
        """Create a Figure and plot the data on the Figure.

        Parameters
        ----------
        variable_name : str
            Name of the variable to plot.
        title : str, optional
            Title for the Figure, automatically generated if None., by default None
        suptitle : str, optional
            Suptitle for the Figure, automatically generated if None., by default None
        **kwargs
            Additional arguments to pass to plt.pcolormesh.

        Returns
        -------
        Figure
            Final Figure.
        """
        fig = plt.figure(figsize=[10, 5])
        ax = plt.subplot(1, 1, 1)
        ax, cbar = self._build_to_axes(
            variable_name=variable_name,
            ax=ax,
            **kwargs,
        )
        fig.colorbar(cbar, label="Number of data points", shrink=0.75)
        if title is None:
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
        if suptitle is None:
            lat_col = self._variables.get(self._variables.latitude_var_name).label
            lon_col = self._variables.get(self._variables.longitude_var_name).label
            lat_min, lat_max = self._constraints.get_extremes(
                lat_col,
                self._storer.data[lat_col].min(),
                self._storer.data[lat_col].max(),
            )
            lon_min, lon_max = self._constraints.get_extremes(
                lon_col,
                self._storer.data[lon_col].min(),
                self._storer.data[lon_col].max(),
            )
            suptitle = (
                "Evolution of data in the area of latitude in "
                f"[{round(lat_min,2)},{round(lat_max,2)}] and longitude in "
                f"[{round(lon_min,2)},{round(lon_max,2)}]"
            )
        plt.suptitle(suptitle)
        plt.title(title)
        plt.xticks(rotation=45)
        plt.tight_layout()
        return fig

    def show(
        self,
        variable_name: str,
        title: str | None = None,
        suptitle: str | None = None,
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
        title: str | None = None,
        suptitle: str | None = None,
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

    def plot_to_axes(
        self,
        variable_name: str,
        ax: "Axes",
        **kwargs,
    ) -> tuple["Axes", "Collection"]:
        """Plot the data on a given axes.

        Parameters
        ----------
        variable_name : str
            Name of the variable to plot the data of.
        ax : Axes
            Axes to plot the data on.
        **kwargs:
            Additional arguments to pass to plt.pcolormesh.

        Returns
        -------
        tuple[Axes, Collection]
            Axes, colorbar
        """
        return self._build_to_axes(
            variable_name=variable_name,
            ax=ax,
            **kwargs,
        )


class TemperatureSalinityDiagram(BasePlot):
    """Class to plot a Temperature-Salinity Diagram.

    Parameters
    ----------
    storer : Storer
        Storer to map data of.
    constraints: Constraints
        Constraint slicer.
    temperature_field : str
        Name of the temperature field in storer (column name).
    salinity_field : str
        Name of the salinity field in storer (column name).
    """

    def __init__(
        self,
        storer: "Storer",
        constraints: "Constraints",
        salinity_field: str,
        temperature_field: str,
        ptemperature_field: str,
    ) -> None:
        super().__init__(storer, constraints)
        self.salinity_field = salinity_field
        self.temperature_field = temperature_field
        self.ptemperature_field = ptemperature_field

    def show(
        self,
        title: str | None = None,
        suptitle: str | None = None,
        **kwargs,
    ) -> None:
        """Plot the Temperature-Salinity diagram.

        Parameters
        ----------
        title : str, optional
            Specify a title to change from default., by default None
        suptitle : str, optional
            Specify a suptitle., by default None
        **kwargs
            Additional arguments to pass to plt.pcolor.
        """
        super().show(title=title, suptitle=suptitle, **kwargs)

    def save(
        self,
        save_path: str,
        title: str | None = None,
        suptitle: str | None = None,
        **kwargs,
    ) -> None:
        """Save the figure of Temperature-Salinity Diagram.

        Parameters
        ----------
        save_path : str
            Path to save the output image.
        title : str, optional
            Specify a title to change from default., by default None
        suptitle : str, optional
            Specify a suptitle to change from default., by default None
        **kwargs
            Additional arguments to pass to plt.scatter.
        """
        super().save(save_path=save_path, title=title, suptile=suptitle, **kwargs)

    def plot_to_axes(self, ax: "Axes", **kwargs) -> tuple["Axes", "PathCollection"]:
        """Plot the data on a given axes.

        Parameters
        ----------
        ax : Axes
            Axes to plot the data on.
        **kwargs:
            Additional arguments to pass to plt.scatter.

        Returns
        -------
        tuple[Axes, Collection]
            Axes, colorbar
        """
        return self._build_to_axes(
            ax=ax,
            **kwargs,
        )

    def _build_to_new_figure(
        self,
        title: str | None,
        suptitle: str | None,
        **kwargs,
    ) -> "Figure":
        """Create a Figure and plot the data on the Figure.

        Parameters
        ----------
        title : str, optional
            Title for the Figure, automatically generated if None., by default None
        suptitle : str, optional
            Suptitle for the Figure, automatically generated if None., by default None
        **kwargs
            Additional arguments to pass to plt.scatter.

        Returns
        -------
        Figure
            Final Figure.
        """
        fig = plt.figure(figsize=[10, 5])
        ax = plt.subplot(1, 1, 1)
        ax, cbar = self._build_to_axes(
            ax=ax,
            **kwargs,
        )
        fig.colorbar(cbar, label="Depth [m]")
        plt.xlabel("Salinity [psu]")
        plt.ylabel("Potential Temperature [°C]")
        if title is None:
            title = "Temperature-Salinity Diagram"
        plt.title(title)
        if suptitle is not None:
            plt.suptitle(suptitle)
        return fig

    def _build_to_axes(self, ax: "Axes", **kwargs) -> tuple["Axes", "PathCollection"]:
        """Build the plot to given axes.

        Parameters
        ----------
        ax : Axes
            Axes to plot the data to.
        **kwargs
            Additional arguments to pass to plt.pcolormesh.

        Returns
        -------
        tuple[Axes, OathCollection]
            Axes, Colorbar.
        """
        df = self._storer.data
        # Remove empty columns
        df = df[~(df[self.ptemperature_field].isna() | df[self.salinity_field].isna())]
        # Select relevant columns
        depth_col = df[self._variables.get(self._variables.depth_var_name).label]
        salinity_col = df[self.salinity_field]
        ptemperature_col = df[self.ptemperature_field]
        temperature_col = df[self.temperature_field]
        # Scatter all data points in the TS diagram
        cbar = ax.scatter(salinity_col, ptemperature_col, c=depth_col, **kwargs)
        # Draw the sigma-t isolines
        salinity_min = salinity_col.min()
        salinity_max = salinity_col.max()
        salinitys = np.linspace(salinity_min, salinity_max, 100)
        temperature_min = temperature_col.min()
        temperature_max = temperature_col.max()
        temperatures = np.linspace(temperature_max, temperature_min, 100)
        temps_2d = np.tile(temperatures.reshape((1, -1)).T, (1, 100))
        salis_2d = np.tile(salinitys, (100, 1))
        sigma_t_values = eos80.dens0(salis_2d, temps_2d) - 1000
        label = ax.contour(salinitys, temperatures, sigma_t_values, colors="grey")
        ax.clabel(label)
        return ax, cbar


class VariableBoxPlot(BasePlot):
    """Class to draw box plots for a given variable.

    Parameters
    ----------
    storer : Storer
        Storer to map the data of.
    constraints : Constraints
        Constraints slicer.
    """

    period_mapping: ClassVar[dict[str, str]] = {
        "year": "%Y",
        "month": "%Y-%m",
        "week": "%Y-%W",
        "day": "%Y-%m-%d",
    }

    def __init__(self, storer: "Storer", constraints: "Constraints") -> None:
        super().__init__(storer, constraints)

    def show(
        self,
        variable_name: str,
        period: str,
        title: str | None = None,
        suptitle: str | None = None,
        **kwargs,
    ) -> None:
        """Plot method.

        Parameters
        ----------
        variable_name: str
            Name of the variable to plot.
        period: str
            Period on which to plot each boxplot.
        title : str, optional
            Specify a title to change from default., by default None
        suptitle : str, optional
            Specify a suptitle to change from default., by default None
        *kwargs: dict
            Additional parameters to pass to plt.boxplot.
        """
        super().show(
            variable_name=variable_name,
            period=period,
            title=title,
            suptitle=suptitle,
            **kwargs,
        )

    def save(
        self,
        variable_name: str,
        period: str,
        save_path: str,
        title: str | None = None,
        suptitle: str | None = None,
        **kwargs,
    ) -> None:
        """Figure saving method.

        Parameters
        ----------
        variable_name : str
            Name of the variable to plot.
        period : str
            Period on which to plot each boxplot.
        save_path : str
            Path to save the ouput image.
        title : str | None, optional
            Specify a title to change from default., by default None
        suptitle : str | None, optional
            Add a suptitle to the figure., by default None
        **kwargs: dict
            Addictional parameters to pass to plt.boxplot.
        """
        return super().save(
            save_path=save_path,
            variable_name=variable_name,
            period=period,
            title=title,
            suptitle=suptitle,
            **kwargs,
        )

    def _build_to_new_figure(
        self,
        variable_name: str,
        period: str,
        title: str | None,
        suptitle: str | None,
        **kwargs,
    ) -> "Figure":
        """Create new figure and axes and build the plot on them.

        Parameters
        ----------
        variable_name : str
            Name of the variable to plot.
        period : str
            Period on which to plot each boxplot.
        title : str | None, optional
            Specify a title to change from default., by default None
        suptitle : str | None, optional
            Add a suptitle to the figure., by default None
        **kwargs: dict
            Addictional parameters to pass to plt.boxplot.

        Returns
        -------
        Figure
            Figure to show or save.
        """
        fig = plt.figure(figsize=[10, 5], layout="tight")
        ax = plt.subplot(1, 1, 1)
        ax = self._build_to_axes(
            variable_name=variable_name,
            period=period,
            ax=ax,
            **kwargs,
        )
        variable = self._variables.get(variable_name)
        if period != "year":
            plt.xticks(rotation=45)
        plt.xlabel(f"{period.capitalize()}")
        plt.ylabel(f"{variable.name} {variable.unit}")
        if title is None:
            title = f"{variable.label} Box Plot"
        plt.title(title)
        if suptitle is not None:
            plt.suptitle(suptitle)
        return fig

    def plot_to_axes(
        self,
        variable_name: str,
        period: str,
        ax: "Axes",
        **kwargs,
    ) -> "Axes":
        """Plot the data to the given axes.

        Parameters
        ----------
        variable_name : str
            Name of the variable to plot.
        period : str
            Period on which to plot each boxplot.
        ax : Axes
            Axes to plot the data on.
        **kwargs: dict
            Additional parameters to pass to plt.boxplot.

        Returns
        -------
        Axes
            Axes where the data is plotted on.
        """
        return self._build_to_axes(
            variable_name=variable_name,
            period=period,
            ax=ax,
            **kwargs,
        )

    def _build_to_axes(
        self,
        variable_name: str,
        period: str,
        ax: "Axes",
        **kwargs,
    ) -> "Axes":
        """Build the data to the given axes.

        Parameters
        ----------
        variable_name : str
            Name of the variable to plot the data of.
        period : str
            Period on which to plot each boxplot.
        ax : Axes
            Axes to plot the data on.
        **kwargs:
            Additional parameters to pass to plt.boxplot.

        Returns
        -------
        Axes
            Axes where the data is plotted on.

        Raises
        ------
        ValueError
            If the 'period' parameters is invalid.
        """
        data = self._storer.data
        variable_label = self._variables.get(variable_name).label
        variable_data = self._storer.data[variable_label]
        variable_data.name = "variable"
        date_variable = self._variables.date_var_name
        date_col = self._variables.get(date_variable).label
        date_data = data[date_col]
        if period in self.period_mapping:
            period_str = self.period_mapping[period]
        else:
            raise ValueError(
                f"Wrong 'period' value, accepted values: {self.period_mapping.keys()}",
            )
        period_data = date_data.dt.strftime(period_str)
        period_data.name = "period"
        concat_data = pd.concat([period_data, variable_data], axis=1)
        pivot = concat_data.pivot(columns="period", values="variable")
        to_plot = [pivot[col][~pivot[col].isna()] for col in pivot.columns]
        ax.boxplot(x=to_plot, labels=pivot.columns, **kwargs)
        return ax


class WaterMassVariableComparison(BasePlot):
    """Class to draw a pressure vs variable comparison of water masses.

    Parameters
    ----------
    storer : Storer
        Storer to map the data of.
    constraints : Constraints
        Constraints slicer.
    pressure_var_name : str
        Name of the pressure variable.
    ptemperature_var_name : str
        Potential temperature variable name.
    salinity_var_name : str
        Salinity variable name.
    sigma_t_var_name : str
        Sigma-t variable name.
    """

    def __init__(
        self,
        storer: "Storer",
        constraints: "Constraints",
        pressure_var_name: str,
        ptemperature_var_name: str,
        salinity_var_name: str,
        sigma_t_var_name: str,
    ) -> None:
        super().__init__(storer, constraints)
        self.pressure_var = self._variables.get(pressure_var_name)
        self.ptemp_var = self._variables.get(ptemperature_var_name)
        self.salty_var = self._variables.get(salinity_var_name)
        self.sigma_t_var = self._variables.get(sigma_t_var_name)

    def show(
        self,
        variable_name: str,
        wmasses: list["WaterMass"],
        title: str | None = None,
        suptitle: str | None = None,
        **kwargs,
    ) -> None:
        """Plot method.

        Parameters
        ----------
        variable_name: str
            Name of the variable to plot.
        wmasses : list[WaterMass]
            List all water masses.
        title : str, optional
            Specify a title to change from default., by default None
        suptitle : str, optional
            Specify a suptitle to change from default., by default None
        *kwargs: dict
            Additional parameters to pass to plt.scatter.
        """
        super().show(
            variable_name=variable_name,
            wmasses=wmasses,
            title=title,
            suptitle=suptitle,
            **kwargs,
        )

    def save(
        self,
        variable_name: str,
        wmasses: list["WaterMass"],
        save_path: str,
        title: str | None = None,
        suptitle: str | None = None,
        **kwargs,
    ) -> None:
        """Figure saving method.

        Parameters
        ----------
        variable_name : str
            Name of the variable to plot.
        wmasses : list[WaterMass]
            List all water masses.
        save_path : str
            Path to save the ouput image.
        title : str | None, optional
            Specify a title to change from default., by default None
        suptitle : str | None, optional
            Add a suptitle to the figure., by default None
        **kwargs: dict
            Addictional parameters to pass to plt.scatter.
        """
        super().save(
            variable_name=variable_name,
            wmasses=wmasses,
            save_path=save_path,
            title=title,
            suptitle=suptitle,
            **kwargs,
        )

    def _build_to_new_figure(
        self,
        variable_name: str,
        wmasses: list["WaterMass"],
        title: str,
        suptitle: str,
        **kwargs,
    ) -> "Figure":
        """Create new figure and axes and build the plot on them.

        Parameters
        ----------
        variable_name : str
            Name of the variable to plot.
        wmasses : list[WaterMass]
            List all water masses.
        title : str | None, optional
            Specify a title to change from default., by default None
        suptitle : str | None, optional
            Add a suptitle to the figure., by default None
        **kwargs: dict
            Addictional parameters to pass to plt.scatter.

        Returns
        -------
        Figure
            Figure to show or save.
        """
        fig = plt.figure(figsize=[10, 10], layout="tight")
        ax = plt.subplot(1, 1, 1)
        self._build_to_axes(
            variable_name=variable_name,
            wmasses=wmasses,
            ax=ax,
            **kwargs,
        )
        if title is None:
            title = f"{variable_name} vs {self.pressure_var.name}"
        plt.title(title)
        if suptitle is not None:
            plt.suptitle(suptitle)
        var = self._variables.get(variable_name)
        plt.xlabel(f"{var.name} {var.unit}")
        plt.ylabel(f"{self.pressure_var.name} {self.pressure_var.unit}")
        plt.gca().invert_yaxis()
        plt.legend()
        return fig

    def plot_to_axes(
        self,
        variable_name: str,
        wmasses: list["WaterMass"],
        ax: "Axes",
        **kwargs,
    ) -> "Axes":
        """Plot the data to the given axes.

        Parameters
        ----------
        variable_name : str
            Name of the variable to plot.
        wmasses : list[WaterMass]
            List all water masses.
        ax : Axes
            Axes to plot the data on.
        **kwargs: dict
            Additional parameters to pass to plt.scatter.

        Returns
        -------
        Axes
            Axes where the data is plotted on.
        """
        return self._build_to_axes(
            variable_name=variable_name,
            wmasses=wmasses,
            ax=ax,
            **kwargs,
        )

    def _scatter_single_water_mass(
        self,
        variable_name: str,
        water_mass: "WaterMass",
        ax: "Axes",
        **kwargs,
    ) -> None:
        """Add a single trace to the axes.

        Parameters
        ----------
        variable_name : str
            name of the variable to plot.
        water_mass : WaterMass
            Water mass.
        ax : Axes
            Axes to plot the data on.
        **kwargs: dict
            Additional parameters to pass to plt.scatter.
        """
        variable_label = self._variables.get(variable_name).label
        wm_storer = water_mass.extract_from_storer(
            storer=self._storer,
            ptemperature_name=self.ptemp_var.name,
            salinity_name=self.salty_var.name,
            sigma_t_name=self.sigma_t_var.name,
        )
        ax.scatter(
            wm_storer.data[variable_label],
            wm_storer.data[self.pressure_var.label],
            label=water_mass.name,
            **kwargs,
        )

    def _build_to_axes(
        self,
        variable_name: str,
        wmasses: list["WaterMass"],
        ax: "Axes",
        **kwargs,
    ) -> "Axes":
        """Build the data to the given axes.

        Parameters
        ----------
        variable_name : str
            Name of the variable to plot the data of.
        wmasses : list[WaterMass]
            List all water masses.
        ax : Axes
            Axes to plot the data on.
        **kwargs: dict
            Additional parameters to pass to plt.scatter.

        Returns
        -------
        Axes
            Axes where the data is plotted on.
        """
        for wm in wmasses:
            self._scatter_single_water_mass(
                variable_name=variable_name,
                water_mass=wm,
                ax=ax,
                **kwargs,
            )
        return ax


class VariableHistogram(BasePlot):
    """Class to draw histogram for a given variable.

    Parameters
    ----------
    storer : Storer
        Storer to map the data of.
    constraints : Constraints
        Constraints slicer.
    """

    bin_number: int = 100

    def __init__(self, storer: "Storer", constraints: "Constraints") -> None:
        super().__init__(storer, constraints)

    def show(
        self,
        variable_name: str,
        title: str | None = None,
        suptitle: str | None = None,
        **kwargs,
    ) -> None:
        """Plot method.

        Parameters
        ----------
        variable_name: str
            Name of the variable to plot.
        title : str, optional
            Specify a title to change from default., by default None
        suptitle : str, optional
            Specify a suptitle to change from default., by default None
        *kwargs: dict
            Additional parameters to pass to plt.hist.
        """
        super().show(
            variable_name=variable_name,
            title=title,
            suptitle=suptitle,
            **kwargs,
        )

    def save(
        self,
        variable_name: str,
        save_path: str,
        title: str | None = None,
        suptitle: str | None = None,
        **kwargs,
    ) -> None:
        """Figure saving method.

        Parameters
        ----------
        variable_name : str
            Name of the variable to plot.
        save_path : str
            Path to save the ouput image.
        title : str | None, optional
            Specify a title to change from default., by default None
        suptitle : str | None, optional
            Add a suptitle to the figure., by default None
        **kwargs: dict
            Addictional parameters to pass to plt.hist.
        """
        return super().save(
            save_path=save_path,
            variable_name=variable_name,
            title=title,
            suptitle=suptitle,
            **kwargs,
        )

    def _build_to_new_figure(
        self,
        variable_name: str,
        title: str | None,
        suptitle: str | None,
        **kwargs,
    ) -> "Figure":
        """Create new figure and axes and build the plot on them.

        Parameters
        ----------
        variable_name : str
            Name of the variable to plot.
        title : str | None, optional
            Specify a title to change from default., by default None
        suptitle : str | None, optional
            Add a suptitle to the figure., by default None
        **kwargs: dict
            Addictional parameters to pass to plt.hist.

        Returns
        -------
        Figure
            Figure to show or save.
        """
        fig = plt.figure(figsize=[10, 5], layout="tight")
        ax = plt.subplot(1, 1, 1)
        ax = self._build_to_axes(
            variable_name=variable_name,
            ax=ax,
            **kwargs,
        )
        variable = self._variables.get(variable_name)
        plt.ylabel(f"{variable.name} {variable.unit}")
        if title is None:
            title = f"{variable.label} Histogram"
        plt.title(title)
        if suptitle is not None:
            plt.suptitle(suptitle)
        return fig

    def plot_to_axes(
        self,
        variable_name: str,
        ax: "Axes",
        **kwargs,
    ) -> "Axes":
        """Plot the data to the given axes.

        Parameters
        ----------
        variable_name : str
            Name of the variable to plot.
        ax : Axes
            Axes to plot the data on.
        **kwargs: dict
            Additional parameters to pass to plt.hist.

        Returns
        -------
        Axes
            Axes where the data is plotted on.
        """
        return self._build_to_axes(
            variable_name=variable_name,
            ax=ax,
            **kwargs,
        )

    def _build_to_axes(
        self,
        variable_name: str,
        ax: "Axes",
        **kwargs,
    ) -> "Axes":
        """Build the data to the given axes.

        Parameters
        ----------
        variable_name : str
            Name of the variable to plot the data of.
        ax : Axes
            Axes to plot the data on.
        **kwargs:
            Additional parameters to pass to plt.hist.

        Returns
        -------
        Axes
            Axes where the data is plotted on.
        """
        variable_label = self._variables.get(variable_name).label
        variable_data = self._storer.data[variable_label]
        variable_data = variable_data[~variable_data.isna()]
        min_value = variable_data.min()
        max_value = variable_data.max()
        mean_value = variable_data.mean()
        std_value = variable_data.std()
        ax.hist(variable_data, bins=self.bin_number, **kwargs)
        x = np.linspace(min_value, max_value, 1000)
        ax2 = ax.twinx()
        ax2.plot(x, norm.pdf(x, mean_value, std_value), color="red")
        ax2.get_yaxis().set_visible(False)
        ax.set_xlabel(f"{round(mean_value,2)} \u00B1 {round(std_value,2)}")
        return ax
