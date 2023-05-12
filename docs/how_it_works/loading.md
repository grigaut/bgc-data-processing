# Loading

In order to load the data from its sources (providers csv or netcdf files, already processed files), one can use loaders. Basically, the loaders are initializated with all necessary infomations on providers, files locations and variables and only calling the \__call__ method is needed to load the data and return a storer. <br/>
## Loading from providers data

When loading from a procider, the following arguments must be given to the loader at least:

- The name of the provider: `provider_name`
- The directory containing the files to load: `dirin`
- The category of the data ('float' or 'in_situ'): `category`
- The pattern of the names of the files to read ([re](https://docs.python.org/3/library/re.html) compliant if a regex): `files_pattern`
- The VariablesStorer object containing all variables: `variables`

=== "CSVLoader"

    Loader for CSV files, uses the `read_params` additional argument to pass specific argument to [pandas.read_csv](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html)

    ``` py
    from bgc_data_processing.csv_tools import CSVLoader

    loader = CSVLoader(
        provider_name="GLODAP_2022",
        dirin="path/to/files/directory",
        category="in_situ",
        files_pattern="GLODAPv2.2022_all.csv",
        variables=variables,                        # (1)
        read_params={
            "low_memory": False,
            "index_col": False,
            "na_values": -9999,
        },
    )
    ```

    1. Pre-set VariablesStorer object

=== "NetCDFLoader"

    Loader for NetCDF files.

    ``` py
    from bgc_data_processing.netcdf_tools import NetCDFLoader

    loader = netcdf_tools.NetCDFLoader(
        provider_name="ARGO",
        dirin="path/to/files/directory",
        category="float",
        files_pattern=".*.nc",
        variables=variables,                        # (1)
    )
    ```

    1. Pre-set VariablesStorer object

Once the loader is set, it is simple to get the corresponding storer :

```py
storer = loader()
```
## Loading from already processed file

It is also possible to load data from files which have saved using the [.save]({{fix_url("../reference/data_classes/#bgc_data_processing.data_classes.Storer.save")}}) method of a storer using the [.from_files]({{fix_url("../reference/data_classes/#bgc_data_processing.data_classes.Storer.from_files")}}) class method:

```py
from bgc_data_processing.dataclasses import Storer
files = [
    "file1.csv",
    "file2.csv",
]
storer = Storer.from_files(
    filepath = [ "file1.csv","file2.csv"],  # (1)!
    providers_column_label = "PROVIDER",    # (2)!
    expocode_column_label = "EXPOCODE",     # (3)!
    date_column_label = "DATE",             # (4)!
    year_column_label = "YEAR",             # (5)!
    month_column_label = "MONTH",           # (6)!
    day_column_label = "DAY",               # (7)!
    hour_column_label = "HOUR",             # (8)!
    latitude_column_label = "LATITUDE",     # (9)!
    longitude_column_label = "LONGITUDE",   # (10)!
    depth_column_label = "DEPH",            # (11)!
    category = "in_situ",                   # (12)!
    unit_row_index = 1,                     # (13)!
    delim_whitespace = True,                # (14)!
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
12. Category of **all** files (otherwise they shouldn't be aggregated together in a single storer)
13. Index of the unit row.
14. Whether to delimitate values based on whitespaces

## Storers

Once the data in a Storer, it is easy to save this data to a file using the [.save]({{fix_url("../reference/data_classes/#bgc_data_processing.data_classes.Storer.save")}}) method:

```py
storer.save("filepath/to/save/in")
```

It also possible to slice the Dataframe based on the dates of the rows using the [.slice_on_dates]({{fix_url("../reference/data_classes/#bgc_data_processing.data_classes.Storer.slice_on_dates")}}) method. This will return a Slice object, a child class of Storer but only storing indexes of the dataframe slice and not the dataframe slice itself (to reduce the amount of memory used) :

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

Or, using slice_on_date as a class method from Slice:

``` py
import pandas as pd
import datetime as dt
drng = pd.Series(
    {
        "start_date": dt.datetime(2000,1,1),
        "end_date": dt.datetime(2020,1,1),
    }
)
slicer = Slice.slice_on_dates(drng, storer)     # (1)
```

1. Storer is a pre-set Storer object.

Slice objects can be saved in the same way as any Storer:

```py
slicer.save("filepath/to/save/in")
```
