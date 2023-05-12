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
    name_format="%-12s",                        # (4)
    value_format="%12.6f",                      # (5)
).set_aliases(("Longitude", "longitudef", [1])) # (6)
```

1. Name of the variable (can be different from its name in the dataset).
2. Unit of the variable, as one wants it to appear when saving.
3. Data type, used to convert types in the dataframe.
4. Format string to use to format the label and the unit of the variable when saving.
5. Format string to use to format the values of the variable when saving.
6. Sets the Aliases list to the given args where each element is a tuple containing:
    - alias: variable name in the source data
    - flag alias: variable flag name in the source data
    - flag correct value: list of values to keep from the flag column

!!! note ""
    [More informations on variables]({{fix_url("how_it_works/variables.md")}})

## Loading the data

In order to load the data from a provider, one must use the loader which corresponds to the data type of the source ([CSV]({{fix_url("../reference/csv_tools/#bgc_data_processing.csv_tools.CSVLoader")}}) of [NetCDF]({{fix_url("../reference/netcdf_tools/#bgc_data_processing.netcdf_tools.NetCDFLoader")}})). <br/>
This loader contains all the informations on the provider (name, files location, required variables stored in a [variable storing object]({{fix_url("../reference/variables/#bgc_data_processing.variables.VariablesStorer")}})).

Defining a loader for GLODAPv2.2022 :

``` py
from bgc_data_processing.csv_tools import CSVLoader
from bgc_data_processing.variables import VariablesStorer

variables = VariablesStorer(
    longitude,                          # (1)!
    latitude,                           # (2)!
)
loader = CSVLoader(
    provider_name="GLODAP_2022",        # (3)!
    dirin="path/to/file/directory",     # (4)!
    category="in_situ",                 # (5)!
    files_pattern="glodap_2022.csv",    # (6)!
    variables=variables,                # (7)!
    read_params={
        "low_memory": False,
        "index_col": False,
        "na_values": -9999,
    },                                  # (8)!
)
storer = loader()                       # (9)!
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
9. The \__call__ method from the loader will then load the data and return a [storer]({{fix_url("../reference/data_classes/#bgc_data_processing.data_classes.Storer")}}) containing the resulting dataframe.

!!! note ""
    [More informations on loading]({{fix_url("how_it_works/loading.md")}})

## Aggregating the data

Once data has been loaded from some providers, the aggregation of the resulting storers can be done using the `+` operator. However, in order for the aggregation to work, all storer must have similar variables (to concatenates the data) and same category ('in_situ' and 'float' can't be aggregated). <br/>
Then, in order to save a storer, one only has to call the [.save]({{fix_url("../reference/data_classes/#bgc_data_processing.data_classes.Storer.save")}}) method of the object.

``` py
storer_glodap = loader_glodap()                 # (1)!
storer_imr = loader_imr()                       # (2)!
# Aggregation
aggregated_storer = storer_glodap + storer_imr  # (3)!
# Saving
aggregated_storer.save("path/to/save/file")     # (4)!
```

1. Loader for GLODAP 2022.
2. Loader for IMR.
3. Summing both storer returns the aggregation of them.
4. Calling the .save methods to save the file.

## Plotting the data

To plot the data, one has to create a [MeshPlotter]({{fix_url("../reference/tracers/#bgc_data_processing.tracers.MeshPlotter")}}) (to create 2D Mesh) and then call its [.show]({{fix_url("../reference/tracers/#bgc_data_processing.tracers.MeshPlotter.show")}}) method.
To save the data, one has to use the [.save]({{fix_url("../reference/tracers/#bgc_data_processing.tracers.MeshPlotter.save")}}) method.

``` py
from bgc_data_processing.tracers import MeshPlotter

mesher = MeshPlotter(storer)                # (1)!
mesher.set_bins_soze(bins_size=[0.1, 0.2])  # (2)!
mesher.set-geographic_boundaries(
    latitude_min = 50,
    latitude_max = 90,
    longitude_min = -40,
    longitude_max = 40,
)
mesher.plot(
    variable_name="CPHL",                   # (3)!
    title="some title",                     # (4)!
    suptitle="some suptitle",               # (5)!
)
mesher.save(
    save_path="path/to/figure"              # (6)!
    variable_name="CPHL",                   # (7)!
    title="some title",                     # (8)!
    suptitle="some suptitle",               # (9)!
)
```

1. Storer object to map the data of.
2. Size of the binning square (latitude, longitude)
3. Name of the variable to plot on the map.
4. Title for the plot.
5. Suptitle for the plot.
6. Path to the saving location.
7. Name of the variable to plot on the map.
8. Title for the plot.
9. Suptitle for the plot.

!!! note ""
    [More informations on plotting]({{fix_url("how_it_works/plotting.md")}})
