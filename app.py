"""
app.py – Flask ML Inference Service for DISHA (port 8000)

Accepts simplified UI inputs (attendance, gpa, assignmentCompletion, midtermScore)
and maps them into the three saved model pipelines shipped with the project.
The service loads the serialized .pkl artifacts at startup, applies the saved
preprocessors, and returns a unified 0-100 risk score.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS

# ── Add the package root to sys.path so sibling modules resolve ──────────────
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MODELS_DIR = str(ROOT / "models")

MODEL_CONFIG = {
    "dropout": {
        "model_path": ROOT / "models" / "dropout_model.pkl",
        "preprocessor_path": ROOT / "models" / "dropout_preprocessor.pkl",
        "risk_class_index": 2,
        "weight": 0.4,
    },
    "wellbeing": {
        "model_path": ROOT / "models" / "wellbeing_model.pkl",
        "preprocessor_path": ROOT / "models" / "wellbeing_preprocessor.pkl",
        "risk_class_index": 2,
        "weight": 0.3,
    },
    "depression": {
        "model_path": ROOT / "models" / "depression_model.pkl",
        "preprocessor_path": ROOT / "models" / "depression_preprocessor.pkl",
        "risk_class_index": 1,
        "weight": 0.3,
    },
}

MODEL_BUNDLES: dict[str, dict] = {}
LOAD_ERRORS: list[str] = []


def _load_model_bundle(name: str, config: dict) -> None:
    model_path = config["model_path"]
    preprocessor_path = config["preprocessor_path"]

    if not model_path.exists():
        raise FileNotFoundError(f"Missing model artifact: {model_path}")
    if not preprocessor_path.exists():
        raise FileNotFoundError(f"Missing preprocessor artifact: {preprocessor_path}")

    MODEL_BUNDLES[name] = {
        "model": load_pickle(str(model_path)),
        "preprocessor": load_pickle(str(preprocessor_path)),
        "risk_class_index": config["risk_class_index"],
        "weight": config["weight"],
    }


# Lazy-import the project modules (gives a clean error if sklearn version mismatch)
try:
    from preprocessing import (
        engineer_dropout_features,
        engineer_wellbeing_features,
        engineer_depression_features,
    )
    from utils import load_pickle

    for model_name, model_config in MODEL_CONFIG.items():
        try:
            _load_model_bundle(model_name, model_config)
        except Exception as exc:
            LOAD_ERRORS.append(f"{model_name}: {exc}")

    if LOAD_ERRORS:
        MODELS_LOADED = bool(MODEL_BUNDLES)
        LOAD_ERROR = "; ".join(LOAD_ERRORS)
        logging.error("Failed to load one or more model bundles: %s", LOAD_ERROR)
    else:
        MODELS_LOADED = True
        LOAD_ERROR = None
except Exception as exc:
    MODELS_LOADED = False
    LOAD_ERROR = str(exc)
    logging.error("Failed to import ML modules or load models: %s", exc)

# ── Flask app setup ──────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app, origins=["http://localhost:5173", "http://localhost:5000"])

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── Feature column lists (matches train_*.py exactly) ────────────────────────
DROPOUT_FEATURE_COLUMNS = [
    "admission_grade", "tuition_up_to_date", "scholarship_holder", "age",
    "gender", "approved_sem1", "grade_sem1", "approved_sem2", "grade_sem2",
    "semester_improvement", "academic_performance_index",
    "semester_success_ratio", "grade_improvement", "total_approved_credits",
    "average_semester_grade",
]

WELLBEING_FEATURE_COLUMNS = [
    "age", "gender", "academic_year", "study_hours_per_day", "exam_pressure",
    "academic_performance", "stress_level", "anxiety_score",
    "depression_score", "sleep_hours", "physical_activity", "social_support",
    "screen_time", "internet_usage", "financial_stress", "family_expectation",
    "burnout_score", "mental_health_index", "lifestyle_score",
    "mental_risk_index", "stress_balance", "financial_risk_index",
]

DEPRESSION_FEATURE_COLUMNS = [
    "Gender", "Age", "Academic Pressure", "Work Pressure", "CGPA",
    "Study Satisfaction", "Job Satisfaction", "Dietary Habits", "Degree",
    "Have you ever had suicidal thoughts ?", "Work/Study Hours",
    "Financial Stress", "Family History of Mental Illness", "sleep_hours",
    "suicidal_thoughts", "family_history", "pressure_balance",
    "satisfaction_index", "stress_pressure_ratio",
]


def map_inputs_to_model_features(attendance: float, gpa: float,
                                  assignment_completion: float,
                                  midterm_score: float) -> dict:
    """
    Maps the 4 simplified UI inputs to rich feature dicts for all three models.

    Mapping rationale:
    - attendance (0-100) → proxy for engagement, tuition_up_to_date, social_support
    - gpa (0-10 CGPA scale)  → proxy for academic grade, academic_performance
    - assignmentCompletion (0-100) → proxy for study consistency, seat credits
    - midtermScore (0-100)  → proxy for exam performance, anxiety inverse

    All unmapped features are set to sensible neutral/average values so the
    preprocessor's imputer doesn't distort results.
    """
    # Derived composite values
    engagement = attendance / 100.0         # 0..1
    academic_perf = (gpa / 10.0) * 10.0    # keep on 0-10 scale
    assignment_norm = assignment_completion / 100.0   # 0..1
    midterm_norm = midterm_score / 100.0    # 0..1

    # Grade on 0-20 scale (Portuguese-style, matching UCI dropout dataset)
    grade_equivalent = midterm_norm * 20.0
    gpa_20 = (gpa / 10.0) * 20.0

    # Stress & anxiety are inversely related to performance & engagement
    stress = round((1.0 - (engagement * 0.4 + assignment_norm * 0.3 + midterm_norm * 0.3)) * 10, 1)
    anxiety = round(stress * 0.9, 1)
    burnout = round(stress * 0.85, 1)
    depression_score_val = round(stress * 0.7, 1)
    mental_health_idx = round(10.0 - stress, 1)
    sleep_hrs = round(6.0 + engagement * 2.0, 1)   # 6-8 hours based on engagement
    financial_stress = round((1.0 - engagement) * 8 + 2, 1)

    # Approved credits per semester (max ~6 per semester if all approved)
    approved_credits = round(assignment_norm * 6.0, 1)

    dropout_raw = {
        "admission_grade": gpa_20,
        "tuition_up_to_date": 1 if attendance >= 60 else 0,
        "scholarship_holder": 0,
        "age": 21,
        "gender": 0,
        "approved_sem1": approved_credits,
        "grade_sem1": grade_equivalent,
        "approved_sem2": approved_credits,
        "grade_sem2": grade_equivalent,
    }

    wellbeing_raw = {
        "age": 21,
        "gender": "F",
        "academic_year": 2,
        "study_hours_per_day": round(assignment_norm * 6.0 + 1.0, 1),
        "exam_pressure": round(10 - midterm_norm * 5, 1),
        "academic_performance": academic_perf,
        "stress_level": stress,
        "anxiety_score": anxiety,
        "depression_score": depression_score_val,
        "sleep_hours": sleep_hrs,
        "physical_activity": round(engagement * 5, 1),
        "social_support": round(engagement * 8 + 2, 1),
        "screen_time": round((1 - engagement) * 8 + 2, 1),
        "internet_usage": round((1 - assignment_norm) * 6 + 2, 1),
        "financial_stress": financial_stress,
        "family_expectation": 6.0,
        "burnout_score": burnout,
        "mental_health_index": mental_health_idx,
    }

    # dietary_habits: derive from engagement
    if engagement >= 0.75:
        dietary = "Healthy"
    elif engagement >= 0.45:
        dietary = "Moderate"
    else:
        dietary = "Unhealthy"

    depression_raw = {
        "Gender": "Female",
        "Age": 21,
        "Academic Pressure": round(10 - midterm_norm * 4, 1),
        "Work Pressure": round(financial_stress * 0.3, 1),
        "CGPA": gpa,
        "Study Satisfaction": round(assignment_norm * 4 + 1, 1),
        "Job Satisfaction": 0,
        "Dietary Habits": dietary,
        "Degree": "B.Tech",
        "Have you ever had suicidal thoughts ?": "No",
        "Work/Study Hours": round(assignment_norm * 8 + 2, 1),
        "Financial Stress": round(financial_stress / 10 * 5, 1),
        "Family History of Mental Illness": "No",
        "Sleep Duration": f"{sleep_hrs} hours",
    }

    return {
        "dropout_raw": dropout_raw,
        "wellbeing_raw": wellbeing_raw,
        "depression_raw": depression_raw,
    }


def build_feature_df(raw: dict, engineer_fn, feature_cols: list) -> pd.DataFrame:
    """Apply the training-time feature engineering and return a single-row DataFrame."""
    df = pd.DataFrame([raw])
    df = engineer_fn(df)
    cols = [c for c in feature_cols if c in df.columns]
    return df[cols]


def score_bundle(bundle_name: str, features_df: pd.DataFrame) -> float:
    bundle = MODEL_BUNDLES[bundle_name]
    processed = bundle["preprocessor"].transform(features_df)
    probabilities = bundle["model"].predict_proba(processed)
    class_index = bundle["risk_class_index"]

    if class_index >= probabilities.shape[1]:
        raise ValueError(
            f"Model '{bundle_name}' returned {probabilities.shape[1]} classes, expected index {class_index}"
        )

    return float(probabilities[0, class_index] * 100)


def compute_final_risk_score(scores: dict[str, float]) -> float:
    available_scores = {name: score for name, score in scores.items() if score is not None}
    if not available_scores:
        raise ValueError("No model scores available to compute a final risk score.")

    total_weight = sum(MODEL_BUNDLES[name]["weight"] for name in available_scores)
    if total_weight <= 0:
        raise ValueError("Model weights are invalid.")

    final_score = sum(
        available_scores[name] * (MODEL_BUNDLES[name]["weight"] / total_weight)
        for name in available_scores
    )
    return round(final_score, 2)


def determine_risk_level(score: float) -> str:
    if score >= 70:
        return "HIGH"
    elif score >= 35:
        return "MEDIUM"
    return "LOW"


def build_top_factors(attendance: float, gpa: float,
                       assignment_completion: float, midterm_score: float,
                       breakdown: dict) -> list[str]:
    """
    Produce human-readable top-factor strings ranked by contribution.
    Uses both the model breakdown and the raw input values.
    """
    factors = []

    # Academic factors
    if attendance < 60:
        factors.append(f"Low attendance ({attendance:.0f}%) — Critical engagement risk")
    elif attendance < 75:
        factors.append(f"Below-average attendance ({attendance:.0f}%)")

    if gpa < 5.0:
        factors.append(f"Very low CGPA ({gpa:.1f}/10) — Academic failure risk")
    elif gpa < 7.0:
        factors.append(f"Below-average CGPA ({gpa:.1f}/10)")

    if assignment_completion < 50:
        factors.append(f"Poor assignment completion ({assignment_completion:.0f}%)")
    elif assignment_completion < 70:
        factors.append(f"Inconsistent assignment submission ({assignment_completion:.0f}%)")

    if midterm_score < 40:
        factors.append(f"Critical midterm score ({midterm_score:.0f}%) — Urgent intervention needed")
    elif midterm_score < 60:
        factors.append(f"Below-average midterm score ({midterm_score:.0f}%)")

    # Model-specific breakdown factors
    d_score = breakdown.get("dropout_score") or 0
    w_score = breakdown.get("wellbeing_score") or 0
    dep_score = breakdown.get("depression_score") or 0

    if d_score > 60:
        factors.append(f"High academic dropout risk ({d_score:.1f}/100)")
    if w_score > 60:
        factors.append(f"High wellbeing concern ({w_score:.1f}/100)")
    if dep_score > 60:
        factors.append(f"Elevated mental health indicators ({dep_score:.1f}/100)")

    # Add positive factors / low-risk indicators if list is short
    if not factors:
        if attendance >= 90:
            factors.append(f"Excellent attendance ({attendance:.0f}%)")
        if gpa >= 8.0:
            factors.append(f"Strong academic performance (CGPA {gpa:.1f})")
        if assignment_completion >= 90:
            factors.append(f"Consistent assignment submission ({assignment_completion:.0f}%)")
        if midterm_score >= 80:
            factors.append(f"High midterm score ({midterm_score:.0f}%)")

    if not factors:
        factors.append("All academic indicators within normal range")

    return factors[:5]  # return top 5


# ── Routes ───────────────────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "modelsLoaded": MODELS_LOADED,
        "error": LOAD_ERROR,
    })


@app.route("/predict", methods=["POST"])
def predict():
    if not MODEL_BUNDLES:
        return jsonify({
            "error": f"ML model artifacts failed to load: {LOAD_ERROR}"
        }), 503

    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    # Validate and clamp inputs
    try:
        attendance = float(data.get("attendance", 75))
        gpa = float(data.get("gpa", 7.0))
        assignment_completion = float(data.get("assignmentCompletion", 75))
        midterm_score = float(data.get("midtermScore", 65))
    except (TypeError, ValueError) as e:
        return jsonify({"error": f"Invalid input values: {e}"}), 400

    # Clamp to valid ranges
    attendance = max(0.0, min(100.0, attendance))
    gpa = max(0.0, min(10.0, gpa))
    assignment_completion = max(0.0, min(100.0, assignment_completion))
    midterm_score = max(0.0, min(100.0, midterm_score))

    logger.info(
        "Predict request: attendance=%.1f gpa=%.2f assignment=%.1f midterm=%.1f",
        attendance, gpa, assignment_completion, midterm_score,
    )

    try:
        feature_sets = map_inputs_to_model_features(
            attendance, gpa, assignment_completion, midterm_score
        )

        dropout_df = build_feature_df(
            feature_sets["dropout_raw"],
            engineer_dropout_features,
            DROPOUT_FEATURE_COLUMNS,
        )
        wellbeing_df = build_feature_df(
            feature_sets["wellbeing_raw"],
            engineer_wellbeing_features,
            WELLBEING_FEATURE_COLUMNS,
        )
        depression_df = build_feature_df(
            feature_sets["depression_raw"],
            engineer_depression_features,
            DEPRESSION_FEATURE_COLUMNS,
        )

        dropout_score = score_bundle("dropout", dropout_df)
        wellbeing_score = score_bundle("wellbeing", wellbeing_df)
        depression_score = score_bundle("depression", depression_df)

        result = {
            "dropout_score": dropout_score,
            "wellbeing_score": wellbeing_score,
            "depression_score": depression_score,
        }

        final_score = compute_final_risk_score({
            "dropout": dropout_score,
            "wellbeing": wellbeing_score,
            "depression": depression_score,
        })
        risk_level = determine_risk_level(final_score)
        top_factors = build_top_factors(
            attendance, gpa, assignment_completion, midterm_score, result
        )

        logger.info(
            "Prediction complete: score=%.2f level=%s", final_score, risk_level
        )

        return jsonify({
            "riskScore": round(final_score, 2),
            "riskLevel": risk_level,
            "topFactors": top_factors,
            "breakdown": {
                "dropoutScore": round(dropout_score, 2),
                "wellbeingScore": round(wellbeing_score, 2),
                "depressionScore": round(depression_score, 2),
            },
        })

    except Exception as exc:
        logger.error("Prediction failed: %s", exc, exc_info=True)
        return jsonify({"error": f"Inference error: {str(exc)}"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("FLASK_PORT", 8000))
    logger.info("Starting DISHA ML Inference Service on port %d", port)
    logger.info("Models directory: %s", MODELS_DIR)
    logger.info("Models loaded: %s", MODELS_LOADED)
    if not MODELS_LOADED:
        logger.error("LOAD ERROR: %s", LOAD_ERROR)
    app.run(host="0.0.0.0", port=port, debug=False)
