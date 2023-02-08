import os
import tomllib

from bgc_data_processing.variables import Var

__all__ = [
    "CONFIG",
]
# Default variables setup using the format :
# Var(name, unit, type, loading_sort_nb, saving_sort_nb, name_str_format, value_str_format)

DEFAULT_VARS: dict[str, Var] = {}
DEFAULT_VARS["provider"] = Var("PROVIDER", "[]", str, 0, 0, "%-15s", "%15s")
DEFAULT_VARS["expocode"] = Var("EXPOCODE", "[]", str, 1, 1, "%-15s", "%15s")
DEFAULT_VARS["date"] = Var("DATE", "[]", "datetime64[ns]", 2, None, None)
DEFAULT_VARS["year"] = Var("YEAR", "[]", int, 3, 2, "%-4s", "%4d")
DEFAULT_VARS["month"] = Var("MONTH", "[]", int, 4, 3, "%-5s", "%5d")
DEFAULT_VARS["day"] = Var("DAY", "[]", int, 5, 4, "%-3s", "%3d")
DEFAULT_VARS["longitude"] = Var("LONGITUDE", "[deg_E]", float, 6, 5, "%-12s", "%12.6f")
DEFAULT_VARS["latitude"] = Var("LATITUDE", "[deg_N]", float, 7, 6, "%-12s", "%12.6f")
DEFAULT_VARS["depth"] = Var("DEPH", "[meter]", float, 8, 7, "%-10s", "%10.2f")
DEFAULT_VARS["temperature"] = Var("TEMP", "[deg_C]", float, 9, 8, "%-10s", "%10.3f")
DEFAULT_VARS["salinity"] = Var("PSAL", "[psu]", float, 10, 9, "%-10s", "%10.3f")
DEFAULT_VARS["oxygen"] = Var("DOXY", "[ml/l]", float, 11, 10, "%-10s", "%10.3f")
DEFAULT_VARS["phosphate"] = Var("PHOS", "[umol/l]", float, 12, 11, "%-10s", "%10.3f")
DEFAULT_VARS["nitrate"] = Var("NTRA", "[umol/l]", float, 13, 12, "%-10s", "%10.3f")
DEFAULT_VARS["silicate"] = Var("SLCA", "[umol/l]", float, 14, 13, "%-10s", "%10.3f")
DEFAULT_VARS["chlorophyll"] = Var("CPHL", "[mg/m3]", float, 15, 14, "%-10s", "%10.3f")

with open("config.toml", "rb") as f:
    CONFIG = tomllib.load(f)
if not os.path.isdir(CONFIG["SAVING"]["FILES_DIR"]):
    os.mkdir(CONFIG["SAVING"]["FILES_DIR"])
