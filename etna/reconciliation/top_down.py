from enum import Enum

import numpy as np
import pandas as pd
from scipy.sparse import lil_matrix

from etna.datasets import TSDataset
from etna.reconciliation.base import BaseReconciliator


class ReconciliationProportionsMethod(str, Enum):
    """Enum for different default forecasts modes."""

    AHP = "AHP"
    PHA = "PHA"

    @classmethod
    def _missing_(cls, method):
        raise ValueError(
            f"Unable to recognize reconciliation method '{method}'! "
            f"Supported methods: {', '.join(sorted(m for m in cls))}."
        )


class TopDownReconciler(BaseReconciliator):
    """Top-down reconciliation methods."""

    def __init__(self, target_level: str, source_level: str, period_length: int, method: str):
        """Create top-down reconciler from ``source_level`` to ``target_level``.

        Parameters
        ----------
        target_level:
            Level to be reconciled from the forecasts.
        source_level:
            Level to be forecasted.
        period_length:
            Period length for calculation reconciliation proportions.
        method:
            Method for calculation reconciliation proportions. Selects last ``period_length`` timestamps for estimation.
            Currently supported options:

            * AHP - Average historical proportions

            * PHA - Proportions of the historical averages
        """
        super(TopDownReconciler, self).__init__(target_level=target_level, source_level=source_level)

        if period_length < 1:
            raise ValueError("Period length must be positive!")

        self.period_length = period_length

        proportions_method = ReconciliationProportionsMethod(method)
        if proportions_method == ReconciliationProportionsMethod.AHP:
            self.proportions_method = self._estimate_ahp_proportion
        elif proportions_method == ReconciliationProportionsMethod.PHA:
            self.proportions_method = self._estimate_pha_proportion

    def fit(self, ts: TSDataset) -> "TopDownReconciler":
        """Fit the reconciliator parameters.

        Parameters
        ----------
        ts:
            TSDataset on the level which is lower or equal to ``target_level``, ``source_level``.

        Returns
        -------
        :
            Fitted instance of reconciliator.
        """
        if ts.hierarchical_structure is None:
            raise ValueError(f"The method can be applied only to instances with a hierarchy!")

        current_level_index = ts.hierarchical_structure.get_level_depth(ts.current_df_level)
        source_level_index = ts.hierarchical_structure.get_level_depth(self.source_level)
        target_level_index = ts.hierarchical_structure.get_level_depth(self.target_level)

        if target_level_index < source_level_index:
            raise ValueError("Target level should be lower or equal in the hierarchy than the source level!")

        if current_level_index < target_level_index:
            raise ValueError("Current TSDataset level should be lower or equal in the hierarchy than the target level!")

        source_level_ts = ts.get_level_dataset(self.source_level)
        target_level_ts = ts.get_level_dataset(self.target_level)

        if source_level_index < target_level_index:

            summing_matrix = target_level_ts.hierarchical_structure.get_summing_matrix(
                target_level=self.source_level, source_level=self.target_level
            )

            source_level_segments = source_level_ts.hierarchical_structure.get_level_segments(self.source_level)
            target_level_segments = target_level_ts.hierarchical_structure.get_level_segments(self.target_level)

            self.mapping_matrix = lil_matrix((len(target_level_segments), len(source_level_segments)))

            for source_index, target_index in zip(*summing_matrix.nonzero()):
                source_segment = source_level_segments[source_index]
                target_segment = target_level_segments[target_index]

                self.mapping_matrix[target_index, source_index] = self.proportions_method(
                    target_series=target_level_ts[:, target_segment, "target"],
                    source_series=source_level_ts[:, source_segment, "target"],
                )

        else:
            self.mapping_matrix = target_level_ts.hierarchical_structure.get_summing_matrix(
                target_level=self.target_level, source_level=self.source_level
            )

        return self

    def _estimate_ahp_proportion(self, target_series: pd.Series, source_series: pd.Series) -> float:
        """Calculate reconciliation proportion with Average historical proportions method."""
        data = pd.concat((target_series, source_series), axis=1).values
        data = data[-self.period_length :]
        return np.nanmean(data[..., 0] / data[..., 1])

    def _estimate_pha_proportion(self, target_series: pd.Series, source_series: pd.Series) -> float:
        """Calculate reconciliation proportions with Proportions of the historical averages method."""
        target_data = target_series.values
        source_data = source_series.values
        return np.nanmean(target_data[-self.period_length :]) / np.nanmean(source_data[-self.period_length :])
