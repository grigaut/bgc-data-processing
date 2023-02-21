"""Parsing tools to determine date ranges"""
import datetime as dt
import os
import tomllib
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


class TOMLParser:
    def __init__(self, filepath: str) -> None:
        self.filepath = filepath
        with open(filepath, "rb") as f:
            self.config = tomllib.load(f)

    def _check_type(self, var: Any, var_type: Type | tuple[Type, Type]) -> bool:
        if isinstance(var_type, tuple):
            is_correct_iterator = isinstance(var, var_type[0])
            is_all_correct = all(isinstance(x, var_type[1]) for x in var)
            return is_correct_iterator and is_all_correct
        else:
            return isinstance(var, var_type)

    def _make_error_msg(self, keys: list[str], types: list[Type]) -> str:
        wrong_type_msg = f"Variable {'.'.join(keys)} from {self.filepath} does not have the correct type."
        crop = lambda x: str(str(x).split("'")[1])
        iterables = [t for t in types if isinstance(t, tuple)]
        str_iter = [crop(t[0]) + "[" + crop(t[1]) + "]" for t in iterables]
        str_other = [crop(t) for t in types if not isinstance(t, tuple)]
        str_types = ", ".join(str_other + str_iter)
        correct_type_msg = f"Must be of one of these types: {str_types}."
        return f"{wrong_type_msg} {correct_type_msg}"

    def get(self, keys: list[str]) -> Any:
        if keys[0] not in self.config.keys():
            raise KeyError(
                f"Variable {'.'.join(keys[:1])} does not exist in {self.filepath}"
            )
        var = self.config[keys[0]]
        for i in range(len(keys[1:])):
            key = keys[1:][i]
            if (not isinstance(var, dict)) or (key not in var.keys()):
                raise KeyError(
                    f"Variable {'.'.join(keys[:i+2])} does not exist in {self.filepath}"
                )
            var = var[key]
        return var

    def raise_if_wrong_type(
        self,
        keys: list[str],
        var_type: Type | tuple[Type, Type],
        *args,
    ) -> None:
        var = self.get(keys)
        types = [var_type] + list(args)
        # Check type:
        is_any_type = any(self._check_type(var, var_type) for var_type in types)
        if not is_any_type:
            raise TypeError(self._make_error_msg(keys=keys, types=types))

    @property
    def aggregation(self):
        self.raise_if_wrong_type(["AGGREGATION", "YEARS"], (list, int))
        self.raise_if_wrong_type(["AGGREGATION", "PROVIDERS"], str, (list, str))
        self.raise_if_wrong_type(["AGGREGATION", "LIST_DIR"], str)
        return self.get(["AGGREGATION"])

    @property
    def mapping(self):
        mapping = self.get(["MAPPING"])
        self.raise_if_wrong_type(["MAPPING", "DATE_MIN"], str)
        self.raise_if_wrong_type(["MAPPING", "DATE_MAX"], str)
        self.raise_if_wrong_type(["MAPPING", "BINS_SIZE"], (list, float), (list, int))
        self.raise_if_wrong_type(["MAPPING", "PROVIDERS"], str, (list, str))
        self.raise_if_wrong_type(["MAPPING", "DEPTH_AGGREGATION"], str)
        self.raise_if_wrong_type(["MAPPING", "BIN_AGGREGATION"], str)
        mapping["DATE_MIN"] = dt.datetime.strptime(mapping["DATE_MIN"], "%Y%m%d")
        mapping["DATE_MAX"] = dt.datetime.strptime(mapping["DATE_MAX"], "%Y%m%d")
        return mapping

    @property
    def providers(self):
        for provider in self.config["PROVIDERS"]:
            self.raise_if_wrong_type(["PROVIDERS", provider, "PATH"], str)
            self.raise_if_wrong_type(["PROVIDERS", provider, "CATEGORY"], str)
            self.raise_if_wrong_type(["PROVIDERS", provider, "EXCLUDE"], (list, str))
        return self.get(["PROVIDERS"])

    @property
    def utils(self):
        self.raise_if_wrong_type(["UTILS", "VERBOSE"], int)
        self.raise_if_wrong_type(["UTILS", "SAVING_DIR"], str)
        saving_dir = self.get(["UTILS", "SAVING_DIR"])
        if not os.path.isdir(saving_dir):
            os.mkdir(saving_dir)
        return self.get(["UTILS"])
