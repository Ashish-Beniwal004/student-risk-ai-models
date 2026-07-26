"""
Combines outputs from the three independently-trained risk models
(dropout, wellbeing, depression) into one unified 0-100 risk score.

IMPORTANT: These three models were trained on three separate, unrelated
datasets (see train_dropout.py, train_wellbeing.py, train_depression.py).
They do NOT share a student ID or feature schema. This module treats
each model's input as optional per-student data — a real student may
have data available for some models and not others (e.g., academic
records but no wellbeing survey response).
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np

from utils import load_pickle  # confirmed present in utils.py (joblib-backed)


# ---------------------------------------------------------------------------
# CLASS INDEX CONSTANTS
# Confirmed against the encode_*_target() functions in preprocessing.py.
# Getting these wrong silently inverts the risk score, so do not change
# without re-checking preprocessing.py's mapping first.
# ---------------------------------------------------------------------------
DROPOUT_CLASS_INDEX = 2     # confirmed: "Dropout" = 2 in {"Graduate":0, "Enrolled":1, "Dropout":2}
WELLBEING_CLASS_INDEX = 2   # confirmed: highest-risk class = 2 in both encode_wellbeing_target() paths
DEPRESSION_CLASS_INDEX = 1  # confirmed: "has depression" = 1 under both dtype paths in encode_depression_target()


def _load_model_and_preprocessor(models_dir: str, prefix: str):
    model = load_pickle(str(Path(models_dir) / f"{prefix}_model.pkl"))
    preprocessor = load_pickle(str(Path(models_dir) / f"{prefix}_preprocessor.pkl"))
    return model, preprocessor


def score_dropout(features_df, models_dir: str) -> Optional[float]:
    """
    features_df: a single-row DataFrame with the dropout model's expected
    raw feature columns (see feature_columns list in train_dropout.py).
    Returns a 0-100 score, or None if features_df is None.
    """
    if features_df is None:
        return None
    model, preprocessor = _load_model_and_preprocessor(models_dir, "dropout")
    X_processed = preprocessor.transform(features_df)
    y_prob = model.predict_proba(X_processed)
    return float(y_prob[0, DROPOUT_CLASS_INDEX] * 100)


def score_wellbeing(features_df, models_dir: str) -> Optional[float]:
    if features_df is None:
        return None
    model, preprocessor = _load_model_and_preprocessor(models_dir, "wellbeing")
    X_processed = preprocessor.transform(features_df)
    y_prob = model.predict_proba(X_processed)
    return float(y_prob[0, WELLBEING_CLASS_INDEX] * 100)


def score_depression(features_df, models_dir: str) -> Optional[float]:
    if features_df is None:
        return None
    model, preprocessor = _load_model_and_preprocessor(models_dir, "depression")
    X_processed = preprocessor.transform(features_df)
    y_prob = model.predict_proba(X_processed)
    return float(y_prob[0, DEPRESSION_CLASS_INDEX] * 100)


def compute_final_risk_score(
    dropout_score: Optional[float],
    wellbeing_score: Optional[float],
    depression_score: Optional[float],
    weights: Optional[dict] = None,
) -> float:
    """
    Combines up to three 0-100 model scores into one unified risk score.
    Any score can be None if that model's data wasn't available for this
    student — weights are renormalized across whatever scores ARE present.
    """
    if weights is None:
        weights = {"dropout": 0.4, "wellbeing": 0.3, "depression": 0.3}

    scores = {
        "dropout": dropout_score,
        "wellbeing": wellbeing_score,
        "depression": depression_score,
    }
    available = {k: v for k, v in scores.items() if v is not None}

    if not available:
        raise ValueError("No model scores available to compute risk score.")

    total_weight = sum(weights[k] for k in available)
    final_score = sum(available[k] * (weights[k] / total_weight) for k in available)

    return round(final_score, 2)


def compute_student_risk(
    dropout_features_df,
    wellbeing_features_df,
    depression_features_df,
    models_dir: str,
    weights: Optional[dict] = None,
) -> dict:
    """
    End-to-end convenience function: scores a student across all three
    models (skipping any whose features weren't provided) and returns
    both the individual scores and the final fused score, so the
    counsellor-facing explanation can show a per-model breakdown.
    """
    d_score = score_dropout(dropout_features_df, models_dir)
    w_score = score_wellbeing(wellbeing_features_df, models_dir)
    dep_score = score_depression(depression_features_df, models_dir)

    final = compute_final_risk_score(d_score, w_score, dep_score, weights)

    return {
        "dropout_score": d_score,
        "wellbeing_score": w_score,
        "depression_score": dep_score,
        "final_risk_score": final,
    }