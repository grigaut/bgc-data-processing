# Density Map

Example script to create a density map of the data. The data has previously been saved in the files "data1.csv", "data2.csv", "data3.csv", "data4.csv" and "data5.csv" and can be loaded from these files.

``` py
from bgc_data_processing.data_classes import Storer
from bgc_data_processing.tracers import GeoMesher

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
    providers="PROVIDERS",
    category="in_situ",
    unit_row_index=1,
    delim_whitespace=False,
)
# Mapping
mesh = GeoMesher(storer)
mesh.plot(
    variable_name="PHOS",
    bins_size=[0.5,1.5],
    depth_aggr="count",
    bin_aggr="count",
    title="Phosphate data density",
)
```
