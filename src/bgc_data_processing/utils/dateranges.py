"""Date range generating objects."""


import datetime as dt

import pandas as pd


class DateRangeGenerator:
    """Generate date ranges.

    Parameters
    ----------
    start : dt.datetime
        Starting date of the range.
    end : dt.datetime
        Ending date of the range.
    interval : str
        Type of interval, 'day', 'week', 'month', 'year' or 'custom'.
    interval_length : int, optional
        Length of custom interval, in days., by default 1
    """

    freqs = {
        "day": "D",
        "week": "W",
        "month": "M",
        "year": "Y",
    }
    start_column_name: str = "start_date"
    end_column_name: str = "end_date"

    def __init__(
        self,
        start: dt.datetime,
        end: dt.datetime,
        interval: str,
        interval_length: int = 1,
    ) -> None:
        """Generate date ranges.

        Parameters
        ----------
        start : dt.datetime
            Starting date of the range.
        end : dt.datetime
            Ending date of the range.
        interval : str
            Type of interval, 'day', 'week', 'month', 'year' or 'custom'.
        interval_length : int, optional
            Length of custom interval, in days., by default 1
        """
        self.start = pd.to_datetime(start).normalize()
        self.end = pd.to_datetime(end).normalize()
        self.interval = interval
        self.interval_length = interval_length

    def __call__(self) -> "DateRange":
        """Load the date ranges.

        Returns
        -------
        pd.DataFrame
            Range DataFrame with self.start_column_name and \
            self.end_column_name columns. Both start and end dates \
            are supposed to be included in the final range.
        """
        if self.interval == "custom":
            return self._make_custom_range()
        return self._make_range()

    def _make_custom_range(self) -> pd.DataFrame:
        """Create the range DataFrame for custom date intervals.

        Returns
        -------
        pd.DataFrame
            Range DataFrame with self.start_column_name and \
            self.end_column_name columns. Both start and end dates \
            are supposed to be included in the final range.
        """
        # Create the date range
        date_range = pd.date_range(
            start=self.start,
            end=self.end,
            freq=f"{self.interval_length}{self.freqs['day']}",
            inclusive="both",
            normalize=True,
        )
        dates: pd.Series = date_range.to_series().reset_index(drop=True)
        # Use as start dates
        starts = dates
        # Create end date by shifting by 1 day to get previous day
        ends = dates.shift(-1) - pd.to_timedelta("1 day")
        # Add final date.
        ends.loc[ends.index[-1]] = self.end
        # Rename Series
        starts.rename(self.start_column_name, inplace=True)
        ends.rename(self.end_column_name, inplace=True)
        # Sort indexes
        starts.sort_index(inplace=True)
        ends.sort_index(inplace=True)
        ends = ends + pd.Timedelta(86399, "s")
        return pd.concat([starts, ends], axis=1)

    def _make_range(self) -> "DateRange":
        """Create the range DataFrame for date intervals as: day, week, month or year.

        Returns
        -------
        pd.DataFrame
            Range DataFrame with self.start_column_name and \
            self.end_column_name columns. Both start and end dates \
            are supposed to be included in the final range.
        """
        # Create the date range
        date_range = pd.date_range(
            start=self.start,
            end=self.end,
            freq=self.freqs[self.interval],
            inclusive="both",
            normalize=True,
        )
        dates: pd.Series = date_range.to_series().reset_index(drop=True)
        # Use as end dates
        ends = dates
        # Create start days by shifting by 1 and adding a day
        starts = dates.shift(1) + pd.to_timedelta("1 day")
        # Add start date as first date
        starts.loc[ends.index[0]] = self.start
        # If last end is not `sef.end`
        if ends[ends.index[-1]].date() != self.end.date():
            # Compute last period start date using current last period end
            last_period_start = ends[ends.index[-1]] + pd.to_timedelta("1 day")
            starts[starts.index[-1] + 1] = last_period_start
            # Add `self.end` as the last ending date
            ends[ends.index[-1] + 1] = self.end
        # Rename Series
        starts.rename(self.start_column_name, inplace=True)
        ends.rename(self.end_column_name, inplace=True)
        # Sort indexes
        starts.sort_index(inplace=True)
        ends.sort_index(inplace=True)
        ends = ends + pd.Timedelta(86399, "s")
        data = pd.concat([starts, ends], axis=1)
        return DateRange(data, self.start_column_name, self.end_column_name)


class DateRange:
    """Class to hold dateranges dataframes.

    Parameters
    ----------
    data : pd.DataFrame
        The actual daterange dataframe.
    start_col : str
        Name of the column with starting dates.
    end_col : str
        Name of the column with ending dates.
    """

    def __init__(self, data: pd.DataFrame, start_col: str, end_col: str) -> None:
        self._data = data
        self._start = start_col
        self._end = end_col

    @property
    def start_field(self) -> str:
        """Satrting date column name."""
        return self._start

    @property
    def end_field(self) -> str:
        """Ending date column name."""
        return self._end

    @property
    def start_dates(self) -> pd.Series:
        """Starting date column."""
        return self._data[self._start]

    @property
    def end_dates(self) -> pd.Series:
        """Ending date column."""
        return self._data[self._end]

    def as_dataframe(self) -> pd.DataFrame:
        """Return the dateranges as a DataFrame, ie self._data."""
        return self._data

    def as_str(self) -> pd.Series:
        """Return a Series of dateranges as strings with format: 'YYYYMMDD-YYYYMMDD'."""
        str_start = pd.to_datetime(self.start_dates).dt.strftime("%Y%m%d")
        str_end = pd.to_datetime(self.end_dates).dt.strftime("%Y%m%d")
        return str_start + "-" + str_end
