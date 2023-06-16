"""Tools to load and display standardized biogeochemical data."""

from pathlib import Path

from bgc_data_processing import parsers

BASE_DIR = Path(__file__).parent.resolve()

__all__ = [
    "PROVIDERS_CONFIG",
    "DEFAULT_VARS",
    "DEFAULT_WATER_MASSES",
]

PROVIDERS_CONFIG = parsers.ConfigParser(Path("config/providers.toml"), True)

DEFAULT_VARS = parsers.DefaultTemplatesParser(
    filepath=Path("config/variables.toml"),
    check_types=True,
)
DEFAULT_WATER_MASSES = parsers.WaterMassesParser(
    filepath=Path("config/water_masses.toml"),
    check_types=True,
)
