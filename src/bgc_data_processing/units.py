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


def convert_nitrate_mgc_by_m3_to_umol_by_l(
    data_mgc_m3: pd.Series,
) -> pd.Series:
    """Convert nitrate concentration from mgC/m3 to μmol/L.

    Parameters
    ----------
    data_ml_by_l : pd.Series
        Original data (mgC/m3)

    Returns
    -------
    pd.Series
        Converted data (μmol/L)
    """
    mgc_by_mgno3 = 6.625 * 12.01  # 6.625*12.01 mg(NO3) <=> 1 mg(C)
    mgno3_by_mgc = 1 / mgc_by_mgno3
    g_by_molno3 = 62.009  # Nitrate molar mass: 62.009 g <=> 1 mol
    mg_by_g = 1_000  # 1000 mg = 1 g
    mg_by_molno3 = mg_by_g * g_by_molno3
    molno3_by_mg = 1 / mg_by_molno3
    l_by_m3 = 1_000  # 1000 L <=> 1 m3
    umol_by_mol = 1_000_000  # 1 000 000 μmol = 1 mol
    return data_mgc_m3 * mgno3_by_mgc * molno3_by_mg * umol_by_mol / l_by_m3
