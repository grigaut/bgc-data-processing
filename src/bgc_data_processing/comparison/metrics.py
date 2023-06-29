"""Metrics to evaluate Simulations against observations."""

from abc import ABC, abstractmethod

import numpy as np
import pandas as pd

from bgc_data_processing.core.storers import Storer
from bgc_data_processing.exceptions import IncomparableStorersError


class BaseMetric(ABC):
    """Base class to implement metrics.

    Parameters
    ----------
    variables_to_evaluate : list[str]
        List of the names of the variables to use to evaluate.
    """

    metric_name: str

    def __init__(self, variables_to_evaluate: list[str]) -> None:
        self._eval_vars = variables_to_evaluate

    @abstractmethod
    def _eval(
        self,
        observations: pd.DataFrame,
        simulations: pd.DataFrame,
    ) -> pd.Series:
        """Evaluate observations dataframe against simulations."""

    def evaluate(
        self,
        observations: pd.DataFrame,
        simulations: pd.DataFrame,
    ) -> pd.Series:
        """Evaluate observations dataframe against simulations.

        Parameters
        ----------
        observations : pd.DataFrame
            Observations dataframe.
        simulations : pd.DataFrame
            Simulations dataframe.

        Returns
        -------
        pd.Series
            Evaluation result, for every column.
        """
        result = self._eval(observations=observations, simulations=simulations)
        result.name = self.metric_name
        return result

    def evaluate_storers(
        self,
        observations_storer: Storer,
        simulations_storer: Storer,
    ) -> pd.Series:
        """Evaluate two storers against each other.

        Parameters
        ----------
        observations_storer : Storer
            Observations storer.
        simulations_storer : Storer
            Simulations storer.

        Returns
        -------
        pd.Series
            Result for every column.

        Raises
        ------
        IncomparableStorersError
            If the storers have different shapes.
        """
        obs_vars = observations_storer.variables
        obs_eval_labels = [obs_vars.get(name).label for name in self._eval_vars]
        sim_vars = simulations_storer.variables
        sim_eval_labels = [sim_vars.get(name).label for name in self._eval_vars]
        obs_df = observations_storer.data.filter(obs_eval_labels, axis=1)
        sim_df = simulations_storer.data.filter(sim_eval_labels, axis=1)

        if obs_df.shape != sim_df.shape:
            error_msg = (
                f"DataFrame shapes don't match(observations: {obs_df.shape} "
                "- simulations: {sim_df.shape}) -> make sure both storer have "
                "the variables to evaluate on"
                f" (variables: {self._eval_vars})"
            )
            raise IncomparableStorersError(error_msg)

        nans = obs_df.isna().all(axis=1) | sim_df.isna().all(axis=1)
        return self.evaluate(observations=obs_df[~nans], simulations=sim_df[~nans])


class RMSE(BaseMetric):
    """Root-Mean Square Error (RMSE).

    See Also
    --------
    https://en.wikipedia.org/wiki/Root-mean-square_deviation

    Parameters
    ----------
    variables_to_evaluate : list[str]
        List of the names of the variables to use to evaluate.
    """

    metric_name = "RMSE"

    def __init__(self, variables_to_evaluate: list[str]) -> None:
        super().__init__(variables_to_evaluate)

    def _eval(
        self,
        observations: pd.DataFrame,
        simulations: pd.DataFrame,
    ) -> pd.Series:
        """Evaluate observations dataframe against simulations.

        Parameters
        ----------
        observations : pd.DataFrame
            Observations dataframe.
        simulations : pd.DataFrame
            Simulations dataframe.

        Returns
        -------
        pd.Series
            Evaluation result, for every column.
        """
        diff_2 = np.power(observations - simulations, 2)
        return np.sqrt(np.mean(diff_2, axis=0))


class Bias(BaseMetric):
    """Bias.

    See Also
    --------
    https://en.wikipedia.org/wiki/Bias_of_an_estimator

    Parameters
    ----------
    variables_to_evaluate : list[str]
        List of the names of the variables to use to evaluate.
    """

    metric_name = "Bias"

    def _eval(
        self,
        observations: pd.DataFrame,
        simulations: pd.DataFrame,
    ) -> pd.Series:
        """Evaluate observations dataframe against simulations.

        Parameters
        ----------
        observations : pd.DataFrame
            Observations dataframe.
        simulations : pd.DataFrame
            Simulations dataframe.

        Returns
        -------
        pd.Series
            Evaluation result, for every column.
        """
        return np.mean(simulations - observations, axis=0)
