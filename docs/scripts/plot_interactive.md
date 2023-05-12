# Interactive Map

`make run-plot_interactive`
## Summary

This scripts shows an interactive map on which it is possible to draw polygon in order to view data density and profile on a given area.

The following keys are used to interact with this map:

- **D** to start drawing a polygon, then:
    - **Left Click** to draw polygon (keep the button clicked).
    - **Middle Click** to close the polygon shape.
- **Enter** key to confirm the drawn polygon as area to zoom in.
- **Z** key to remove the polygon.
- **S** to save the data within the polygon (then you must enter a filename in the terminal).
- **P** to save the polygon (then you must enter a filename in the terminal).
- **L** to load a polygon (then you must enter the name of the file to load).
## Configuration

The configuration file for this script is `config/plot_interactive.toml` (based on [`config/default_plot_interactive.toml`]({{repo_blob}}/config/default/plot_interactive.toml)). All the parameters and their functionality are listed below:
### **Input/Output**
??? question "LOADING_DIR"

    Directory from which to load the data.

    **default**: `"bgc_data"`

    Expected type: `str`

??? question "POLYGONS_FOLDER"

    Directory from which to load already existing polygons and in which to save the drawn polygons.

    **default**: `"polygons"`

    Expected type: `str`
### **Data Selection**

??? question "VARIABLE"

    Variable to map. If 'all': will map density of datapoints, regardless of their variables.

    **default**: `"all"`

    Expected type: `str`

??? question "DATE_MIN"

    First date to map (included).

    **default**: `"20070101"`

    Expected type: `str` (must match the `YYYYMMDD` format)

??? question "DATE_MAX"

    Last date to map (included).

    **default**: `"20071231"`

    Expected type: `str` (must match the `YYYYMMDD` format)

??? question "LATITUDE_MIN"

    Minimum latitude boundary to consider for the loaded data (included).

    **default**: `50`

    Expected type: `int` or `float`

??? question "LATITUDE_MAX"

    Maximum latitude boundary to consider for the loaded data (included).

    **default**: `90`

    Expected type: `int` or `float`

??? question "LONGITUDE_MIN"

    Minimum longitude boundary to consider for the loaded data (included).

    **default**: `-180`

    Expected type: `int` or `float`

??? question "LONGITUDE_MAX"

    Maximum longitude boundary to consider for the loaded data (included).

    **default**: `180`

    Expected type: `int` or `float`

??? question "DEPTH_MIN"

    Minimum depth boundary to consider for the loaded data (included).

    **default**: `nan`

    Expected type: `int` or `float`

??? question "DEPTH_MAX"

    Maximum depth boundary to consider for the loaded data (included)

    **default**: `0`

    Expected type: `int` or `float`

??? question "EXPOCODES_TO_LOAD"

    Precise expocode to load alone. If empty, no discrimination on expocode will be conducted.

    **default**: `[]`

    Expected type: `list[str]`

??? question "PRIORITY"

    Providers priority list to use when removing duplicates

    **default**: `["GLODAP_2022", "CMEMS", "ARGO", "NMDC", "CLIVAR", "IMR", "ICES"]`

    Expected type: `list[str]`
### **Mapping Options**
??? question "LATITUDE_MAP_MIN"

    Minimum latitude boundary displayed on the map (included). If set to nan, the map boundaries will match the extremum of the dataframe

    **default**: `50`

    Expected type: `int` or `float`

??? question "LATITUDE_MAP_MAX"

    Maximum latitude boundary displayed on the map (included). If set to nan, the map boundaries will match the extremum of the dataframe

    **default**: `90`

    Expected type: `int` or `float`

??? question "LONGITUDE_MAP_MIN"

    Minimum longitude boundary displayed on the map (included). If set to nan, the map boundaries will match the extremum of the dataframe

    **default**: `-180`

    Expected type: `int` or `float`

??? question "LONGITUDE_MAP_MAX"

    Maximum longitude boundary displayed on the map (included). If set to nan, the map boundaries will match the extremum of the dataframe

    **default**: `180`

    Expected type: `int` or `float`

??? question "BIN_SIZE"

    Bins size. If list, first component is latitude size, second is longitude size. If int or float, represents both latitude and longitude size.

    **default**: `[0.5, 1.5]`

    Expected type: `list[float]` or `list[int]` or `float` or `int`

??? question "CONSIDER_DEPTH"

    If `true`: the plotted density will consider all data points (even the ones in the water column). If `false`: the plotted density will only consider one data point per location and date

    **default**: ``true``

    Expected type: `bool`
## Script Output
When executed, this script will display an interactive map with three panels:

1. The general map of the loaded data, on the left panel.
2. A zoomed view of any selected data, on the top right panel.
3. A depth vs date density view of any selected data, on the bottom right panel.

This is an example of what the displayed figure could look like:

![interactive map output example]({{fix_url("assets/plots/interactive_map.png")}}){width=750px}

Source code: [:octicons-file-code-16:]({{repo_blob}}/scripts/plot_interactive.py)
