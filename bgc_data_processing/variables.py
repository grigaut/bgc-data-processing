import copy
from typing import Callable, Iterable, Iterator, Self

import numpy as np
from _collections_abc import dict_keys

from bgc_data_processing.exceptions import VariableInstantiationError


class Var:
    """Class to store Meta data on a variable of interest.

    Parameters
    ----------
    name : str
        'Official' name for the variable : name to use when displaying the variable.
    unit : str
        Variable unit (written using the following format :
        [deg_C] for Celsius degree of [kg] for kilograms).
    var_type : str
        Variable type (str, int, datetime...).
        It will be used to convert the data using df[variable].astype(type)
    load_nb : int, optional
        Number to sort the variable when loading the data.
        None implies that the varible will be remove from the dataframe, by default None
    save_nb : int, optional
        Number to sort the variable when saving the data.
        None implies that the varible will be remove from the dataframe, by default None
    name_format: str
        Format to use to save the data name and unit in a csv of txt file., by default "%-15s"
    value_format: str
        Format to use to save the data value in a csv of txt file., by default "%15s"

    Examples
    --------
    >>> var_lat = Var("LATITUDE", "[deg_N]", float, 7, 6, "%-12s", "%12.6f")
    """

    exist_in_dset: bool = None
    _correction: callable = None
    _has_correction: bool = False
    _remove_if_nan: bool = False
    _remove_if_all_nan: bool = False
    _aliases: list[tuple[str, str, list]] = []

    def __init__(
        self,
        name: str,
        unit: str,
        var_type: str,
        load_nb: int = None,
        save_nb: int = None,
        name_format: str = "%-15s",
        value_format: str = "%15s",
    ):

        self.name = name
        self.unit = unit
        self.type = var_type
        self.load_nb = load_nb
        self.save_nb = save_nb
        self.name_format = name_format
        self.value_format = value_format

    def __str__(self) -> str:
        return f"{self.name} - {self.unit} ({self.type})"

    def __repr__(self) -> str:
        txt = f"{self.name}_{self.unit}"
        return txt

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, Var):
            return repr(self) == repr(__o)
        else:
            return False

    @property
    def aliases(self) -> list[tuple[str, str, list]]:
        """Getter for aliases

        Returns
        -------
        list[tuple[str, str, list]]
            alias, flag column alias (None if not), values to keep from flag column (None if not)
        """
        return self._aliases

    @property
    def label(self) -> str:
        """Returns the label to use to find the variable data in a dataframe.

        Returns
        -------
        str
            label.
        """
        return self.name

    @property
    def here(self) -> bool:
        """Returns a boolean which indicates if the variable exists in the dataset.

        Returns
        -------
        bool
            True if the variable is in the dataset, False if not.
        """
        return self.exist_in_dset

    @here.setter
    def here(self, value: bool):
        self.exist_in_dset = value

    @property
    def remove_if_all_nan(self) -> bool:
        """Get the boolean indicating whether or not to suppress the row when multiple variables
        (this one included if True) are np.nan.

        Returns
        -------
        bool
            True if this variable must be included when removing where some variables are all nan.
        """
        return self._remove_if_all_nan

    @property
    def remove_if_nan(self) -> bool:
        """Get the boolean indicating whether or not to suppress the row when the variable is np.nan

        Returns
        -------
        bool
            True if rows must be removed when this variable is nan.
        """
        return self._remove_if_nan

    def in_file_as(self, *args: str) -> "Var":
        """Returns a Var object with same properties and the property 'alias' set up as 'name'
        which is the name of the variable in the file.

        Parameters
        ----------
        args : str
            Name(s) of the variable in the dataset.

        Returns
        -------
        Var
            Updated copy of self.
        """
        var = copy.deepcopy(self)
        var.here = True
        aliases = []
        for arg in args:
            if isinstance(arg, str):
                alias = arg
                flag_alias = None
                flag_value = None
            elif isinstance(arg, Iterable):
                if len(arg) == 1:
                    alias = arg[0]
                    flag_alias = None
                    flag_value = None
                elif len(arg) == 3:
                    alias = arg[0]
                    flag_alias = arg[1]
                    flag_value = arg[2]
                else:
                    raise ValueError(f"{arg} can't be of length {len(arg)}")
            else:
                raise ValueError(f"{arg} must be str or Iterable")
            aliases.append((alias, flag_alias, flag_value))
        var._aliases = aliases
        return var

    def not_in_file(self) -> "Var":
        """Returns a Var object with same properties and the property 'alias' set up as None
        as the variable does not exist in the file.

        Returns
        -------
        Var
            Updated copy of self.
        """
        var = copy.deepcopy(self)
        var.here = False
        return var

    def correct_with(self, function: Callable) -> Self:
        """Correction function definition.

        Parameters
        ----------
        function : Callable
            Function to apply to the dataframe row storing this variable's values.

        Returns
        -------
        Self
            self.

        Raises
        ------
        VariableInstantiationError
            If the given object is not callable.
        """
        if not isinstance(function, Callable):
            raise VariableInstantiationError("Correcting function must be callable.")
        self._correction = function
        self._has_correction = True
        return self

    def remove_when_all_nan(self) -> Self:
        """Sets self._remove_if_all_nan to True.

        Returns
        -------
        Self
            self
        """
        self._remove_if_all_nan = True
        return self

    def remove_when_nan(self) -> Self:
        """Sets self._remove_if_nan to True.

        Returns
        -------
        Self
            self
        """
        self._remove_if_nan = True
        return self


class VariablesStorer:
    """General storer for Var object to represent the set of both variables present in the file and
    variables to take in consideration (therefore to add even if empty) when loading the data.

    Parameters
    ----------
    *args: list
        Var objects to represent the variables stored by the object.
        It is better if these Var object have been instanciated using .not_here or .here_as methods.

    Raises
    ------
    ValueError:
        If multiplie var object have the same name.
    """

    def __init__(self, *args: Var) -> None:
        if len(args) != len(set(var.name for var in args)):
            raise ValueError(
                "To set multiple alias for the same variable, use Var.in_file_as([alias1, alias2])"
            )

        self._elements = list(args)

    def __getitem__(self, __k: str) -> Var:
        return self.mapper_by_name[__k]

    def __iter__(self) -> Iterator[Var]:
        return iter(self._elements)

    def __str__(self) -> str:
        txt = ""
        for var in self._elements:
            if var.here is None:
                here_txt = "not attributed"
            elif var.here:
                here_txt = var.aliases
            else:
                here_txt = "not in file"
            txt += str(var) + f": {here_txt}\n"
        return txt

    def __len__(self) -> int:
        return len(self._elements)

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, VariablesStorer):
            if len(self) != len(__o):
                return False
            elif set(self.mapper_by_name.keys()) != set(__o.mapper_by_name.keys()):
                return False
            else:
                repr_eq = [
                    repr(self[key]) == repr(__o[key])
                    for key in self.mapper_by_name.keys()
                ]
                return np.all(repr_eq)
        else:
            return False

    def add_var(self, var: Var) -> None:
        """Adds a new variable to self._elements.

        Parameters
        ----------
        var : Var
            Variable to add
        """
        if var.name in self.keys():
            raise ValueError("A variable already exists with his name")
        self._elements.append(var)

    def has_name(self, var_name: str) -> bool:
        """Checks if a variable name is the nam eof one of the variables.

        Parameters
        ----------
        var_name : str
            Name to test.

        Returns
        -------
        bool
            True if the name is in self.keys(), False otherwise.
        """
        return var_name in self.keys()

    def keys(self) -> dict_keys:
        """Keys to use when calling self[key].

        Returns
        -------
        dict_keys
            View of self.mapper_by_name keys.
        """
        return self.mapper_by_name.keys()

    @property
    def labels(self) -> dict[str, str]:
        """Returns a dicitonnary mapping variable names to variables labels

        Returns
        -------
        dict[str, str]
            name : label
        """
        return {var.name: var.label for var in self._elements}

    @property
    def mapper_by_name(self) -> dict[str, "Var"]:
        """Mapper between variables names and variables Var objects (for __getitem__ mostly).

        Returns
        -------
        dict[str, Var]
            Mapping between names (str) and variables (Var)
        """
        return {var.name: var for var in self._elements}

    @property
    def unit_mapping(self) -> dict[str, str]:
        """Mapper between variables names and variables units.
        Mostly used to create unit row.

        Returns
        -------
        dict[str, str]
            Mapping between names (str) and units (str).
        """
        return {var.name: var.unit for var in self._elements}

    @property
    def _save_vars(self) -> dict[int, Var]:
        """Sorting order to use when saving data.

        Returns
        -------
        list[str | tuple[str]]
            List of columns keys to pass as df[self.save_sort] to sort data.
        """
        return {var.save_nb: var for var in self._elements if var.save_nb is not None}

    @property
    def save_labels(self) -> list[str | tuple[str]]:
        """Sorting order to use when saving data.

        Returns
        -------
        list[str | tuple[str]]
            List of columns keys to pass as df[self.save_sort] to sort data.
        """
        return [self._save_vars[key].label for key in sorted(self._save_vars.keys())]

    @property
    def name_save_format(self) -> str:
        """String line to use as formatting for name and unit rows.

        Returns
        -------
        str
            Format string

        Examples
        --------
        >>> var_year = Var("YEAR", "[]", int, 0, 0,"%-4s", "%4d")
        >>> var_provider = Var("PROVIDER", "[]", str, 1, 1, "%-15s", "%15s")
        >>> storer = VariablesStorer(var_year, var_provider)
        >>> print(storer.name_save_format)
        "%-4s %-15s"
        >>> storer.name_save_format % tuple(storer.save_labels)
        "YEAR PROVIDER "
        """
        format_string = " ".join(
            [self._save_vars[key].name_format for key in sorted(self._save_vars.keys())]
        )
        return format_string

    @property
    def value_save_format(self) -> str:
        """String line to use as formatting for value rows.

        Returns
        -------
        str
            Format string"
        """
        format_string = " ".join(
            [
                self._save_vars[key].value_format
                for key in sorted(self._save_vars.keys())
            ]
        )
        return format_string

    @property
    def in_dset(self) -> list[Var]:
        """List of Var object supposedly present in the dataset.

        Returns
        -------
        list[Var]
            Var objects in the dataset.
        """
        return [var for var in self._elements if var.exist_in_dset]

    @property
    def corrections(self) -> dict[str, Callable]:
        """Mapping between variables keys and correcting functions

        Returns
        -------
        dict[str, Callable]
            Mapping.
        """
        return {
            var.label: var._correction for var in self._elements if var._has_correction
        }

    @property
    def to_remove_if_all_nan(self) -> list[str]:
        """Returns the list of keys to inspect when removing rows where all variables are np.nan.

        Returns
        -------
        list[str]
            List of keys to use.
        """
        return [var.label for var in self._elements if var.remove_if_all_nan]

    @property
    def to_remove_if_any_nan(self) -> list[str]:
        """Returns the list of keys to inspect when removing rows where any variable is np.nan.

        Returns
        -------
        list[str]
            List of keys to use.
        """
        return [var.label for var in self._elements if var.remove_if_nan]
