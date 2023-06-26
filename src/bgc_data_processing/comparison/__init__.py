"""Tools to perform Comparison between observations and simulations."""

from bgc_data_processing.comparison import metrics
from bgc_data_processing.comparison.interpolation import Interpolator
from bgc_data_processing.comparison.matching import (
    NearestNeighborStrategy,
    SelectiveDataSource,
)

__all__ = [
    "Interpolator",
    "NearestNeighborStrategy",
    "SelectiveDataSource",
    "metrics",
]
