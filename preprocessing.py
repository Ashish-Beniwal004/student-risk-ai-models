from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, OrdinalEncoder, StandardScaler
from typing import List, Optional


def load_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop_duplicates().reset_index(drop=True)


def build_preprocessor(
    numeric_features: List[str],
    categorical_features: List[str],
    scale_features: bool = True,
) -> ColumnTransformer:
    numeric_steps = [("imputer", SimpleImputer(strategy="median"))]
    if scale_features:
        numeric_steps.append(("scaler", StandardScaler()))
    numeric_pipeline = Pipeline(numeric_steps)
    categorical_pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            (
                "onehot",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
            ),
        ]
    )
    return ColumnTransformer(
        [
            ("numeric", numeric_pipeline, numeric_features),
            ("categorical", categorical_pipeline, categorical_features),
        ],
        remainder="drop",
        sparse_threshold=0,
    )


def _map_sleep_duration(duration: Optional[str]) -> float:
    if pd.isna(duration):
        return np.nan
    value = str(duration).strip().lower()
    if "less than" in value:
        return 4.5
    if "more than" in value:
        return 9.0
    if "5-6" in value:
        return 5.5
    if "7-8" in value:
        return 7.5
    if "8-9" in value:
        return 8.5
    if "hours" in value:
        try:
            return float(value.split()[0])
        except ValueError:
            return np.nan
    return np.nan


def encode_dropout_target(df: pd.DataFrame) -> pd.DataFrame:
    mapping = {"Graduate": 0, "Enrolled": 1, "Dropout": 2}
    data = df.copy()
    data["target_encoded"] = data["target"].map(mapping)
    return data


def encode_wellbeing_target(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    if "risk_level" in data.columns:
        mapping = {"Low": 0, "Medium": 1, "High": 2}
        data["target_encoded"] = data["risk_level"].map(mapping)
    elif "mental_health_index" in data.columns:
        data["target_encoded"] = pd.cut(
            data["mental_health_index"],
            bins=[-np.inf, 4.0, 7.0, np.inf],
            labels=[2, 1, 0],
        ).astype(int)
    else:
        raise ValueError("No suitable wellbeing target found.")
    return data


def encode_depression_target(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    if data["Depression"].dtype == object:
        data["target_encoded"] = pd.Categorical(data["Depression"]).codes
    else:
        data["target_encoded"] = data["Depression"].astype(int)
    return data


def engineer_dropout_features(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    data["semester_improvement"] = data["grade_sem2"].fillna(0) - data["grade_sem1"].fillna(0)
    data["academic_performance_index"] = (
        data[["grade_sem1", "grade_sem2"]].fillna(0).mean(axis=1) * 0.7
        + data["admission_grade"].fillna(0) / 20.0 * 3.0
    )
    data["semester_success_ratio"] = (
        data[["approved_sem1", "approved_sem2"]].fillna(0).sum(axis=1) / 20.0
    )
    data["grade_improvement"] = data["grade_sem2"].fillna(0) - data["grade_sem1"].fillna(0)
    data["total_approved_credits"] = data["approved_sem1"].fillna(0) + data["approved_sem2"].fillna(0)
    data["average_semester_grade"] = data[["grade_sem1", "grade_sem2"]].fillna(0).mean(axis=1)
    return data


def engineer_wellbeing_features(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    data["sleep_quality_index"] = data["sleep_hours"].fillna(0) / 8.0
    data["stress_balance"] = data["academic_performance"].fillna(0) - data["stress_level"].fillna(0)
    data["lifestyle_score"] = (
        data["study_hours_per_day"].fillna(0) * 0.25
        + data["physical_activity"].fillna(0) * 0.2
        + data["social_support"].fillna(0) * 0.25
        + data["sleep_quality_index"].fillna(0) * 0.3
    )
    data["mental_risk_index"] = (
        data["burnout_score"].fillna(0) * 0.4
        + data["depression_score"].fillna(0) * 0.35
        + data["stress_level"].fillna(0) * 0.25
    )
    data["financial_risk_index"] = (
        data["financial_stress"].fillna(0)
        / (data["screen_time"].fillna(0) + 1.0)
    )
    return data


def engineer_depression_features(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    data["sleep_hours"] = data["Sleep Duration"].apply(_map_sleep_duration)
    data["suicidal_thoughts"] = data["Have you ever had suicidal thoughts ?"].map({"Yes": 1, "No": 0}).fillna(0).astype(int)
    data["family_history"] = data["Family History of Mental Illness"].map({"Yes": 1, "No": 0}).fillna(0).astype(int)
    data["pressure_balance"] = data["Academic Pressure"].fillna(0) - data["Work Pressure"].fillna(0)
    data["satisfaction_index"] = (
        data["Study Satisfaction"].fillna(0) + data["Job Satisfaction"].fillna(0)
    ) / 2.0
    data["stress_pressure_ratio"] = (
        data["Financial Stress"].fillna(0)
        / (data["Academic Pressure"].fillna(0) + data["Work Pressure"].fillna(0) + 1.0)
    )
    return data


def encode_categorical_for_selection(df: pd.DataFrame, categorical_columns: List[str]) -> pd.DataFrame:
    data = df.copy()
    if not categorical_columns:
        return data
    encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
    data[categorical_columns] = encoder.fit_transform(data[categorical_columns].fillna("missing"))
    return data


def get_feature_columns(df: pd.DataFrame, exclude_columns: List[str]) -> List[str]:
    return [col for col in df.columns if col not in exclude_columns]


def encode_labels(series: pd.Series) -> List[str]:
    if series.dtype == object or series.dtype.name == "category":
        return list(pd.Categorical(series).categories)
    return []
