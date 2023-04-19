"""Functions to convert a shaeply Polygon to list of nodes."""

from typing import TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from shapely import Polygon


def polygon_to_list(polygon: "Polygon") -> Tuple[list, list]:
    """Convert polygon from shapely to list of coordinates.

    Parameters
    ----------
    polygon : Polygon
        Polygon to convert.

    Returns
    -------
    Tuple[list, list]
        List of longitude values, list of latitude values.
    """
    x_raw, y_raw = polygon.exterior.coords.xy
    x = list(x_raw)
    y = list(y_raw)
    return x, y
