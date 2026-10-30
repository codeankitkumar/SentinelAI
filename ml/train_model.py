"""Train the SentinelAI model from the repo root.

Runs the backend ML pipeline (feature scaling, XGBoost training, metric
reporting) and writes artifacts under ml/models/ plus training_report.json.

Usage (from repo root so `backend` is importable):
    python ml/train_model.py                          # uses sample dataset
    python ml/train_model.py --csv ml/datasets/sample_netflow.csv
    python ml/train_model.py --model gradient_boosting
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.ml.train import train  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Train SentinelAI threat classifier")
    parser.add_argument("--csv", type=str, default=None)
    parser.add_argument("--model", type=str, default="xgboost",
                        choices=["xgboost", "gradient_boosting"])
    args = parser.parse_args()

    print("Training SentinelAI model...")
    report = train(args.csv, model_type=args.model)

    def _default(o):
        if isinstance(o, (np := __import__("numpy")).generic):
            return o.item()
        return str(o)

    report_path = ROOT / "ml" / "models" / "training_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, default=_default))
    print(json.dumps({k: v for k, v in report.items() if k not in ("confusion_matrix", "classification_report")}, indent=2, default=_default))
    print(f"Full report -> {report_path}")


if __name__ == "__main__":
    main()