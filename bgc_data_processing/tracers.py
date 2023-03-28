"""Plotting objects."""


import warnings
from typing import TYPE_CHECKING, Iterable, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from cartopy import crs, feature

from bgc_data_processing.base import BasePlot
from bgc_data_processing.data_classes import Storer, Constraints
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
        data = self._constraints.apply_constraints(self._data, False)
        if var_key == "all":
            data.insert(0, var_key, 1)
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

        if not np.isnan(self._lat_map_min):
            lat_map_min = self._lat_map_min
        else:
            lat_map_min = lat_min
        if not np.isnan(self._lat_map_max):
            lat_map_max = self._lat_map_max
        else:
            lat_map_max = lat_max
        if not np.isnan(self._lon_map_min):
            lon_map_min = self._lon_map_min
        else:
            lon_map_min = lon_min
        if not np.isnan(self._lon_map_max):
            lon_map_max = self._lon_map_max
        else:
            lon_map_max = lon_max

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
        """Define the boundaries of the map \
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
        extent = self._get_map_extent(df)
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
        """Set the depth interval value. This represents the vertical resolution \
        of the final plot.

        Parameters
        ----------
        depth_interval : int | float | list[int|float], optional
            Depth interval values, if numeric, interval resolution, if instance of list,
            list of depth bins to use., by default np.nan
        """
        if isinstance(depth_interval, list) or (not np.isnan(depth_interval)):
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
            depth_bins = pd.IntervalIndex.from_arrays(intervals[:-1], intervals[1:])
        # if only the bin value resolution is given
        else:
            depth_bins = pd.interval_range(
                start=depth_min - depth_min % self._depth_interval,
                end=depth_max,
                freq=self._depth_interval,
                closed="right",
            )
        return depth_bins

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
        intervals = pd.IntervalIndex.from_arrays(
            pd.to_datetime(drng[drng_generator.start_column_name]),
            pd.to_datetime(drng[drng_generator.end_column_name]),
            closed="both",
        )
        return intervals

    def _create_cut_and_ticks(
        self,
        column_to_cut: pd.Series,
        cut_intervals: pd.IntervalIndex,
    ) -> Tuple[pd.IntervalIndex, np.ndarray]:
        """Return both the cut and the ticks values to use for the Figure.

        Parameters
        ----------
        column_to_cut : pd.Series
            Column to apply the cut to.
        cut_intervals : pd.IntervalIndex
            Intervals to use for the cut.

        Returns
        -------
        Tuple[pd.IntervalIndex, np.ndarray]
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
        if variable_name == "all":
            var_label = "all"
        else:
            var_label = self._variables.get(variable_name).label
        df = self._constraints.apply_constraints(self._storer.data, inplace=False)
        if var_label == "all":
            df.insert(0, var_label, 1)
        # Set 1 when the variable is not nan, otherwise 0
        var_count = (~df[var_label].isna()).astype(int)
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
        fig = plt.figure(figsize=[10, 5])
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
        suptitle = (
            "Evolution of data in the area of latitude in "
            f"[{round(lat_min,2)},{round(lat_max,2)}] and longitude in "
            f"[{round(lon_min,2)},{round(lon_max,2)}]"
        )
        plt.suptitle(suptitle)
        ax = plt.subplot(1, 1, 1)
        X, Y = np.meshgrid(date_ticks, depth_ticks)
        # Color mesh
        cbar = ax.pcolormesh(X, Y, df_pivot.values, **kwargs)
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
        plt.xticks(rotation=45)
        plt.tight_layout()
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
