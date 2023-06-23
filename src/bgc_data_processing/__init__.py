"""Tools to load and display standardized biogeochemical data."""

from pathlib import Path

from bgc_data_processing import (
    comparison,
    defaults,
    features,
    parsers,
    providers,
    tracers,
    units,
)
from bgc_data_processing.comparison import SelectiveDataSource
from bgc_data_processing.core import variables
from bgc_data_processing.core.filtering import Constraints
from bgc_data_processing.core.io import read_files, save_storer, savers
from bgc_data_processing.core.storers import Storer
from bgc_data_processing.core.variables.sets import SourceVariableSet
from bgc_data_processing.utils import dateranges
from bgc_data_processing.water_masses import WaterMass

BASE_DIR = Path(__file__).parent.resolve()

__all__ = [
    "PROVIDERS_CONFIG",
    "DEFAULT_VARS",
    "DEFAULT_WATER_MASSES",
    "parsers",
    "read_files",
    "save_storer",
    "Constraints",
    "variables",
    "SourceVariableSet",
    "Storer",
    "SelectiveDataSource",
    "comparison",
    "providers",
    "defaults",
    "dateranges",
    "features",
    "tracers",
    "units",
    "savers",
    "WaterMass",
]
