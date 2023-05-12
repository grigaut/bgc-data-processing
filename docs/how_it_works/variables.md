# Variables

Variable objects save the meta data for data variables. <br/>
The object's informations are among:

- variable name in file: `alias`
- variable name to use to manipulate the object: `name`
- name to write in the dataframe: `label`
- unit name to display in the dataframe: `unit`
- the data type to use for this particular data: `var_type`

Additionally, the object also contains the informations on the transformations to apply to the data :

- corrections functions to apply to the column (for example to change its unit)
- flags informations to use to only keep data with a 'good' flag

Different types of variables exist :

=== "TemplateVar"
    Pre-created variable which can then be turned into ExistingVar or NotExistingVar depending on the variables in the dataset.

    ```py
    from bgc_data_processing import TemplateVar

    template = TemplateVar(
        name = "LATITUDE",
        unit = "[deg_N]",
        var_type = float,
        name_format = "%-12s",
        value_format = "%12.6f",
    )
    ```

    !!! tip "Usecase of TemplateVar"
        When loading data from different sources, it is recommended to use TemplateVar to define all variable and then properly instantiate the variable for each source using the [.not_in_file]({{fix_url("../reference/variables/#bgc_data_processing.variables.TemplateVar.not_in_file")}}) and [.in_file_as]({{fix_url("../reference/variables/#bgc_data_processing.variables.TemplateVar.in_file_as")}}) methods.

=== "NotExistingVar"
    Variable which is known to not exist in the dataset. If needed, the corresponding column in the dataframe can be filled later or it will remain as nan.

    They can be created from a TemplateVar (recommended):

    ```py
    from bgc_data_processing import TemplateVar

    template = TemplateVar(
        name = "LATITUDE",
        unit = "[deg_N]",
        var_type = float,
        name_format = "%-12s",
        value_format = "%12.6f",
    )
    notexisting = template.not_in_file()
    ```

    or they can be created from scratch:

    ```py
    from bgc_data_processing import NotExistingVar

    notexisting = NotExistingVar(
        name = "LATITUDE",
        unit = "[deg_N]",
        var_type = float,
        name_format = "%-12s",
        value_format = "%12.6f",
    )
    ```

=== "ExistingVar"
    Variable which is supposed to be find in the dataset under a certain alias. These objects also come methods to define correction functions and flag filtering options. <br/>To use theses variables properly, one must define the aliases (the name of the variable in the dataset) for the variable. It can be given any number of aliases, but the order of the aliases in important since if defines their relative priority (the first the highest priority). When loading the dataset, the first found aliases will be used to load the variable from the dataset.

    They can be created from a TemplateVar (recommended):

    ```py
    from bgc_data_processing import TemplateVar

    template = TemplateVar(
        name = "LATITUDE",
        unit = "[deg_N]",
        var_type = float,
        name_format = "%-12s",
        value_format = "%12.6f",
    )
    existing = template.in_file_as(
        ("latitude","latitude_flag", [1])   # (1)
        ("latitude2",None,None),            # (2)
    )
    ```

    1. Use column "latitude" from source, only keep rows where the flag column (name "latitude_flag") value is 1.
    2. No flag filtering for the second alias.

    or they can be created from scratch:

    ```py
    from bgc_data_processing import ExistingVar

    existing = ExistingVar(
        name = "LATITUDE",
        unit = "[deg_N]",
        var_type = float,
        name_format = "%-12s",
        value_format = "%12.6f",
    ).in_file_as(
        ("latitude","latitude_flag", [1])
        ("latitude2",None,None),
    )
    ```

=== "ParsedVar"
    Variable partially reconstructed from a csv file saved through the [.save]({{fix_url("../reference/data_classes/#bgc_data_processing.data_classes.Storer.save")}}) method of a Storer.

    They can be created from scratch but usually it useless to manually use them.


!!! warning ""
    Note that no variable is created by the loader. For example, if the 'DATE' variable is required in the loader's routine, then the variable must exists in the VariableStorer provided when initializating the object.


## Corrections

It is possible to specify corrections functions to apply to an ExistingVar in order to apply minor correction. This can be done using the [.correct_with]({{fix_url("../reference/variables/#bgc_data_processing.variables.ExistingVar.correct_with")}}) method. The function given to the method will then be applied to the column once the data loaded.

```py
from bgc_data_processing import TemplateVar

template = TemplateVar(
    name = "LATITUDE",
    unit = "[deg_N]",
    var_type = float,
    name_format = "%-12s",
    value_format = "%12.6f",
)
existing = template.in_file_as(
    ("latitude","latitude_flag", [1])
    ("latitude2",None,None),
).correct_with(
    lambda x : 2*x                      # (1)
)
```

1. Correction function definition to double the value of the variable in all rows.

## Removing rows when variables are NaN

It possible to specify settings for ExistingVar and NotExistingVar to remove the rows where the variable is NaN or where specific variable ar all NaN

=== "When a particular variable is NaN"
    It can be done using the [.remove_when_nan]({{fix_url("../reference/variables/#bgc_data_processing.variables.ExistingVar.remove_when_nan")}}) method. Then, when the values associated to the object returned by this method will be nan, the row will be deleted.

    ```py
    from bgc_data_processing import TemplateVar

    template = TemplateVar(
        name = "LATITUDE",
        unit = "[deg_N]",
        var_type = float,
        name_format = "%-12s",
        value_format = "%12.6f",
    )
    existing = template.in_file_as(
        ("latitude","latitude_flag", [1])
        ("latitude2",None,None),
    ).remove_when_nan()                     # (1)
    ```

    1. If latitude value is NaN, the row is dropped.

=== "When many variables are Nan"
    It can be done using the [.remove_when_all_nan]({{fix_url("../reference/variables/#bgc_data_processing.variables.ExistingVar.remove_when_all_nan")}}) method. Then, when the values associated to the object returned by this method will be nan, the row will be deleted.

    ```py
    from bgc_data_processing import TemplateVar

    template_lat = TemplateVar(
        name = "LATITUDE",
        unit = "[deg_N]",
        var_type = float,
        name_format = "%-12s",
        value_format = "%12.6f",
    )
    template_lon = TemplateVar(
        name = "LONGITUDE",
        unit = "[deg_E]",
        var_type = float,
        name_format = "%-12s",
        value_format = "%12.6f",
    )
    existing_lat = template_lat.in_file_as(
        ("latitude","latitude_flag", [1])
    ).remove_when_all_nan()                     # (1)
    existing_lon = template_lon.in_file_as(
        ("longitude","longitude_flag", [1])
    ).remove_when_all_nan()                     # (2)
    ```

    1. If both latitude **and** longitude value are NaN, the row is dropped.
    2. If both latitude **and** longitude value are NaN, the row is dropped.

## Variables Storer

All variables can then be stored in a [VariablesStorer]({{fix_url("../reference/variables/#bgc_data_processing.variables.VariablesStorer")}}) object so that loaders can easily interact with them.

``` py
from bgc_data_processing import TemplateVar, VariablesStorer

template_lat = TemplateVar(
    name = "LATITUDE",
    unit = "[deg_N]",
    var_type = float,
    name_format = "%-12s",
    value_format = "%12.6f",
)
template_lon = TemplateVar(
    name = "LONGITUDE",
    unit = "[deg_E]",
    var_type = float,
    name_format = "%-12s",
    value_format = "%12.6f",
)
existing_lat = template_lat.in_file_as(
    ("latitude","latitude_flag", [1])
)
existing_lon = template_lon.in_file_as(
    ("longitude","longitude_flag", [1])
)
variables_storer = VariablesStorer(
    latitude=existing_lat,
    longitude=existing_lon,
)
```

## Default variables
By default, some variables are alreadey defined in `variables.toml` as TemplateVar. These variables are the most common ones for this project and the templates can be used to instanciate the ExistingVar or notExistingvar depending on the source dataset.

One variable definition example can be found here:
``` toml
--8<-- "config/default/variables.toml::13"
```

To add a new variable, one simply has to create and edit a new set of rows, following the pattern of the already defined variables, creating for example the variable `var`:
``` toml
[var1]
#? var1.NAME: str: variable name
NAME="VAR1"
#? var1.UNIT: str: variable unit
UNIT="[]"
#? var1.TYPE: str: variable type (among ['int', 'float', 'str', 'datetime64[ns]'])
TYPE="str"
#? var1.DEFAULT: str | int | float: default variable value if nan or not existing
DEFAULT=nan
#? var1.NAME_FORMAT: str: format to use to save the name and unit of the variable
NAME_FORMAT="%-15s"
#? var1.VALUE_FORMAT: str: format to use to save the values of the variable
VALUE_FORMAT="%15s"
```

The lines starting with `#? ` are not mandatory, but they allow type hinting for the variables to ensure that the correct value type is inputed.
