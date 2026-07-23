from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from utils import ensure_directory

ROOT = Path(__file__).resolve().parent
REPORTS_DIR = ROOT / "reports"
ensure_directory(str(REPORTS_DIR))

MODEL_CONFIGS = [
    {
        "name": "dropout",
        "dataset": "uci_refined.csv",
        "dataset_path": ROOT / "data" / "raw" / "uci_refined.csv",
        "model_path": ROOT / "models" / "dropout_model.pkl",
        "preprocessor_path": ROOT / "models" / "dropout_preprocessor.pkl",
        "metric_path": ROOT / "results" / "dropout_metrics.json",
        "feature_importance_path": ROOT / "feature_importance" / "dropout_feature_importance.csv",
        "transformed_names_path": ROOT / "models" / "dropout_feature_names.json",
        "expected_target": "target (encoded as 0=Graduate, 1=Enrolled, 2=Dropout)",
        "prediction_format": "Class label prediction and multi-class probability vector for [0, 1, 2]",
        "shap_summary_path": ROOT / "shap" / "dropout_summary.png",
    },
    {
        "name": "wellbeing",
        "dataset": "student_mental_health_burnout_1M.csv",
        "dataset_path": ROOT / "data" / "raw" / "student_mental_health_burnout_1M.csv",
        "model_path": ROOT / "models" / "wellbeing_model.pkl",
        "preprocessor_path": ROOT / "models" / "wellbeing_preprocessor.pkl",
        "metric_path": ROOT / "results" / "wellbeing_metrics.json",
        "feature_importance_path": ROOT / "feature_importance" / "wellbeing_feature_importance.csv",
        "transformed_names_path": ROOT / "models" / "wellbeing_feature_names.json",
        "expected_target": "risk_level (encoded as 0=Low, 1=Medium, 2=High)",
        "prediction_format": "Class label prediction and multi-class probability vector for [0, 1, 2]",
        "shap_summary_path": ROOT / "shap" / "wellbeing_summary.png",
    },
    {
        "name": "depression",
        "dataset": "Student Depression Dataset.csv",
        "dataset_path": ROOT / "data" / "raw" / "student_depression" / "Student Depression Dataset.csv",
        "model_path": ROOT / "models" / "depression_model.pkl",
        "preprocessor_path": ROOT / "models" / "depression_preprocessor.pkl",
        "metric_path": ROOT / "results" / "depression_metrics.json",
        "feature_importance_path": ROOT / "feature_importance" / "depression_feature_importance.csv",
        "transformed_names_path": ROOT / "models" / "depression_feature_names.json",
        "expected_target": "Depression (binary 0/1)",
        "prediction_format": "Class label prediction and binary probability score for class 1",
        "shap_summary_path": ROOT / "shap" / "depression_summary.png",
    },
]


def load_metrics(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_top_features(path: Path) -> list[str]:
    df = pd.read_csv(path)
    return df["feature"].astype(str).head(10).tolist()


def load_transformed_features(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_preprocessor_inputs(path: Path) -> list[str]:
    preprocessor = joblib.load(path)
    if hasattr(preprocessor, "feature_names_in_"):
        return list(preprocessor.feature_names_in_)
    if hasattr(preprocessor, "transformers_"):
        features: list[str] = []
        for _, _, columns in preprocessor.transformers_:
            if columns is None or columns == "drop":
                continue
            if isinstance(columns, (list, tuple)):
                features.extend(list(columns))
        return features
    return []


def build_model_summary(config: dict[str, Any]) -> dict[str, Any]:
    metrics = load_metrics(config["metric_path"])
    preprocessor_inputs = load_preprocessor_inputs(config["preprocessor_path"])
    transformed_features = load_transformed_features(config["transformed_names_path"])
    top_features = load_top_features(config["feature_importance_path"])

    model = joblib.load(config["model_path"])
    algorithm = type(model).__name__
    params = getattr(model, "get_params", lambda: {})()
    objective = params.get("objective", "unknown")
    if algorithm == "XGBClassifier":
        algorithm = f"XGBoost XGBClassifier ({objective})"

    return {
        "model_name": config["name"].capitalize(),
        "dataset": config["dataset"],
        "dataset_path": str(config["dataset_path"].resolve()),
        "samples": int(metrics.get("n_samples", 0)),
        "original_features": len(preprocessor_inputs),
        "transformed_features": len(transformed_features),
        "target_variable": config["expected_target"],
        "algorithm": algorithm,
        "best_hyperparameters": metrics.get("best_parameters", {}),
        "accuracy": metrics.get("accuracy", None),
        "precision": metrics.get("precision", None),
        "recall": metrics.get("recall", None),
        "f1": metrics.get("f1", None),
        "roc_auc": metrics.get("roc_auc", None),
        "cross_validation_score": metrics.get("cross_validation_score", None),
        "top_features": top_features,
        "shap_summary_path": str(config["shap_summary_path"].resolve()),
        "model_location": str(config["model_path"].resolve()),
        "preprocessor_location": str(config["preprocessor_path"].resolve()),
        "expected_input_features": preprocessor_inputs,
        "prediction_output_format": config["prediction_format"],
    }


def write_markdown_report(model_summaries: list[dict[str, Any]], path: Path) -> None:
    with path.open("w", encoding="utf-8") as handle:
        handle.write("# Machine Learning Model Documentation\n\n")
        handle.write("This package documents the three saved trained models and the artifacts required to use them. No retraining is required.\n\n")
        for summary in model_summaries:
            handle.write("---\n\n")
            handle.write(f"## {summary['model_name']} Model\n\n")
            handle.write(f"**Dataset Used:** {summary['dataset']}\n\n")
            handle.write(f"**Dataset Path:** `{summary['dataset_path']}`\n\n")
            handle.write(f"**Number of Samples:** {summary['samples']}\n\n")
            handle.write(f"**Number of Original Features:** {summary['original_features']}\n\n")
            handle.write(f"**Number of Transformed Features:** {summary['transformed_features']}\n\n")
            handle.write(f"**Target Variable:** {summary['target_variable']}\n\n")
            handle.write(f"**Algorithm Used:** {summary['algorithm']}\n\n")
            handle.write("### Best Hyperparameters\n\n")
            handle.write("```json\n")
            json.dump(summary['best_hyperparameters'], handle, indent=2)
            handle.write("\n```\n\n")
            handle.write("### Evaluation Metrics\n\n")
            handle.write(f"- Accuracy: {summary['accuracy']}\n")
            handle.write(f"- Precision: {summary['precision']}\n")
            handle.write(f"- Recall: {summary['recall']}\n")
            handle.write(f"- F1 Score: {summary['f1']}\n")
            handle.write(f"- ROC AUC: {summary['roc_auc']}\n")
            handle.write(f"- Cross Validation Score: {summary['cross_validation_score']}\n\n")
            handle.write("### Top 10 Most Important Features\n\n")
            for feature in summary['top_features']:
                handle.write(f"- {feature}\n")
            handle.write("\n")
            handle.write(f"**SHAP Summary:** `{summary['shap_summary_path']}`\n\n")
            handle.write(f"**Saved Model Location:** `{summary['model_location']}`\n\n")
            handle.write(f"**Saved Preprocessor Location:** `{summary['preprocessor_location']}`\n\n")
            handle.write("### Expected Input Features\n\n")
            for feature in summary['expected_input_features']:
                handle.write(f"- {feature}\n")
            handle.write("\n")
            handle.write(f"**Prediction Output Format:** {summary['prediction_output_format']}\n\n")


def write_comparison_csv(model_summaries: list[dict[str, Any]], path: Path) -> None:
    fieldnames = [
        "Model",
        "Dataset",
        "Samples",
        "Original Features",
        "Transformed Features",
        "Accuracy",
        "Precision",
        "Recall",
        "F1",
        "ROC AUC",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for summary in model_summaries:
            writer.writerow(
                {
                    "Model": summary['model_name'],
                    "Dataset": summary['dataset'],
                    "Samples": summary['samples'],
                    "Original Features": summary['original_features'],
                    "Transformed Features": summary['transformed_features'],
                    "Accuracy": summary['accuracy'],
                    "Precision": summary['precision'],
                    "Recall": summary['recall'],
                    "F1": summary['f1'],
                    "ROC AUC": summary['roc_auc'],
                }
            )


def write_feature_summary_csv(model_summaries: list[dict[str, Any]], path: Path) -> None:
    fieldnames = [
        "Model",
        "Original Feature Count",
        "Transformed Feature Count",
        "Expected Input Features",
        "Top 10 Features",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for summary in model_summaries:
            writer.writerow(
                {
                    "Model": summary['model_name'],
                    "Original Feature Count": summary['original_features'],
                    "Transformed Feature Count": summary['transformed_features'],
                    "Expected Input Features": "; ".join(summary['expected_input_features']),
                    "Top 10 Features": "; ".join(summary['top_features']),
                }
            )


def write_artifacts_summary(path: Path, model_summaries: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        handle.write("# Artifacts Summary\n\n")
        handle.write("This summary lists the generated documentation files and the trained model artifacts required to use the saved models.\n\n")
        handle.write("## Documentation Files\n\n")
        handle.write(f"- {REPORTS_DIR / 'ML_Report.md'}\n")
        handle.write(f"- {REPORTS_DIR / 'Model_Comparison.csv'}\n")
        handle.write(f"- {REPORTS_DIR / 'Feature_Summary.csv'}\n")
        handle.write(f"- {REPORTS_DIR / 'Artifacts_Summary.md'}\n\n")
        handle.write("## Saved Model Artifacts\n\n")
        for summary in model_summaries:
            handle.write(f"### {summary['model_name']}\n")
            handle.write(f"- Model file: `{summary['model_location']}`\n")
            handle.write(f"- Preprocessor file: `{summary['preprocessor_location']}`\n")
            handle.write(f"- Metrics file: `{Path(summary['model_location']).parent.parent / 'results' / f'{summary['model_name'].lower()}_metrics.json'}`\n")
            handle.write(f"- Feature importance file: `{Path(summary['model_location']).parent.parent / 'feature_importance' / f'{summary['model_name'].lower()}_feature_importance.csv'}`\n")
            handle.write(f"- Transformed feature names: `{Path(summary['model_location']).parent / f'{summary['model_name'].lower()}_feature_names.json'}`\n")
            handle.write(f"- SHAP summary: `{summary['shap_summary_path']}`\n\n")
        handle.write("## Generated Evaluation Plots\n\n")
        handle.write("The following evaluation plots were generated in the `plots/` directory by the model evaluation step:\n")
        handle.write("- dropout_confusion_matrix.png\n")
        handle.write("- dropout_roc_curve.png\n")
        handle.write("- dropout_precision_recall.png\n")
        handle.write("- dropout_calibration_curve.png\n")
        handle.write("- wellbeing_confusion_matrix.png\n")
        handle.write("- wellbeing_roc_curve.png\n")
        handle.write("- wellbeing_precision_recall.png\n")
        handle.write("- wellbeing_calibration_curve.png\n")
        handle.write("- depression_confusion_matrix.png\n")
        handle.write("- depression_roc_curve.png\n")
        handle.write("- depression_precision_recall.png\n")
        handle.write("- depression_calibration_curve.png\n")


def main() -> None:
    model_summaries = [build_model_summary(config) for config in MODEL_CONFIGS]
    write_markdown_report(model_summaries, REPORTS_DIR / "ML_Report.md")
    write_comparison_csv(model_summaries, REPORTS_DIR / "Model_Comparison.csv")
    write_feature_summary_csv(model_summaries, REPORTS_DIR / "Feature_Summary.csv")
    write_artifacts_summary(REPORTS_DIR / "Artifacts_Summary.md", model_summaries)
    print(f"Generated documentation package in {REPORTS_DIR}")


if __name__ == "__main__":
    main()
