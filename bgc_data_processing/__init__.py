from bgc_data_processing.parsers import ConfigParser
from bgc_data_processing.variables import TemplateVar

__all__ = [
    "CONFIG",
]
CONFIG = ConfigParser(filepath="config.toml", check_types=True)

# Default variables setup using the format :
# TemplateVar(
#   name,
#   unit,
#   type,
#   loading_sort_nb,
#   saving_sort_nb,
#   name_str_format,
#   value_str_format,
# )


DEFAULT_VARS: dict[str, TemplateVar] = {}
DEFAULT_VARS["provider"] = TemplateVar("PROVIDER", "[]", str, 0, 0, "%-15s", "%15s")
DEFAULT_VARS["expocode"] = TemplateVar("EXPOCODE", "[]", str, 1, 1, "%-15s", "%15s")
DEFAULT_VARS["date"] = TemplateVar("DATE", "[]", "datetime64[ns]", 2, None, None)
DEFAULT_VARS["year"] = TemplateVar("YEAR", "[]", int, 3, 2, "%-4s", "%4d")
DEFAULT_VARS["month"] = TemplateVar("MONTH", "[]", int, 4, 3, "%-5s", "%5d")
DEFAULT_VARS["day"] = TemplateVar("DAY", "[]", int, 5, 4, "%-3s", "%3d")
DEFAULT_VARS["longitude"] = TemplateVar(
    "LONGITUDE", "[deg_E]", float, 6, 5, "%-12s", "%12.6f"
)
DEFAULT_VARS["latitude"] = TemplateVar(
    "LATITUDE", "[deg_N]", float, 7, 6, "%-12s", "%12.6f"
)
DEFAULT_VARS["depth"] = TemplateVar("DEPH", "[meter]", float, 8, 7, "%-10s", "%10.2f")
DEFAULT_VARS["temperature"] = TemplateVar(
    "TEMP", "[deg_C]", float, 9, 8, "%-10s", "%10.3f"
)
DEFAULT_VARS["salinity"] = TemplateVar("PSAL", "[psu]", float, 10, 9, "%-10s", "%10.3f")
DEFAULT_VARS["oxygen"] = TemplateVar("DOXY", "[ml/l]", float, 11, 10, "%-10s", "%10.3f")
DEFAULT_VARS["phosphate"] = TemplateVar(
    "PHOS", "[umol/l]", float, 12, 11, "%-10s", "%10.3f"
)
DEFAULT_VARS["nitrate"] = TemplateVar(
    "NTRA", "[umol/l]", float, 13, 12, "%-10s", "%10.3f"
)
DEFAULT_VARS["silicate"] = TemplateVar(
    "SLCA", "[umol/l]", float, 14, 13, "%-10s", "%10.3f"
)
DEFAULT_VARS["chlorophyll"] = TemplateVar(
    "CPHL", "[mg/m3]", float, 15, 14, "%-10s", "%10.3f"
)
