import pathlib
import tempfile
from copy import deepcopy
from typing import List
from typing import Tuple

import pandas as pd

from etna.datasets import TSDataset
from etna.pipeline.base import AbstractPipeline
from tests.utils import select_segments_subset


def get_loaded_pipeline(pipeline: AbstractPipeline, ts: TSDataset = None) -> AbstractPipeline:
    with tempfile.TemporaryDirectory() as dir_path_str:
        dir_path = pathlib.Path(dir_path_str)
        path = dir_path.joinpath("dummy.zip")
        pipeline.save(path)
        if ts is None:
            loaded_pipeline = pipeline.load(path)
        else:
            loaded_pipeline = pipeline.load(path, ts=ts)
    return loaded_pipeline


def assert_pipeline_equals_loaded_original(
    pipeline: AbstractPipeline, ts: TSDataset, load_ts: bool = True
) -> Tuple[AbstractPipeline, AbstractPipeline]:
    import torch  # TODO: remove after fix at issue-802

    initial_ts = deepcopy(ts)

    pipeline.fit(ts)
    torch.manual_seed(11)
    forecast_ts_1 = pipeline.forecast()

    if load_ts:
        loaded_pipeline = get_loaded_pipeline(pipeline, ts=initial_ts)
        torch.manual_seed(11)
        forecast_ts_2 = loaded_pipeline.forecast()
    else:
        loaded_pipeline = get_loaded_pipeline(pipeline)
        torch.manual_seed(11)
        forecast_ts_2 = loaded_pipeline.forecast(ts=initial_ts)

    pd.testing.assert_frame_equal(forecast_ts_1.to_pandas(), forecast_ts_2.to_pandas())

    return pipeline, loaded_pipeline


def assert_pipeline_forecasts_with_given_ts(
    pipeline: AbstractPipeline, ts: TSDataset, segments_to_check: List[str]
) -> AbstractPipeline:
    import torch  # TODO: remove after fix at issue-802

    segments_to_check = list(set(segments_to_check))
    ts_selected = select_segments_subset(ts=deepcopy(ts), segments=segments_to_check)

    pipeline.fit(ts)
    torch.manual_seed(11)
    forecast_ts_1 = pipeline.forecast()
    forecast_df_1 = forecast_ts_1.to_pandas().loc[:, pd.IndexSlice[segments_to_check, :]]

    torch.manual_seed(11)
    forecast_ts_2 = pipeline.forecast(ts=ts_selected)
    forecast_df_2 = forecast_ts_2.to_pandas()

    pd.testing.assert_frame_equal(forecast_df_1, forecast_df_2)

    return pipeline
