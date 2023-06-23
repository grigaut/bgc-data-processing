"""Defaults objects."""
from pathlib import Path

from bgc_data_processing import parsers

PROVIDERS_CONFIG = parsers.ConfigParser(Path("config/providers.toml"), True)

DEFAULT_VARS = parsers.DefaultTemplatesParser(
    filepath=Path("config/variables.toml"),
    check_types=True,
)
DEFAULT_WATER_MASSES = parsers.WaterMassesParser(
    filepath=Path("config/water_masses.toml"),
    check_types=True,
)
