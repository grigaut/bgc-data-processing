"""Objects related to water masses."""
from collections.abc import Iterable

import numpy as np
import pandas as pd

from bgc_data_processing.data_classes import Constraints, Storer
from bgc_data_processing.variables import NotExistingVar


class WaterMass:
    """Water Mass.

    Parameters
    ----------
    name : str
        Water mass name.
    ptemperature_range : Iterable[float, float], optional
        Potential temperature range: (minimum, maximum), by default (np.nan, np.nan)
    salinity_range : Iterable[float, float], optional
        Salinity range: (minimum, maximum), by default (np.nan, np.nan)
    density0_range : Iterable[float, float], optional
        Density at pressure 0 range: (minimum, maximum), by default (np.nan, np.nan)
    """

    def __init__(
        self,
        name: str,
        ptemperature_range: Iterable[float, float] = (np.nan, np.nan),
        salinity_range: Iterable[float, float] = (np.nan, np.nan),
        density0_range: Iterable[float, float] = (np.nan, np.nan),
    ) -> None:
        self.name = name
        self.ptemperature_min = ptemperature_range[0]
        self.ptemperature_max = ptemperature_range[1]
        self.salinity_min = salinity_range[0]
        self.salinity_max = salinity_range[1]
        self.density0_min = density0_range[0]
        self.density0_max = density0_range[1]

    def make_constraints(
        self,
        ptemperature_label: str,
        salinity_label: str,
        density0_label: str,
    ) -> Constraints:
        """Create the constraint for the water mass.

        Parameters
        ----------
        ptemperature_label : str
            Potential temperature label.
        salinity_label : str
            Salinity label.
        density0_label : str
            Density 0 label.

        Returns
        -------
        Constraints
            Constraint corresponding to the water mass.
        """
        constraints = Constraints()
        constraints.add_boundary_constraint(
            field_label=ptemperature_label,
            minimal_value=self.ptemperature_min,
            maximal_value=self.ptemperature_max,
        )
        constraints.add_boundary_constraint(
            field_label=salinity_label,
            minimal_value=self.salinity_min,
            maximal_value=self.salinity_max,
        )
        constraints.add_boundary_constraint(
            field_label=density0_label,
            minimal_value=self.density0_min,
            maximal_value=self.density0_max,
        )
        return constraints

    def extract_from_storer(
        self,
        storer: "Storer",
        ptemperature_name: str,
        salinity_name: str,
        density0_name: str,
    ) -> "Storer":
        """Extract a the storer whose values are in the water mass.

        Parameters
        ----------
        storer : Storer
            Original Storer.
        ptemperature_name : str
            Potenital temperature variable name.
        salinity_name : str
            Salinity Variable name.
        density0_name : str
            Density at pressure 0 variable name.

        Returns
        -------
        Storer
            Storer whose values are in the water mass.
        """
        constraints = self.make_constraints(
            ptemperature_label=storer.variables.get(ptemperature_name).label,
            salinity_label=storer.variables.get(salinity_name).label,
            density0_label=storer.variables.get(density0_name).label,
        )
        return constraints.apply_constraints_to_storer(storer)

    def flag_in_storer(
        self,
        original_storer: "Storer",
        water_mass_variable_name: str,
        ptemperature_name: str,
        salinity_name: str,
        density0_name: str,
        create_var_if_missing: bool = True,
    ) -> "Storer":
        """Flag the.

        Parameters
        ----------
        original_storer : Storer
            original storer.
        water_mass_variable_name : str
            Name of the water mass variable.
        ptemperature_name : str
            Potential temperature variable name.
        salinity_name : str
            Salinity Variable name.
        density0_name : str
            Density at pressure 0 variable name.
        create_var_if_missing : bool, optional
            Wehtehr to create the water mass variable in the storer., by default True

        Returns
        -------
        Storer
            Copy of original storer with an updated 'water mass' field.

        Raises
        ------
        ValueError
            If the water mass variable doens't exists and can't be created.
        """
        constraints = self.make_constraints(
            ptemperature_label=original_storer.variables.get(ptemperature_name).label,
            salinity_label=original_storer.variables.get(salinity_name).label,
            density0_label=original_storer.variables.get(density0_name).label,
        )
        full_data = original_storer.data
        compliant = constraints.apply_constraints_to_dataframe(full_data).index
        if water_mass_variable_name in original_storer.variables.keys():  # noqa: SIM118
            water_mass_var = original_storer.variables.get(water_mass_variable_name)
            water_mass_label = water_mass_var.label
            data = full_data[water_mass_label]
            data[compliant] = self.name
            full_data[water_mass_label] = data
            return Storer(
                data=full_data,
                category=original_storer.category,
                providers=original_storer.providers[:],
                variables=original_storer.variables,
                verbose=original_storer.verbose,
            )
        if not create_var_if_missing:
            raise ValueError(
                f"{water_mass_variable_name} invalid for the given storer.",
            )

        data = pd.Series(np.nan, index=full_data.index)
        data[compliant] = self.name
        new_var = NotExistingVar(
            water_mass_variable_name,
            "[]",
            str,
            np.nan,
            "%-15s",
            "%15s",
        )
        new_storer = Storer(
            data=full_data,
            category=original_storer.category,
            providers=original_storer.providers[:],
            variables=original_storer.variables,
            verbose=original_storer.verbose,
        )
        new_storer.add_feature(new_var, data)
        return new_storer
