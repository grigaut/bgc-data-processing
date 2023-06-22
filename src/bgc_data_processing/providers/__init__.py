"""Contain all loaders for given providers."""

from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bgc_data_processing.data_sources import DataSource

BASE_DIR = Path(__file__).parent.parent.resolve()

__all__ = [
    "LOADERS",
]

LOADERS: dict[str, "DataSource"] = {}
for file in BASE_DIR.joinpath("providers").glob("*.py"):
    if file.name != "__init__.py":
        mod = import_module(f"bgc_data_processing.providers.{file.stem}")
        LOADERS[mod.loader.provider] = mod.loader
