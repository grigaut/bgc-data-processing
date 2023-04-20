"""Parsing tools to determine date ranges."""

import datetime as dt
import os
import shutil
from copy import deepcopy
from typing import Any, Callable, Type
from functools import wraps
import tomllib

from bgc_data_processing.variables import TemplateVar


class TomlParser:
    """Parsing class for config.toml.

    Parameters
    ----------
    filepath : str
        Path to the config file.
    check_types : bool, optional
        Whether to check types or not., by default True
    """

    _str_to_type = {
        "str": str,
        "int": int,
        "list": list,
        "tuple": tuple,
        "float": float,
        "bool": bool,
        "datetime64[ns]": "datetime64[ns]",
    }

    def __init__(self, filepath: str, check_types: bool = True) -> None:
        """Instanciate a parsing class for config.toml.

        Parameters
        ----------
        filepath : str
            Path to the config file.
        check_types : bool, optional
            Whether to check types or not., by default True
        """
        self.filepath = filepath
        self._check = check_types
        with open(filepath, "rb") as f:
            self._elements = tomllib.load(f)
        if check_types:
            self._parsed_types = self._parse_types(filepath=filepath)

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
            raise KeyError(
                f"Variable {'.'.join(keys[:1])} does not exist in {self.filepath}",
            )
        var = self._elements[keys[0]]
        for i in range(len(keys[1:])):
            key = keys[1:][i]
            if (not isinstance(var, dict)) or (key not in var.keys()):
                raise KeyError(
                    f"Variable {'.'.join(keys[:i+2])} doesn't exist in {self.filepath}",
                )
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
            raise KeyError(
                f"Variable {'.'.join(keys[:1])} does not exist in {self.filepath}",
            )
        if len(keys) > 1:
            var = self._elements[keys[0]]
            for i in range(len(keys[1:-1])):
                key = keys[1:][i]
                if (not isinstance(var, dict)) or (key not in var.keys()):
                    keys_str = ".".join(keys[: i + 2])
                    raise KeyError(
                        f"Variable {keys_str} does not exist in {self.filepath}",
                    )
                var = var[key]
            var[keys[-1]] = value
        elif len(keys) == 1:
            self._elements[keys[0]] = value

    def _get_keys_types(
        self,
        line: str,
    ) -> tuple[list[str], list[Type | tuple[Type, Type]]]:
        """Parse a type hinting line.

        Parameters
        ----------
        line : str
            Line from config file to parse.

        Returns
        -------
        tuple[list[str], list[Type | tuple[Type, Type]]]
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

    def _parse_types(self, filepath: str) -> dict:
        """Parse the variables types from the type-hinting rows in config.toml.

        Parameters
        ----------
        filepath : str
            Path to the config.toml file.

        Returns
        -------
        dict
            Dictionnary with same structure as config dictionnary referring to types.
        """
        # reads config file
        with open(filepath, "r") as file:
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

    def _check_type(self, var: Any, var_type: Type | tuple[Type, Type]) -> bool:
        """Check if the type of the variable correspond to the required type.

        Parameters
        ----------
        var : Any
            Variable to check type.
        var_type : Type | tuple[Type, Type]
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
        else:
            return isinstance(var, var_type)

    def _make_error_msg(self, keys: list[str], types: list[Type]) -> str:
        """Create error message for TypeErrors.

        Parameters
        ----------
        keys : list[str]
            List path to the variable: ["VAR1", "VAR2", "VAR3"]
            is the path to the variable VAR1.VAR2.VAR3 in the toml.
        types : list[Type]
            Correct types for the variable.

        Returns
        -------
        str
            Error message to pass to TypeError.
        """
        type_msg = f"Variable {'.'.join(keys)} from {self.filepath} has incorrect type."
        crop = lambda x: str(str(x).split("'")[1])
        iterables = [t for t in types if isinstance(t, tuple)]
        str_iter = [crop(t[0]) + "[" + crop(t[1]) + "]" for t in iterables]
        str_other = [crop(t) for t in types if not isinstance(t, tuple)]
        str_types = ", ".join(str_other + str_iter)
        correct_type_msg = f"Must be of one of these types: {str_types}."
        return f"{type_msg} {correct_type_msg}"

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
                for key in var.keys():
                    self.raise_if_wrong_type_below(keys=[*keys, key])
        elif not isinstance(self._elements, dict):
            raise TypeError("Wrong type for toml object, should be a dictionnary")
        else:
            for key in self._elements.keys():
                self.raise_if_wrong_type_below(keys=[*keys, key])

    def _get_type(self, keys: list[str]) -> list[Type | tuple[Type, Type]]:
        """Return a variable from the toml using its path.

        Parameters
        ----------
        keys : list[str]
            List path to the variable: ["VAR1", "VAR2", "VAR3"]
            is the path to the variable VAR1.VAR2.VAR3 in the toml.

        Returns
        -------
        list[Type | tuple[Type, Type]]
            Possible types for the variable.

        Raises
        ------
        KeyError
            If the type can't be found in the config file.
        """
        if keys[0] not in self._parsed_types.keys():
            raise KeyError(
                f"Type of {'.'.join(keys[:1])} can't be parsed from {self.filepath}",
            )
        var_type = self._parsed_types[keys[0]]
        for i in range(len(keys[1:])):
            key = keys[1:][i]
            if (not isinstance(var_type, dict)) or (key not in var_type.keys()):
                keys_str = ".".join(keys[: i + 2])
                raise KeyError(
                    f"Type of {keys_str} can't be parsed from {self.filepath}",
                )
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
            raise TypeError(self._make_error_msg(keys=keys, types=types))


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
        if isinstance(keys, str):
            keys_dirs = [keys]
        else:
            keys_dirs = keys
        if (
            keys_dirs in self.dirs_vars_keys
            and not self._dir_created["-".join(keys_dirs)]
        ):
            directory = get_variable(self, keys)
            if os.path.isdir(directory):
                if os.listdir(directory):
                    if self.existing_dir_behavior == "raise":
                        raise IsADirectoryError(
                            f"Directory {directory} already exists and is not empty.",
                        )
                    elif self.existing_dir_behavior == "merge":
                        pass
                    elif self.existing_dir_behavior == "clean":
                        shutil.rmtree(directory)
                        os.mkdir(directory)
            else:
                os.mkdir(directory)
            self._dir_created["-".join(keys_dirs)] = True
            return directory
        else:
            return get_variable(self, keys)

    return wrapper_func


class ConfigParser(TomlParser):
    """Class to parse toml config scripts.

    Parameters
    ----------
    filepath : str
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
        filepath: str,
        check_types: bool = True,
        dates_vars_keys: list[str | list[str]] = [],
        dirs_vars_keys: list[str | list[str]] = [],
        existing_directory: str = "raise",
    ) -> None:
        """Class to parse toml config scripts.

        Parameters
        ----------
        filepath : str
            Path to the file.
        check_types : bool, optional
            Whether to check types or not., by default True
        dates_vars_keys : list[str | list[str]], optional
            Keys to variable defining dates., by default []
        dirs_vars_keys : list[str | list[str]], optional
            Keys to variable defining directories., by default []
        existing_directory: str, optional
            Behavior for directory creation, 'raise' raises an error if the directory
            exists and is not empty, 'merge' will keep the directory as is
            but might replace its content when savong file and 'clean'
            will erase the directory if it exists.
        """
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
                raise TypeError(f"Unsupported type for directpory key {var}")
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
        else:
            self._parsed = True
        self.raise_if_wrong_type_below([])
        for keys in self.dates_vars_keys:
            if isinstance(keys, str):
                all_keys = [keys]
            else:
                all_keys = keys
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
        template = TemplateVar(
            name=var_args["NAME"],
            unit=var_args["UNIT"],
            var_type=self._str_to_type[var_args["TYPE"]],
            default=var_args["DEFAULT"],
            name_format=var_args["NAME_FORMAT"],
            value_format=var_args["VALUE_FORMAT"],
        )
        return template

    @property
    def variables(self) -> dict[str, TemplateVar]:
        """Return the dictionnary with all created variables.

        Returns
        -------
        dict[str, TemplateVar]
            Dictionnary mapping variables names to variables templates.
        """
        variables = {}
        for key in self._elements.keys():
            value = self._elements.get(key)
            variables[key] = self._make_template_from_args(value)
        return variables
