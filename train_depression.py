from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import xgboost as xgb
from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold, train_test_split

from evaluation import (
    compute_classification_metrics,
    get_top_feature_importances,
    get_transformed_feature_names,
    save_shap_summary,
    select_features_rfe,
)
from preprocessing import (
    build_preprocessor,
    encode_categorical_for_selection,
    encode_depression_target,
    engineer_depression_features,
    load_csv,
    remove_duplicates,
)
from utils import ensure_directory, save_json, save_pickle, setup_logger

LOGGER = setup_logger(__name__)


def train_depression_model(
    data_path: str,
    models_dir: str,
    results_dir: str,
    feature_importance_dir: str,
    shap_dir: str,
) -> Dict[str, Any]:
    ensure_directory(models_dir)
    ensure_directory(results_dir)
    ensure_directory(feature_importance_dir)
    ensure_directory(shap_dir)

    df = load_csv(data_path)
    df = remove_duplicates(df)
    df = engineer_depression_features(df)
    df = encode_depression_target(df)
    df = df.drop(columns=[col for col in ["id"] if col in df.columns], errors="ignore")
    df = df.dropna(subset=["target_encoded"]).reset_index(drop=True)

    feature_columns = [
        "Gender",
        "Age",
        "Academic Pressure",
        "Work Pressure",
        "CGPA",
        "Study Satisfaction",
        "Job Satisfaction",
        "Dietary Habits",
        "Degree",
        "Have you ever had suicidal thoughts ?",
        "Work/Study Hours",
        "Financial Stress",
        "Family History of Mental Illness",
        "sleep_hours",
        "suicidal_thoughts",
        "family_history",
        "pressure_balance",
        "satisfaction_index",
        "stress_pressure_ratio",
    ]
    X = df[[col for col in feature_columns if col in df.columns]].copy()
    y = df["target_encoded"].astype(int)

    encoded_for_selection = encode_categorical_for_selection(
        X,
        [col for col in X.select_dtypes(include=["object", "category"]).columns],
    )
    selected_features = select_features_rfe(
        xgb.XGBClassifier(eval_metric="logloss", random_state=42, n_jobs=1),
        encoded_for_selection,
        y,
        n_features=15,
    )
    if not selected_features:
        selected_features = [col for col in feature_columns if col in df.columns]

    numeric_features = [
        col for col in selected_features if col in df.select_dtypes(include=["number"]).columns
    ]
    categorical_features = [col for col in selected_features if col not in numeric_features]
    preprocessor = build_preprocessor(numeric_features, categorical_features)

    X_train, X_test, y_train, y_test = train_test_split(
        X[selected_features],
        y,
        test_size=0.2,
        stratify=y,
        random_state=42,
    )
    X_train_processed = preprocessor.fit_transform(X_train)
    X_test_processed = preprocessor.transform(X_test)
    transformed_feature_names = get_transformed_feature_names(preprocessor, selected_features)

    model = xgb.XGBClassifier(
        objective="binary:logistic",
        eval_metric="logloss",
        random_state=42,
        n_jobs=1,
    )
    param_grid = {
        "n_estimators": [100, 200, 300],
        "learning_rate": [0.01, 0.05, 0.1],
        "max_depth": [3, 5, 7],
        "gamma": [0, 1, 3],
        "subsample": [0.7, 0.8, 1.0],
        "colsample_bytree": [0.6, 0.8, 1.0],
        "min_child_weight": [1, 3, 5],
    }
    search = RandomizedSearchCV(
        estimator=model,
        param_distributions=param_grid,
        n_iter=20,
        scoring="f1",
        cv=StratifiedKFold(n_splits=3, shuffle=True, random_state=42),
        verbose=1,
        random_state=42,
        n_jobs=1,
    )
    search.fit(X_train_processed, y_train)
    best_model = search.best_estimator_

    y_pred = best_model.predict(X_test_processed)
    y_prob = best_model.predict_proba(X_test_processed)
    metrics = compute_classification_metrics(y_test.to_numpy(), y_pred, y_prob)
    metrics["cross_validation_score"] = float(search.best_score_)
    metrics["dataset_path"] = str(Path(data_path).resolve())
    metrics["n_samples"] = int(len(df))
    metrics["n_features"] = int(len(selected_features))
    metrics["best_parameters"] = search.best_params_

    save_pickle(str(Path(models_dir) / "depression_model.pkl"), best_model)
    save_pickle(str(Path(models_dir) / "depression_preprocessor.pkl"), preprocessor)
    save_json(transformed_feature_names, str(Path(models_dir) / "depression_feature_names.json"))
    save_json(metrics, str(Path(results_dir) / "depression_metrics.json"))
    save_json(search.best_params_, str(Path(results_dir) / "depression_best_parameters.json"))

    importance_df = get_top_feature_importances(best_model, transformed_feature_names, top_k=len(transformed_feature_names))
    importance_df.to_csv(str(Path(feature_importance_dir) / "depression_feature_importance.csv"), index=False)
    save_shap_summary(
        best_model,
        X_test_processed,
        transformed_feature_names,
        str(Path(shap_dir) / "depression_summary.png"),
    )

    LOGGER.info("Depression model trained: %s samples, %s features", len(df), len(selected_features))
    return metrics


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    data_path = root / "data" / "raw" / "student_depression" / "Student Depression Dataset.csv"
    models_dir = root / "models"
    results_dir = root / "results"
    feature_importance_dir = root / "feature_importance"
    shap_dir = root / "shap"
    train_depression_model(
        str(data_path),
        str(models_dir),
        str(results_dir),
        str(feature_importance_dir),
        str(shap_dir),
    )
