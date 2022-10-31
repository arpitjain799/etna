from typing import Dict
from typing import List

import numpy as np
from sklearn.base import ClassifierMixin

from etna.datasets import TSDataset
from etna.experimental.classification.classification import TimeSeriesBinaryClassifier
from etna.experimental.classification.feature_extraction.base import BaseTimeSeriesFeatureExtractor
from etna.experimental.classification.utils import crop_nans_single_series


class PredictabilityAnalyzer(TimeSeriesBinaryClassifier):
    """Class for holding time series predictability prediction."""

    def __init__(
        self, feature_extractor: BaseTimeSeriesFeatureExtractor, classifier: ClassifierMixin, threshold: float = 0.5
    ):
        """Init PredictabilityAnalyzer with given parameters.

        Parameters
        ----------
        feature_extractor:
            Instance of time series feature extractor.
        classifier:
            Instance of classifier with sklearn interface.
        threshold:
            Positive class probability threshold.
        """
        super().__init__(feature_extractor=feature_extractor, classifier=classifier, threshold=threshold)

    @staticmethod
    def get_series_from_dataset(ts: TSDataset) -> List[np.ndarray]:
        """Transform the dataset into the array with time series samples.

        Series in the result array are sorted in the alphabetical order of the corresponding segment names.

        Parameters
        ----------
        ts:
            TSDataset with the time series.

        Returns
        -------
        :
            Array with time series from TSDataset.
        """
        series = ts[:, sorted(ts.segments), "target"].values.T
        series = [crop_nans_single_series(x) for x in series]
        return series

    def analyze_predictability(self, ts: TSDataset) -> Dict[str, int]:
        """Analyse the time series in the dataset for predictability.

        Parameters
        ----------
        ts:
            Dataset with time series.

        Returns
        -------
        :
            The indicators of predictability for the each segment in the dataset.
        """
        x = self.get_series_from_dataset(ts=ts)
        y_pred = self.predict(x=x)
        result = dict(zip(sorted(ts.segments), y_pred))
        return result
