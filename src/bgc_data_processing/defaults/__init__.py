"""
**Defaults object built using the configuration files**

The default objects include:

- PROVIDERS_CONFIG -> providers configuration as detailled in config/providers.toml
- VARS -> default variables defined in config/variables.toml
- WATER_MASS -> default water masses defined in config/water_masses.toml

To access the defaults objects:
```
>>> import bgc_data_processing as bgc_dp
>>> bgc_dp.defaults.PROVIDERS_CONFIG    # Providers configuration
>>> bgc_dp.defaults.VARS                # Default variables
>>> bgc_dp.defaults.WATER_MASS          # default water masses
```
"""  # noqa: D400

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

__all__ = [
    "PROVIDERS_CONFIG",
    "VARS",
    "WATER_MASSES",
]
