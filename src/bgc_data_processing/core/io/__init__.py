"""Input-Output methods.

This module regroup all objects which aim at saving storers
or reading data from already saved storers.

From this namespace are accessible:

- `read_files`  -> File reading function
- `save_storer` -> Storer saviing function
"""

from bgc_data_processing.core.io.readers import read_files
from bgc_data_processing.core.io.savers import save_storer

__all__ = ["read_files", "save_storer"]
