"""Data preprocessing for ML training.

Functions work on pandas DataFrames that already contain the canonical
``FEATURE_COLUMNS`` plus a ``label`` column (see ml/prepare_dataset.py).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from . import FEATURE_COLUMNS, STR_TO_LABEL


def load_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


def sanitize(df: pd.DataFrame) -> pd.DataFrame:
    """Drop invalid rows and coerce to numeric floats."""
    df = df.copy()
    df = df[df["label"].isin(list(STR_TO_LABEL.keys()))]
    for col in FEATURE_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=FEATURE_COLUMNS)
    df["label"] = df["label"].map(STR_TO_LABEL).astype(int)
    return df


def split_features_target(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    return df[FEATURE_COLUMNS], df["label"]


def scale_fit(X_train: pd.DataFrame) -> tuple[pd.DataFrame, StandardScaler]:
    scaler = StandardScaler()
    X_train_scaled = pd.DataFrame(
        scaler.fit_transform(X_train), columns=FEATURE_COLUMNS
    )
    return X_train_scaled, scaler