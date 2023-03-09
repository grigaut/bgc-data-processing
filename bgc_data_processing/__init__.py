import numpy as np

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
DEFAULT_VARS["provider"] = TemplateVar(
    name="PROVIDER",
    unit="[]",
    var_type=str,
    default=np.nan,
    load_nb=0,
    save_nb=0,
    name_format="%-15s",
    value_format="%15s",
)
DEFAULT_VARS["expocode"] = TemplateVar(
    name="EXPOCODE",
    unit="[]",
    var_type=str,
    default=np.nan,
    load_nb=1,
    save_nb=1,
    name_format="%-15s",
    value_format="%15s",
)
DEFAULT_VARS["date"] = TemplateVar(
    name="DATE",
    unit="[]",
    var_type="datetime64[ns]",
    default=np.nan,
    load_nb=2,
    save_nb=None,
    name_format=None,
    value_format=None,
)
DEFAULT_VARS["year"] = TemplateVar(
    name="YEAR",
    unit="[]",
    var_type=int,
    default=np.nan,
    load_nb=3,
    save_nb=2,
    name_format="%-4s",
    value_format="%4d",
)
DEFAULT_VARS["month"] = TemplateVar(
    name="MONTH",
    unit="[]",
    var_type=int,
    default=np.nan,
    load_nb=4,
    save_nb=3,
    name_format="%-5s",
    value_format="%5d",
)
DEFAULT_VARS["day"] = TemplateVar(
    name="DAY",
    unit="[]",
    var_type=int,
    default=np.nan,
    load_nb=5,
    save_nb=4,
    name_format="%-3s",
    value_format="%3d",
)
DEFAULT_VARS["longitude"] = TemplateVar(
    name="LONGITUDE",
    unit="[deg_E]",
    var_type=float,
    default=np.nan,
    load_nb=6,
    save_nb=5,
    name_format="%-12s",
    value_format="%12.6f",
)
DEFAULT_VARS["latitude"] = TemplateVar(
    name="LATITUDE",
    unit="[deg_N]",
    var_type=float,
    default=np.nan,
    load_nb=7,
    save_nb=6,
    name_format="%-12s",
    value_format="%12.6f",
)
DEFAULT_VARS["depth"] = TemplateVar(
    name="DEPH",
    unit="[meter]",
    var_type=float,
    default=np.nan,
    load_nb=8,
    save_nb=7,
    name_format="%-10s",
    value_format="%10.2f",
)
DEFAULT_VARS["temperature"] = TemplateVar(
    name="TEMP",
    unit="[deg_C]",
    var_type=float,
    default=np.nan,
    load_nb=9,
    save_nb=8,
    name_format="%-10s",
    value_format="%10.3f",
)
DEFAULT_VARS["salinity"] = TemplateVar(
    name="PSAL",
    unit="[psu]",
    var_type=float,
    default=np.nan,
    load_nb=10,
    save_nb=9,
    name_format="%-10s",
    value_format="%10.3f",
)
DEFAULT_VARS["oxygen"] = TemplateVar(
    name="DOXY",
    unit="[ml/l]",
    var_type=float,
    default=np.nan,
    load_nb=11,
    save_nb=10,
    name_format="%-10s",
    value_format="%10.3f",
)
DEFAULT_VARS["phosphate"] = TemplateVar(
    name="PHOS",
    unit="[umol/l]",
    var_type=float,
    default=np.nan,
    load_nb=12,
    save_nb=11,
    name_format="%-10s",
    value_format="%10.3f",
)
DEFAULT_VARS["nitrate"] = TemplateVar(
    name="NTRA",
    unit="[umol/l]",
    var_type=float,
    default=np.nan,
    load_nb=13,
    save_nb=12,
    name_format="%-10s",
    value_format="%10.3f",
)
DEFAULT_VARS["silicate"] = TemplateVar(
    name="SLCA",
    unit="[umol/l]",
    var_type=float,
    default=np.nan,
    load_nb=14,
    save_nb=13,
    name_format="%-10s",
    value_format="%10.3f",
)
DEFAULT_VARS["chlorophyll"] = TemplateVar(
    name="CPHL",
    unit="[mg/m3]",
    var_type=float,
    default=np.nan,
    load_nb=15,
    save_nb=14,
    name_format="%-10s",
    value_format="%10.3f",
)
