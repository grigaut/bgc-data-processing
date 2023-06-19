"""Filenames Patterns building."""

import datetime as dt
import itertools
import re
from collections.abc import Callable
from pathlib import Path


class FileNamePattern:
    """Create the pattern to use to select filenames.

    Parameters
    ----------
    str_pattern : str
        Raw string pattern, with field to infer written in brackets ('{'&'}').
    year_field : str, optional
        Name of the field supposed to contain the year informations.
        , by default "years"
    month_field : str, optional
        Name of the field supposed to contain the month informations.
        , by default "months"
    day_field : str, optional
        Name of the field supposed to contain the day informations.
        , by default "days"
    """

    def __init__(
        self,
        str_pattern: str,
        year_field: str = "years",
        month_field: str = "months",
        day_field: str = "days",
    ) -> None:

        self._base = str_pattern
        self._year = year_field
        self._month = month_field
        self._day = day_field

    def build_from_constraint(self, date_constraint: dict) -> "PatternMatcher":
        """Build the pattern from date constraints.

        Parameters
        ----------
        date_constraint : dict
            Date constraint.

        Returns
        -------
        str
            Final pattern.
        """
        date_min, date_max = self._parse_dates_from_constraints(date_constraint)
        return self.build(date_min=date_min, date_max=date_max)

    def build(self, date_min: dt.date, date_max: dt.date) -> "PatternMatcher":
        """Build the pattern from the starting and ending dates.

        Parameters
        ----------
        date_min : dt.date
            Starting date.
        date_max : dt.date
            Ending date.

        Returns
        -------
        str
            Final pattern.
        """
        interval_patterns = self._slice(date_min=date_min, date_max=date_max)
        pattern = "|".join(map(self._create_pattern, interval_patterns))
        return PatternMatcher(pattern=pattern)

    def _parse_dates_from_constraints(
        self,
        date_constraint: dict,
    ) -> tuple[dt.date | None, dt.date | None]:
        """Parse starting and ending dates from a date constraint.

        Parameters
        ----------
        date_constraint : dict
            Date constraint,

        Returns
        -------
        tuple[dt.date | None, dt.date | None]
            Starting and ending dates. None if no constraints.

        Raises
        ------
        KeyError
            If the date constraint is invalid.
        """
        if not date_constraint:
            return (None, None)
        boundary_in = "boundary" in date_constraint
        superset_in = "superset" in date_constraint
        if boundary_in and superset_in and date_constraint["superset"]:
            b_min = date_constraint["boundary"]["min"]
            b_max = date_constraint["boundary"]["max"]
            s_min = min(date_constraint["superset"])
            s_max = max(date_constraint["superset"])
            min_date = min(b_min, s_min).date()
            max_date = max(b_max, s_max).date()
            return (min_date, max_date)
        if superset_in:
            superset_constraint = date_constraint["superset"]
            min_date = min(superset_constraint).date()
            max_date = max(superset_constraint).date()
            return (min_date, max_date)
        if boundary_in:
            boundary_constraint = date_constraint["boundary"]
            min_date = boundary_constraint["min"].date()
            max_date = boundary_constraint["max"].date()
            return (min_date, max_date)
        raise KeyError("Date constraint dictionnary has invalid keys")

    def _slice(
        self,
        date_min: dt.date,
        date_max: dt.date,
    ) -> list["DateIntervalPattern"]:
        """Slice the date interval in smaller interval patterns..

        Returns
        -------
        list[DateIntervalPattern, DateIntervalPattern]
            List of all interval patterns.
        """
        years_eq = date_min.year == date_max.year
        months_eq = date_min.month == date_max.month

        if years_eq and months_eq:
            return self._slice_same_year_month(date_min, date_max)
        if years_eq:
            return self._slice_same_year(date_min, date_max)
        return self._slice_all_differents(date_min, date_max)

    def _slice_all_differents(
        self,
        date_min: dt.date,
        date_max: dt.date,
    ) -> list["DateIntervalPattern"]:
        """Slice the date interval if the boundaries don't have anything in common.

        Parameters
        ----------
        date_min : dt.date
            Starting date.
        date_max : dt.date
            Ending date.

        Returns
        -------
        list[DateIntervalPattern]
            List of all interval patterns.
        """
        # Since this is can be abstract, an example is provided as commented values.
        # The example considers date_min = 2020-02-05 and date_max = 2023-03-30
        # start = 2020-02-05
        start = date_min
        # end = 2023-03-30
        end = date_max
        # end_1st_month = 2020-02-29
        end_1st_month = dt.date(
            year=start.year,
            month=start.month + 1,
            day=1,
        ) - dt.timedelta(days=1)
        # start_2nd_month = 2020-03-01
        start_2nd_month = dt.date(year=start.year, month=start.month + 1, day=1)
        # end_first_year = 2020-12-31
        end_first_year = dt.date(year=start.year, month=12, day=31)
        # start_2nd_year = 2021-01-01
        start_2nd_year = dt.date(year=start.year + 1, month=1, day=1)
        # end_penultimate_year = 2022-12-31
        end_penultimate_year = dt.date(year=end.year - 1, month=12, day=31)
        # start_last_year = 2023-01-01
        start_last_year = dt.date(year=end.year, month=1, day=1)
        # end_penultimate_month = 2023-02-28
        end_penultimate_month = dt.date(
            year=end.year,
            month=end.month,
            day=1,
        ) - dt.timedelta(days=1)
        # start_last_month = 2023-03-01
        start_last_month = dt.date(year=end.year, month=end.month, day=1)
        return [
            # Interval between 2020-02-05 and 2020-02-29 -> every day in this interval
            DateIntervalPattern.with_day_precision(start, end_1st_month),
            # Interval between 2020-03-01 and 2020-12-31 -> every month in this interval
            DateIntervalPattern.with_month_precision(start_2nd_month, end_first_year),
            # Interval between 2021-01-01 and 2022-12-31 -> every year in this interval
            DateIntervalPattern.with_year_precision(
                start_2nd_year,
                end_penultimate_year,
            ),
            # Interval between 2023-01-01 and 2023-02-28 -> every month in this interval
            DateIntervalPattern.with_month_precision(
                start_last_year,
                end_penultimate_month,
            ),
            # Interval between 2023-03-01 and 2023-03-30 -> every day in this interval
            DateIntervalPattern.with_day_precision(start_last_month, end),
        ]

    def _slice_same_year(
        self,
        date_min: dt.date,
        date_max: dt.date,
    ) -> list["DateIntervalPattern"]:
        """Slice the date interval if the boundaries are in the same year.

        Parameters
        ----------
        date_min : dt.date
            Starting date.
        date_max : dt.date
            Ending date.

        Returns
        -------
        list[DateIntervalPattern]
            List of all interval patterns.
        """
        # Since this is can be abstract, an example is provided as commented values.
        # The example considers date_min = 2020-02-05 and date_max = 2020-08-27
        # start = 2020-02-05
        start = date_min
        # end = 2020-08-27
        end = date_max
        # end_first_month = 2020-02-29
        end_first_month = dt.date(
            year=start.year,
            month=start.month + 1,
            day=1,
        ) - dt.timedelta(days=1)
        # start_second_month = 2020-03-01
        start_second_month = dt.date(
            year=start.year,
            month=start.month + 1,
            day=1,
        )
        # end_penultimate_month = 2020-07-31
        end_penultimate_month = dt.date(
            year=end.year,
            month=end.month,
            day=1,
        ) - dt.timedelta(
            days=1,
        )
        # start_last_month = 2020-08-01
        start_last_month = dt.date(year=end.year, month=end.month, day=1)
        return [
            # Interval between 2020-02-05 and 2020-02-29 -> every day in this interval
            DateIntervalPattern.with_day_precision(start, end_first_month),
            # Interval between 2020-03-01 and 2020-07-31 -> every month in this interval
            DateIntervalPattern.with_month_precision(
                start_second_month,
                end_penultimate_month,
            ),
            # Interval between 2020-08-01 and 2020-08-27 -> every year in this interval
            DateIntervalPattern.with_day_precision(start_last_month, end),
        ]

    def _slice_same_year_month(
        self,
        date_min: dt.date,
        date_max: dt.date,
    ) -> list["DateIntervalPattern"]:
        """Slice the date interval if the boundaries have same year and month.

        Parameters
        ----------
        date_min : dt.date
            Starting date.
        date_max : dt.date
            Ending date.

        Returns
        -------
        list[DateIntervalPattern]
            List of all interval patterns.
        """
        return [DateIntervalPattern.with_day_precision(date_min, date_max)]

    def _create_pattern(self, interval_pattern: "DateIntervalPattern") -> str:
        """Create the pattern for a given  interval.

        Parameters
        ----------
        interval_pattern : DateIntervalPattern
            Interval to use as reference for the pattern.

        Returns
        -------
        str
            Pattern for this interval.
        """
        format_kwargs = {
            self._year: interval_pattern.years,
            self._month: interval_pattern.months,
            self._day: interval_pattern.days,
        }
        format_base = self._base.format(**format_kwargs)
        return f"({format_base})"


class DateIntervalPattern:
    """Create the patterns values for a given date interval.

    Parameters
    ----------
    date_min : dt.date | None
        Starting date of the interval.
    date_max : dt.date | None
        Ending date of the interval.
    precision : str, optional
        Precision of the interval.
        A "day" precision means that year and month are constant,
        therefore the required days are contained between the minimum day number
        and the maximum day number.
        A "month" precision means that year is constant but months are different
        but totally included (from first day to last day.) in the interval.,
        therefore the required months are contained between the minimum months
        number and the maximum months number.
        A "year" precision means the years to include are different
        but totally included (from first day to last day.) in the interval,
        therefore the required years are contained between the minimum year number
        and the maximum year number., by default "day"
    """

    _year_precision_label = "year"
    _month_precision_label = "month"
    _day_precision_label = "day"

    def __init__(
        self,
        date_min: dt.date | None,
        date_max: dt.date | None,
        precision: str = "day",
    ) -> None:
        if not (date_min is None and date_max is None):
            self._validate_inputs(
                date_min=date_min,
                date_max=date_max,
                precision=precision,
            )

        self._precision = precision
        self._min = date_min
        self._max = date_max

    @property
    def years(self) -> str:
        """'year' part of the pattern."""
        if self._min is None and self._max is None:
            return "[0-9][0-9][0-9][0-9]"
        if self._precision == self._year_precision_label:
            min_ = self._min.year
            max_ = self._max.year
            possible_values = "|".join([str(i) for i in range(min_, max_ + 1)])
            return f"({possible_values})"
        return str(self._min.year)

    @property
    def months(self) -> str:
        """'month' part of the pattern."""
        if self._min is None and self._max is None:
            return "[0-1][0-9]"
        if self._precision == self._year_precision_label:
            return "[0-1][0-9]"
        if self._precision == self._month_precision_label:
            min_ = self._min.month
            max_ = self._max.month
            possible_values = "|".join([str(i).zfill(2) for i in range(min_, max_ + 1)])
            return f"({possible_values})"
        return str(self._min.month).zfill(2)

    @property
    def days(self) -> str:
        """'day' part of the pattern."""
        if self._min is None and self._max is None:
            return "[0-1][0-9]"
        if self._precision == self._day_precision_label:
            min_ = self._min.day
            max_ = self._max.day
            possible_values = "|".join([str(i).zfill(2) for i in range(min_, max_ + 1)])
            return f"({possible_values})"
        return "[0-3][0-9]"

    def __repr__(self) -> str:
        """Object representation string.

        Returns
        -------
        str
            Starting date - Ending date ; precision: interval precision.
        """
        return f"{self._min} - {self._max} ; precision: {self._precision}"

    def _validate_inputs(
        self,
        date_min: dt.date,
        date_max: dt.date,
        precision: str,
    ) -> None:
        """Validate the inputs.

        Parameters
        ----------
        date_min : dt.date
            Starting date.
        date_max : dt.date
            Ending date.
        precision : str
            Precision.

        Raises
        ------
        ValueError
            If date_min is None.
        ValueError
            If date_max is None.
        ValueError
            If date_min > date_max.
        ValueError
            If precision is not valid.
        ValueError
            If Month precision is incoherent with given dates.
        ValueError
            If Day precision incoherent with given dates.
        """
        possible_precisions = [
            self._year_precision_label,
            self._month_precision_label,
            self._day_precision_label,
        ]
        if date_min is None:
            raise ValueError("date_min can't be None is date_max isn't.")
        if date_max is None:
            raise ValueError("date_max can't be None is date_min isn't.")
        if date_min > date_max:
            raise ValueError("date_min must be lower than date_max.")
        if precision not in possible_precisions:
            raise ValueError(f"{precision} must be one of {possible_precisions}")
        same_year = date_min.year == date_max.year
        same_month = same_year and date_min.month == date_max.month
        if precision == self._month_precision_label and not same_year:
            raise ValueError(f"'{precision}' only concerns dates in the same year.")
        if precision == self._day_precision_label and not same_month:
            raise ValueError(f"'{precision}' only concerns dates in the same month.")

    @classmethod
    def with_day_precision(
        cls,
        date_min: dt.date,
        date_max: dt.date,
    ) -> "DateIntervalPattern":
        """Create a DateIntervalPattern with day precision.

        Parameters
        ----------
        date_min : dt.date
            Starting date.
        date_max : dt.date
            Ending date.

        Returns
        -------
        DateIntervalPattern
            Date interval pattern.
        """
        return cls(
            date_min=date_min,
            date_max=date_max,
            precision=cls._day_precision_label,
        )

    @classmethod
    def with_month_precision(
        cls,
        date_min: dt.date,
        date_max: dt.date,
    ) -> "DateIntervalPattern":
        """Create a DateIntervalPattern with month precision.

        Parameters
        ----------
        date_min : dt.date
            Starting date.
        date_max : dt.date
            Ending date.

        Returns
        -------
        DateIntervalPattern
            Date interval pattern.
        """
        return cls(
            date_min=date_min,
            date_max=date_max,
            precision=cls._month_precision_label,
        )

    @classmethod
    def with_year_precision(
        cls,
        date_min: dt.date,
        date_max: dt.date,
    ) -> "DateIntervalPattern":
        """Create a DateIntervalPattern with year precision.

        Parameters
        ----------
        date_min : dt.date
            Starting date.
        date_max : dt.date
            Ending date.

        Returns
        -------
        DateIntervalPattern
            Date interval pattern.
        """
        return cls(
            date_min=date_min,
            date_max=date_max,
            precision=cls._year_precision_label,
        )


class PatternMatcher:
    """Matcher to find files which match agiven pattern.

    Parameters
    ----------
    pattern : str
        Pattern to match.
    validation_function : Callable, optional
        Function to use to validate that files
        are to be loaded., by default lambdafilepath
    """

    def __init__(
        self,
        pattern: str,
        validation_function: Callable = lambda filepath, exclude: True,  # noqa: ARG005
    ) -> None:

        self._pattern = pattern
        self.validate = validation_function

    @property
    def validate(self) -> Callable:
        """Validation function."""
        return self._validation_function

    @validate.setter
    def validate(self, validation_function: Callable) -> None:
        if not isinstance(validation_function, Callable):
            raise ValueError("The validation function must be callable.")
        self._validation_function = validation_function

    def select_matching_filepath(
        self,
        research_directory: Path,
        exclude: list[str] = [],
    ) -> list[Path]:
        """Select the filepaths matching the pattern.

        Parameters
        ----------
        research_directory : Path
            Directory to serach for files.
        exclude : list[str], optional
            Filenames to exclude., by default []

        Returns
        -------
        list[Path]
            List of correct paths.
        """
        return self._recursive_match(
            research_dir=research_directory,
            pattern=self._pattern,
            exclude=exclude,
        )

    def _recursive_match(
        self,
        research_dir: Path,
        pattern: str,
        exclude: list[str],
    ) -> list[Path]:
        """Find matching filepaths using recursion.

        Parameters
        ----------
        research_dir : Path
            Directory to search for files.
        pattern : str
            Pattern to use when searching.
        exclude : list[str]
            Files to exclude.

        Returns
        -------
        list[Path]
            List of correct files.
        """
        if "/" not in pattern:
            return self._match_files(
                research_dir=research_dir,
                pattern=pattern,
                exclude=exclude,
            )
        return self._match_folder(
            research_dir=research_dir,
            pattern=pattern,
            exclude=exclude,
        )

    def _match_files(
        self,
        research_dir: Path,
        pattern: str,
        exclude: list[str],
    ) -> list[Path]:
        """Find matching filenames.

        Parameters
        ----------
        research_dir : Path
            Directory to search for filenames.
        pattern : str
            Pattern to use.
        exclude : list[str]
            Filenames to exclude.

        Returns
        -------
        list[Path]
            List of correct files.
        """
        regex = re.compile(pattern)
        files = filter(regex.match, [x.name for x in research_dir.glob("*.*")])
        fulls_paths = map(research_dir.joinpath, files)

        def valid(filepath: Path) -> bool:
            return self.validate(filepath=filepath, exclude=exclude)

        return sorted(filter(valid, fulls_paths))

    def _match_folder(
        self,
        research_dir: Path,
        pattern: str,
        exclude: list[str],
    ) -> list[Path]:
        """Find matching folder names.

        Parameters
        ----------
        research_dir : Path
            Directory to search for filenames.
        pattern : str
            Pattern to use.
        exclude : list[str]
            Filenames to exclude.

        Returns
        -------
        list[Path]
            List of correct files.
        """
        # recursion: Search pattern on folder names
        all_patterns = pattern[1:-1].split(")|(")
        # Collect all folder-related-parts of the pattern
        folder_split = [pat.split("/")[0] for pat in all_patterns]
        folder_pattern = f"({')|('.join(folder_split)})"
        # Collect all remaining parts of the pattern
        remaining_split = ["/".join(pat.split("/")[1:]) for pat in all_patterns]
        files_pattern = f"({')|('.join(remaining_split)})"

        # Compile folder regex
        folder_regex = re.compile(folder_pattern)
        matches = filter(folder_regex.match, [x.name for x in research_dir.glob("*")])

        # Prepare next recursive call
        def recursive_call(folder: str) -> list[Path]:
            return self._recursive_match(
                research_dir=research_dir.joinpath(folder),
                pattern=files_pattern,
                exclude=exclude,
            )

        # apply recursive function to selected folders
        recursion_results = map(recursive_call, matches)
        # return list of all results
        return list(itertools.chain(*recursion_results))
