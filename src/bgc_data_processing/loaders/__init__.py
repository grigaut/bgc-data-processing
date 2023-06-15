"""Data Loading objects."""

from bgc_data_processing.loaders.abfiles_loaders import from_abfile
from bgc_data_processing.loaders.csv_loaders import from_csv
from bgc_data_processing.loaders.netcdf_loaders import from_netcdf

__all__ = [
    "from_abfile",
    "from_csv",
    "from_netcdf",
]
