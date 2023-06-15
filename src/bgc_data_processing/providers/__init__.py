"""Contain all loaders for given providers."""

from importlib import import_module
from typing import TYPE_CHECKING

from bgc_data_processing import BASE_DIR

if TYPE_CHECKING:
    from bgc_data_processing.loaders.base import BaseLoader
__all__ = [
    "LOADERS",
]

LOADERS: dict[str, "BaseLoader"] = {}
for file in BASE_DIR.joinpath("providers").glob("*.py"):
    if file.name != "__init__.py":
        mod = import_module(f"bgc_data_processing.providers.{file.stem}")
        LOADERS[mod.loader.provider] = mod.loader
