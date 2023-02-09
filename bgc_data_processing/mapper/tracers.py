from typing import TYPE_CHECKING

import cartopy.crs as ccrs
import numpy as np
import pandas as pd
from bgc_data_processing.base import Storer

if TYPE_CHECKING:
    from matplotlib.axes import Axes


class GeoTracer:
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
        self._variables = storer._variables
        self._data = storer.data.sort_values(
            self._variables["DEPH"].key, ascending=False
        )
        self._cols_to_group_with = []
        for var_name in [
            "PROVIDER",
            "EXPOCODE",
            "YEAR",
            "MONTH",
            "DAY",
            "LONGITUDE",
            "LATITUDE",
        ]:
            if var_name in self._variables.keys():
                series = self._data[self._variables[var_name].key]
                self._cols_to_group_with.append(series)

    def _group(
        self,
        key: str,
        how: str = "top",
        bins: int | tuple[int, int] = 10,
    ) -> pd.DataFrame:
        var_col_name = self._variables[key].key
        dep_col_name = self._variables["DEPH"].key
        lat_col_name = self._variables["LATITUDE"].key
        lon_col_name = self._variables["LONGITUDE"].key
        if isinstance(bins, tuple):
            lat_bins, lon_bins = bins[0], bins[1]
        else:
            lat_bins, lon_bins = bins, bins
        grouping_series = self._cols_to_group_with
        group = self._data.groupby(grouping_series)
        var_series = self._grouping_functions[how](group[var_col_name])
        dep_series = self._grouping_functions[how](group[dep_col_name])
        concatenated = pd.concat([dep_series, var_series], axis=1).reset_index()
        slice = concatenated[[dep_col_name, var_col_name]]
        lat_bins = pd.cut(concatenated[lat_col_name], bins=lat_bins).apply(
            lambda x: x.mid
        )
        lon_bins = pd.cut(concatenated[lon_col_name], bins=lon_bins).apply(
            lambda x: x.mid
        )
        slice["lat_bins"] = lat_bins
        slice["lon_bins"] = lon_bins
        print(slice)
        group_by_bins = slice.groupby(["lat_bins", "lon_bins"], dropna=True).mean()
        return group_by_bins[~group_by_bins.isna().all(axis=1)]

    def create_hexbin(
        self,
        ax: "Axes",
        variable: str,
        aggregation: str = "mean",
        **kwargs,
    ) -> None:
        """Generates the colormap for a given value.

        Parameters
        ----------
        ax : Axes
            Axes to plot on.
        variable : str
            Variable to base the mapping on.
        aggregation :
            Key name for the aggregation function to use.
            The dictionnary listing the functions is defined as an attribute of BaseGeoTracer., by default "mean"
        kwargs: dict
            Addtitional arguments to pass to ax.scatter.
        """

        data = self.get_data(variable)
        aggr_data = self.aggr_func[aggregation](data["DATA"])
        default_gridsize = int(np.power(aggr_data.shape[0], 1 / 3)) + 1
        gridsize = kwargs.pop("gridsize", default_gridsize)
        cbar = ax.hexbin(
            x=data["LONGITUDE"],
            y=data["LATITUDE"],
            C=aggr_data,
            transform=ccrs.PlateCarree(),
            gridsize=gridsize,
            **kwargs,
        )
        ax.get_figure().colorbar(cbar, label=f"{variable} - {aggregation}")
