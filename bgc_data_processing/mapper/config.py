"""Configuration information to use when using Argo data"""


import os

import numpy as np

FILEIN = "/mnt/data01/submapp/gotm/depth_levels.npy"
DIRIN_ARGO = "/var/sat/S23Eddy/Data/Argo/INSITU_GLO_BGC_REP"
dirout = "/home/gaerig/Projects/bgc-data-processing"
DEPTH_MAX = 500

# Creation of output directories :
dirout_figs = dirout + "/bgc_figs"
if not os.path.isdir(dirout_figs):
    os.mkdir(dirout_figs)
dirout_argo = dirout_figs + "/Argo"
if not os.path.isdir(dirout_argo):
    os.mkdir(dirout_argo)
DIROUT = dirout_argo
# Plotting
PLOTTING = {
    "profile": {
        "PSAL": {
            "C": lambda x: x[:-1, :-1].T,
            "colormesh": {
                "shading": "flat",
                "cmap": "rainbow",
                "vmin": 34.5,
                "vmax": 35.5,
            },
            "label": "Salinity [PSU]",
        },
        "TEMP": {
            "C": lambda x: x[:-1, :-1].T,
            "colormesh": {
                "shading": "flat",
                "cmap": "coolwarm",
                "vmin": 0,
                "vmax": 15,
            },
            "label": "Temperature [°C]",
        },
        "CPHL": {
            "C": lambda x: np.log(x[:-1, :-1].T),
            "colormesh": {
                "shading": "flat",
                "cmap": "viridis",
                "vmin": -4,
                "vmax": 2,
            },
            "label": "Chl [log(mg/m3)]",
        },
        "CPHL Raw": {
            "C": lambda x: np.log(x[:-1, :-1].T),
            "colormesh": {
                "shading": "flat",
                "cmap": "viridis",
                "vmin": -4,
                "vmax": 2,
            },
            "label": "Chl [log(mg/m3)]",
        },
    }
}
