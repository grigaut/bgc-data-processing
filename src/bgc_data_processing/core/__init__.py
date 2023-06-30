"""Core module of `bgc_data_processing` to manipulate data.

Please note that this module's main functionalities are accessible
from the main `bgc_data_processing` namespace.

From this namespace are accessible:

- `filtering`   -> filtering and slicing related objects for bgc data
- `io`          -> input/output related objects
- `loaders`     -> data loading-related objects
- `sources`     -> provider-definition related objects
- `storers`     -> biogeochemical data-realted storing objects
- `variables`   -> variables-related storing objects
"""

from bgc_data_processing.core import filtering, io, loaders, sources, storers, variables

__all__ = [
    "filtering",
    "io",
    "loaders",
    "sources",
    "storers",
    "variables",
]
