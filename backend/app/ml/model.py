"""Model load/save helpers using joblib."""
from __future__ import annotations

import joblib
from pathlib import Path

from ..config import settings

# Make model paths relative to the repo root so both the API and the training
# scripts consistently read/write <repo>/ml/models.
_REPO = Path(__file__).resolve().parents[3]


def _resolve(path: str) -> Path:
    p = Path(path)
    if not p.is_absolute():
        p = _REPO / path
    return p


def save_model(model, scaler, report: dict | None = None, *, metrics: dict | None = None) -> Path:
    model_path = _resolve(settings.ml_model_path)
    scaler_path = _resolve(settings.ml_scaler_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)
    if report is not None:
        report_path = model_path.with_name("training_report.json")
        joblib.dump(report, report_path)
    return model_path


def load_pipeline() -> tuple[object, object] | tuple[None, None]:
    """Load the trained model + scaler. Returns (None, None) if unavailable."""
    model_path = _resolve(settings.ml_model_path)
    scaler_path = _resolve(settings.ml_scaler_path)
    if not (model_path.exists() and scaler_path.exists()):
        return None, None
    return joblib.load(model_path), joblib.load(scaler_path)