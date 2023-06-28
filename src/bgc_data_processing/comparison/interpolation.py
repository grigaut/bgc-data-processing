"""Interpolation objects."""

from collections.abc import Hashable

import numpy as np
import pandas as pd
from scipy import interpolate

from bgc_data_processing.core.storers import Storer
from bgc_data_processing.verbose import with_verbose


class Interpolator:
    """Interpolate slices with common index from a reference dataframe.

    Parameters
    ----------
    base : pd.DataFrame
        DataFrame to use a base data for the interpolation.
    x_column_name : str
        name of the column to use as x for the interpolation.
    kind : str, optional
        Type of interpolation, to pass to scipy.interpolate.interp1d.
        , by default "linear"
    """

    def __init__(
        self,
        base: Storer,
        x_column_name: str,
        y_columns_name: list[str],
        kind: str = "linear",
    ) -> None:
        self._storer = base
        self._columns_order = base.data.columns
        self._x = base.variables.get(x_column_name).label
        self._ys = [base.variables.get(name).label for name in y_columns_name]
        self.kind = kind

    @with_verbose(
        trigger_threshold=2,
        message="Interpolation depth outbound -> keeping max depth value.",
    )
    def _handle_outbound_max(
        self,
        ref_slice: pd.DataFrame | pd.Series,
        obs_depth: float,
        name: Hashable | None,
    ) -> pd.Series:
        """Deal with 'interpolation' when observation depth is outbound.

        Parameters
        ----------
        ref_slice : pd.DataFrame | pd.Series
            Slice of the reference Dataframe to use.
        obs_depth : float
            Depth of the observation.
        name : Hashable | None
            Name for the ouput series (index of the slice).

        Returns
        -------
        pd.Series
            Result for outbound observation.
        """
        if isinstance(ref_slice, pd.Series):
            max_series = ref_slice
        else:
            max_series: pd.Series = ref_slice.iloc[ref_slice[self._x].argmax()]
        max_series[self._x] = obs_depth
        max_series.name = name
        return max_series[self._columns_order]

    @with_verbose(
        trigger_threshold=2,
        message="Interpolation depth outbound -> keeping min depth value.",
    )
    def _handle_outbound_min(
        self,
        ref_slice: pd.DataFrame | pd.Series,
        obs_depth: float,
        name: Hashable | None,
    ) -> pd.Series:
        """Deal with 'interpolation' when observation depth is outbound.

        Parameters
        ----------
        ref_slice : pd.DataFrame | pd.Series
            Slice of the reference Dataframe to use.
        obs_depth : float
            Depth of the observation.
        name : Hashable | None
            Name for the ouput series (index of the slice).

        Returns
        -------
        pd.Series
            Result for outbound observation.
        """
        if isinstance(ref_slice, pd.Series):
            min_series = ref_slice
        else:
            min_series: pd.Series = ref_slice.iloc[ref_slice[self._x].argmin()]
        min_series[self._x] = obs_depth
        min_series.name = name
        return min_series[self._columns_order]

    def _get_columns_to_interp(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Return columns to interpolate (non constant columns).

        Parameters
        ----------
        dataframe : pd.DataFrame
            Dataframe to get the columns from.

        Returns
        -------
        pd.DataFrame
            Dataframe slice (on columns).
        """
        return dataframe.loc[:, dataframe.columns.isin(self._ys)]

    def _get_constant_columns(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Return columns not to interpolate (single valued columns).

        Parameters
        ----------
        dataframe : pd.DataFrame
            Dataframe to get the columns from.

        Returns
        -------
        pd.DataFrame
            Dataframe slice (on columns).
        """
        return dataframe.loc[:, ~dataframe.columns.isin(self._ys)]

    @with_verbose(
        trigger_threshold=2,
        message="NaN depth encountered -> setting values to NaN.",
    )
    def _handle_nan_depth(
        self,
        ref_slice: pd.DataFrame,
        obs_depth: float,
        name: Hashable | None,
    ) -> pd.Series:
        """Deal with 'interpolation' when observation depth is nan.

        Parameters
        ----------
        ref_slice : pd.DataFrame
            Slice of the reference Dataframe to use.
        obs_depth : float
            Depth of the observation.
        name : Hashable | None
            Name for the ouput series (index of the slice).

        Returns
        -------
        pd.Series
            NaN series.
        """
        to_interp = self._get_columns_to_interp(ref_slice)
        constant_columns = self._get_constant_columns(ref_slice)
        constant_values = constant_columns.iloc[0, :]
        non_constant_values = pd.Series(
            np.nan,
            index=to_interp.columns,
        )
        result = pd.concat([constant_values, non_constant_values])
        result.name = name
        result[self._x] = obs_depth
        return result[self._columns_order]

    @with_verbose(
        trigger_threshold=2,
        message="Valid interpolation depth -> interpolation.",
    )
    def _interpolate(
        self,
        ref_slice: pd.DataFrame,
        obs_depth: float,
        name: Hashable | None,
    ):
        """Interpolate data.

        Parameters
        ----------
        ref_slice : pd.DataFrame
            Slice of the reference Dataframe to use.
        obs_depth : float
            Depth of the observation.
        name : Hashable | None
            Name for the ouput series (index of the slice).

        Returns
        -------
        pd.Series
            Interpolated series.
        """
        non_constant = self._get_columns_to_interp(ref_slice)
        constant_columns = self._get_constant_columns(ref_slice)
        constant_values = constant_columns.iloc[0, :]
        interpolation = interpolate.interp1d(
            x=ref_slice[self._x],
            y=non_constant,
            axis=0,
            fill_value=np.nan,
            kind=self.kind,
        )
        non_constant_values = pd.Series(
            interpolation(obs_depth),
            index=non_constant.columns,
            name=name,
        )
        concatenated = pd.concat([constant_values, non_constant_values])
        concatenated[self._x] = obs_depth
        return concatenated[self._columns_order]

    @with_verbose(trigger_threshold=1, message="Interpolating row.")
    def interpolate(
        self,
        row: pd.Series,
    ) -> pd.Series:
        """Interpolate a self.reference slice with same index as row.

        This method is mostly meant to be applied using pd.DataFrame.apply method.

        Parameters
        ----------
        row : pd.Series
            Row to use for interpolation.

        Returns
        -------
        pd.Series
            Interpolated series with same depth as row.
        """
        ref_slice: pd.DataFrame = self._storer.data.loc[row.name, :]
        obs_depth = row[self._x]
        ref_depths = ref_slice[self._x]
        if np.isnan(obs_depth):
            return self._handle_nan_depth(ref_slice, obs_depth, row.name)
        if obs_depth > ref_depths.max():
            return self._handle_outbound_max(ref_slice, obs_depth, row.name)
        if obs_depth < ref_depths.min():
            return self._handle_outbound_min(ref_slice, obs_depth, row.name)
        return self._interpolate(ref_slice, obs_depth, row.name)

    @with_verbose(
        trigger_threshold=0,
        message="Interpolating Data to match observations' depth values.",
    )
    def interpolate_storer(
        self,
        observations_storer: Storer,
    ) -> Storer:
        """Interpolate over all rows a Store's dataframe.

        Parameters
        ----------
        observations_storer : Storer
            Storer to interpolate on each row.

        Returns
        -------
        Storer
            Storer with interpolated rows to match observations_storer's x values.
        """
        obs_data = observations_storer.data
        matching_index = obs_data.loc[self._storer.data.index.unique(), :]
        interpolated_df = matching_index.apply(self.interpolate, axis=1)
        return Storer(
            data=interpolated_df,
            category=self._storer.category,
            providers=self._storer.providers,
            variables=self._storer.variables,
        )
