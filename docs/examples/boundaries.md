# Defining Boundaries

Loading script to load year, latitude, longitude, phosphate and nitrate variables from 2 providers, 'provider1' and 'provider2'. Phosphate variable is not measured by provider1 and nitrate is not measured by provider2. <br />
Therefore, template are created to store basic informations on variables and are then instanciated in order to create relevant ExistingVar or NotExistingVar depending on provider. <br />
Finally, latitude and longitude are applied in order to load the data only on a certain area.

``` py
import datetime as dt

from bgc_data_processing import variables, csv_tools

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
    load_nb = 0,
    save_nb = 0,
    name_format = "%-4s",
    value_format = "%4f",
)
latitude_var = variables.TemplateVar(
    name = "LATITUDE",
    unit = "[deg_N]",
    var_type = float,
    load_nb = 1,
    save_nb = 1,
    name_format = "%-12s",
    value_format = "%12.6f",
)
longitude_var = variables.TemplateVar(
    name = "LONGITUDE",
    unit = "[deg_E]",
    var_type = float,
    load_nb = 2,
    save_nb = 2,
    name_format = "%-12s",
    value_format = "%12.6f",
)
phos_var = TemplateVar(
    name="PHOS",
    unit="[umol/l]",
    var_type=float,
    load_nb=3,
    save_nb=3,
    name_format="%-10s",
    value_format="%10.3f",
)
ntra_var = TemplateVar(
    name="NTRA",
    unit="[umol/l]",
    var_type=float,
    load_nb=4,
    save_nb=4,
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
        year_var.in_file_as(("year",None,None)).remove_when_nan(),
        latitude_var.in_file_as(("lat",None,None)),
        longitude_var.in_file_as(("lon",None,None)),
        phos_var.not_in_file(),
        ntra_var.in_file_as(("ntra",None,None)),
    )
)
loader_prov2 = csv_tools.CSVLoader(
    provider_name="provider2",
    dirin="~/provider2/data",
    category="in_situ",
    files_pattern="data_({years}).csv",
    variables=variables.VariablesStorer(
        year_var.in_file_as(("year",None,None)).remove_when_nan(),
        latitude_var.in_file_as(("latitude",None,None)),
        longitude_var.in_file_as(("longitude",None,None)),
        phos_var.in_file_as(("phosphate",None,None)),
        ntra_var.not_in_file(),
    )
)
# apply boundaries
storers = []
for loader in [loader_prov1, loader_prov2]:
    loader.set_longitude_boundaries(
        longitude_min=longitude_min,
        longitude_max=longitude_max,
    )
    loader.set_latitude_boundaries(
        latitude_min=latitude_min,
        latitude_max=latitude_max,
    )
    storer = loader()
    storers.append(storer)
# Aggregation
aggregated_storer = sum(storers)
```
