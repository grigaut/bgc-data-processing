"""Plot an interative map."""

import os
from matplotlib.axes import Axes
from bgc_data_processing.data_classes import Storer, Constraints
from bgc_data_processing.tracers import MeshPlotter, EvolutionProfile
from cartopy import crs
import time
from matplotlib import cm, colors
from eomaps import Maps
import shapely
from eomaps.draw import ShapeDrawer
import matplotlib.pyplot as plt


POLYGONS_FOLDER = "polygons"

filepaths = [
    f"bgc_data/{file}"
    for file in os.listdir("bgc_data")
    if file[-4:] in [".csv", ".txt"]
]

storer = Storer.from_files(
    filepath=filepaths,
    providers_column_label="PROVIDER",
    expocode_column_label="EXPOCODE",
    date_column_label="DATE",
    year_column_label="YEAR",
    month_column_label="MONTH",
    day_column_label="DAY",
    hour_column_label="HOUR",
    latitude_column_label="LATITUDE",
    longitude_column_label="LONGITUDE",
    depth_column_label="DEPH",
    category="in_situ",
    unit_row_index=1,
    delim_whitespace=True,
    verbose=1,
)
storer.remove_duplicates(
    ["GLODAP_2022", "CMEMS", "ARGO", "NMDC", "CLIVAR", "IMR", "ICES"]
)
# --------- Initialize the axes
figure = plt.figure(figsize=(15, 10), layout="tight")

# Plot axes
main_axes = figure.add_subplot(10, 15, (32, 144), projection=crs.Orthographic(0, 90))
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
text_axes.text(-175, 16, "    - Left Click to draw polygon (keep the button clicked).")
text_axes.text(-175, 8, "    - Middle Click to close the polygon shape.")
text_axes.text(-175, 0, "  - 'Enter' key to confirm the polygon as area to zoom in.")
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
main_map.set_extent((-180, 180, 50, 80), crs=4326)
main_map.add_feature.preset.coastline(zorder=1)
main_map.add_feature.preset.land(zorder=1)
main_map.add_feature.preset.ocean()
# Plotter for the map
plot = MeshPlotter(storer=storer)
plot.set_density_type(consider_depth=True)
plot.set_bins_size(bins_size=[0.5, 1])
plot.set_map_boundaries(
    latitude_min=50,
    latitude_max=90,
    longitude_min=-180,
    longitude_max=180,
)
data = plot.get_df("all")
# Set plotter's data to the map
main_map.set_data(data=data, x="LONGITUDE", y="LATITUDE", crs=4326, parameter="all")
main_map.set_shape.rectangles()
cbar = plt.colorbar(
    cm.ScalarMappable(
        norm=colors.Normalize(vmin=data["all"].min(), vmax=data["all"].max())
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

# --------- Initialize Callbacks
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
    polygon = gdf["geometry"].iloc[-1]
    return polygon


def update_profile(
    polygon: shapely.Polygon,
    storer: Storer,
    axes: Axes,
    colorbar_axes: Axes,
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
    """
    variables = storer.variables
    latitude_field = variables.get(variables.latitude_var_name).label
    longitude_field = variables.get(variables.longitude_var_name).label
    constraints = Constraints()
    constraints.add_polygon_constraint(
        latitude_field=latitude_field,
        longitude_field=longitude_field,
        polygon=polygon,
    )
    profile_tmp = EvolutionProfile(storer, constraints)
    profile_tmp.set_date_intervals("week")
    profile_tmp.set_depth_interval(100)
    _, cbar = profile_tmp.plot_to_axes("all", axes)
    plt.colorbar(cbar, cax=colorbar_axes)


def update_map(
    polygon: shapely.Polygon,
    storer: Storer,
    zoom_map_bg: Maps,
    colorbar_axes: Axes,
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
    """
    variables = storer.variables
    latitude_field = variables.get(variables.latitude_var_name).label
    longitude_field = variables.get(variables.longitude_var_name).label
    constraints = Constraints()
    constraints.add_polygon_constraint(
        latitude_field=latitude_field,
        longitude_field=longitude_field,
        polygon=polygon,
    )
    lon_bin = (polygon.bounds[2] - polygon.bounds[0]) / 100
    plot_tmp = MeshPlotter(storer, constraints)
    plot_tmp.set_density_type(consider_depth=True)
    plot_tmp.set_bins_size(bins_size=[lon_bin, lon_bin * 3])
    df = plot_tmp.get_df("all")
    new_map = zoom_map_bg.new_layer(f"layer{time.time()}")
    new_map.set_data(data=df, x="LONGITUDE", y="LATITUDE", crs=4326, parameter="all")
    new_map.set_shape.rectangles()
    new_map.plot_map(zorder=0)
    plt.colorbar(
        cm.ScalarMappable(
            norm=colors.Normalize(vmin=df["all"].min(), vmax=df["all"].max())
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
    **kwargs,
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
    """
    polygon = get_drawer_polygon(drawer=drawers[-1])
    update_map(
        polygon=polygon,
        storer=storer,
        zoom_map_bg=zoom_map_bg,
        colorbar_axes=zoom_cbar_axes,
    )
    update_profile(
        polygon=polygon,
        storer=storer,
        axes=profile_axes,
        colorbar_axes=profile_cbar_axes,
    )


def update_from_loaded(
    storer: Storer,
    zoom_map_bg: Maps,
    zoom_cbar_axes: Axes,
    profile_axes: Axes,
    profile_cbar_axes: Axes,
    **kwargs,
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
    """
    polygon = load_polygon()
    update_map(
        polygon=polygon,
        storer=storer,
        zoom_map_bg=zoom_map_bg,
        colorbar_axes=zoom_cbar_axes,
    )
    update_profile(
        polygon=polygon,
        storer=storer,
        axes=profile_axes,
        colorbar_axes=profile_cbar_axes,
    )


def clear(
    drawers: list[ShapeDrawer],
    zoom_map_bg: Maps,
    rectilinear_axes: list[Axes],
    **kwargs,
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
    drawers: list[ShapeDrawer],
    storer: Storer,
    **kwargs,
) -> None:
    """Save the data from the polygon in a file.

    Parameters
    ----------
    drawers : list[ShapeDrawer]
        List of all drawers.
    storer : Storer
        Storer to use the dtaa of.
    filepath : str
        Saving filepath.
    """
    polygon = get_drawer_polygon(drawers[-1])
    variables = storer.variables
    latitude_field = variables.get(variables.latitude_var_name).label
    longitude_field = variables.get(variables.longitude_var_name).label
    constraints = Constraints()
    constraints.add_polygon_constraint(
        latitude_field=latitude_field,
        longitude_field=longitude_field,
        polygon=polygon,
    )
    new_storer = Storer.from_constraints(storer=storer, constraints=constraints)
    print("Enter the name of the file (don't write the extension):")
    filename = input() + ".txt"
    if filename == ".txt":
        filename = f"output_{round(time.time())}.txt"
    new_storer.save(filepath=filename)
    print(f"File saved under {filename}")


def start_drawing(drawers: list, main_map: Maps, **kwargs) -> None:
    """Trigger the drawing of a polygon.

    Parameters
    ----------
    drawers : list
        List of all the drawers.
    main_map : Maps
        Map to draw onto.
    """
    drawer = ShapeDrawer(main_map)
    drawer.polygon(draw_on_drag=True)
    if not drawers:
        drawers.append(drawer)
    else:
        drawers[0] = drawer


def save_polygon(drawers: list[ShapeDrawer], **kwargs):
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
    filename = input() + ".txt"
    if filename == ".txt":
        filename = f"polygon_{round(time.time())}.txt"
    filepath = f"{POLYGONS_FOLDER}/" + filename
    polygon_wkt = shapely.to_wkt(polygon)
    with open(filepath, "w") as file:
        file.write(polygon_wkt)
    print(f"Polygon saved under {filepath}")


def load_polygon(**kwargs) -> shapely.Polygon:
    """Load Polygon from a file.

    Returns
    -------
    shapely.Polygon
        The loaded polygon.
    """
    print(
        "Enter the name of file storing a polygon"
        f"(inside the '{POLYGONS_FOLDER}' folder) without its extension"
    )
    filename = input() + ".txt"
    filepath = POLYGONS_FOLDER + "/" + filename
    if not os.path.isfile(filepath):
        print(f"Loading aborted : the file {filepath} doesn't exist.")
        return
    with open(filepath, "r") as file:
        first_line = file.readlines()[0]
        polygon = shapely.from_wkt(first_line)
    print(f"Successfully loaded polygon from {filepath}")
    print(polygon)
    from bgc_data_processing.convert_polygons import polygon_to_list

    print(polygon_to_list(polygon))
    return polygon


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
    filepath="output.txt",
)


main_map.cb.keypress.attach(save_polygon, key="p", drawers=drawers)

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
)
plt.show()
