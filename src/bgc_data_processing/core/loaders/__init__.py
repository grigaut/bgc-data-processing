"""Contains data loaders.

From this namespace are accessible:

- `ABFileLoader`            -> ABfiles loader
- `CSVLoader`               -> CSV files loader
- `NetCDFLoader`            -> NetCDF files loader
- `SatelliteNetCDFLoader`   -> NetCDF files loader for satellite data

"""

from bgc_data_processing.core.loaders.abfile_loaders import ABFileLoader
from bgc_data_processing.core.loaders.csv_loaders import CSVLoader
from bgc_data_processing.core.loaders.netcdf_loaders import (
    NetCDFLoader,
    SatelliteNetCDFLoader,
)

__all__ = [
    "ABFileLoader",
    "CSVLoader",
    "NetCDFLoader",
    "SatelliteNetCDFLoader",
]
