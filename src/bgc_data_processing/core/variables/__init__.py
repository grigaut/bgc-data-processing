"""Contain all variables-related objects.

From this namespace are accessibel:

- `ExistingVar`     -> Existing variable object
- `FeatureVar`      -> Feature variable (variable depending on operations)
- `NotExistingVar`  -> Non existing variables object
- `TemplateVar`     -> Template defining object
"""

from bgc_data_processing.core.variables.vars import (
    ExistingVar,
    FeatureVar,
    NotExistingVar,
    TemplateVar,
)

__all__ = [
    "ExistingVar",
    "FeatureVar",
    "NotExistingVar",
    "TemplateVar",
]
