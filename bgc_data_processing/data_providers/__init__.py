import os
from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bgc_data_processing.base import BaseLoader
__all__ = [
    "LOADERS",
]

LOADERS: dict[str, "BaseLoader"] = {}
for file in os.listdir("bgc_data_processing/data_providers"):
    if file[-3:] == ".py" and file != "__init__.py":
        mod = import_module(f"bgc_data_processing.data_providers.{file[:-3]}")
        LOADERS[mod.loader.provider] = mod.loader
