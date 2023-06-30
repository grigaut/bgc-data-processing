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
    import bgc_data_processing as bgc_dp

    template = bgc_dp.variables.TemplateVar(
        name = "LATITUDE",
        unit = "[deg_N]",
        var_type = float,
        name_format = "%-12s",
        value_format = "%12.6f",
    )
    ```

    !!! tip "Usecase of TemplateVar"
        When loading data from different sources, it is recommended to use TemplateVar to define all variable and then properly instantiate the variable for each source using the [`.not_in_file`]({{fix_url("../reference/core/variables/#bgc_data_processing.core.variables.TemplateVar.not_in_file")}}) and [`.in_file_as`]({{fix_url("../reference/core/variables/#bgc_data_processing.core.variables.TemplateVar.in_file_as")}}) methods.

=== "NotExistingVar"
    Variable which is known to not exist in the dataset. If needed, the corresponding column in the dataframe can be filled later or it will remain as nan.

    They can be created from a TemplateVar (recommended):

    ```py
    import bgc_data_processing as bgc_dp

    template = bgc_dp.variables.TemplateVar(
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
    import bgc_data_processing as bgc_dp

    notexisting = bgc_dp.variables.NotExistingVar(
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
    import bgc_data_processing as bgc_dp

    template = bgc_dp.variables.TemplateVar(
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
    import bgc_data_processing as bgc_dp

    existing = bgc_dp.variables.ExistingVar(
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
    Variable partially reconstructed from a csv file saved with a [`StorerSaver`]({{fix_url("../reference/core/io/savers/#bgc_data_processing.core.io.savers.StorerSaver")}}).

    They can be created from scratch but usually it useless to manually use them.


=== "FeatureVar"
    Variable which result from a [`feature`]({{fix_url("../reference/features/#bgc_data_processing.features.BaseFeature")}}). A feature variable is made out of operations over other variables.

    For example, the `CPHL` (chlorophyll) variable, made from `DIAC`(diatoms) and `FLAC` (flagellates) :

    ```py
    import numpy as np

    import bgc_data_processing as bgc_dp

    feature_var = bgc_dp.variables.FeatureVar(
        feature = bgc_dp.features.ChlorophyllFromDiatomFlagellate(
            diatom_variable=DIATOM_VAR,                             # (1)!
            flagellate_variable=FLAGELLATE_VAR,                     # (2)!
            var_name = "CPHL",
            var_unit = "[mg/m3]",
            var_type = float,
            var_default = np.nan,
            var_name_format = "%-10s",
            var_value_format = "%10.3f",
        )
    )
    ```

    1. Pre-defined `Existingvar` for diatom concentration
    2. Pre-defined `Existingvar` for flagellate concentration

    using the [`is_loadable`]({{fix_url("../reference/core/variables/vars/#bgc_data_processing.core.variables.vars.FeatureVar.is_loadable")}}) from the feature will return True if the input list of variables contains all necessary variable to create the feature.

    Then, using the [`insert_in_storer`]({{fix_url("../reference/features/#bgc_data_processing.features.BaseFeature.insert_in_storer")}}) of the FeatureVar.feature property makes it possible to insert the FeatureVar into a storer containing all required variables.


!!! warning ""
    Note that no variable is created by the [`DataSource`]({{fix_url("../reference/core/sources/#bgc_data_processing.core.sources.DataSource")}}). For example, if the 'DATE' variable is required in the loader's routine, then the variable must exists in the [`SourceVariableSet`]({{fix_url("../reference/core/variables/sets/#bgc_data_processing.core.variables.sets.SourceVariableSet")}}) provided when initializating the object.


## Corrections

It is possible to specify corrections functions to apply to an ExistingVar in order to apply minor correction. This can be done using the [`.correct_with`]({{fix_url("../reference/core/variables/vars/#bgc_data_processing.core.variables.vars.ExistingVar.correct_with")}}) method. The function given to the method will then be applied to the column once the data loaded.

```py
import bgc_data_processing as bgc_dp

template = bgc_dp.variables.TemplateVar(
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
    It can be done using the [.remove_when_nan]({{fix_url("../reference/core/variables/vars/#bgc_data_processing.core.variables.vars.ExistingVar.remove_when_nan")}}) method. Then, when the values associated to the object returned by this method will be nan, the row will be deleted.

    ```py
    import bgc_data_processing as bgc_dp

    template = bgc_dp.variables.TemplateVar(
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
    It can be done using the [`.remove_when_all_nan`]({{fix_url("../reference/core/variables/vars/#bgc_data_processing.core.variables.vars.ExistingVar.remove_when_all_nan")}}) method. Then, when the values associated to the object returned by this method will be nan, the row will be deleted.

    ```py
    import bgc_data_processing as bgc_dp

    template_lat = bgc_dp.variables.TemplateVar(
        name = "LATITUDE",
        unit = "[deg_N]",
        var_type = float,
        name_format = "%-12s",
        value_format = "%12.6f",
    )
    template_lon = bgc_dp.variables.TemplateVar(
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

## Variables Sets

All variables can then be stored in a [`VariableSet`]({{fix_url("../reference/core/variables/sets/#bgc_data_processing.core.variables.sets.VariableSet")}}) object so that loaders can easily interact with them.

``` py
from bgc_data_processing.core.variables.vars import TemplateVar
from bgc_data_processing.core.variables.sets import VariableSet

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
By default, some variables are alreadey defined in `config/variables.toml` (in [`config/default/variables.toml`]({{repo_blob}}/config/default/variables.toml)) as TemplateVar. These variables are the most common ones for this project and the templates can be used to instanciate the `ExistingVar` or `NotExistingvar` depending on the source dataset.

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

The lines starting with `#? ` allow type hinting for the variables to ensure that the correct value type is inputed.
