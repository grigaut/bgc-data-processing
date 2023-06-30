# Loading

In order to load the data from its sources (providers csv or netcdf files, already processed files), one can use [DataSource objects]({{fix_url("../reference/core/sources/#bgc_data_processing.core.sources.DataSource")}}). Basically, the data sources are initializated with all necessary infomations on providers, files locations and variables and only calling the [`load_all`]({{fix_url("../reference/core/sources/#bgc_data_processing.core.sources.DataSource.load_all")}}) method is needed to load the data and return a storer. <br/>
## Loading from providers data

When loading from a provider, the following arguments must be given to the DataSource at least:

- The name of the provider: `provider_name`
- The format of the data: `data_format`
- The directory containing the files to load: `dirin`
- The category of the data ('float' or 'in_situ'): `data_category`
- The pattern of the names of the files to read (a [FileNamePattern]({{fix_url("../reference/utils/patterns/#bgc_data_processing.utils.patterns.FileNamePattern")}})): `files_pattern`
- The [SourceVariableSet]({{fix_url("../reference/core/variables/sets/#bgc_data_processing.core.variables.sets.SourceVariableSet")}}) object containing all variables: `variable_ensemble`

Behind the hood, theses `DataSource` object instantiate loaders, all deriving from [`BaseLoader`]({{fix_url("../reference/core/loaders/base/#bgc_data_processing.core.loaders.base.BaseLoader")}}). All loaders are file-format specific, meaning that at least one specific subclass of `Baseloader` exists for every supported data format.

=== "CSV"

    Loader for CSV files uses the `read_params` additional argument to pass specific argument to [pandas.read_csv](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html)

    ``` py
    from bgc_data_processing.core.loaders.csv_loaders import CSVLoader

    loader = CSVLoader(
        provider_name="GLODAP_2022",
        category="in_situ",
        exclude=[],
        variables=variables,                        # (1)
        read_params={
            "low_memory": False,
            "index_col": False,
            "na_values": -9999,
        },
    )
    ```

    1. Pre-set [`SourceVariableSet`]({{fix_url("../reference/core/variables/sets/#bgc_data_processing.core.variables.sets.SourceVariableSet")}}) object

=== "NetCDF"

    Loader for NetCDF files.

    ``` py
    from bgc_data_processing.loaders.netcdf_loaders import NetCDFLoader

    loader = NetCDFLoader(
        provider_name="ARGO",
        category="float",
        exclude=[],
        variables=variables,                        # (1)
    )
    ```

    1. Pre-set VariablesStorer object

=== "AB files"

    Loader for AB files uses the `grid_basename` additional argument to get the regional grid for the AB file. The AB files are handled using a [library](https://github.com/nansencenter/NERSC-HYCOM-CICE/tree/cee8873e2603f88296efbe1a224162b5470bb02d/pythonlibs/abfile/abfile) developped by the Nansen Environmental and remote Sensing center. Ths library is included into the src folder and therefore will not be improved / impacted by any change that could occur in the original repository.

    ``` py
    from bgc_data_processing.loaders.abfile_loaders import ABFileLoader

    loader = ABFileLoader(
        provider_name="HYCOM",
        category="float",
        exclude=[],
        variables=variables,                        # (1)
        grid_basename="regional.grid"
    )
    ```

    1. Pre-set VariablesStorer object

Once the data source is set, it is simple to get the corresponding storer :

```py
storer = dsource.load_all()
```
## Loading from already processed file

It is also possible to load data from files which have saved using the [read_files]({{fix_url("../reference/core/io/readers/#bgc_data_processing.core.io.readers.read_files")}}) function:

```py
from pathlib import Path
import bgc_data_processing as bgc_dp

storer = bgc_dp.io.read_files(
    filepath = [Path("file1.txt"), Path("file2.txt")],      # (1)!
    providers_column_label = "PROVIDER",                    # (2)!
    expocode_column_label = "EXPOCODE",                     # (3)!
    date_column_label = "DATE",                             # (4)!
    year_column_label = "YEAR",                             # (5)!
    month_column_label = "MONTH",                           # (6)!
    day_column_label = "DAY",                               # (7)!
    hour_column_label = "HOUR",                             # (8)!
    latitude_column_label = "LATITUDE",                     # (9)!
    longitude_column_label = "LONGITUDE",                   # (10)!
    depth_column_label = "DEPH",                            # (11)!
    category = "in_situ",                                   # (12)!
    unit_row_index = 1,                                     # (13)!
    delim_whitespace = True,                                # (14)!
)
```

1. List of the filepaths of the files to load
2. Name of the column containing the provider informations in **all** files
3. Name of the column containing the expocode informations in **all** files
4. Name of the column containing the date informations in **all** files
5. Name of the column containing the year informations in **all** files
6. Name of the column containing the month informations in **all** files
7. Name of the column containing the day informations in **all** files
8. Name of the column containing the hour informations in **all** files
9. Name of the column containing the latitude informations in **all** files
10. Name of the column containing the longitude informations in **all** files
11. Name of the column containing the depth informations in **all** files
12. Category of **all** files (otherwise they couldn't be aggregated together in a single storer)
13. Index of the unit row.
14. Whether to delimitate values based on whitespaces

## Storers

Once the data in a Storer, it is easy to save this data to a file using the [save_storer]({{fix_url("../reference/core/io/savers/#bgc_data_processing.core.io.savers.save_storer")}}) function:

```py
import bgc_data_processing as bgc_dp
bgc_dp.io.save_all_storer(Path("filepath/to/save/in.txt"))
```

It also possible to slice the Dataframe based on the dates of the rows using the [.slice_on_dates]({{fix_url("../reference/core/storers/#bgc_data_processing.core.storers.Storer.slice_on_dates")}}) method. This will return a Slice object, a child class of Storer but only storing indexes of the dataframe slice and not the dataframe slice itself (to reduce the amount of memory used) :

``` py
import pandas as pd
import datetime as dt
drng = pd.Series(
    {
        "start_date": dt.datetime(2000,1,1),
        "end_date": dt.datetime(2020,1,1),
    }
)
slicer = storer.slice_on_dates(drng)            # (1)
```

1. Storer is a pre-set Storer object.

Slice objects can be saved in the same way as any Storer:

```py
import bgc_data_processing as bgc_dp
bgc_dp.io.save_all_storer("filepath/to/save/in")
```
