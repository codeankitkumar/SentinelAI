"""ML training orchestration exposed via the API and CLI."""
from __future__ import annotations

from pathlib import Path

from .evaluate import train_from_csv

_DEFAULT_DATASET = Path(__file__).resolve().parents[3] / "ml" / "datasets" / "sample_netflow.csv"


def train(csv_path: str | None = None, model_type: str = "xgboost") -> dict:
    path = Path(csv_path) if csv_path else _DEFAULT_DATASET
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {path}. Run ml/generate_sample_data.py "
            "or prepare a real dataset (see docs/DATASETS.md)."
        )
    return train_from_csv(str(path), model_type=model_type)