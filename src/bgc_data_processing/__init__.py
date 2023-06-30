"""
Biogeochemical Data Processing module for Python
================================================

bgc-data-processing is a module to preprocess and analyze Biogeochemical Data
with standard formats (CSV, NetCDF...).

This module provides tools to:

- Preprocess Data from different sources
- Save preprocessed data under a standardized format
- Read preprocessed data and perform some analysis on it (visual validation,
    water mass comparison...)

All docstrings examples will assume that `bgc_data_processing`
has been imported as `bgc_dp`:

```
>>> import bgc_data_processing as bgc_dp
```

From this namespace are accessible:

- `Constraints`             -> Constraints object to slice storers
- `DataSource`              -> Providers defining object
- `SelectiveDataSource`     -> Selective loader
- `SourceVariableSet`       -> Set of variables to pass to datasource
- `Storer`                  -> Biogeochemical data and metadat storer
- `WaterMass`               -> Water mass defining object
- `comparison`              -> Comparison tools to compare observations to simulations
- `dateranges`              -> Daterange-related objects
- `defaults`                -> Defaults objects parsed from the configuration files
- `exceptions`              -> Exceptions fro the project
- `features`                -> Features to compute new variables
- `io`                      -> Input/Output tools
- `metrics`                 -> Comparison metrics
- `parsers`                 -> Configuartion parsing objects
- `providers`               -> Providers loaders
- `savers`                  -> Saving objects
- `set_verbose_level`       -> Set the verbose level
- `tracers`                 -> Plotting objects
- `units`                   -> Unit conversion
- `utils`                   -> Utilities
- `variables`               -> Variables-related objects
- `water_masses`            -> Water mass definition

"""  # noqa: D205, D400

from pathlib import Path

from bgc_data_processing import (
    comparison,
    defaults,
    exceptions,
    features,
    parsers,
    providers,
    tracers,
    units,
    utils,
    water_masses,
)
from bgc_data_processing.comparison import metrics
from bgc_data_processing.comparison.matching import SelectiveDataSource
from bgc_data_processing.core import io, variables
from bgc_data_processing.core.filtering import Constraints
from bgc_data_processing.core.io import savers
from bgc_data_processing.core.sources import DataSource
from bgc_data_processing.core.storers import Storer
from bgc_data_processing.core.variables.sets import SourceVariableSet
from bgc_data_processing.utils import dateranges
from bgc_data_processing.verbose import set_verbose_level
from bgc_data_processing.water_masses import WaterMass

BASE_DIR = Path(__file__).parent.resolve()

__all__ = [
    "Constraints",
    "DataSource",
    "SelectiveDataSource",
    "SourceVariableSet",
    "Storer",
    "WaterMass",
    "comparison",
    "dateranges",
    "defaults",
    "exceptions",
    "features",
    "io",
    "metrics",
    "parsers",
    "providers",
    "savers",
    "set_verbose_level",
    "tracers",
    "units",
    "utils",
    "variables",
    "water_masses",
]
