"""Parsing tools to determine date ranges."""

import datetime as dt
import shutil
import tomllib
from collections.abc import Callable
from copy import deepcopy
from functools import wraps
from pathlib import Path
from typing import Any, ClassVar

from bgc_data_processing.core.variables.vars import TemplateVar
from bgc_data_processing.exceptions import (
    ImpossibleTypeParsingError,
    InvalidParameterKeyError,
)
from bgc_data_processing.water_masses import WaterMass


class TomlParser:
    """Parsing class for config.toml.

    Parameters
    ----------
    filepath : Path | str
        Path to the config file.
    check_types : bool, optional
        Whether to check types or not., by default True
    """

    _str_to_type: ClassVar[dict[str, type | str]] = {
        "str": str,
        "int": int,
        "list": list,
        "tuple": tuple,
        "float": float,
        "bool": bool,
        "datetime64[ns]": "datetime64[ns]",
    }

    def __init__(self, filepath: Path | str, check_types: bool = True) -> None:
        self.filepath = Path(filepath)
        self._check = check_types
        with self.filepath.open("rb") as f:
            self._elements = tomllib.load(f)
        if check_types:
            self._parsed_types = self._parse_types(filepath=self.filepath)

    def _get(self, keys: list[str]) -> Any:
        """Return a variable from the toml using its path.

        Parameters
        ----------
        keys : list[str]
            List path to the variable: ["VAR1", "VAR2", "VAR3"]
            is the path to the variable VAR1.VAR2.VAR3 in the toml.

        Returns
        -------
        Any
            Variable.

        Raises
        ------
        KeyError
            If the path doesn't match the file's architecture
        """
        if keys[0] not in self._elements.keys():
            raise InvalidParameterKeyError(keys[:1], self.filepath)
        var = self._elements[keys[0]]
        for i in range(len(keys[1:])):
            key = keys[1:][i]
            if (not isinstance(var, dict)) or (key not in var.keys()):
                raise InvalidParameterKeyError(keys[: i + 2, self.filepath])
            var = var[key]
        return deepcopy(var)

    def _set(self, keys: list[str], value: Any) -> None:
        """Set the value of an element of the dictionnary.

        Parameters
        ----------
        keys : list[str]
            List path to the variable: ["VAR1", "VAR2", "VAR3"]
            is the path to the variable VAR1.VAR2.VAR3 in the toml.
        value : Any
            Value to set.

        Raises
        ------
        KeyError
            If the path doesn't match the file's architecture
        """
        if keys[0] not in self._elements.keys():
            raise InvalidParameterKeyError(keys[:1], self.filepath)
        if len(keys) > 1:
            var = self._elements[keys[0]]
            for i in range(len(keys[1:-1])):
                key = keys[1:][i]
                if (not isinstance(var, dict)) or (key not in var.keys()):
                    raise InvalidParameterKeyError(keys[: i + 2], self.filepath)
                var = var[key]
            var[keys[-1]] = value
        elif len(keys) == 1:
            self._elements[keys[0]] = value

    def _get_keys_types(
        self,
        line: str,
    ) -> tuple[list[str], list[type | tuple[type, type]]]:
        """Parse a type hinting line.

        Parameters
        ----------
        line : str
            Line from config file to parse.

        Returns
        -------
        tuple[list[str], list[type | tuple[type, type]]]
            List of keys: path to the variable,
            list of types/tuples: possible type for the variable.
        """
        # Remove comment part on the line
        str_keys, str_types = line.split(": ")[:2]
        str_types = str_types.replace(":", "")
        keys = str_keys.split(".")
        types_list = str_types.split(" | ")
        types = []
        for str_type in types_list:
            # Iterable type
            if "[" in str_type:
                splitted_type = str_type[:-1].split("[")
                final_type = tuple([self._str_to_type[x] for x in splitted_type])
            else:
                final_type = self._str_to_type[str_type]
            types.append(final_type)
        return keys, types

    def _parse_types(self, filepath: Path) -> dict:
        """Parse the variables types from the type-hinting rows in config.toml.

        Parameters
        ----------
        filepath : Path
            Path to the config.toml file.

        Returns
        -------
        dict
            Dictionnary with same structure as config dictionnary referring to types.
        """
        # reads config file
        with filepath.open() as file:
            lines = [line.strip() for line in file.readlines()]
        # Select only type hinting lines
        type_hints = [line[3:].replace("\n", "") for line in lines if line[:3] == "#? "]
        types_dict = {}
        for line in type_hints:
            keys, types = self._get_keys_types(line=line)
            dict_level = types_dict
            # Save type in a dictionnary with similar structure as config
            for key in keys[:-1]:
                if key not in dict_level.keys():
                    dict_level[key] = {}
                dict_level = dict_level[key]
            dict_level[keys[-1]] = tuple(types)
        return types_dict

    def _check_type(self, var: Any, var_type: type | tuple[type, type]) -> bool:
        """Check if the type of the variable correspond to the required type.

        Parameters
        ----------
        var : Any
            Variable to check type.
        var_type : type | tuple[type, type]
            Type for the variable, if tuple, means that the first value is an ierable
            and the second one the type of the values in the iterable.

        Returns
        -------
        bool
            True if the variable matches the type, False otherwise.
        """
        if isinstance(var_type, tuple):
            is_correct_iterator = isinstance(var, var_type[0])
            return is_correct_iterator and all(isinstance(x, var_type[1]) for x in var)
        return isinstance(var, var_type)

    def raise_if_wrong_type_below(
        self,
        keys: list[str],
    ) -> None:
        """Verify types for all variables 'below' keys level.

        Parameters
        ----------
        keys : list[str]
            'Root' level which to start checking types after
        """
        if not self._check:
            return
        if keys:
            var = self._get(keys)
            if not isinstance(var, dict):
                self.raise_if_wrong_type(keys)
            else:
                for key in var:
                    self.raise_if_wrong_type_below(keys=[*keys, key])
        elif not isinstance(self._elements, dict):
            error_msg = "Wrong type for toml object, should be a dictionnary"
            raise TypeError(error_msg)
        else:
            for key in self._elements:
                self.raise_if_wrong_type_below(keys=[*keys, key])

    def _get_type(self, keys: list[str]) -> list[type | tuple[type, type]]:
        """Return a variable from the toml using its path.

        Parameters
        ----------
        keys : list[str]
            List path to the variable: ["VAR1", "VAR2", "VAR3"]
            is the path to the variable VAR1.VAR2.VAR3 in the toml.

        Returns
        -------
        list[type | tuple[type, type]]
            Possible types for the variable.

        Raises
        ------
        KeyError
            If the type can't be found in the config file.
        """
        if keys[0] not in self._parsed_types.keys():
            raise ImpossibleTypeParsingError(keys[:1], self.filepath)
        var_type = self._parsed_types[keys[0]]
        for i in range(len(keys[1:])):
            key = keys[1:][i]
            if (not isinstance(var_type, dict)) or (key not in var_type.keys()):
                raise ImpossibleTypeParsingError(keys[: i + 2], self.filepath)
            var_type = var_type[key]
        return var_type

    def raise_if_wrong_type(
        self,
        keys: list[str],
    ) -> None:
        """Raise a TypeError if the variable type is none of the specified types.

        Parameters
        ----------
        keys : list[str]
            List path to the variable: ["VAR1", "VAR2", "VAR3"]
            is the path to the variable VAR1.VAR2.VAR3 in the toml.

        Raises
        ------
        TypeError
            If the variable doesn't match any of the required types.
        """
        var = self._get(keys)
        types = self._get_type(keys)
        # Check type:
        is_any_type = any(self._check_type(var, var_type) for var_type in types)
        if not is_any_type:
            type_msg = f"Type of {'.'.join(keys)} from {self.filepath} is incorrect."
            crop = lambda x: str(x).split("'")[1]
            iterables = [t for t in types if isinstance(t, tuple)]
            str_iter = [crop(t[0]) + "[" + crop(t[1]) + "]" for t in iterables]
            str_other = [crop(t) for t in types if not isinstance(t, tuple)]
            str_types = ", ".join(str_other + str_iter)
            correct_type_msg = f"Must be of one of these types: {str_types}."
            error_msg = f"{type_msg} {correct_type_msg}"
            raise TypeError(error_msg)


def directory_check(get_variable: Callable) -> Callable:
    """Use as decorator to create directories only when needed.

    Parameters
    ----------
    get_variable : Callable
        get of __getitem__ function.

    Returns
    -------
    Callable
        Wrapper function.

    Raises
    ------
    IsADirectoryError
        If the directory exists
    """

    @wraps(get_variable)
    def wrapper_func(self: "ConfigParser", keys: str | list[str]):
        keys_dirs = [keys] if isinstance(keys, str) else keys
        if (
            keys_dirs in self.dirs_vars_keys
            and not self._dir_created["-".join(keys_dirs)]
        ):
            directory = Path(get_variable(self, keys))
            if directory.is_dir():
                if [p for p in directory.glob("*.*") if p.name != ".gitignore"]:
                    if self.existing_dir_behavior == "raise":
                        error_msg = (
                            f"Directory {directory} already exists and is not empty."
                        )
                        raise IsADirectoryError(error_msg)
                    if self.existing_dir_behavior == "merge":
                        pass
                    elif self.existing_dir_behavior == "clean":
                        shutil.rmtree(directory)
                        directory.mkdir()
            else:
                directory.mkdir()
                gitignore = directory.joinpath(".gitignore")
                with gitignore.open("w") as file:
                    file.write("*")
            self._dir_created["-".join(keys_dirs)] = True
            return directory
        return get_variable(self, keys)

    return wrapper_func


class ConfigParser(TomlParser):
    """Class to parse toml config scripts.

    Parameters
    ----------
    filepath : Path | str
        Path to the file.
    check_types : bool, optional
        Whether to check types or not., by default True
    dates_vars_keys : list[str | list[str]], optional
        Keys to variable defining dates., by default []
    dirs_vars_keys : list[str | list[str]], optional
        Keys to variable defining directories., by default []
    existing_directory: str, optional
        Behavior for directory creation, 'raise' raises an error if the directory
        exists and is not empty, 'merge' will keep the directory as is but might replace
        its content when savong file and 'clean' will erase the directory if it exists.
    """

    def __init__(
        self,
        filepath: Path | str,
        check_types: bool = True,
        dates_vars_keys: list[str | list[str]] = [],
        dirs_vars_keys: list[str | list[str]] = [],
        existing_directory: str = "raise",
    ) -> None:
        super().__init__(filepath, check_types)
        self.dates_vars_keys = dates_vars_keys
        self.dirs_vars_keys: list[list[str]] = []
        self._parsed = False
        for var in dirs_vars_keys:
            if isinstance(var, list):
                self.dirs_vars_keys.append(var)
            elif isinstance(var, str):
                self.dirs_vars_keys.append([var])
            else:
                error_msg = f"Unsupported type for directory key {var}: {type(var)}."
                raise TypeError(error_msg)
        self.existing_dir_behavior = existing_directory
        self._dir_created = {
            "-".join(directory): False for directory in self.dirs_vars_keys
        }

    def parse(
        self,
    ) -> dict:
        """Parse the elements to verify types, convert dates and create directries.

        Returns
        -------
        dict
            Transformed dictionnary
        """
        if self._parsed:
            return
        self._parsed = True
        self.raise_if_wrong_type_below([])
        for keys in self.dates_vars_keys:
            all_keys = [keys] if isinstance(keys, str) else keys
            date = dt.datetime.strptime(self._get(all_keys), "%Y%m%d")
            self._set(all_keys, date)

    @directory_check
    def get(self, keys: list[str]) -> Any:
        """Get a variable by giving the list of keys to reach the variable.

        Parameters
        ----------
        keys : list[str]
            Keys to the variable.

        Returns
        -------
        Any
            The desired variable.
        """
        return super()._get(keys)

    @directory_check
    def __getitem__(self, __k: str) -> Any:
        """Return self._elements[__k].

        Parameters
        ----------
        __k : str
            Key

        Returns
        -------
        Any
            Value associated to __k.
        """
        self.parse()
        return self._elements[__k]

    def __repr__(self) -> str:
        """Represent the object as a string.

        Returns
        -------
        str
            self._elements.__repr__()
        """
        return self._elements.__repr__()


class DefaultTemplatesParser(TomlParser):
    """Parser for variables.toml to create Template Variables."""

    def to_list(self) -> list[TemplateVar]:
        """Return the variable ensemble as a list.

        Returns
        -------
        list[TemplateVar]
            LIst of all templates.
        """
        return list(self.variables.values())

    def __getitem__(self, __k: str) -> TemplateVar:
        """Return self.variables[__k].

        Parameters
        ----------
        __k : str
            Variable name as defined in variables.toml.

        Returns
        -------
        TemplateVar
            Template Variable associated to __k.
        """
        return self.variables[__k]

    def _make_template_from_args(self, var_args: dict[str, Any]) -> TemplateVar:
        """Make the TemplateVar from the parsed arguments.

        Parameters
        ----------
        var_args : dict[str, Any]
            Arguments to initialize the TemplateVar.

        Returns
        -------
        TemplateVar
            Template variable corresponding to the arguments.
        """
        return TemplateVar(
            name=var_args["NAME"],
            unit=var_args["UNIT"],
            var_type=self._str_to_type[var_args["TYPE"]],
            default=var_args["DEFAULT"],
            name_format=var_args["NAME_FORMAT"],
            value_format=var_args["VALUE_FORMAT"],
        )

    @property
    def variables(self) -> dict[str, TemplateVar]:
        """Return the dictionnary with all created variables.

        Returns
        -------
        dict[str, TemplateVar]
            Dictionnary mapping variables names to variables templates.
        """
        variables = {}
        for key in self._elements:
            value = self._elements.get(key)
            variables[key] = self._make_template_from_args(value)
        return variables


class WaterMassesParser(TomlParser):
    """Parser for water_masses.toml to create WaterMass objects."""

    @property
    def variables(self) -> dict[str, WaterMass]:
        """Return the dictionnary with all created WaterMass.

        Returns
        -------
        dict[str, WaterMass]
            Dictionnary mapping WaterMass acronyms to WaterMass.
        """
        variables = {}
        for key in self._elements:
            value = self._elements.get(key)
            variables[key] = self._make_water_mass_from_args(value)
        return variables

    def __getitem__(self, __k: str) -> WaterMass:
        """Return self.variables[__k].

        Parameters
        ----------
        __k : str
            WaterMass acronym as defined in water_masses.toml.

        Returns
        -------
        WaterMass
            WaterMass associated to __k.
        """
        return self.variables[__k]

    def _make_water_mass_from_args(self, var_args: dict[str, Any]) -> WaterMass:
        """Create WaterMass from the required parameters.

        Parameters
        ----------
        var_args : dict[str, Any]
            Dictionnary with all parameters to build a WaterMass.

        Returns
        -------
        WaterMass
            Resulting WaterMass.
        """
        ptemp_min = var_args["POTENTIAL_TEMPERATURE_MIN"]
        ptemp_max = var_args["POTENTIAL_TEMPERATURE_MAX"]
        salinity_min = var_args["SALINITY_MIN"]
        salinity_max = var_args["SALINITY_MAX"]
        sigma_t_min = var_args["SIGMAT_MIN"]
        sigma_t_max = var_args["SIGMAT_MAX"]
        return WaterMass(
            name=var_args["NAME"],
            acronym=var_args["ACRONYM"],
            ptemperature_range=(ptemp_min, ptemp_max),
            salinity_range=(salinity_min, salinity_max),
            sigma_t_range=(sigma_t_min, sigma_t_max),
        )
