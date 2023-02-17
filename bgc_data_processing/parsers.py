"""Parsing tools to determine date ranges"""


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
