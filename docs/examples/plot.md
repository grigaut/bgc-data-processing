# Density Map

Example script to create a density map of the data. The data has previously been saved in the files `"data1.txt"`, `"data2.txt"`, `"data3.txt"`, `"data4.txt"` and `"data5.txt"` and can be loaded from these files.

In order to plot the data density, we use the [DensityPlotter]({{fix_url("../reference/tracers/#bgc_data_processing.tracers.DensityPlotter")}}).

``` py
from pathlib import Path

import bgc_data_processing as bgc_dp

files = [
    Path("path/to/data1.txt"),
    Path("path/to/data2.txt"),
    Path("path/to/data3.txt"),
    Path("path/to/data4.txt"),
    Path("path/to/data5.txt"),
]
# Files Loading
storer = bgc_dp.io.read_files(
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
constraints = bgc_dp.Constraints()            # (1)!
# Mapping
mesh = bgc_dp.tracers.DensityPlotter(storer, constraints=constraints)
mesh.set_bin_size(bins_size=[0.5,1.5])
mesh.show(
    variable_name="PHOS",
    title="Phosphate data density",
)
```

1. No constraint defined for this example
