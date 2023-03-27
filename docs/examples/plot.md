# Density Map

Example script to create a density map of the data. The data has previously been saved in the files "data1.csv", "data2.csv", "data3.csv", "data4.csv" and "data5.csv" and can be loaded from these files.

``` py
from bgc_data_processing.data_classes import Storer
from bgc_data_processing.tracers import MeshPlotter

files = [
    "path/to/data1.csv",
    "path/to/data2.csv",
    "path/to/data3.csv",
    "path/to/data4.csv",
    "path/to/data5.csv",
]
# Files Loading
storer = Storer.from_files(
    filepath=files,
    providers_column_label = "PROVIDER",
    expocode_column_label = "EXPOCODE",
    date_column_label = "DATE",
    year_column_label = "YEAR",
    month_column_label = "MONTH",
    day_column_label = "DAY",
    hour_column_label = "HOUR",
    latitude_column_label = "LATITUDE",
    longitude_column_label = "LONGITUDE",
    depth_column_label = "DEPH",
    category="in_situ",
    unit_row_index=1,
    delim_whitespace=False,
)
# Constraints
constraints = data_classes.Constraints()            # (1)!
# Mapping
mesh = MeshPlotter(storer, constraints=constraints)
mesh.set_bin_size(bins_size=[0.5,1.5])
mesh.show(
    variable_name="PHOS",
    title="Phosphate data density",
)
```

1. No constraint defined for this example
