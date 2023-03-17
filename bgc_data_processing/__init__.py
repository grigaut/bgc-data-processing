from bgc_data_processing import parsers

__all__ = [
    "SAVE_CONFIG",
    "PLOT_CONFIG",
    "PROVIDERS_CONFIG",
    "DEFAULT_VARS",
]

SAVE_CONFIG = parsers.ConfigParser(
    "config/save_data.toml",
    True,
    ["DATE_MIN", "DATE_MAX"],
    ["SAVING_DIR"],
)
PLOT_CONFIG = parsers.ConfigParser(
    "config/plot_mesh.toml",
    True,
    ["DATE_MIN", "DATE_MAX"],
    ["SAVING_DIR"],
)
PROVIDERS_CONFIG = parsers.ConfigParser("config/providers.toml", True)

DEFAULT_VARS = parsers.DefaultTemplatesParser(
    filepath="config/variables.toml",
    check_types=True,
)
