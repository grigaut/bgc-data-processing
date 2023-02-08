"""Plotting tools"""


import os
from typing import TYPE_CHECKING

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from bgc_data_processing.mapper import config
from bgc_data_processing.mapper.tracers import GeoTracerNetCDF
from cartopy import crs, feature

if TYPE_CHECKING:
    from bgc_data_processing.mapper.loaders import NetCDFStorer
    from cartopy.mpl.geoaxes import GeoAxesSubplot
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure


def add_netcdf_lines(
    ax: "GeoAxesSubplot",
    to_plot: list["NetCDFStorer"],
    **kwargs,
) -> None:
    """Adds lines to an existing geo axes

    Parameters
    ----------
    ax : GeoAxesSubplot
        geo axes to add lines on
    to_plot : list[NetCDFStorer]
        List of objects to plot
    **kwargs : dict
        Additional plotting arguments that will be passed to 'plt.Line2D'.
    """
    for ncstorer in to_plot:
        GeoTracerNetCDF(ncstorer).create_line(ax=ax, **kwargs)


def create_fig(
    figsize: tuple[int],
    title: str,
) -> "Figure":
    """Creates a matplotlib figure.

    Parameters
    ----------
    figsize : tuple[int]
        Figure size.
    title : str
        Figure title.

    Returns
    -------
    Figure
        Created figure.
    """
    fig = plt.figure(figsize=figsize)
    fig.suptitle(title)
    return fig


def create_geoaxes(
    fig: "Figure",
    extent: tuple[int | float],
) -> "GeoAxesSubplot":
    """Creates a geoaxes on an existing figure.

    Parameters
    ----------
    fig : Figure
        Figure to add the axes on.
    extent : tuple[int  |  float]
        Location boundaries for the axes in the format (x0, x1, y0, y1)

    Returns
    -------
    GeoAxesSubplot
        Genrated Geoaxes.
    """
    ax = fig.add_subplot(
        1,
        1,
        1,
        projection=crs.Orthographic(0, 90),
    )
    ax.set_extent(
        extent,
        crs=crs.PlateCarree(),
    )
    ax.gridlines(
        draw_labels=True,
        dms=True,
        x_inline=False,
        y_inline=False,
    )
    ax.coastlines()
    ax.add_feature(feature.OCEAN, facecolor=feature.COLORS["water"], zorder=1)
    ax.add_feature(feature.LAND, facecolor="gray", zorder=2)
    return ax


def create_profile_axes(
    fig: "Figure",
    depth_max: int | float = 500,
) -> "Axes":
    """Creates axes for a depth profile.

    Parameters
    ----------
    fig : Figure
        Figure to add the axes on.
    depth_max : int | float, optional
        Maximal depth of the profile., by default 500

    Returns
    -------
    Axes
        Generated axes.
    """
    fig.autofmt_xdate()
    fig.tight_layout()
    ax: "Axes" = fig.add_subplot(
        1,
        1,
        1,
    )
    ax.invert_yaxis()
    ax.set_ylabel("Depth [m]")
    ax.set_xlabel("Date [YYYY-MM]")
    dfmt = mdates.DateFormatter("%Y-%m")
    lfmt = mdates.MonthLocator(interval=3)
    ax.xaxis.set_major_formatter(dfmt)
    ax.xaxis.set_major_locator(lfmt)
    ax.set_ylim([depth_max, 0])
    return ax


def plot_profile(
    ax: "Axes",
    df: pd.DataFrame,
    variable: str,
    profile_args: dict = config.PLOTTING["profile"],
) -> None:
    """Add a profile to an existing axes.

    Parameters
    ----------
    ax : Axes
        Axes to map the profile on.
    df : pd.DataFrame
        Data to map on the profile. Must contains "Depth level", "Date" and 'variable' columns.
    variable : str
        Variable to map on the profile.
    profile_args : dict, optional
        Additional mapping arguments, must contains the following keys :
        'variable', C, colormesh and label., by default config.PLOTTING["profile"]
    """
    plot_args = profile_args[variable]
    depths = df["Depth level"].unique()
    dates = df["Date"].unique()

    variable_array = df[[variable]].to_numpy()
    variable_array = variable_array.reshape((len(dates), len(depths)))
    xx, yy = np.meshgrid(dates, depths)

    cf = ax.pcolormesh(
        xx,
        yy,
        plot_args["C"](variable_array),
        **plot_args["colormesh"],
    )
    cb = plt.colorbar(cf, orientation="vertical", extend="both")
    cb.set_label(plot_args["label"], rotation=270, labelpad=15.0)


def create_output(
    fig: "Figure",
    show: bool = True,
    save: bool = False,
    dirout: str = None,
) -> None:
    """Generates the output (save and/or plot) of a figure.

    Parameters
    ----------
    fig : Figure
        Figure to display/save.
    show : bool, optional
        Whether to show the figure or not., by default True
    save : bool, optional
        Whether to save the figure or not., by default False
    dirout : str, optional
        Directory to save the figure in., by default None

    Raises
    ------
    ValueError
        If the outout directory is not an existing directory.
    """
    if show:
        plt.show()
    if save and dirout is not None:
        if os.path.isdir(dirout):
            title = fig._suptitle.get_text().lower().replace(" ", "_")
            fileout = dirout + "/" + title + ".png"
            fig.savefig(fileout)
        else:
            raise ValueError(f"{dirout} is not a directory")
    plt.close()
