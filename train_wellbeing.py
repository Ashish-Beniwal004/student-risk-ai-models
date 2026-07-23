from __future__ import annotations

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
    encode_wellbeing_target,
    engineer_wellbeing_features,
    load_csv,
    remove_duplicates,
)
from utils import ensure_directory, save_json, save_pickle, setup_logger

LOGGER = setup_logger(__name__)


def train_wellbeing_model(
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
    df = df.dropna(subset=["risk_level", "mental_health_index"], how="any")
    df = engineer_wellbeing_features(df)
    df = encode_wellbeing_target(df)
    df = df.dropna(subset=["target_encoded"]).reset_index(drop=True)

    if len(df) > 100000:
        df, _ = train_test_split(
            df,
            train_size=100000,
            stratify=df["target_encoded"],
            random_state=42,
        )
        df = df.reset_index(drop=True)

    feature_columns = [
        "age",
        "gender",
        "academic_year",
        "study_hours_per_day",
        "exam_pressure",
        "academic_performance",
        "stress_level",
        "anxiety_score",
        "depression_score",
        "sleep_hours",
        "physical_activity",
        "social_support",
        "screen_time",
        "internet_usage",
        "financial_stress",
        "family_expectation",
        "burnout_score",
        "mental_health_index",
        "lifestyle_score",
        "mental_risk_index",
        "stress_balance",
        "financial_risk_index",
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
        selected_features = [col for col in feature_columns if col in X.columns]

    numeric_features = [
        col for col in selected_features if col in X.select_dtypes(include=["number"]).columns
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
        objective="multi:softprob",
        eval_metric="mlogloss",
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
        scoring="f1_macro",
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

    save_pickle(str(Path(models_dir) / "wellbeing_model.pkl"), best_model)
    save_pickle(str(Path(models_dir) / "wellbeing_preprocessor.pkl"), preprocessor)
    save_json(transformed_feature_names, str(Path(models_dir) / "wellbeing_feature_names.json"))
    save_json(metrics, str(Path(results_dir) / "wellbeing_metrics.json"))
    save_json(search.best_params_, str(Path(results_dir) / "wellbeing_best_parameters.json"))

    importance_df = get_top_feature_importances(best_model, transformed_feature_names, top_k=len(transformed_feature_names))
    importance_df.to_csv(str(Path(feature_importance_dir) / "wellbeing_feature_importance.csv"), index=False)
    save_shap_summary(
        best_model,
        X_test_processed,
        transformed_feature_names,
        str(Path(shap_dir) / "wellbeing_summary.png"),
    )

    LOGGER.info("Wellbeing model trained: %s samples, %s features", len(df), len(selected_features))
    return metrics


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    data_path = root / "data" / "raw" / "student_mental_health_burnout_1M.csv"
    models_dir = root / "models"
    results_dir = root / "results"
    feature_importance_dir = root / "feature_importance"
    shap_dir = root / "shap"
    train_wellbeing_model(
        str(data_path),
        str(models_dir),
        str(results_dir),
        str(feature_importance_dir),
        str(shap_dir),
    )
