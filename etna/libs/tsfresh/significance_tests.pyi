import pandas as pd

def target_binary_feature_binary_test(x: pd.Series, y: pd.Series) -> float: ...
def target_binary_feature_real_test(x: pd.Series, y: pd.Series, test: str) -> float: ...
def target_real_feature_binary_test(x: pd.Series, y: pd.Series) -> float: ...
def target_real_feature_real_test(x: pd.Series, y: pd.Series) -> float: ...
