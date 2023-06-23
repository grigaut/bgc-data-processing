"""Defaults objects."""
from pathlib import Path

from bgc_data_processing import parsers

PROVIDERS_CONFIG = parsers.ConfigParser(Path("config/providers.toml"), True)

VARS = parsers.DefaultTemplatesParser(
    filepath=Path("config/variables.toml"),
    check_types=True,
)
WATER_MASSES = parsers.WaterMassesParser(
    filepath=Path("config/water_masses.toml"),
    check_types=True,
)
