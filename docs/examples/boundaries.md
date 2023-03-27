# Defining Boundaries

Loading script to load year, latitude, longitude, phosphate and nitrate variables from 2 providers, 'provider1' and 'provider2'. Phosphate variable is not measured by provider1 and nitrate is not measured by provider2. <br />
Therefore, template are created to store basic informations on variables and are then instanciated in order to create relevant ExistingVar or NotExistingVar depending on provider. <br />
Finally, latitude and longitude are applied in order to load the data only on a certain area. These are define using through the [Constraints](/reference/data_classes/#bgc_data_processing.data_classes.Constraints) objects. Passing a Constraints object to the loader's [__call__](/reference/csv_tools/#bgc_data_processing.csv_tools.CSVLoader.__call__) magic method will load the constraints to apply to the object and apply them when loading (or plotting) the data.

``` py
import datetime as dt

from bgc_data_processing import variables, csv_tools, data_classes

# Boundaries definition
latitude_min = 50
latitude_max = 89
longitude_min = -40
longitude_max = 40
# Variables definition
year_var = variables.TemplateVar(
    name = "YEAR",
    unit = "[]",
    var_type = int,
    name_format = "%-4s",
    value_format = "%4f",
)
latitude_var = variables.TemplateVar(
    name = "LATITUDE",
    unit = "[deg_N]",
    var_type = float,
    name_format = "%-12s",
    value_format = "%12.6f",
)
longitude_var = variables.TemplateVar(
    name = "LONGITUDE",
    unit = "[deg_E]",
    var_type = float,
    name_format = "%-12s",
    value_format = "%12.6f",
)
phos_var = TemplateVar(
    name="PHOS",
    unit="[umol/l]",
    var_type=float,
    name_format="%-10s",
    value_format="%10.3f",
)
ntra_var = TemplateVar(
    name="NTRA",
    unit="[umol/l]",
    var_type=float,
    name_format="%-10s",
    value_format="%10.3f",
)
# loaders definition
loader_prov1 = csv_tools.CSVLoader(
    provider_name="provider1",
    dirin="~/provider1/data",
    category="in_situ",
    files_pattern="prov1_data_({years}).csv",
    variables=variables.VariablesStorer(
        year=year_var.in_file_as(("year",None,None)).remove_when_nan(),
        latitude=latitude_var.in_file_as(("lat",None,None)),
        longitude=longitude_var.in_file_as(("lon",None,None)),
        phophate=phos_var.not_in_file(),
        ...                                                            # (1)!
        nitrate=ntra_var.in_file_as(("ntra",None,None)),
    )
)
loader_prov2 = csv_tools.CSVLoader(
    provider_name="provider2",
    dirin="~/provider2/data",
    category="in_situ",
    files_pattern="data_({years}).csv",
    variables=variables.VariablesStorer(
        year=year_var.in_file_as(("year",None,None)).remove_when_nan(),
        latitude=latitude_var.in_file_as(("latitude",None,None)),
        longitude=longitude_var.in_file_as(("longitude",None,None)),
        ...                                                             # (2)!
        phosphate=phos_var.in_file_as(("phosphate",None,None)),
        nitrate=ntra_var.not_in_file(),
    )
)
# apply boundaries
storers = []
for loader in [loader_prov1, loader_prov2]:
    variables = loader.variables
    constraints = data_classes.Constraints()
    constraints.add_boundary_constraint(
        field_label=variables.get(variables.latitude_var_name).label,
        minimal_value=LATITUDE_MIN,
        maximal_value=LATITUDE_MAX,
    )
    constraints.add_boundary_constraint(
        field_label=variables.get(variables.longitude_var_name).label,
        minimal_value=LONGITUDE_MIN,
        maximal_value=LONGITUDE_MAX,
    )
    loader.set_longitude_boundaries(
        longitude_min=longitude_min,
        longitude_max=longitude_max,
    )
    loader.set_latitude_boundaries(
        latitude_min=latitude_min,
        latitude_max=latitude_max,
    )
    storer = loader(constraints=constraints)
    storers.append(storer)
# Aggregation
aggregated_storer = sum(storers)
```

1. This is just an example script to show the expected structure of a script file, some mandatory variables are missing to initialize the VariablesStorer, such as 'provider', 'expocode', 'date', 'month', 'day', 'hour' and 'depth'.
2. This is just an example script to show the expected structure of a script file, some mandatory variables are missing to initialize the VariablesStorer, such as 'provider', 'expocode', 'date', 'month', 'day', 'hour' and 'depth'.

It is also possible to use [Constraints](/reference/data_classes/#bgc_data_processing.data_classes.Constraints) objects as argument when creating a plot. The plot will then follow the constraints defined in the object. Using Constraints object with plotting method allows to load a large dataset once and for all and then only plotting slices of this dataset.
