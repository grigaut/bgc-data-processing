"""Parsing tools to determine date ranges"""
import datetime as dt
import os
import tomllib
from copy import deepcopy
from typing import Any, Type

import pandas as pd


class RanCycleParser:
    """ran_cycle files parser

    Parameters
    ----------
    filepath : str
        path to the file ot parse
    """

    def __init__(self, filepath: str) -> None:
        self.filepath = filepath

    @property
    def first_dates(self):
        """First date column of the file"""
        return self._get_first_date()

    def _get_first_date(self) -> pd.Series:
        """Reads cycle file and returns first columns with dates.

        Parameters
        ----------
        filepath : str
            Path to the cycle file.

        Returns
        -------
        pd.Series
            Dates with YYYYMMDD format.
        """
        df = pd.read_table(self.filepath, header=None, delim_whitespace=True)
        return df.loc[:, 2]

    def _make_daterange(
        self,
        dates_col: pd.Series,
        start: int,
        end: int,
    ) -> pd.DataFrame:
        """Computes daterange based on offset day numbers

        Parameters
        ----------
        dates_col : pd.Series
            Dates to use to make the dateranges
        start : int
            Number of days to consider before the given date to define start date
        end : int
            Number of days to consider after the given date to define end date

        Returns
        -------
        pd.DataFrame
            Dataframe with starting (start_dates) and ending (end_dates) dates of dateranges
        """
        dates_start = dates_col - pd.DateOffset(start)
        dates_start.name = "start_date"
        dates_end = dates_col + pd.DateOffset(end)
        dates_end.name = "end_date"
        return pd.concat([dates_start.dt.date, dates_end.dt.date], axis=1)

    def get_daterange(self, start: int, end: int) -> pd.DataFrame:
        """Parses ran_cycle files to define dateranges

        Parameters
        ----------
        start : int
            Number of days to consider before the given date to define start date
        end : int
            Number of days to consider after the given date to define end date

        Returns
        -------
        pd.DataFrame
            Dataframe with starting (start_dates) and ending (end_dates) dates of dateranges
        """
        initial_dates = pd.to_datetime(
            self.first_dates,
            format="%Y%m%d",
        )
        initial_dates.name = "dates"
        initial_dates.index.name = "cycle"
        drng = self._make_daterange(initial_dates, start, end)
        return drng


class ConfigParser:
    """Parsing class for config.toml

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
    }

    def __init__(self, filepath: str, check_types: bool = True) -> None:
        self.filepath = filepath
        self._check = check_types
        with open(filepath, "rb") as f:
            self._config = tomllib.load(f)
        if check_types:
            self._parsed_types = self._parse_types(filepath=filepath)

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
            List of keys: path to the variable, list of types/tuples: possible type for the variable.
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
        # reads config file
        with open(filepath, "r") as file:
            lines = [line.strip() for line in file.readlines()]
        # Select only type hinting lines
        type_hints = [line[3:].replace("\n", "") for line in lines if line[:3] == "## "]
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
        """Creates error message for TypeErrors

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
        wrong_type_msg = f"Variable {'.'.join(keys)} from {self.filepath} does not have the correct type."
        crop = lambda x: str(str(x).split("'")[1])
        iterables = [t for t in types if isinstance(t, tuple)]
        str_iter = [crop(t[0]) + "[" + crop(t[1]) + "]" for t in iterables]
        str_other = [crop(t) for t in types if not isinstance(t, tuple)]
        str_types = ", ".join(str_other + str_iter)
        correct_type_msg = f"Must be of one of these types: {str_types}."
        return f"{wrong_type_msg} {correct_type_msg}"

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
        if keys[0] not in self._config.keys():
            raise KeyError(
                f"Variable {'.'.join(keys[:1])} does not exist in {self.filepath}"
            )
        var = self._config[keys[0]]
        for i in range(len(keys[1:])):
            key = keys[1:][i]
            if (not isinstance(var, dict)) or (key not in var.keys()):
                raise KeyError(
                    f"Variable {'.'.join(keys[:i+2])} does not exist in {self.filepath}"
                )
            var = var[key]
        return deepcopy(var)

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
                raise KeyError(
                    f"Type of {'.'.join(keys[:i+2])} can't be parsed from {self.filepath}"
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

    @property
    def aggregation(self) -> dict:
        """Data-aggregation related part of the toml.

        Returns
        -------
        dict
            self._config["AGGREGATION"]
        """
        self.raise_if_wrong_type_below(["AGGREGATION"])
        return self.get(["AGGREGATION"])

    @property
    def mapping(self) -> dict:
        """Data-mapping related part of the toml.

        Returns
        -------
        dict
            self._config["MAPPING"] with converted date times
        """
        mapping = self.get(["MAPPING"])
        self.raise_if_wrong_type_below(["MAPPING"])
        mapping["DATE_MIN"] = dt.datetime.strptime(mapping["DATE_MIN"], "%Y%m%d")
        mapping["DATE_MAX"] = dt.datetime.strptime(mapping["DATE_MAX"], "%Y%m%d")
        return mapping

    @property
    def providers(self) -> dict:
        """Providers related part of the toml.

        Returns
        -------
        dict
            self._config["PROVIDERS"]
        """
        self.raise_if_wrong_type_below(["PROVIDERS"])
        return self.get(["PROVIDERS"])

    @property
    def utils(self):
        """'Utils'' part of the toml.

        Returns
        -------
        dict
            self._config["UTILS"]
        """
        self.raise_if_wrong_type_below(["UTILS"])
        saving_dir = self.get(["UTILS", "SAVING_DIR"])
        if not os.path.isdir(saving_dir):
            os.mkdir(saving_dir)
        return self.get(["UTILS"])
