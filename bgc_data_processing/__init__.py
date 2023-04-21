"""Tools to load and display standardized biogeochemical data."""

from bgc_data_processing import parsers

__all__ = [
    "PROVIDERS_CONFIG",
    "DEFAULT_VARS",
]
PROVIDERS_CONFIG = parsers.ConfigParser("config/providers.toml", True)

DEFAULT_VARS = parsers.DefaultTemplatesParser(
    filepath="config/variables.toml",
    check_types=True,
)
