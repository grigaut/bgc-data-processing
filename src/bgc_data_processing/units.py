"""Unit conversion functions."""

import pandas as pd


def convert_umol_by_kg_to_mmol_by_m3(
    data_umol_by_kg: pd.Series,
) -> pd.Series:
    """Convert umol/kg to mmol/m3 using sewater denisty.

    Parameters
    ----------
    data_umol_by_kg : pd.Series
        Original data (in umol/kg)

    Returns
    -------
    pd.Series
        Converted data (mmol/m3)
    """
    kg_by_m3 = 1025  # seawater density: 1025 kg <=> 1 m3
    mmol_by_umol = 10 ** (-3)  # 1000 mmol = 1 mol
    return data_umol_by_kg * mmol_by_umol * kg_by_m3


def convert_doxy_ml_by_l_to_mmol_by_m3(
    data_ml_by_l: pd.Series,
) -> pd.Series:
    """Convert dissolved oxygen from mL/L to mmol/m3.

    Parameters
    ----------
    data_ml_by_l : pd.Series
        Original data (mL/L)

    Returns
    -------
    pd.Series
        Converted data (mmol/m3)
    """
    return data_ml_by_l * 44.6608009
