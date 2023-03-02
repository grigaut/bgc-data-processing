# How does it work ?

This project loads data from different providers, standardizes the data and saves (or maps) the resulting data.

In order to do so, one needs to follow 4 major steps :
## Defining variables

Variable objects save the meta data for data variables.
It contains informations about a variable's name, unit, storing type in the output dataframe.
These objects can also be instanciated to 'fit' a proper source. <br />
For example, one can specify a particular alias under which the variable is stored in the source data,
flag columns and values to use to filter the source data, a particular function to correct the data from the source...

Defining a variable existing in the source data: <br />

``` py
from bgc_data_processing.variables import ExistingVar

variable = ExistingVar(
    name="LONGITUDE",                           # (1)
    unit="[deg_E]",                             # (2)
    var_type=float,                             # (3)
    load_nb=6,                                  # (4)
    save_nb=5,                                  # (5)
    name_format="%-12s",                        # (6)
    value_format="%12.6f",                      # (7)
).set_aliases(("Longitude", "longitudef", [1])) # (8)
```

1. Name of the variable (can be different from its name in the dataset).
2. Unit of the variable, as one wants it to appear when saving.
3. Data type, used to convert types in the dataframe.
4. Relative order to use to sort the variable, the smaller the more to the left.
5. Relative order to use to save the variable, the smaller the more to the left.
6. Format string to use to format the label and the unit of the variable when saving.
7. Format string to use to format the values of the variable when saving.
8. Sets the Aliases list to the given args where each element is a tuple containing:
    - alias: variable name in the source data
    - flag alias: variable flag name in the source data
    - flag correct value: list of values to keep from the flag column

!!! note ""
    [More informations on variables](/how_it_works/variables)

## Loading the data

In order to load the data from a provider, one must use the loader which corresponds to the data type of the source ([CSV](/reference/csv_tools/#bgc_data_processing.csv_tools.CSVLoader) of [NetCDF](/reference/netcdf_tools/#bgc_data_processing.netcdf_tools.NetCDFLoader)). <br/>
This loader contains all the informations on the provider (name, files location, required variables stored in a [variable storing object](/reference/variables/#bgc_data_processing.variables.VariablesStorer)).

Defining a loader for GLODAPv2.2022 :

``` py
from bgc_data_processing.csv_tools import CSVLoader
from bgc_data_processing.variables import VariablesStorer

variables = VariablesStorer(
    longitude,                          # (1)
    latitude,                           # (2)
)
loader = CSVLoader(
    provider_name="GLODAP_2022",        # (3)
    dirin="path/to/file/directory",     # (4)
    category="in_situ",                 # (5)
    files_pattern="glodap_2022.csv",    # (6)
    variables=variables,                # (7)
    read_params={
        "low_memory": False,
        "index_col": False,
        "na_values": -9999,
    },                                  # (8)
)
storer = loader()                       # (9)
```

1. Variable object of type ExistingVar or NotExistingVar referring to longitude variable.
2. Variable object of type ExistingVar or NotExistingVar referring to latitude variable.
3. Name of the data provider.
4. Path to the directory containing the files to load.
5. The category of the provider, can be 'in_situ' or 'float'.
6. Files pattern, only the files matching the pattern will be loaded. If the string '({years})' is included, this will be replaced by the years to load. For example: <br/>
if the pattern is "glodap_({years}).csv" and the years to load are 2007 and 2008, only the files matching the regex "glodap_(2007|2008).csv" will be loaded.
7. Variables to load (if the variables are not in the data source, the column will still be created)
8. Additionnal parameter passed to pd.read_csv
9. The \__call__ method from the loader will then load the data and return a [storer](/reference/data_classes/#bgc_data_processing.data_classes.Storer) containing the resulting dataframe.

!!! note ""
    [More informations on loading](/how_it_works/loading)

## Aggregating the data

Once data has been loaded from some providers, the aggregation of the resulting storers can be done using the `+` operator. However, in order for the aggregation to work, all storer must have similar variables (to concatenates the data) and same category ('in_situ' and 'float' can't be aggregated). <br/>
Then, in order to save a storer, one only has to call the [.save](/reference/data_classes/#bgc_data_processing.data_classes.Storer.save) method of the object.

``` py
storer_glodap = loader_glodap()                 # (1)
storer_imr = loader_imr()                       # (2)
# Aggregation
aggregated_storer = storer_glodap + storer_imr  # (3)
# Saving
aggregated_storer.save("path/to/save/file")     # (4)
```

1. Loader for GLODAP 2022.
2. Loader for IMR.
3. Summing both storer returns the aggregation of them.
4. Calling the .save methods to save the file.
!!! note ""
    [More informations on aggregation](/how_it_works/aggregation)

## Plotting the data

To plot the data, one has to create a [GeoMesher](/reference/tracers/#bgc_data_processing.tracers.GeoMesher) (to create 2D Mesh) and then call its [.plot](/reference/tracers/#bgc_data_processing.tracers.GeoMesher.plot) method.
To save the data, one has to use the [.save_fig](/reference/tracers/#bgc_data_processing.tracers.GeoMesher.save_fig) method.

``` py
from bgc_data_processing.tracers import GeoMesher

mesher = GeoMesher(
    storer,                         # (1)
)
mesher.plot(
    variable_name="CPHL",           # (2)
    bins_size=(0.1, 0.2),           # (3)
    depth_aggr="top",               # (4)
    bin_aggr="count",               # (5)
    title="some title",             # (8)
    suptitle="some suptitle",       # (7)
    extent=(-40, 40, 50, 89),       # (8)
)
mesher.save(
    save_path="path/to/figure"      # (9)
    variable_name="CPHL",           # (10)
    bins_size=(0.1, 0.2),           # (11)
    depth_aggr="top",               # (12)
    bin_aggr="count",               # (13)
    title="some title",             # (14)
    suptitle="some suptitle",       # (15)
    extent=(-40, 40, 50, 89),       # (16)
)
```

1. Storer object to map the data of.
2. Name of the variable to plot on the map.
3. Size of the binning square (latitude, longitude)
4. String reference (see /reference/tracers/#bgc_data_processing.tracers.GeoMesher._depth_aggr) or function to use to aggregate data points with same location and different depth.
5. String reference (see /reference/tracers/#bgc_data_processing.tracers.GeoMesher._bin_aggr) or function to use to aggregate data points within the same bining area.
6. Title for the plot.
7. Suptitle for the plot.
8. Area extent to restrains the mapping to.
9. Path to the saving location.
10. Name of the variable to plot on the map.
11. Size of the binning square (latitude, longitude)
12. String reference (see /reference/tracers/#bgc_data_processing.tracers.GeoMesher._depth_aggr) or function to use to aggregate data points with same location and different depth.
13. String reference (see /reference/tracers/#bgc_data_processing.tracers.GeoMesher._bin_aggr) or function to use to aggregate data points within the same bining area.
14. Title for the plot.
15. Suptitle for the plot.
16. Area extent to restrains the mapping to.
!!! note ""
    [More informations on plotting](/how_it_works/plotting)
