"""Plotting tools"""


import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from bgc_data_processing.mapper import config
from matplotlib.axes import Axes
from matplotlib.figure import Figure


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
