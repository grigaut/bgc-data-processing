"""Parsing tools to determine date ranges."""

import datetime as dt
import os
from copy import deepcopy
from typing import Any, Type

import tomllib

from bgc_data_processing.variables import TemplateVar


class TomlParser:
    """Parsing class for config.toml.

    Parameters
    ----------
    filepath : str
        Path to the config file.
    """

    _str_to_type = {
        "str": str,
        "int": int,
        "list": list,
        "tuple": tuple,
        "float": float,
        "datetime64[ns]": "datetime64[ns]",
    }

    def __init__(self, filepath: str, check_types: bool = True) -> None:
        self.filepath = filepath
        self._check = check_types
        with open(filepath, "rb") as f:
            self._elements = tomllib.load(f)
        if check_types:
            self._parsed_types = self._parse_types(filepath=filepath)

    def get(self, keys: list[str]) -> Any:
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
                f"Variable {'.'.join(keys[:1])} does not exist in {self.filepath}"
            )
        var = self._elements[keys[0]]
        for i in range(len(keys[1:])):
            key = keys[1:][i]
            if (not isinstance(var, dict)) or (key not in var.keys()):
                raise KeyError(
                    f"Variable {'.'.join(keys[:i+2])} does not exist in {self.filepath}"
                )
            var = var[key]
        return deepcopy(var)

    def _get_keys_types(
        self,
        line: str,
    ) -> tuple[list[str], list[Type | tuple[Type, Type]]]:
        """Parses a type hinting line.

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
                str_type = str_type[:-1].split("[")
                str_type = tuple([self._str_to_type[x] for x in str_type])
            else:
                str_type = self._str_to_type[str_type]
            types.append(str_type)
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
        """Checks if the type of the variable correspond to the required type.

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
        """Creates error message for TypeErrors.

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
        """Verifies types for all variables 'below' keys level.

        Parameters
        ----------
        keys : list[str]
            'Root' level which to start checking types after
        """
        var = self.get(keys)
        if not self._check:
            return
        if not isinstance(var, dict):
            self.raise_if_wrong_type(keys)
        else:
            for key in var.keys():
                self.raise_if_wrong_type_below(keys=keys + [key])

    def get_type(self, keys: list[str]) -> list[Type | tuple[Type, Type]]:
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
                f"Type of {'.'.join(keys[:1])} can't be parsed from {self.filepath}"
            )
        var_type = self._parsed_types[keys[0]]
        for i in range(len(keys[1:])):
            key = keys[1:][i]
            if (not isinstance(var_type, dict)) or (key not in var_type.keys()):
                keys_str = ".".join(keys[: i + 2])
                raise KeyError(
                    f"Type of {keys_str} can't be parsed from {self.filepath}"
                )
            var_type = var_type[key]
        return var_type

    def raise_if_wrong_type(
        self,
        keys: list[str],
    ) -> None:
        """Raises a TypeError if the variable type is none of the specified types.

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
        var = self.get(keys)
        types = self.get_type(keys)
        # Check type:
        is_any_type = any(self._check_type(var, var_type) for var_type in types)
        if not is_any_type:
            raise TypeError(self._make_error_msg(keys=keys, types=types))


class ConfigParser(TomlParser):
    """Parser for config.toml to read config parameters."""

    @property
    def aggregation(self) -> dict:
        """Data-aggregation related part of the toml.

        Returns
        -------
        dict
            self._elements["AGGREGATION"]
        """
        aggregation = self.get(["AGGREGATION"])
        self.raise_if_wrong_type_below(["AGGREGATION"])
        aggregation["DATE_MIN"] = dt.datetime.strptime(
            aggregation["DATE_MIN"],
            "%Y%m%d",
        )
        aggregation["DATE_MAX"] = dt.datetime.strptime(
            aggregation["DATE_MAX"],
            "%Y%m%d",
        )
        saving_dir = self.get(["AGGREGATION", "SAVING_DIR"])
        if not os.path.isdir(saving_dir):
            os.mkdir(saving_dir)
        return aggregation

    @property
    def mapping(self) -> dict:
        """Data-mapping related part of the toml.

        Returns
        -------
        dict
            self._elements["MAPPING"] with converted date times
        """
        mapping = self.get(["MAPPING"])
        self.raise_if_wrong_type_below(["MAPPING"])
        mapping["DATE_MIN"] = dt.datetime.strptime(mapping["DATE_MIN"], "%Y%m%d")
        mapping["DATE_MAX"] = dt.datetime.strptime(mapping["DATE_MAX"], "%Y%m%d")
        saving_dir = self.get(["MAPPING", "SAVING_DIR"])
        if not os.path.isdir(saving_dir):
            os.mkdir(saving_dir)
        return mapping

    @property
    def providers(self) -> dict:
        """Providers related part of the toml.

        Returns
        -------
        dict
            self._elements["PROVIDERS"]
        """
        self.raise_if_wrong_type_below(["PROVIDERS"])
        return self.get(["PROVIDERS"])

    @property
    def utils(self) -> dict:
        """'utils'' part of the toml.

        Returns
        -------
        dict
            self._elements["UTILS"]
        """
        self.raise_if_wrong_type_below(["UTILS"])
        return self.get(["UTILS"])


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
