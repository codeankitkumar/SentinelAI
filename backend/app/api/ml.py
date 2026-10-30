"""ML endpoints: status/metrics, retraining, and metrics report."""
from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException
from pathlib import Path

from ..core.deps import AdminDep, AnalystDep
from ..ml.inference import get_inferencer, reload as reload_inferencer
from ..ml.train import train as do_train

router = APIRouter(prefix="/ml", tags=["ml"])

_REPORT = Path(__file__).resolve().parents[3] / "ml" / "models" / "training_report.json"


@router.get("/status")
def ml_status(_: AnalystDep) -> dict:
    inf = get_inferencer()
    report = None
    if _REPORT.exists():
        try:
            report = json.loads(_REPORT.read_text())
        except (json.JSONDecodeError, OSError):
            report = None
    return {
        "mode": inf.version,
        "model_loaded": inf.model is not None,
        "training_report_available": report is not None,
        "metrics": report,
    }


@router.post("/retrain")
def retrain(payload: dict | None = None, _: AdminDep = None) -> dict:
    """(Re)train the model. Admin only. Optionally pass a CSV path."""
    csv_path = (payload or {}).get("csv_path")
    model_type = (payload or {}).get("model_type", "xgboost")
    try:
        report = do_train(csv_path, model_type=model_type)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    reload_inferencer()  # new artifacts take effect immediately
    return {"trained": True, "report": report}