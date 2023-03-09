from bgc_data_processing import parsers

__all__ = [
    "CONFIG",
    "DEFAULT_VARS",
]
CONFIG = parsers.ConfigParser(filepath="config.toml", check_types=True)
DEFAULT_VARS = parsers.DefaultTemplatesParser(
    filepath="variables.toml",
    check_types=True,
)
