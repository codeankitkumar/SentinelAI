"""Model evaluation: classification metrics and confusion matrix.

All reported numbers come from actually running the model on the evaluation
split. Nothing is fabricated.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

from . import CLASS_LABELS, FEATURE_COLUMNS
from .preprocessing import load_csv, sanitize, scale_fit, split_features_target
from .model import save_model


def train_from_csv(
    csv_path: str,
    test_size: float = 0.25,
    random_state: int = 42,
    model_type: str = "xgboost",
) -> dict:
    """Train, evaluate and persist a classifier. Returns an honest report."""
    df = sanitize(load_csv(csv_path))
    X, y = split_features_target(df)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    X_train_scaled, scaler = scale_fit(X_train)
    X_test_scaled, scaler_test = scale_fit(X_test)
    # Standardize test with the training scaler for correctness.
    X_test_scaled = pd.DataFrame(
        scaler.transform(X_test), columns=FEATURE_COLUMNS
    )

    model = _build_model(model_type, random_state)
    model.fit(X_train_scaled, y_train)

    y_pred = model.predict(X_test_scaled)
    proba = model.predict_proba(X_test_scaled)

    report = {
        "model_type": model_type,
        "num_samples": int(len(df)),
        "num_features": len(FEATURE_COLUMNS),
        "classes": CLASS_LABELS,
        "test_size": len(y_test),
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "precision_macro": round(float(precision_score(y_test, y_pred, average="macro")), 4),
        "recall_macro": round(float(recall_score(y_test, y_pred, average="macro")), 4),
        "f1_macro": round(float(f1_score(y_test, y_pred, average="macro")), 4),
        "confusion_matrix": confusion_matrix(y_test, y_pred, labels=list(range(len(CLASS_LABELS)))).tolist(),
        "classification_report": classification_report(
            y_test, y_pred, labels=list(range(len(CLASS_LABELS))),
            target_names=CLASS_LABELS, output_dict=True,
        ),
        "class_confidence_avg": {
            c: round(float(proba[y_test == i, i].mean()), 4)
            for i, c in enumerate(CLASS_LABELS)
        },
    }

    # Persist model + scaler, and a human/machine readable training report.
    save_model(model, scaler, report=report)
    return report


def _build_model(model_type: str, random_state: int):
    if model_type == "gradient_boosting":
        return GradientBoostingClassifier(n_estimators=120, random_state=random_state)
    return XGBClassifier(
        n_estimators=150,
        max_depth=6,
        learning_rate=0.12,
        subsample=0.9,
        colsample_bytree=0.9,
        use_label_encoder=False,
        eval_metric="mlogloss",
        random_state=random_state,
        verbosity=0,
    )