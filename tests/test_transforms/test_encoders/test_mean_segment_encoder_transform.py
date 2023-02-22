import numpy as np
import pandas as pd
import pytest

from etna.datasets import TSDataset
from etna.metrics import R2
from etna.models import LinearMultiSegmentModel
from etna.transforms import MeanSegmentEncoderTransform
from tests.test_transforms.utils import assert_transformation_equals_loaded_original


@pytest.mark.parametrize("expected_global_means", ([[3, 30]]))
def test_mean_segment_encoder_fit(simple_ts, expected_global_means):
    encoder = MeanSegmentEncoderTransform()
    encoder.fit(simple_ts)
    assert (encoder.global_means == expected_global_means).all()


def test_mean_segment_encoder_transform(simple_ts, transformed_simple_df):
    encoder = MeanSegmentEncoderTransform()
    transformed_df = encoder.fit_transform(simple_ts).to_pandas()
    transformed_simple_df.index.freq = "D"
    pd.testing.assert_frame_equal(transformed_simple_df, transformed_df)


@pytest.fixture
def almost_constant_ts(random_seed) -> TSDataset:
    df_1 = pd.DataFrame.from_dict({"timestamp": pd.date_range("2021-06-01", "2021-07-01", freq="D")})
    df_2 = pd.DataFrame.from_dict({"timestamp": pd.date_range("2021-06-01", "2021-07-01", freq="D")})
    df_1["segment"] = "Moscow"
    df_1["target"] = 1 + np.random.normal(0, 0.1, size=len(df_1))
    df_2["segment"] = "Omsk"
    df_2["target"] = 10 + np.random.normal(0, 0.1, size=len(df_1))
    classic_df = pd.concat([df_1, df_2], ignore_index=True)
    ts = TSDataset(df=TSDataset.to_dataset(classic_df), freq="D")
    return ts


def test_mean_segment_encoder_forecast(almost_constant_ts):
    """Test that MeanSegmentEncoderTransform works correctly in forecast pipeline
    and helps to correctly forecast almost constant series."""
    horizon = 5
    model = LinearMultiSegmentModel()
    encoder = MeanSegmentEncoderTransform()

    train, test = almost_constant_ts.train_test_split(test_size=horizon)
    train.fit_transform([encoder])
    model.fit(train)
    future = train.make_future(horizon, transforms=[encoder])
    pred_mean_segment_encoding = model.forecast(future)
    pred_mean_segment_encoding.inverse_transform([encoder])

    metric = R2(mode="macro")

    # R2=0 => model predicts the optimal constant
    assert np.allclose(metric(pred_mean_segment_encoding, test), 0)


def test_fit_transform_with_nans(ts_diff_endings):
    encoder = MeanSegmentEncoderTransform()
    encoder.fit_transform(ts_diff_endings)


def test_save_load(almost_constant_ts):
    transform = MeanSegmentEncoderTransform()
    assert_transformation_equals_loaded_original(transform=transform, ts=almost_constant_ts)
