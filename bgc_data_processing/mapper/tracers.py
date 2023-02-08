import datetime as dt
from typing import TYPE_CHECKING

import cartopy.crs as ccrs
import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.collections import PathCollection


class BaseGeoTracer:
    """Base class for tracing on earthmaps.

    Parameters
    ----------
    data : pd.DataFrame
        Data to use when plotting.
    """

    def __init__(
        self,
        data: pd.DataFrame,
    ) -> None:
        self._data = data
        self.all_latitude
        self.aggr_func = {
            "mean": lambda x: np.nanmean(x, axis=1),
            "max": lambda x: np.nanmax(x, axis=1),
            "min": lambda x: np.nanmin(x, axis=1),
            "top": lambda x: x[:, 0],
            "bottom": lambda x: x[:, -1],
            "count": lambda x: (~np.isnan(x)).sum(axis=1),
        }

    @property
    def all_longitude(self) -> np.ndarray:
        return self._data["LONGITUDE"][:]

    @property
    def all_latitude(self) -> np.ndarray:
        return self._data["LATITUDE"][:]

    def create_line(
        self,
        ax: "Axes",
        **kwargs,
    ) -> list:
        """Creates a line linking all observation points.

        Parameters
        ----------
        ax : Axes
            Axes to plot on.
        kwargs : dict
            Additional parmeter to pass to ax.plot.

        Returns
        -------
        list
            ax.plot output.
        """
        return ax.plot(
            self.all_longitude,
            self.all_latitude,
            transform=ccrs.PlateCarree(),
            **kwargs,
        )

    def get_data(self, variable: str) -> dict:
        """Returns the data values (and dates and positions) for the given variable.
        This method must be created for each subclass.

        Parameters
        ----------
        variable : str
            Variable to select

        Returns
        -------
        dict
            Output data
        """
        # To be define in each subclass
        pass

    def create_colored_scatter(
        self,
        ax: "Axes",
        variable: str,
        aggregation: str = "mean",
        **kwargs,
    ) -> "PathCollection":
        """Colorates scatter points depennding on the value.

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
        ax.scatter(
            x=data["LONGITUDE"],
            y=data["LATITUDE"],
            transform=ccrs.PlateCarree(),
            c=aggr_data,
            **kwargs,
        )

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

    def create_scatter(
        self,
        ax: "Axes",
        **kwargs,
    ) -> "PathCollection":
        """Creates the scatter plot

        Parameters
        ----------
        ax : Axes
            Axes to plot on.
        kwargs: dict
            Additional arguments to pass to ax.scatter
        """
        ax.scatter(
            x=self.all_longitude,
            y=self.all_latitude,
            transform=ccrs.PlateCarree(),
            **kwargs,
        )


class GeoTracerDataFrame(BaseGeoTracer):
    """GeoTracer implementation to handle data stored in dataframe

    Parameters
    ----------
    data : pd.dataFrame
        Data to use when mapping.
    """

    def __init__(
        self,
        data: pd.DataFrame,
    ) -> None:

        self.all_dates = pd.to_datetime(data[["YEAR", "MONTH", "DAY"]])
        super().__init__(data)

    def get_data(
        self,
        variable: str,
    ) -> dict:
        """Collect data for the variable specified.
        The variable is mapped on a 2D array in order to represent its 2 dimensions :
        location on the ocean (latitude, longitude and date) and its depth.
        Therefore, this of representing the data matches the way netCDF data is stored.

        Parameters
        ----------
        variable : str
            Data variable to collect.

        Returns
        -------
        dict
            Data (variable, locations, dates) from self._data corresponding to the variable.
        """
        slice = self._data.filter(
            [
                "YEAR",
                "MONTH",
                "DAY",
                "LONGITUDE",
                "LATITUDE",
                "DEPH",
                variable,
            ]
        )
        # Switching to positive values for the data
        slice["DEPH"] = slice["DEPH"].map(lambda x: np.abs(x))
        # Pivoting table to create a 2D variable
        piv = pd.pivot_table(
            slice,
            values=variable,
            index=["YEAR", "MONTH", "DAY", "LONGITUDE", "LATITUDE"],
            columns=["DEPH"],
            fill_value=np.nan,
        )
        # Sorting depths
        piv.sort_index(axis=0, inplace=True)
        output_data = {}
        output_data["DATA"] = piv.values
        output_data["DEPH"] = pd.Series(piv.columns)
        # Index reset to get latitude, longitude and date of the data samples
        reset = piv.reset_index()
        output_data["LATITUDE"] = reset["LATITUDE"]
        output_data["LONGITUDE"] = reset["LONGITUDE"]
        output_data["DATE"] = pd.to_datetime(reset[["YEAR", "MONTH", "DAY"]])
        return output_data


class GeoTracerNetCDF(BaseGeoTracer):
    """GeoTracer implementation to handle data stored in NetCDFStorer

    Parameters
    ----------
    netcdf_data : NetCDFStorer
        Data to use when mapping.
    """

    def __init__(
        self,
        netcdf_data,
    ) -> None:
        data_start_date = dt.datetime(1950, 1, 1, 0, 0, 0)
        data = netcdf_data.get_content().variables
        timedeltas = pd.to_timedelta(data["TIME"][:], "D")
        self.all_dates = (timedeltas + data_start_date).values
        super().__init__(data)

    def get_data(self, variable: str) -> dict:
        """Collect data for the variable specified.

        Parameters
        ----------
        variable : str
            Data variable to collect.

        Returns
        -------
        dict
            Data (variable, locations, dates) from self._data corresponding to the variable.
        """
        output_data = {}
        output_data["DATES"] = self.all_dates
        output_data["LATITUDE"] = self.all_latitude
        output_data["LONGITUDE"] = self.all_longitude
        output_data["DEPH"] = self._data["PRES"][:].filled(np.nan)
        output_data["DATA"] = self._data[variable][:].filled(np.nan)
        return output_data
