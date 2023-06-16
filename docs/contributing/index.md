# How to contribute to this project ?

A few precautions must be taken when contributing to this project.

## Adding a new variable
In order to register a new variable, one must create the variable entry in the `config/variables.toml` configuration file. In order for this addition to be permanent, the change must be done as well in the [`config/default/variables.toml`]({{repo_blob}}/config/default/variables.toml) file since `config/variables.toml` is only local.
Once the variable is created, one must manually add this variable to all the loaders defined in every file of [providers]({{fix_url("reference/providers")}}). The variable template should be automatically loaded in the `DEFAULT_VARS` dictionnary if it has been properly defined in `config/variables.toml`.
### Example

CMEMS's orginal loader's definition:
``` python title="bgc_data_processing/providers/cmems.py"
"""Specific parameters to load CMEMS-provided data."""
from bgc_data_processing import DEFAULT_VARS, PROVIDERS_CONFIG, loaders, variables

loader = loaders.from_netcdf(
    provider_name="CMEMS",
    dirin=PROVIDERS_CONFIG["CMEMS"]["PATH"],
    category=PROVIDERS_CONFIG["CMEMS"]["CATEGORY"],
    files_pattern=".*.nc",
    variables=variables.VariablesStorer(
        provider=DEFAULT_VARS["provider"].not_in_file(),
        expocode=DEFAULT_VARS["expocode"].not_in_file(),
        date=DEFAULT_VARS["date"].in_file_as("TIME"),
        year=DEFAULT_VARS["year"].not_in_file(),
        month=DEFAULT_VARS["month"].not_in_file(),
        day=DEFAULT_VARS["day"].not_in_file(),
        hour=DEFAULT_VARS["hour"].not_in_file(),
        longitude=DEFAULT_VARS["longitude"].in_file_as("LONGITUDE"),
        latitude=DEFAULT_VARS["latitude"].in_file_as("LATITUDE"),
        depth=DEFAULT_VARS["depth"]
        .in_file_as("DEPH", "PRES")
        .remove_when_nan()
        .correct_with(lambda x: -x if x > 0 else x),
        temperature=DEFAULT_VARS["temperature"].in_file_as("TEMP"),
        salinity=DEFAULT_VARS["salinity"].in_file_as("PSAL"),
        oxygen=DEFAULT_VARS["oxygen"].in_file_as("DOX1"),
        phosphate=DEFAULT_VARS["phosphate"]
        .in_file_as(("PHOS", "PHOS_QC", [1]))
        .remove_when_all_nan(),
        nitrate=DEFAULT_VARS["nitrate"]
        .in_file_as(("NTRA", "NTRA_QC", [1]))
        .remove_when_all_nan(),
        silicate=DEFAULT_VARS["silicate"]
        .in_file_as(("SLCA", "SLCA_QC", [1]))
        .remove_when_all_nan(),
        chlorophyll=DEFAULT_VARS["chlorophyll"]
        .in_file_as(("CPHL", "CPHL_QC", [1]))
        .remove_when_all_nan(),
    ),
)
```

Creating the new variable 'carbon':
``` toml title="config/variables.toml"
...
[carbon]
#? carbon.NAME: str: variable name
NAME = "CARB"
#? carbon.UNIT: str: variable unit
UNIT = "[umol/l]"
#? carbon.TYPE: str: variable type (among ['int', 'float', 'str', 'datetime64[ns]'])
TYPE = "float"
#? carbon.DEFAULT: str | int | float: default variable value if nan or not existing
DEFAULT = nan
#? carbon.NAME_FORMAT: str: format to use to save the name and unit of the variable as text
NAME_FORMAT = "%-10s"
#? carbon.VALUE_FORMAT: str: format to use to save the values of the variable as text
VALUE_FORMAT = "%10.3f"
```

Updating the loader by adding the variable (supposedly not in the file here):

``` python hl_lines="38" title="bgc_data_processing/providers/cmems.py"
"""Specific parameters to load CMEMS-provided data."""
from bgc_data_processing import DEFAULT_VARS, PROVIDERS_CONFIG, loaders, variables

loader = loaders.from_netcdf(
    provider_name="CMEMS",
    dirin=PROVIDERS_CONFIG["CMEMS"]["PATH"],
    category=PROVIDERS_CONFIG["CMEMS"]["CATEGORY"],
    files_pattern=".*.nc",
    variables=variables.VariablesStorer(
        provider=DEFAULT_VARS["provider"].not_in_file(),
        expocode=DEFAULT_VARS["expocode"].not_in_file(),
        date=DEFAULT_VARS["date"].in_file_as("TIME"),
        year=DEFAULT_VARS["year"].not_in_file(),
        month=DEFAULT_VARS["month"].not_in_file(),
        day=DEFAULT_VARS["day"].not_in_file(),
        hour=DEFAULT_VARS["hour"].not_in_file(),
        longitude=DEFAULT_VARS["longitude"].in_file_as("LONGITUDE"),
        latitude=DEFAULT_VARS["latitude"].in_file_as("LATITUDE"),
        depth=DEFAULT_VARS["depth"]
        .in_file_as("DEPH", "PRES")
        .remove_when_nan()
        .correct_with(lambda x: -x if x > 0 else x),
        temperature=DEFAULT_VARS["temperature"].in_file_as("TEMP"),
        salinity=DEFAULT_VARS["salinity"].in_file_as("PSAL"),
        oxygen=DEFAULT_VARS["oxygen"].in_file_as("DOX1"),
        phosphate=DEFAULT_VARS["phosphate"]
        .in_file_as(("PHOS", "PHOS_QC", [1]))
        .remove_when_all_nan(),
        nitrate=DEFAULT_VARS["nitrate"]
        .in_file_as(("NTRA", "NTRA_QC", [1]))
        .remove_when_all_nan(),
        silicate=DEFAULT_VARS["silicate"]
        .in_file_as(("SLCA", "SLCA_QC", [1]))
        .remove_when_all_nan(),
        chlorophyll=DEFAULT_VARS["chlorophyll"]
        .in_file_as(("CPHL", "CPHL_QC", [1]))
        .remove_when_all_nan(),
        carbon=DEFAULT_VARS["carbon"].not_in_file(), # (1)!
    ),
)
```

1. Additional row to use the 'carbon' variable

!!! warning "Warning"
    The new variable must be define in **every** loader's definition file.

## Adding a new provider
In order to register a new provider, one must be create a new entry in the `config/providers.toml` configuration file. In order for this addition to be permanent, the change must be done as well in the [`config/default/providers.toml`]({{repo_blob}}/config/default/providers.toml) file since `config/providers.toml` is only local.
Once the entry is created, one must manually create a file to define this provider's loader in [providers]({{repo_tree}}/src/bgc_data_processing/providers). All the available variables must be properly defined in the loader's VariablesStorer (proper names, correction functions, flag informations...).

### Example
Creating a new provider entry:

``` toml title="config/providers.toml"
...
[BGC_PROVIDER]
#? BGC_PROVIDER.PATH: str: path to the folder containing the data
PATH = "/path/to/data/directory"
#? BGC_PROVIDER.CATEGORY: str: data category, either 'float' or 'in_situ'
CATEGORY = "in_situ"
#? BGC_PROVIDER.EXCLUDE: list[str]: files to exclude from loading
EXCLUDE = []
```

Creating a new file in [providers]({{repo_tree}}/src/bgc_data_processing/providers) :

``` py title="bgc_data_processing/providers/bgc_provider.py"
"""Specific parameters to load BGC_PROVIDER-provided data."""

from bgc_data_processing import DEFAULT_VARS, PROVIDERS_CONFIG, loaders, variables

loader = loaders.from_netcdf(
    provider_name="BGC_PROVIDER",
    dirin=PROVIDERS_CONFIG["BGC_PROVIDER"]["PATH"],
    category=PROVIDERS_CONFIG["BGC_PROVIDER"]["CATEGORY"],
    files_pattern=".*.csv",                                             # (1)!
    variables=variables.VariablesStorer(
        provider=DEFAULT_VARS["provider"].in_file_as("provider"),
        expocode=DEFAULT_VARS["expocode"].not_in_file(),
        date=DEFAULT_VARS["date"].in_file_as("time"),
        year=DEFAULT_VARS["year"].not_in_file(),
        month=DEFAULT_VARS["month"].not_in_file(),
        day=DEFAULT_VARS["day"].not_in_file(),
        hour=DEFAULT_VARS["hour"].not_in_file(),
        longitude=DEFAULT_VARS["longitude"].in_file_as("longitude"),
        latitude=DEFAULT_VARS["latitude"].in_file_as("latitude"),
        depth=DEFAULT_VARS["depth"]
        .in_file_as("DEPH")
        .remove_when_nan(),
        temperature=DEFAULT_VARS["temperature"].in_file_as("temperature"),
        salinity=DEFAULT_VARS["salinity"].in_file_as("salinity"),
        oxygen=DEFAULT_VARS["oxygen"].in_file_as("doxygen"),
        phosphate=DEFAULT_VARS["phosphate"]
        .in_file_as(("PHOS", "PHOS_QC", [1]))
        .remove_when_all_nan(),
        nitrate=DEFAULT_VARS["nitrate"]
        .in_file_as(("NTRA", "NTRA_QC", [1]))
        .remove_when_all_nan(),
        silicate=DEFAULT_VARS["silicate"]
        .in_file_as(("SLCA", "SLCA_QC", [1]))
        .remove_when_all_nan(),
        chlorophyll=DEFAULT_VARS["chlorophyll"]
        .in_file_as(("CPHL", "CPHL_QC", [1]))
        .remove_when_all_nan(),
    ),
)
```

1. File pattern must be updated as well if possible
