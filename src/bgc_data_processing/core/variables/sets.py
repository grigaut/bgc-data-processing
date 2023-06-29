"""Variable Ensembles."""
import itertools
from collections.abc import Callable, Iterator
from copy import copy, deepcopy
from typing import TypeAlias

import numpy as np
from _collections_abc import dict_keys

from bgc_data_processing.core.variables.vars import (
    ExistingVar,
    FeatureVar,
    NotExistingVar,
    ParsedVar,
)
from bgc_data_processing.exceptions import (
    DuplicatedVariableNameError,
    FeatureConstructionError,
    IncorrectVariableNameError,
)

AllVariablesTypes: TypeAlias = ExistingVar | NotExistingVar | ParsedVar | FeatureVar
NotParsedvar: TypeAlias = ExistingVar | NotExistingVar | FeatureVar
FromFileVariables: TypeAlias = ExistingVar | NotExistingVar


class VariableSet:
    """Variable ensemble behavior implementation.

    This class represents the set of both variables present \
    in the file and variables to take in consideration \
    (therefore to add even if empty) when loading the data.

    Parameters
    ----------
    *args: list
        Var objects to represent the variables stored by the object.
        It is better if these Var object have been instanciated
        using .not_here or .here_as methods.
    *kwargs: dict
        Var objects to represent the variables stored by the object.
        It is better if these Var object have been instanciated
        using .not_here or .here_as methods. The parameter name has no importance.

    Raises
    ------
    ValueError:
        If multiple var object have the same name.
    """

    def __init__(
        self,
        *args: FromFileVariables,
        **kwargs: FromFileVariables,
    ) -> None:
        if len(args) != len({var.name for var in args}):
            error_msg = (
                "To set multiple alias for the same variable, "
                "use Var.in_file_as([alias1, alias2])"
            )
            raise ValueError(error_msg)
        self._instantiate_from_elements([*args, *kwargs.values()])

    def _instantiate_from_elements(self, elements: list[AllVariablesTypes]) -> None:
        """Set instance's attribute to aa correct value based on the list of elements.

        Parameters
        ----------
        elements : list[AllVariablesTypes]
            List of all elements.
        """
        self._elements: list[FromFileVariables | ParsedVar] = copy(elements)
        self._save = [var.name for var in elements]
        self._in_dset = [var for var in self._elements if var.exist_in_dset]
        self._not_in_dset = [var for var in self._elements if not var.exist_in_dset]

    def __getitem__(self, __k: str) -> FromFileVariables:
        """Get variable by its name.

        Parameters
        ----------
        __k : str
            Variable name

        Returns
        -------
        FromFileVariables
            Corresponding variable with name __k
        """
        return self.get(__k)

    def __iter__(self) -> Iterator[FromFileVariables]:
        """Get an iterator of all variables.

        Yields
        ------
        Iterator[FromFileVariables]
            Ietrator of all element in the storer.
        """
        return iter(self._elements)

    def __str__(self) -> str:
        """Convert the object to string.

        Returns
        -------
        str
            All variable as strings.
        """
        txt = ""
        for var in self._elements:
            if var.exist_in_dset is None:
                here_txt = "not attributed"
            elif var.exist_in_dset:
                here_txt = var.aliases
            else:
                here_txt = "not in file"
            txt += str(var) + f": {here_txt}\n"
        return txt

    def __len__(self) -> int:
        """Return the number of elements.

        Returns
        -------
        int
            Number of elements.
        """
        return len(self._elements)

    def __eq__(self, __o: object) -> bool:
        """Compare to object for equality.

        Parameters
        ----------
        __o : object
            Object to compare with.

        Returns
        -------
        bool
            True if the objects have same types and all equal variables.
        """
        if not isinstance(__o, VariableSet):
            return False

        has_wrong_len = len(self) != len(__o)
        self_keys = set(self.mapper_by_name.keys())
        other_keys = set(__o.mapper_by_name.keys())
        has_wrong_keys = self_keys != other_keys

        if has_wrong_len or has_wrong_keys:
            return False

        repr_eq = [repr(self[key]) == repr(__o[key]) for key in self.mapper_by_name]
        return np.all(repr_eq)

    def get(self, var_name: str) -> FromFileVariables:
        """Return the variable which name corresponds to var_name.

        Parameters
        ----------
        var_name : str
            Name of the variable to get.

        Returns
        -------
        FromFileVariables
            Variable with corresponding name in self._elements.

        Raises
        ------
        IncorrectVariableNameError
            If var_name doesn't correspond to any name.
        """
        if self.has_name(var_name=var_name):
            return self.mapper_by_name[var_name]
        error_msg = (
            f"{var_name} is not a valid variable name.Valid names are: "
            f"{list(self.mapper_by_name.keys())}"
        )
        raise IncorrectVariableNameError(error_msg)

    def add_var(self, var: FromFileVariables) -> None:
        """Add a new variable to self._elements.

        Parameters
        ----------
        var : Var
            Variable to add

        Raises
        ------
        DuplicatedVariableNameError
            If the variable name is already in the set.
        """
        if var.name in self.keys():  # noqa: SIM118
            error_msg = "A variable already exists with his name"
            raise DuplicatedVariableNameError(error_msg)
        self._elements.append(var)
        self._instantiate_from_elements(self._elements)

    def pop(self, var_name: str) -> AllVariablesTypes:
        """Remove and return the variable with the given name.

        Parameters
        ----------
        var_name : str
            Name of the variable to remove from the ensemble.

        Returns
        -------
        AllVariablesTypes
            Removed variable.
        """
        var_to_suppress = self.get(var_name)
        elements = [e for e in self._elements if e.name != var_name]
        self._instantiate_from_elements(elements)
        return var_to_suppress

    def has_name(self, var_name: str) -> bool:
        """Check if a variable name is the nam eof one of the variables.

        Parameters
        ----------
        var_name : str
            Name to test.

        Returns
        -------
        bool
            True if the name is in self.keys(), False otherwise.
        """
        return var_name in self.keys()  # noqa: SIM118

    def keys(self) -> dict_keys:
        """Keys to use when calling self[key].

        Returns
        -------
        dict_keys
            View of self.mapper_by_name keys.
        """
        return self.mapper_by_name.keys()

    def _get_mandatory_variables_as_input_dict(self) -> dict[str, AllVariablesTypes]:
        """Return Mandatory variables as dict suitable for Set instanciation..

        Returns
        -------
        dict[str, AllVariablesTypes]
            Mapping between parameter name and variable value.
        """
        return {}

    def _get_inputs_for_new_ensemble(
        self,
        variables_list: list[AllVariablesTypes],
    ) -> dict[str, AllVariablesTypes]:
        """Load elements to instanciate a new set.

        Parameters
        ----------
        variables_list : list[AllVariablesTypes]
            List of all variables to return.

        Returns
        -------
        dict[str, AllVariablesTypes]
            Mapping between variables name or parameter name and variable value.
        """
        variables = self._get_mandatory_variables_as_input_dict()
        mandatory_names = [var.name for var in variables.values()]
        for var in variables_list:
            if var.name not in mandatory_names:
                variables[var.name] = var
        return variables

    @property
    def elements(self) -> list[AllVariablesTypes]:
        """All variables in the ensemble."""
        return self._elements

    @property
    def labels(self) -> dict[str, str]:
        """Returns a dicitonnary mapping variable names to variables labels.

        Returns
        -------
        dict[str, str]
            name : label
        """
        return {var.name: var.label for var in self._elements}

    @property
    def mapper_by_name(self) -> dict[str, FromFileVariables]:
        """Mapper between variables names and variables Var objects (for __getitem__).

        Returns
        -------
        dict[str, Var]
            Mapping between names (str) and variables (Var)
        """
        return {var.name: var for var in self._elements}


class FeatureVariablesSet(VariableSet):
    """Ensemble of features.

    This class represents the set of both variables present \
    in the file and variables to take in consideration \
    (therefore to add even if empty) when loading the data.

    Parameters
    ----------
    *args: list
        Var objects to represent the variables stored by the object.
        It is better if these Var object have been instanciated
        using .not_here or .here_as methods.
    *kwargs: dict
        Var objects to represent the variables stored by the object.
        It is better if these Var object have been instanciated
        using .not_here or .here_as methods. The parameter name has no importance.

    Raises
    ------
    ValueError:
        If multiple var object have the same name.
    """

    def __init__(self, *args: "FeatureVar", **kwargs: "FeatureVar") -> None:
        super().__init__(*args, **kwargs)

    def _get_constructable_features(
        self,
        to_inspect: list[FeatureVar],
        available_vars: list[AllVariablesTypes],
    ) -> list[FeatureVar]:
        """Get constructables features given available variables.

        Parameters
        ----------
        to_inspect : list[FeatureVar]
            Features to inspect for constructibility.
        available_vars : list[AllVariablesTypes]
            Variables to use to construct the variables.

        Returns
        -------
        list[FeatureVar]
            Construtable variables.
        """
        return [f for f in to_inspect if f.is_loadable(available_vars)]

    def iter_constructables_features(
        self,
        available_vars: list[AllVariablesTypes],
    ) -> Iterator[FeatureVar]:
        """Create an iterator returning constructables features.

        The Iterator considers that all constructed features
        are available to construct the following ones.

        Parameters
        ----------
        available_vars : list[AllVariablesTypes]
            Variable available to build the features.

        Yields
        ------
        Iterator[FeatureVar]
            Iterator.

        Raises
        ------
        FeatureConstructionError
            If all features can not be constructed.
        """
        available = available_vars.copy()
        features = self._elements.copy()
        constructables = self._get_constructable_features(features, available)
        while constructables:
            for feature in constructables:
                available.append(feature)
                yield feature
            features = [f for f in features if all(f != a for a in available)]
            constructables = self._get_constructable_features(features, available)
        if features:
            error_msg = (
                f"The following features can not be loaded: {features}. "
                "They probably depend on non loaded variables."
            )
            raise FeatureConstructionError(error_msg)


class BaseRequiredVarsSet(VariableSet):
    """Storer for Variable objects with some required variables.

    This class represents the set of both variables present \
    in the file and variables to take in consideration \
    (therefore to add even if empty) when loading the data.

    Parameters
    ----------
    expocode : FromFileVariables
        Expocode related variable.
    date : FromFileVariables
        Date related variable.
    year : FromFileVariables
        Year related variable.
    month : FromFileVariables
        Month related variable.
    day : FromFileVariables
        Day related variable.
    latitude : FromFileVariables
        Latitude related variable.
    longitude : FromFileVariables
        Longitude related variable.
    depth : FromFileVariables
        Depth related variable.
    provider : FromFileVariables, optional
        Provider related variable. Can be set to None to be ignored., by default None
    hour : FromFileVariables, optional
        Hour related variable. Can be set to None to be ignored., by default None
    *args: list
        Var objects to represent the variables stored by the object.
        It is better if these Var object have been instanciated
        using .not_here or .here_as methods.
    *kwargs: dict
        Var objects to represent the variables stored by the object.
        It is better if these Var object have been instanciated
        using .not_here or .here_as methods. The parameter name has no importance.

    Raises
    ------
    ValueError:
        If multiple var object have the same name.
    """

    def __init__(
        self,
        expocode: FromFileVariables,
        date: FromFileVariables,
        year: FromFileVariables,
        month: FromFileVariables,
        day: FromFileVariables,
        latitude: FromFileVariables,
        longitude: FromFileVariables,
        depth: FromFileVariables,
        hour: FromFileVariables | None = None,
        provider: FromFileVariables | None = None,
        *args: FromFileVariables,
        **kwargs: FromFileVariables,
    ) -> None:
        if len(args) != len({var.name for var in args}):
            error_msg = (
                "To set multiple alias for the same variable, "
                "use Var.in_file_as([alias1, alias2])"
            )
            raise ValueError(error_msg)
        mandatory_variables = []
        if provider is None:
            self.has_provider = False
            self.provider_var_name = None
        else:
            self.has_provider = True
            self.provider_var_name = provider.name
            mandatory_variables.append(provider)
        self.expocode_var_name = expocode.name
        mandatory_variables.append(expocode)
        self.date_var_name = date.name
        mandatory_variables.append(date)
        self.year_var_name = year.name
        mandatory_variables.append(year)
        self.month_var_name = month.name
        mandatory_variables.append(month)
        self.day_var_name = day.name
        mandatory_variables.append(day)
        if hour is None:
            self.has_hour = False
            self.hour_var_name = None
        else:
            self.has_hour = True
            self.hour_var_name = hour.name
            mandatory_variables.append(hour)
        self.latitude_var_name = latitude.name
        mandatory_variables.append(latitude)
        self.longitude_var_name = longitude.name
        mandatory_variables.append(longitude)
        self.depth_var_name = depth.name
        mandatory_variables.append(depth)
        self._elements: list[FromFileVariables | ParsedVar] = (
            mandatory_variables + list(args) + list(kwargs.values())
        )
        self._save = [var.name for var in self._elements]
        self._in_dset = [var for var in self._elements if var.exist_in_dset]
        self._not_in_dset = [var for var in self._elements if not var.exist_in_dset]

    def pop(self, var_name: str) -> AllVariablesTypes:
        """Remove and return the variable with the given name.

        Parameters
        ----------
        var_name : str
            Name of the variable to remove from the ensemble.

        Returns
        -------
        AllVariablesTypes
            Removed variable.

        Raises
        ------
        KeyError
            If the variable is mandatory.
        """
        mandatory_variables_names = [
            self.expocode_var_name,
            self.provider_var_name,
            self.date_var_name,
            self.year_var_name,
            self.month_var_name,
            self.day_var_name,
            self.hour_var_name,
            self.latitude_var_name,
            self.longitude_var_name,
            self.depth_var_name,
        ]
        if var_name in mandatory_variables_names:
            error_msg = (
                f"Variable {var_name} can not be removed since "
                "it is a mandatory variable."
            )
            raise IncorrectVariableNameError(error_msg)
        return super().pop(var_name)

    def _get_mandatory_variables_as_input_dict(self) -> dict[str, AllVariablesTypes]:
        """Return Mandatory variables as dict suitable for Set instanciation..

        Returns
        -------
        dict[str, AllVariablesTypes]
            Mapping between parameter name and variable value.
        """
        return {
            "expocode": self.get(self.expocode_var_name),
            "provider": self.get(self.provider_var_name) if self.has_provider else None,
            "date": self.get(self.date_var_name),
            "year": self.get(self.year_var_name),
            "month": self.get(self.month_var_name),
            "day": self.get(self.day_var_name),
            "hour": self.get(self.hour_var_name) if self.has_hour else None,
            "latitude": self.get(self.latitude_var_name),
            "longitude": self.get(self.longitude_var_name),
            "depth": self.get(self.depth_var_name),
        }


class LoadingVariablesSet(BaseRequiredVarsSet):
    """Storer for Var object which are going to be loaded.

    This class represents the set of both variables present \
    in the file and variables to take in consideration \
    (therefore to add even if empty) when loading the data.

    Parameters
    ----------
    expocode : FromFileVariables
        Expocode related variable.
    date : FromFileVariables
        Date related variable.
    year : FromFileVariables
        Year related variable.
    month : FromFileVariables
        Month related variable.
    day : FromFileVariables
        Day related variable.
    latitude : FromFileVariables
        Latitude related variable.
    longitude : FromFileVariables
        Longitude related variable.
    depth : FromFileVariables
        Depth related variable.
    provider : FromFileVariables, optional
        Provider related variable. Can be set to None to be ignored., by default None
    hour : FromFileVariables, optional
        Hour related variable. Can be set to None to be ignored., by default None
    *args: list
        Var objects to represent the variables stored by the object.
        It is better if these Var object have been instanciated
        using .not_here or .here_as methods.
    *kwargs: dict
        Var objects to represent the variables stored by the object.
        It is better if these Var object have been instanciated
        using .not_here or .here_as methods. The parameter name has no importance.

    Raises
    ------
    ValueError:
        If multiple var object have the same name.
    """

    def __init__(
        self,
        expocode: FromFileVariables,
        date: FromFileVariables,
        year: FromFileVariables,
        month: FromFileVariables,
        day: FromFileVariables,
        latitude: FromFileVariables,
        longitude: FromFileVariables,
        depth: FromFileVariables,
        hour: FromFileVariables | None = None,
        provider: FromFileVariables | None = None,
        *args: FromFileVariables,
        **kwargs: FromFileVariables,
    ) -> None:
        super().__init__(
            expocode,
            date,
            year,
            month,
            day,
            latitude,
            longitude,
            depth,
            hour,
            provider,
            *args,
            **kwargs,
        )

    @property
    def in_dset(self) -> list[ExistingVar]:
        """List of Var object supposedly present in the dataset.

        Returns
        -------
        list[Var]
            Var objects in the dataset.
        """
        return self._in_dset

    @property
    def corrections(self) -> dict[str, Callable]:
        """Mapping between variables keys and correcting functions.

        Returns
        -------
        dict[str, Callable]
            Mapping.
        """
        return {
            var.label: var.correction
            for var in self._in_dset
            if var.correction is not None
        }

    @property
    def to_remove_if_all_nan(self) -> list[str]:
        """Return the list of keys to inspect when removing rows.

        This is suited when seeking for rows to delete
        when many given variables are NaN.

        Returns
        -------
        list[str]
            List of keys to use.
        """
        return [var.label for var in self._elements if var.remove_if_all_nan]

    @property
    def to_remove_if_any_nan(self) -> list[str]:
        """Return the list of keys to inspect when removing rows.

        This is suited when seeking for rows to delete
        when at least one given variable is NaN.

        Returns
        -------
        list[str]
            List of keys to use.
        """
        return [var.label for var in self._elements if var.remove_if_nan]


class StoringVariablesSet(BaseRequiredVarsSet):
    """Storer for Var object which are going to be stored.

    This class represents the set of both variables present \
    in the file and variables to take in consideration \
    (therefore to add even if empty) when loading the data.

    Parameters
    ----------
    expocode : FromFileVariables
        Expocode related variable.
    date : FromFileVariables
        Date related variable.
    year : FromFileVariables
        Year related variable.
    month : FromFileVariables
        Month related variable.
    day : FromFileVariables
        Day related variable.
    latitude : FromFileVariables
        Latitude related variable.
    longitude : FromFileVariables
        Longitude related variable.
    depth : FromFileVariables
        Depth related variable.
    provider : FromFileVariables, optional
        Provider related variable. Can be set to None to be ignored., by default None
    hour : FromFileVariables, optional
        Hour related variable. Can be set to None to be ignored., by default None
    *args: list
        Var objects to represent the variables stored by the object.
        It is better if these Var object have been instanciated
        using .not_here or .here_as methods.
    *kwargs: dict
        Var objects to represent the variables stored by the object.
        It is better if these Var object have been instanciated
        using .not_here or .here_as methods. The parameter name has no importance.

    Raises
    ------
    ValueError:
        If multiple var object have the same name.
    """

    def __init__(
        self,
        expocode: FromFileVariables,
        date: FromFileVariables,
        year: FromFileVariables,
        month: FromFileVariables,
        day: FromFileVariables,
        latitude: FromFileVariables,
        longitude: FromFileVariables,
        depth: FromFileVariables,
        hour: FromFileVariables | None = None,
        provider: FromFileVariables | None = None,
        *args: FromFileVariables,
        **kwargs: FromFileVariables,
    ) -> None:
        super().__init__(
            expocode,
            date,
            year,
            month,
            day,
            latitude,
            longitude,
            depth,
            hour,
            provider,
            *args,
            **kwargs,
        )
        self._save = [var.name for var in self._elements]

    def set_saving_order(self, var_names: list[str] = []) -> None:
        """Set the saving order for the variables.

        Parameters
        ----------
        var_names : list[str], optional
            List of variable names => saving variables sorted., by default []

        Raises
        ------
        ValueError
            If a variable name is not one of the variables'.
        """
        if not var_names:
            return
        # new_save = [self.get(name) for name in var_names]
        new_save = deepcopy(var_names)
        self._save = new_save

    @property
    def saving_variables(self) -> "SavingVariablesSet":
        """Order of the variables to save."""
        variables = self._get_inputs_for_new_ensemble(self._elements)
        return SavingVariablesSet(**variables, save_order=self._save.copy())


class SavingVariablesSet(BaseRequiredVarsSet):
    """Storer for Var object which are going to be saved.

    This class represents the set of both variables present \
    in the file and variables to take in consideration \
    (therefore to add even if empty) when loading the data.

    Parameters
    ----------
    expocode : FromFileVariables
        Expocode related variable.
    date : FromFileVariables
        Date related variable.
    year : FromFileVariables
        Year related variable.
    month : FromFileVariables
        Month related variable.
    day : FromFileVariables
        Day related variable.
    latitude : FromFileVariables
        Latitude related variable.
    longitude : FromFileVariables
        Longitude related variable.
    depth : FromFileVariables
        Depth related variable.
    provider : FromFileVariables, optional
        Provider related variable. Can be set to None to be ignored., by default None
    hour : FromFileVariables, optional
        Hour related variable. Can be set to None to be ignored., by default None
    *args: list
        Var objects to represent the variables stored by the object.
        It is better if these Var object have been instanciated
        using .not_here or .here_as methods.
    *kwargs: dict
        Var objects to represent the variables stored by the object.
        It is better if these Var object have been instanciated
        using .not_here or .here_as methods. The parameter name has no importance.

    Raises
    ------
    ValueError:
        If multiple var object have the same name.
    """

    def __init__(
        self,
        expocode: FromFileVariables,
        date: FromFileVariables,
        year: FromFileVariables,
        month: FromFileVariables,
        day: FromFileVariables,
        latitude: FromFileVariables,
        longitude: FromFileVariables,
        depth: FromFileVariables,
        hour: FromFileVariables | None = None,
        provider: FromFileVariables | None = None,
        save_order: list[AllVariablesTypes] = [],
        *args: FromFileVariables,
        **kwargs: FromFileVariables,
    ) -> None:
        super().__init__(
            expocode,
            date,
            year,
            month,
            day,
            latitude,
            longitude,
            depth,
            hour,
            provider,
            *args,
            **kwargs,
        )
        if not save_order:
            self._save = [var.name for var in self._elements.copy()]
        else:
            self._save = save_order

    def set_saving_order(self, var_names: list[str] = []) -> None:
        """Set the saving order for the variables.

        Parameters
        ----------
        var_names : list[str], optional
            List of variable names => saving variables sorted., by default []

        Raises
        ------
        ValueError
            If a variable name is not one of the variables'.
        """
        if not var_names:
            return
        self._save = deepcopy(var_names)

    @property
    def save_labels(self) -> list[str | tuple[str]]:
        """Sorting order to use when saving data.

        Returns
        -------
        list[str | tuple[str]]
            List of columns keys to pass as df[self.save_sort] to sort data.
        """
        return [self.get(name).label for name in self._save]

    @property
    def save_names(self) -> list[str | tuple[str]]:
        """Sorted names of variables to use for saving.

        Returns
        -------
        list[str | tuple[str]]
            List of columns keys to pass as df[self.save_sort] to sort data.
        """
        return self._save

    @property
    def name_save_format(self) -> str:
        """String line to use as formatting for name and unit rows.

        Returns
        -------
        str
            Format string
        """
        return " ".join([self.get(name).name_format for name in self._save])

    @property
    def value_save_format(self) -> str:
        """String line to use as formatting for value rows.

        Returns
        -------
        str
            Format string"
        """
        return " ".join([self.get(name).value_format for name in self._save])


class SourceVariableSet(BaseRequiredVarsSet):
    """Ensemble of variables.

    This class represents the set of both variables present \
    in the file and variables to take in consideration \
    (therefore to add even if empty) when loading the data.

    Parameters
    ----------
    expocode : FromFileVariables
        Expocode related variable.
    date : FromFileVariables
        Date related variable.
    year : FromFileVariables
        Year related variable.
    month : FromFileVariables
        Month related variable.
    day : FromFileVariables
        Day related variable.
    latitude : FromFileVariables
        Latitude related variable.
    longitude : FromFileVariables
        Longitude related variable.
    depth : FromFileVariables
        Depth related variable.
    provider : FromFileVariables, optional
        Provider related variable. Can be set to None to be ignored., by default None
    hour : FromFileVariables, optional
        Hour related variable. Can be set to None to be ignored., by default None
    *args: list
        Var objects to represent the variables stored by the object.
        It is better if these Var object have been instanciated
        using .not_here or .here_as methods.
    *kwargs: dict
        Var objects to represent the variables stored by the object.
        It is better if these Var object have been instanciated
        using .not_here or .here_as methods. The parameter name has no importance.

    Raises
    ------
    ValueError:
        If multiple var object have the same name.
    """

    def __init__(
        self,
        expocode: FromFileVariables,
        date: FromFileVariables,
        year: FromFileVariables,
        month: FromFileVariables,
        day: FromFileVariables,
        latitude: FromFileVariables,
        longitude: FromFileVariables,
        depth: FromFileVariables,
        hour: FromFileVariables | None = None,
        provider: FromFileVariables | None = None,
        *args: FromFileVariables,
        **kwargs: FromFileVariables,
    ) -> None:
        super().__init__(
            expocode,
            date,
            year,
            month,
            day,
            latitude,
            longitude,
            depth,
            hour,
            provider,
            *args,
            **kwargs,
        )

    def _get_loadable_required_vars(
        self,
        var: FromFileVariables | ParsedVar | FeatureVar,
    ) -> list[FromFileVariables | ParsedVar]:
        """Return Variable to load.

        This function 'unwraps' features and return the variables required
        for the features. For example, for feature variable which required
        Temperature and Salinity variables (both not features as well),
        this will return a list with those two variables.
        Additionally, if a feature variable is required for another feature,
        this feature will be unwrapped as well.

        Parameters
        ----------
        var : FromFileVariables | ParsedVar | FeatureVar
            Variable to unwrap.

        Returns
        -------
        list[FromFileVariables | ParsedVar]
            List of all required variables to create the input variable.
            (The list can contain only the input variable if the input is
            not a feature.)
        """
        if var.is_feature:
            loadables = map(self._get_loadable_required_vars, var.required_vars)
            return list(itertools.chain(*loadables))
        return [var]

    def _get_featured_vars(
        self,
        var: FromFileVariables | ParsedVar | FeatureVar,
    ) -> list[FromFileVariables | ParsedVar]:
        """Return all needed features.

        This function will'unwrap' a variable and return all feature that this variable
        could require.

        Parameters
        ----------
        var : FromFileVariables | ParsedVar | FeatureVar
            Variable to unwrap.

        Returns
        -------
        list[FromFileVariables | ParsedVar]
            List of all required features for the given variable.
        """
        if not var.is_feature:
            return []
        loadables = map(self._get_featured_vars, var.required_vars)
        return [var, *list(itertools.chain(*loadables))]

    @property
    def features(self) -> FeatureVariablesSet:
        """FeatureVar list."""
        all_features_map = map(self._get_featured_vars, self._elements)
        features = list(set(itertools.chain(*all_features_map)))
        return FeatureVariablesSet(*features)

    @property
    def loading_variables(self) -> LoadingVariablesSet:
        """Ensembles of variables to load."""
        all_non_features_map = map(self._get_loadable_required_vars, self._elements)
        variables = self._get_inputs_for_new_ensemble(
            list(set(itertools.chain(*all_non_features_map))),
        )
        return LoadingVariablesSet(**variables)

    @property
    def storing_variables(self) -> StoringVariablesSet:
        """Ensemble of variables to store."""
        # variables = self._get_inputs_for_new_ensemble(self._elements)
        all_non_features_map = map(self._get_loadable_required_vars, self._elements)
        variables = self._get_inputs_for_new_ensemble(
            list(set(itertools.chain(*all_non_features_map))),
        )
        return StoringVariablesSet(**variables)
