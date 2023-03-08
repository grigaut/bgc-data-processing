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

    def __init__(
        self,
        start: dt.datetime,
        end: dt.datetime,
        interval: str,
        interval_length: int = 1,
    ) -> None:

        self.start = start
        self.end = end
        self.interval = interval
        self.interval_length = interval_length

    def __call__(self) -> pd.DataFrame:
        if self.interval == "custom":
            return self._make_custom_range()
        else:
            return self._make_range()

    def _make_custom_range(self) -> pd.DataFrame:
        """Create the range DataFrame for custom date intervals.

        Returns
        -------
        pd.DataFrame
            Range DataFrame with "start_date" and "end_date" columns.
            Both start and end dates are supposed to be included in the final range.
        """
        # Create the date range
        date_range = pd.date_range(
            start=self.start,
            end=self.end,
            freq=f"{self.interval_length}{self.freqs['day']}",
            inclusive="both",
        )
        dates: pd.Series = date_range.to_series().reset_index(drop=True)
        # Use as start dates
        starts = dates
        # Create end date by shifting by 1 day to get previous day
        ends = dates.shift(-1) - pd.to_timedelta("1 day")
        # Add final date.
        ends.loc[ends.index[-1]] = self.end
        # Rename Series
        starts.name = "start_date"
        ends.name = "end_date"
        # Sort indexes
        starts.sort_index(inplace=True)
        ends.sort_index(inplace=True)
        return pd.concat([starts, ends], axis=1)

    def _make_range(self) -> pd.DataFrame:
        """Create the range DataFrame for 'usual' date intervals:
        day, week, month or year.

        Returns
        -------
        pd.DataFrame
            Range DataFrame with "start_date" and "end_date" columns.
            Both start and end dates are supposed to be included in the final range.
        """
        # Create the date range
        date_range = pd.date_range(
            start=self.start,
            end=self.end,
            freq=self.freqs[self.interval],
            inclusive="both",
        )
        dates: pd.Series = date_range.to_series().reset_index(drop=True)
        # Use as end dates
        ends = dates
        # Create start days by shifting by 1 and adding a day
        starts = dates.shift(1) + pd.to_timedelta("1 day")
        # Add start date as first date
        starts.loc[ends.index[0]] = self.start
        # If last end is not `sef.end`
        if ends[ends.index[-1]] != self.end:
            # Compute last period start date using current last period end
            last_period_start = ends[ends.index[-1]] + pd.to_timedelta("1 day")
            starts[starts.index[-1] + 1] = last_period_start
            # Add `self.end` as the last ending date
            ends[ends.index[-1] + 1] = self.end
        # Rename Series
        starts.name = "start_date"
        ends.name = "end_date"
        # Sort indexes
        starts.sort_index(inplace=True)
        ends.sort_index(inplace=True)
        return pd.concat([starts, ends], axis=1)
