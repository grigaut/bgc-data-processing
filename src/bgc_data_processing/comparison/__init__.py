"""Tools to perform Comparison between observations and simulations.

From this namespace are accessible:
- `Interpolator`            -> Tool to interpolate data to match data's depth values
- `NearestNeighborStrategy` -> Closest point finding strategy
- `SelectiveDataSource`     -> Selective loader to retrieve data on given location only
- `metrics`                 -> Metrics to compare observations and simulations
"""

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
