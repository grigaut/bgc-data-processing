"""Plot an interative map."""

import datetime as dt
import time
from copy import deepcopy
from pathlib import Path

import matplotlib.pyplot as plt
import shapely
from bgc_data_processing import DEFAULT_VARS, core
from bgc_data_processing.core import Constraints, Storer, StorerSaver
from bgc_data_processing.parsers import ConfigParser
from bgc_data_processing.tracers import DensityPlotter, EvolutionProfile
from cartopy import crs
from eomaps import Maps
from eomaps.draw import ShapeDrawer
from matplotlib import cm, colors
from matplotlib.axes import Axes

CONFIG_FOLDER = Path("config")

# Callbacks


def get_drawer_polygon(
    drawer: ShapeDrawer,
) -> shapely.Polygon:
    """Collect the polygon from a ShapeDrawer.

    Parameters
    ----------
    drawer : ShapeDrawer
        Drawer to get the polygon from.

    Returns
    -------
    shapely.Polygon
        Polygon object.
    """
    gdf = drawer.gdf
    gdf.to_crs(crs=4326, inplace=True)
    return gdf["geometry"].iloc[-1]


def update_profile(
    polygon: shapely.Polygon,
    storer: Storer,
    axes: Axes,
    colorbar_axes: Axes,
    constraints_base: Constraints,
):
    """Update the evolution profile plot.

    Parameters
    ----------
    polygon : shapely.Polygon
        Polygon to use to select data.
    storer : Storer
        Storer to use the data of for plotting.
    axes : Axes
        Axes to plot the resulting plot onto.
    colorbar_axes: Axes
        Axes to plot the colorbar to.
    constraints_base: Constraints
        Base of constraint to use for the new data.
    """
    variables = storer.variables
    latitude_field = variables.get(variables.latitude_var_name).label
    longitude_field = variables.get(variables.longitude_var_name).label
    constraints = deepcopy(constraints_base)
    constraints.add_polygon_constraint(
        latitude_field=latitude_field,
        longitude_field=longitude_field,
        polygon=polygon,
    )
    profile_tmp = EvolutionProfile(storer, constraints)
    profile_tmp.set_date_intervals("week")
    profile_tmp.set_depth_interval(100)
    _, cbar = profile_tmp.plot_to_axes(VARIABLE, axes)
    axes.tick_params(axis="x", labelrotation=45)
    plt.colorbar(cbar, cax=colorbar_axes)


def update_map(
    polygon: shapely.Polygon,
    storer: Storer,
    zoom_map_bg: Maps,
    colorbar_axes: Axes,
    constraints_base: Constraints,
):
    """Update the zoomed map.

    Parameters
    ----------
    polygon : shapely.Polygon
        Polygon to use to select data.
    storer : Storer
        Storer to use the data of for plotting.
    zoom_map_bg : Maps
        Map to update.
    colorbar_axes: Axes
        Axes to plot the colorbar to.
    constraints_base: Constraints
        Base of constraint to use for the new data.
    """
    variables = storer.variables
    latitude_field = variables.get(variables.latitude_var_name).label
    longitude_field = variables.get(variables.longitude_var_name).label
    constraints = deepcopy(constraints_base)
    constraints.add_polygon_constraint(
        latitude_field=latitude_field,
        longitude_field=longitude_field,
        polygon=polygon,
    )
    lon_bin = (polygon.bounds[2] - polygon.bounds[0]) / 100
    plot_tmp = DensityPlotter(storer, constraints)
    plot_tmp.set_density_type(consider_depth=True)
    plot_tmp.set_bins_size(bins_size=[lon_bin, lon_bin * 3])
    df = plot_tmp.get_df(VARIABLE)
    new_map = zoom_map_bg.new_layer(f"layer{time.time()}")
    new_map.set_data(
        data=df,
        x="LONGITUDE",
        y="LATITUDE",
        crs=4326,
        parameter=VARIABLE,
    )
    new_map.set_shape.rectangles()
    new_map.plot_map(zorder=0)
    plt.colorbar(
        cm.ScalarMappable(
            norm=colors.Normalize(vmin=df[VARIABLE].min(), vmax=df[VARIABLE].max()),
        ),
        cax=colorbar_axes,
    )
    zoom_map_bg.show_layer(zoom_map_bg.layer, new_map.layer)


def update_from_drawer(
    drawers: list[ShapeDrawer],
    storer: Storer,
    zoom_map_bg: Maps,
    zoom_cbar_axes: Axes,
    profile_axes: Axes,
    profile_cbar_axes: Axes,
    constraints_base: Constraints,
    **_kwargs,
):
    """Update the lateral maps using the ShapeDrawer polygon.

    Parameters
    ----------
    drawers : list[ShapeDrawer]
        List of all drawers, only the last one will be used.
    storer : Storer
        Storer to use the data of.
    zoom_map_bg : Maps
        Map on which to plot the zoomed view.
    zoom_cbar_axes : Axes
        Axes on which to plot the zoomed view colorbar.
    profile_axes : Axes
        Axes on which to plot the evolution profile.
    profile_cbar_axes : Axes
        Axes on which to plot the evolution profile colorbar.
    constraints_base: Constraints
        Base of constraint to use for the new data.
    """
    polygon = get_drawer_polygon(drawer=drawers[-1])
    update_map(
        polygon=polygon,
        storer=storer,
        zoom_map_bg=zoom_map_bg,
        colorbar_axes=zoom_cbar_axes,
        constraints_base=constraints_base,
    )
    update_profile(
        polygon=polygon,
        storer=storer,
        axes=profile_axes,
        colorbar_axes=profile_cbar_axes,
        constraints_base=constraints_base,
    )


def update_from_loaded(
    storer: Storer,
    zoom_map_bg: Maps,
    zoom_cbar_axes: Axes,
    profile_axes: Axes,
    profile_cbar_axes: Axes,
    constraints_base: Constraints,
    polygons_history: list[tuple[str, ShapeDrawer | shapely.Polygon]],
    **_kwargs,
):
    """Update the lateral maps from a loaded polygon.

    Parameters
    ----------
    storer : Storer
        Storer to use the data of.
    zoom_map_bg : Maps
        Map on which to plot the zoomed view.
    zoom_cbar_axes : Axes
        Axes on which to plot the zoomed view colorbar.
    profile_axes : Axes
        Axes on which to plot the evolution profile.
    profile_cbar_axes : Axes
        Axes on which to plot the evolution profile colorbar.
    constraints_base: Constraints
        Base of constraint to use for the new data.
    """
    polygon = load_polygon()
    polygons_history.append(("load", polygon))
    update_map(
        polygon=polygon,
        storer=storer,
        zoom_map_bg=zoom_map_bg,
        colorbar_axes=zoom_cbar_axes,
        constraints_base=constraints_base,
    )
    update_profile(
        polygon=polygon,
        storer=storer,
        axes=profile_axes,
        colorbar_axes=profile_cbar_axes,
        constraints_base=constraints_base,
    )


def clear(
    drawers: list[ShapeDrawer],
    zoom_map_bg: Maps,
    rectilinear_axes: list[Axes],
    **_kwargs,
):
    """Clear the temporary plots and the polygon trace.

    Parameters
    ----------
    drawers : list[ShapeDrawer]
        List of all drawers.
    main_map : Maps
        Main map to create a new polygon drawer.
    zoom_map_bg : Maps
        Background map of the zoomed map.
    rectilinear_axes : list[Axes]
        All rectilinear axes (colorbars for example) to clear.
    """
    for axes in rectilinear_axes:
        axes.clear()
        axes.relim()
    zoom_map_bg.show_layer(zoom_map_bg.layer)
    if drawers:
        drawers[0].remove_last_shape()


def save(
    storer: Storer,
    constraints_base: Constraints,
    polygons_history: list[tuple[str, ShapeDrawer | shapely.Polygon]],
    **_kwargs,
) -> None:
    """Save the data from the polygon in a file.

    Parameters
    ----------
    drawers : list[ShapeDrawer]
        List of all drawers.
    storer : Storer
        Storer to use the data of.
    constraints_base: Constraints
        Base of constraint to use for the new data.
    """
    last_polygon = polygons_history[-1]
    if last_polygon[0] == "load":
        polygon = last_polygon[1]
    else:
        polygon = get_drawer_polygon(last_polygon[1])
    variables = storer.variables
    latitude_field = variables.get(variables.latitude_var_name).label
    longitude_field = variables.get(variables.longitude_var_name).label
    constraints = constraints_base
    constraints.add_polygon_constraint(
        latitude_field=latitude_field,
        longitude_field=longitude_field,
        polygon=polygon,
    )
    new_storer = Storer.from_constraints(storer=storer, constraints=constraints)
    print("Enter the name of the file (don't write the extension):")
    filename = Path(input().replace(" ", "_") + ".txt")
    if filename == ".txt":
        filename = Path(f"output_{round(time.time())}.txt")
    saver = StorerSaver(new_storer)
    saver.save_all_storer(filepath=filename)
    print(f"File saved under {filename}")


def start_drawing(
    drawers: list,
    main_map: Maps,
    polygons_history: list[tuple[str, ShapeDrawer | shapely.Polygon]],
    **_kwargs,
) -> None:
    """Trigger the drawing of a polygon.

    Parameters
    ----------
    drawers : list
        List of all the drawers.
    main_map : Maps
        Map to draw onto.
    """
    drawer = ShapeDrawer(main_map)
    drawer.polygon(draw_on_drag=True, fill=False, color="red")
    if not drawers:
        drawers.append(drawer)
    else:
        drawers[0] = drawer
    polygons_history.append(("draw", drawer))


def save_polygon(drawers: list[ShapeDrawer], **_kwargs):
    """Save polygon to file.

    Parameters
    ----------
    drawers : list[ShapeDrawer]
        List of drawers, only the last one will be saved.
    """
    if not drawers:
        print("No Polygon existing at the moment")
        return
    gdf = drawers[-1].gdf
    gdf.to_crs(crs=4326, inplace=True)
    if gdf.empty:
        print("No Polygon existing at the moment")
        return
    polygon = gdf["geometry"].iloc[-1]
    print("Enter the name of the file (don't write the extension):")
    filename = Path(input().replace(" ", "_") + ".txt")
    if filename == ".txt":
        filename = f"polygon_{round(time.time())}.txt"
    filepath = POLYGONS_FOLDER.joinpath(filename)
    polygon_wkt = shapely.to_wkt(polygon)
    with filepath.open("w") as file:
        file.write(polygon_wkt)
    print(f"Polygon saved under {filepath}")


def load_polygon(**_kwargs) -> shapely.Polygon:
    """Load Polygon from a file.

    Returns
    -------
    shapely.Polygon
        The loaded polygon.

    Raises
    ------
    FileNotFoundError
        If the file doesn't exist.
    """
    print(
        "Enter the name of file storing a polygon"
        f"(inside the '{POLYGONS_FOLDER}' folder) without its extension",
    )
    filename = Path(input().replace(" ", "_") + ".txt")
    filepath = POLYGONS_FOLDER.joinpath(filename)
    if not filepath.is_file():
        raise FileNotFoundError(f"Loading aborted : the file {filepath} doesn't exist.")
    with filepath.open() as file:
        first_line = file.readlines()[0]
        print(first_line)
        polygon = shapely.from_wkt(first_line)
    print(f"Successfully loaded polygon from {filepath}")
    return polygon


if __name__ == "__main__":
    config_filepath = CONFIG_FOLDER.joinpath(Path(__file__).stem)
    CONFIG = ConfigParser(
        filepath=config_filepath.with_suffix(".toml"),
        dates_vars_keys=["DATE_MIN", "DATE_MAX"],
        dirs_vars_keys=[],
        existing_directory="raise",
    )
    LOADING_DIR = Path(CONFIG["LOADING_DIR"])
    VARIABLE: str = CONFIG["VARIABLE"]
    EXPOCODES_TO_LOAD: list[str] = CONFIG["EXPOCODES_TO_LOAD"]
    DATE_MIN: dt.datetime = CONFIG["DATE_MIN"]
    DATE_MAX: dt.datetime = CONFIG["DATE_MAX"]
    LONGITUDE_MIN: int | float = CONFIG["LONGITUDE_MIN"]
    LONGITUDE_MAX: int | float = CONFIG["LONGITUDE_MAX"]
    LATITUDE_MIN: int | float = CONFIG["LATITUDE_MIN"]
    LATITUDE_MAX: int | float = CONFIG["LATITUDE_MAX"]
    DEPTH_MIN: int | float = CONFIG["DEPTH_MIN"]
    DEPTH_MAX: int | float = CONFIG["DEPTH_MAX"]
    CONSIDER_DEPTH: bool = CONFIG["CONSIDER_DEPTH"]
    BIN_SIZE: list[int | float] = CONFIG["BIN_SIZE"]
    LATITUDE_MAP_MIN: int | float = CONFIG["LATITUDE_MAP_MIN"]
    LATITUDE_MAP_MAX: int | float = CONFIG["LATITUDE_MAP_MAX"]
    LONGITUDE_MAP_MIN: int | float = CONFIG["LONGITUDE_MAP_MIN"]
    LONGITUDE_MAP_MAX: int | float = CONFIG["LONGITUDE_MAP_MAX"]
    PRIORITY: list[str] = CONFIG["PRIORITY"]
    POLYGONS_FOLDER = Path(CONFIG["POLYGONS_FOLDER"])

    filepaths_txt = list(LOADING_DIR.glob("*.txt"))
    filepaths_csv = list(LOADING_DIR.glob("*.csv"))
    filepaths = filepaths_txt + filepaths_csv

    storer = core.read_files(
        filepath=filepaths,
        providers_column_label=DEFAULT_VARS["provider"].label,
        expocode_column_label=DEFAULT_VARS["expocode"].label,
        date_column_label=DEFAULT_VARS["date"].label,
        year_column_label=DEFAULT_VARS["year"].label,
        month_column_label=DEFAULT_VARS["month"].label,
        day_column_label=DEFAULT_VARS["day"].label,
        hour_column_label=DEFAULT_VARS["hour"].label,
        latitude_column_label=DEFAULT_VARS["latitude"].label,
        longitude_column_label=DEFAULT_VARS["longitude"].label,
        depth_column_label=DEFAULT_VARS["depth"].label,
        category="in_situ",
        unit_row_index=1,
        delim_whitespace=True,
        verbose=1,
    )
    storer.remove_duplicates(PRIORITY)
    variables = storer.variables
    constraints = Constraints()
    constraints.add_superset_constraint(
        field_label=variables.get(variables.expocode_var_name).label,
        values_superset=EXPOCODES_TO_LOAD,
    )
    constraints.add_boundary_constraint(
        field_label=variables.get(variables.date_var_name).label,
        minimal_value=DATE_MIN,
        maximal_value=DATE_MAX,
    )
    constraints.add_boundary_constraint(
        field_label=variables.get(variables.latitude_var_name).label,
        minimal_value=LATITUDE_MIN,
        maximal_value=LATITUDE_MAX,
    )
    constraints.add_boundary_constraint(
        field_label=variables.get(variables.longitude_var_name).label,
        minimal_value=LONGITUDE_MIN,
        maximal_value=LONGITUDE_MAX,
    )
    constraints.add_boundary_constraint(
        field_label=variables.get(variables.depth_var_name).label,
        minimal_value=DEPTH_MIN,
        maximal_value=DEPTH_MAX,
    )
    constraints_copy = deepcopy(constraints)
    # --------- Initialize the axes
    figure = plt.figure(figsize=(15, 10), layout="tight")

    # Plot axes
    main_axes = figure.add_subplot(
        10,
        15,
        (32, 144),
        projection=crs.Orthographic(0, 90),
    )
    zoom_axes = figure.add_subplot(10, 15, (10, 74), projection=crs.Orthographic(0, 90))
    profile_axes = figure.add_subplot(10, 15, (85, 149), projection="rectilinear")

    # Instructions axes
    text_axes = figure.add_subplot(10, 15, (1, 24), projection=crs.PlateCarree())

    # Colorbars axes
    main_axes_cbar = figure.add_subplot(10, 15, (31, 136), projection="rectilinear")
    zoom_axes_cbar = figure.add_subplot(10, 15, (15, 75), projection="rectilinear")
    profile_axes_cbar = figure.add_subplot(10, 15, (90, 150), projection="rectilinear")

    # --------- Initialize Instructions Axes
    # We use a Maps otherwise the axes doesn't render in the beginning
    text_map = Maps(ax=text_axes)
    text_map.set_extent([-180, 180, -34, 40])
    text_axes.text(-175, 32, "Controls:")
    text_axes.text(-175, 24, "  - 'D' to start drawing a polygon, then: ")
    text_axes.text(
        -175,
        16,
        "    - Left Click to draw polygon (keep the button clicked).",
    )
    text_axes.text(-175, 8, "    - Middle Click to close the polygon shape.")
    text_axes.text(
        -175,
        0,
        "  - 'Enter' key to confirm the polygon as area to zoom in.",
    )
    text_axes.text(-175, -8, "  - 'Z' key to remove the polygon and draw another one.")
    text_axes.text(
        -175,
        -16,
        "  - 'S' to save the data within the polygon"
        " (then you must enter a filename in the terminal).",
    )
    text_axes.text(
        -175,
        -24,
        "  - 'P' to save the polygon (then you must enter a filename in the terminal).",
    )
    text_axes.text(
        -175,
        -32,
        "  - 'L' to load a polygon (then you must enter the name of the file to load).",
    )

    # --------- Initialize Main Map
    # Create Map
    main_map = Maps(ax=main_axes)
    # Set extent and background
    main_map.set_extent(
        (LONGITUDE_MAP_MIN, LONGITUDE_MAP_MAX, LATITUDE_MAP_MIN, LATITUDE_MAP_MAX),
        crs=4326,
    )
    main_map.add_feature.preset.coastline(zorder=1)
    main_map.add_feature.preset.land(zorder=1)
    main_map.add_feature.preset.ocean()
    # Plotter for the map
    plot = DensityPlotter(storer=storer, constraints=constraints_copy)
    plot.set_density_type(consider_depth=CONSIDER_DEPTH)
    plot.set_bins_size(bins_size=BIN_SIZE)
    plot.set_map_boundaries(
        latitude_min=LATITUDE_MAP_MIN,
        latitude_max=LATITUDE_MAP_MAX,
        longitude_min=LONGITUDE_MAP_MIN,
        longitude_max=LONGITUDE_MAP_MAX,
    )
    data = plot.get_df(VARIABLE)
    # Set plotter's data to the map
    longitude_var_name = storer.variables.longitude_var_name
    latitude_var_name = storer.variables.latitude_var_name
    main_map.set_data(
        data=data,
        x=storer.variables.get(longitude_var_name).label,
        y=storer.variables.get(latitude_var_name).label,
        crs=4326,
        parameter=VARIABLE,
    )
    main_map.set_shape.rectangles()
    cbar = plt.colorbar(
        cm.ScalarMappable(
            norm=colors.Normalize(vmin=data[VARIABLE].min(), vmax=data[VARIABLE].max()),
        ),
        cax=main_axes_cbar,
    )
    # plot the map
    main_map.plot_map()

    # --------- Initialize zoomed map
    # Create map
    zoom_map_bg = Maps(ax=zoom_axes)
    # Set background
    zoom_map_bg.add_feature.preset.coastline(zorder=1)
    zoom_map_bg.add_feature.preset.land(zorder=1)
    zoom_map_bg.add_feature.preset.ocean()
    zoom_map_bg.show_layer(zoom_map_bg.layer)

    # --------- Initialize Drawers
    drawers = []

    # --------- Initialize polygon origin list
    polygons_history: list[tuple[str, ShapeDrawer | shapely.Polygon]] = []

    # --------- Callbacks
    main_map.cb.keypress.attach(
        update_from_drawer,
        key="enter",
        drawers=drawers,
        storer=storer,
        zoom_map_bg=zoom_map_bg,
        zoom_cbar_axes=zoom_axes_cbar,
        profile_axes=profile_axes,
        profile_cbar_axes=profile_axes_cbar,
        constraints_base=constraints,
    )
    main_map.cb.keypress.attach(
        clear,
        key="z",
        drawers=drawers,
        zoom_map_bg=zoom_map_bg,
        rectilinear_axes=[profile_axes, profile_axes_cbar, zoom_axes_cbar],
    )
    main_map.cb.keypress.attach(
        save,
        key="s",
        drawers=drawers,
        storer=storer,
        constraints_base=constraints,
        polygons_history=polygons_history,
    )

    main_map.cb.keypress.attach(
        save_polygon,
        key="p",
        drawers=drawers,
        constraints_base=constraints,
    )

    main_map.cb.keypress.attach(
        clear,
        key="d",
        drawers=drawers,
        zoom_map_bg=zoom_map_bg,
        rectilinear_axes=[profile_axes, profile_axes_cbar, zoom_axes_cbar],
    )
    main_map.cb.keypress.attach(
        start_drawing,
        key="d",
        drawers=drawers,
        main_map=main_map,
        zoom_map_bg=zoom_map_bg,
        rectilinear_axes=[profile_axes, profile_axes_cbar, zoom_axes_cbar],
        polygons_history=polygons_history,
    )
    main_map.cb.keypress.attach(
        clear,
        key="l",
        drawers=drawers,
        zoom_map_bg=zoom_map_bg,
        rectilinear_axes=[profile_axes, profile_axes_cbar, zoom_axes_cbar],
    )
    main_map.cb.keypress.attach(
        update_from_loaded,
        key="l",
        storer=storer,
        zoom_map_bg=zoom_map_bg,
        zoom_cbar_axes=zoom_axes_cbar,
        profile_axes=profile_axes,
        profile_cbar_axes=profile_axes_cbar,
        constraints_base=constraints,
        polygons_history=polygons_history,
    )
    plt.show()
