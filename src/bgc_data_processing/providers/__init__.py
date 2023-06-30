"""Build all data sources which are defined in src/bgc_data_processing/providers.

From this namespace is accessible:

- `PROVIDERS` -> Providers mapping between: name -> DataSource
"""

from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bgc_data_processing.core.sources import DataSource

BASE_DIR = Path(__file__).parent.parent.resolve()


PROVIDERS: dict[str, "DataSource"] = {}
for file in BASE_DIR.joinpath("providers").glob("*.py"):
    if file.name != "__init__.py":
        mod = import_module(f"bgc_data_processing.providers.{file.stem}")
        PROVIDERS[mod.loader.provider] = mod.loader

__all__ = [
    "PROVIDERS",
]
