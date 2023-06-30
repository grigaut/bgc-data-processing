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
import bgc_data_processing as bgc_dp

variable = bgc_dp.variables.ExistingVar(
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

In order to load the data from a provider, one must instanciate a [`DataSource`]({{fix_url("reference/core/sources/#bgc_data_processing.core.sources.DataSource")}}). This data source instanciate a loader which correspond to the format of the data of the source ([CSV]({{fix_url("reference/core/loaders/csv_loaders/#bgc_data_processing.core.loaders.csv_loaders.CSVLoader")}}), [NetCDF]({{fix_url("reference/core/loaders/netcdf_loaders/#bgc_data_processing.core.loaders.netcdf_loaders.NetCDFLoader")}}) or [abfile]({{fix_url("reference/core/loaders/abfile_loaders/#bgc_data_processing.core.loaders.abfile_loaders.ABFileLoader")}})). <br/>
This data source object contains all the informations on the provider (name, files location, required variables stored in a [variable storing object]({{fix_url("reference/core/variables/sets/#bgc_data_processing.core.variables.sets.SourceVariableSet")}})).

Defining a DataSource for GLODAPv2.2022 :

``` py
import bgc_data_processing as bgc_dp

variables = bgc_dp.SourceVariableSet(
longitude=longitude,                                                        # (1)!
latitude=latitude,                                                          # (2)!
...                                                                         # (3)!
)
dsource = bgc_dp.DataSource(
    provider_name="GLODAP_2022",                                            # (4)!
    data_format="csv",                                                      # (5)!
    dirin="path/to/file/directory",                                         # (6)!
    data_category="in_situ",                                                # (7)!
    excluded_files=[],                                                      # (8)!
    files_pattern=bgc_dp.utils.patterns.FileNamepattern("glodap_2022.csv"), # (9)!
    variable_ensemble=variables,                                            # (10)!
    read_params={
        "low_memory": False,
        "index_col": False,
        "na_values": -9999,
    },                                                                      # (11)!
)
storer = dsource.load_all()                                                 # (12)!
```

1. Variable object of type ExistingVar or NotExistingVar referring to longitude variable.
2. Variable object of type ExistingVar or NotExistingVar referring to latitude variable.
3. his is just an example script to show the expected structure of a script file, some mandatory variables are missing to initialize the SourceVariableSet, such as 'provider', 'expocode', 'date', 'month', 'day', 'hour' and 'depth'.
4. Name of the data provider.
5. Format of the provided data.
6. Path to the directory containing the files to load.
7. The category of the provider, can be 'in_situ' or 'float'.
8. Filenames to exclude when loading the data.
9. Files pattern, only the files matching the pattern will be loaded. If the strings `'{years}'`, `'{months}'` or `'{days}'` are included, they will be replaced by the dates to load. For example: <br/>
if the pattern is "glodap_{years}.csv" and the years to load are 2007 and 2008, only the files matching the regex "glodap_(2007|2008).csv" will be loaded.
10. Variables to load (if the variables are not in the data source, the column will still be created)
11. Additionnal parameter passed to pd.read_csv
12. The load_all method from the loader will then load the data and return a [`Storer`]({{fix_url("reference/core/storers/#bgc_data_processing.core.storers.Storer")}}) containing the resulting dataframe.

!!! note ""
    [More informations on loading]({{fix_url("how_it_works/loading.md")}})

## Aggregating the data

Once data has been loaded from some providers, the aggregation of the resulting storers can be done using the `+` operator. However, in order for the aggregation to work, all storer must have similar variables (to concatenates the data) and same category (category-different storers can't be aggregated together). <br/>
Then, in order to save a storer, one has to use a [`StorerSaver`]({{fix_url("reference/core/io/savers/#bgc_data_processing.core.io.savers.StorerSaver")}}).

``` py
storer_glodap = dsource_glodap.load_all()                   # (1)!
storer_imr = dsource_imr.load_all()                         # (2)!
# Aggregation
aggregated_storer = storer_glodap + storer_imr              # (3)!
# Saving
saver = StorerSaver(aggregated_storer)
saver.save_all_storer(Path("path/to/save/file.txt"))        # (4)!
```

1. Loader for GLODAP 2022.
2. Loader for IMR.
3. Summing both storer returns the aggregation of them.
4. Calling the .save_all_storer method to save the entire storer.

## Plotting the data

To plot the data, one has to create a [`DensityPlotter`]({{fix_url("reference/tracers/#bgc_data_processing.tracers.DensityPlotter")}}) (to create 2D Mesh) and then call its [`.show`]({{fix_url("reference/tracers/#bgc_data_processing.tracers.DensityPlotter.show")}}) method.
To save the data, one has to use the [`.save`]({{fix_url("reference/tracers/#bgc_data_processing.tracers.DensityPlotter.save")}}) method.

``` py
import bgc_data_processing.tracers as bgc_dp

mesher = bgc_dp.tracers.DensityPlotter(storer)                # (1)!
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
