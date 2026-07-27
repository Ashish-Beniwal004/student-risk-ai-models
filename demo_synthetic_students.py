"""
demo_synthetic_students.py

Builds 2-3 hand-crafted synthetic student profiles and runs them through
the full Phase 1 pipeline end-to-end: raw features -> engineered features
-> model scoring -> fused risk score.

WHY THIS EXISTS:
The three trained models (dropout, wellbeing, depression) were each trained
on a separate, unrelated public dataset with no shared student ID or feature
schema (see train_dropout.py, train_wellbeing.py, train_depression.py).
There is currently no real dataset where one student has records across
all three. This script manually constructs plausible per-model feature
rows for the SAME conceptual student, so the fusion logic in
risk_fusion.py can be demonstrated working end-to-end.

This is a demo/validation script, not production code. In production,
each model's raw features would come from real institutional records
(academic system, fee system, wellbeing survey, etc.) rather than being
hand-typed here.

Run from the repo root:
    python demo_synthetic_students.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from preprocessing import (
    engineer_dropout_features,
    engineer_wellbeing_features,
    engineer_depression_features,
)
from risk_fusion import compute_student_risk

ROOT = Path(__file__).resolve().parent
MODELS_DIR = str(ROOT / "models")


# ---------------------------------------------------------------------------
# Feature column lists — copied directly from each train_*.py file so this
# script always selects exactly what each model expects.
# ---------------------------------------------------------------------------
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


def build_dropout_row(raw: dict) -> pd.DataFrame:
    """Takes raw dropout-relevant fields, engineers derived features,
    returns a single-row DataFrame matching DROPOUT_FEATURE_COLUMNS."""
    df = pd.DataFrame([raw])
    df = engineer_dropout_features(df)
    return df[DROPOUT_FEATURE_COLUMNS]


def build_wellbeing_row(raw: dict) -> pd.DataFrame:
    df = pd.DataFrame([raw])
    df = engineer_wellbeing_features(df)
    return df[WELLBEING_FEATURE_COLUMNS]


def build_depression_row(raw: dict) -> pd.DataFrame:
    df = pd.DataFrame([raw])
    df = engineer_depression_features(df)
    return df[DEPRESSION_FEATURE_COLUMNS]


# ---------------------------------------------------------------------------
# STUDENT 1: Low risk — strong grades, stable finances, healthy lifestyle
# ---------------------------------------------------------------------------
student_1_dropout_raw = {
    "admission_grade": 16.5,
    "tuition_up_to_date": 1,
    "scholarship_holder": 0,
    "age": 19,
    "gender": 0,  # numeric, matching uci_refined.csv's encoding (0/1, not text)
    "approved_sem1": 6,
    "grade_sem1": 15.2,
    "approved_sem2": 6,
    "grade_sem2": 15.8,
}

student_1_wellbeing_raw = {
    "age": 19,
    "gender": "F",
    "academic_year": 2,
    "study_hours_per_day": 4.0,
    "exam_pressure": 3,
    "academic_performance": 8.5,
    "stress_level": 3,
    "anxiety_score": 2,
    "depression_score": 1,
    "sleep_hours": 7.5,
    "physical_activity": 4,
    "social_support": 8,
    "screen_time": 3.0,
    "internet_usage": 2.5,
    "financial_stress": 2,
    "family_expectation": 5,
    "burnout_score": 2,
    "mental_health_index": 8.0,
}

student_1_depression_raw = {
    "Gender": "Female",
    "Age": 19,
    "Academic Pressure": 2,
    "Work Pressure": 0,
    "CGPA": 8.7,
    "Study Satisfaction": 4,
    "Job Satisfaction": 0,
    "Dietary Habits": "Healthy",
    "Degree": "B.Tech",
    "Have you ever had suicidal thoughts ?": "No",
    "Work/Study Hours": 5,
    "Financial Stress": 2,
    "Family History of Mental Illness": "No",
    "Sleep Duration": "7-8 hours",
}


# ---------------------------------------------------------------------------
# STUDENT 2: Medium risk — declining grades, moderate financial stress
# ---------------------------------------------------------------------------
student_2_dropout_raw = {
    "admission_grade": 13.0,
    "tuition_up_to_date": 1,
    "scholarship_holder": 0,
    "age": 20,
    "gender": 1,
    "approved_sem1": 6,
    "grade_sem1": 12.5,
    "approved_sem2": 5,
    "grade_sem2": 11.8,
}

student_2_wellbeing_raw = {
    "age": 21,
    "gender": "M",
    "academic_year": 3,
    "study_hours_per_day": 2.0,
    "exam_pressure": 7,
    "academic_performance": 5.5,
    "stress_level": 7,
    "anxiety_score": 6,
    "depression_score": 5,
    "sleep_hours": 5.5,
    "physical_activity": 1,
    "social_support": 4,
    "screen_time": 7.0,
    "internet_usage": 6.0,
    "financial_stress": 7,
    "family_expectation": 8,
    "burnout_score": 6,
    "mental_health_index": 4.5,
}

student_2_depression_raw = {
    "Gender": "Male",
    "Age": 20,
    "Academic Pressure": 3,
    "Work Pressure": 1,
    "CGPA": 7.0,
    "Study Satisfaction": 3,
    "Job Satisfaction": 0,
    "Dietary Habits": "Moderate",
    "Degree": "B.Sc",
    "Have you ever had suicidal thoughts ?": "No",
    "Work/Study Hours": 6,
    "Financial Stress": 3,
    "Family History of Mental Illness": "No",
    "Sleep Duration": "7-8 hours",
}


# ---------------------------------------------------------------------------
# STUDENT 3: High risk — poor academics, high financial/emotional distress
# ---------------------------------------------------------------------------
student_3_dropout_raw = {
    "admission_grade": 9.5,
    "tuition_up_to_date": 0,
    "scholarship_holder": 0,
    "age": 23,
    "gender": 1,
    "approved_sem1": 2,
    "grade_sem1": 7.0,
    "approved_sem2": 1,
    "grade_sem2": 5.5,
}

student_3_wellbeing_raw = {
    "age": 23,
    "gender": "M",
    "academic_year": 4,
    "study_hours_per_day": 0.5,
    "exam_pressure": 9,
    "academic_performance": 3.0,
    "stress_level": 9,
    "anxiety_score": 9,
    "depression_score": 8,
    "sleep_hours": 4.0,
    "physical_activity": 0,
    "social_support": 2,
    "screen_time": 10.0,
    "internet_usage": 9.0,
    "financial_stress": 9,
    "family_expectation": 9,
    "burnout_score": 9,
    "mental_health_index": 2.0,
}

student_3_depression_raw = {
    "Gender": "Male",
    "Age": 23,
    "Academic Pressure": 5,
    "Work Pressure": 3,
    "CGPA": 4.8,
    "Study Satisfaction": 1,
    "Job Satisfaction": 1,
    "Dietary Habits": "Unhealthy",
    "Degree": "B.A",
    "Have you ever had suicidal thoughts ?": "Yes",
    "Work/Study Hours": 10,
    "Financial Stress": 5,
    "Family History of Mental Illness": "Yes",
    "Sleep Duration": "Less than 5 hours",
}


STUDENTS = {
    "Student 1 (expected: low risk)": {
        "dropout": student_1_dropout_raw,
        "wellbeing": student_1_wellbeing_raw,
        "depression": student_1_depression_raw,
    },
    "Student 2 (expected: medium risk)": {
        "dropout": student_2_dropout_raw,
        "wellbeing": student_2_wellbeing_raw,
        "depression": student_2_depression_raw,
    },
    "Student 3 (expected: high risk)": {
        "dropout": student_3_dropout_raw,
        "wellbeing": student_3_wellbeing_raw,
        "depression": student_3_depression_raw,
    },
}


def main():
    for label, raw_data in STUDENTS.items():
        dropout_df = build_dropout_row(raw_data["dropout"])
        wellbeing_df = build_wellbeing_row(raw_data["wellbeing"])
        depression_df = build_depression_row(raw_data["depression"])

        result = compute_student_risk(
            dropout_features_df=dropout_df,
            wellbeing_features_df=wellbeing_df,
            depression_features_df=depression_df,
            models_dir=MODELS_DIR,
        )

        print(f"\n{label}")
        print("-" * len(label))
        print(f"  Dropout score:     {result['dropout_score']:.2f}")
        print(f"  Wellbeing score:   {result['wellbeing_score']:.2f}")
        print(f"  Depression score:  {result['depression_score']:.2f}")
        print(f"  FINAL RISK SCORE:  {result['final_risk_score']:.2f}")


if __name__ == "__main__":
    main()