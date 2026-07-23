from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.calibration import calibration_curve
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    roc_curve,
    auc,
    precision_recall_curve,
    average_precision_score,
    confusion_matrix,
)
from sklearn.preprocessing import label_binarize

from preprocessing import (
    build_preprocessor,
    encode_depression_target,
    encode_dropout_target,
    encode_wellbeing_target,
    engineer_depression_features,
    engineer_dropout_features,
    engineer_wellbeing_features,
    load_csv,
    remove_duplicates,
)
from utils import load_pickle, ensure_directory

ROOT = Path(__file__).resolve().parent
PLOTS_DIR = ROOT / "plots"
ensure_directory(str(PLOTS_DIR))

MODEL_CONFIGS = [
    {
        "name": "dropout",
        "model_path": ROOT / "models" / "dropout_model.pkl",
        "preprocessor_path": ROOT / "models" / "dropout_preprocessor.pkl",
        "data_path": ROOT / "data" / "raw" / "uci_refined.csv",
        "load_data": "load_dropout_data",
        "plot_prefix": "dropout",
    },
    {
        "name": "wellbeing",
        "model_path": ROOT / "models" / "wellbeing_model.pkl",
        "preprocessor_path": ROOT / "models" / "wellbeing_preprocessor.pkl",
        "data_path": ROOT / "data" / "raw" / "student_mental_health_burnout_1M.csv",
        "load_data": "load_wellbeing_data",
        "plot_prefix": "wellbeing",
    },
    {
        "name": "depression",
        "model_path": ROOT / "models" / "depression_model.pkl",
        "preprocessor_path": ROOT / "models" / "depression_preprocessor.pkl",
        "data_path": ROOT / "data" / "raw" / "student_depression" / "Student Depression Dataset.csv",
        "load_data": "load_depression_data",
        "plot_prefix": "depression",
    },
]

FONT_SIZE = 12
plt.rcParams.update({"font.size": FONT_SIZE})


def load_dropout_data(path: Path) -> pd.DataFrame:
    df = load_csv(str(path))
    df = remove_duplicates(df)
    df = engineer_dropout_features(df)
    df = encode_dropout_target(df)
    df = df.dropna(subset=["target_encoded"]).reset_index(drop=True)
    return df


def load_wellbeing_data(path: Path) -> pd.DataFrame:
    df = load_csv(str(path))
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
    return df


def load_depression_data(path: Path) -> pd.DataFrame:
    df = load_csv(str(path))
    df = remove_duplicates(df)
    df = engineer_depression_features(df)
    df = encode_depression_target(df)
    df = df.drop(columns=[col for col in ["id"] if col in df.columns], errors="ignore")
    df = df.dropna(subset=["target_encoded"]).reset_index(drop=True)
    return df


def get_selected_features_from_preprocessor(preprocessor: object) -> list[str]:
    if hasattr(preprocessor, "feature_names_in_"):
        return list(preprocessor.feature_names_in_)
    if hasattr(preprocessor, "transformers_"):
        for _, transformer, columns in preprocessor.transformers_:
            if columns is not None and columns != "drop":
                return list(columns)
    raise RuntimeError("Unable to infer selected feature columns from preprocessor.")


def prepare_test_data(data: pd.DataFrame, preprocessor: object) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    selected_features = get_selected_features_from_preprocessor(preprocessor)
    X = data.loc[:, selected_features].copy()
    y = data["target_encoded"].astype(int)
    _, X_test, _, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        stratify=y,
        random_state=42,
    )
    X_test_processed = preprocessor.transform(X_test)
    return X_test, X_test_processed, y_test.to_numpy()


def save_plot(fig: plt.Figure, path: Path) -> None:
    ensure_directory(str(path.parent))
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)
    print(f"Saved plot: {path}")


def plot_confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray, labels: np.ndarray, title: str, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 7), dpi=200)
    disp = ConfusionMatrixDisplay(confusion_matrix=confusion_matrix(y_true, y_pred, labels=labels), display_labels=[str(label) for label in labels])
    disp.plot(ax=ax, cmap="Blues", colorbar=False)
    ax.set_title(title)
    ax.set_xlabel("Predicted label")
    ax.set_ylabel("True label")
    save_plot(fig, path)


def plot_roc_curve(y_test: np.ndarray, y_prob: np.ndarray, classes: np.ndarray, title: str, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 7), dpi=200)
    if y_prob.ndim == 1 or y_prob.shape[1] == 2:
        scores = y_prob[:, 1] if y_prob.ndim > 1 else y_prob
        fpr, tpr, _ = roc_curve(y_test, scores)
        roc_auc = auc(fpr, tpr)
        ax.plot(fpr, tpr, label=f"ROC curve (AUC = {roc_auc:.3f})", lw=2)
    else:
        y_test_binarized = label_binarize(y_test, classes=classes)
        for idx, cls in enumerate(classes):
            fpr, tpr, _ = roc_curve(y_test_binarized[:, idx], y_prob[:, idx])
            class_auc = auc(fpr, tpr)
            ax.plot(fpr, tpr, label=f"Class {cls} (AUC = {class_auc:.3f})", lw=2)
    ax.plot([0, 1], [0, 1], color="navy", lw=1, linestyle="--")
    ax.set_xlabel("False positive rate")
    ax.set_ylabel("True positive rate")
    ax.set_title(title)
    ax.legend(loc="lower right", fontsize=10)
    save_plot(fig, path)


def plot_precision_recall_curve(y_test: np.ndarray, y_prob: np.ndarray, classes: np.ndarray, title: str, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 7), dpi=200)
    if y_prob.ndim == 1 or y_prob.shape[1] == 2:
        scores = y_prob[:, 1] if y_prob.ndim > 1 else y_prob
        precision, recall, _ = precision_recall_curve(y_test, scores)
        average_precision = average_precision_score(y_test, scores)
        ax.plot(recall, precision, label=f"AP = {average_precision:.3f}", lw=2)
    else:
        y_test_binarized = label_binarize(y_test, classes=classes)
        for idx, cls in enumerate(classes):
            precision, recall, _ = precision_recall_curve(y_test_binarized[:, idx], y_prob[:, idx])
            average_precision = average_precision_score(y_test_binarized[:, idx], y_prob[:, idx])
            ax.plot(recall, precision, label=f"Class {cls} (AP = {average_precision:.3f})", lw=2)
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_title(title)
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.legend(loc="lower left", fontsize=10)
    save_plot(fig, path)


def plot_calibration_curve(y_test: np.ndarray, y_prob: np.ndarray, classes: np.ndarray, title: str, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 7), dpi=200)
    if y_prob.ndim == 1 or y_prob.shape[1] == 2:
        prob_pos = y_prob[:, 1] if y_prob.ndim > 1 else y_prob
        fraction_of_positives, mean_predicted_value = calibration_curve(y_test, prob_pos, n_bins=10, strategy="uniform")
        ax.plot(mean_predicted_value, fraction_of_positives, "s-", label="Calibration", lw=2)
    else:
        y_test_binarized = label_binarize(y_test, classes=classes)
        for idx, cls in enumerate(classes):
            prob_pos = y_prob[:, idx]
            fraction_of_positives, mean_predicted_value = calibration_curve(y_test_binarized[:, idx], prob_pos, n_bins=10, strategy="uniform")
            ax.plot(mean_predicted_value, fraction_of_positives, "o-", label=f"Class {cls}", lw=2)
    ax.plot([0, 1], [0, 1], "k--", label="Perfect calibration")
    ax.set_xlabel("Mean predicted probability")
    ax.set_ylabel("Fraction of positives")
    ax.set_title(title)
    ax.legend(loc="upper left", fontsize=10)
    save_plot(fig, path)


def evaluate_model(config: dict) -> None:
    model = load_pickle(str(config["model_path"]))
    preprocessor = load_pickle(str(config["preprocessor_path"]))
    data = globals()[config["load_data"]](Path(config["data_path"]))
    X_test, X_test_processed, y_test = prepare_test_data(data, preprocessor)
    y_pred = model.predict(X_test_processed)
    y_prob = model.predict_proba(X_test_processed)
    classes = np.asarray(model.classes_)

    plot_confusion_matrix(
        y_test,
        y_pred,
        labels=classes,
        title=f"{config['name'].capitalize()} Model Confusion Matrix",
        path=PLOTS_DIR / f"{config['plot_prefix']}_confusion_matrix.png",
    )
    plot_roc_curve(
        y_test,
        y_prob,
        classes=classes,
        title=f"{config['name'].capitalize()} Model ROC Curve",
        path=PLOTS_DIR / f"{config['plot_prefix']}_roc_curve.png",
    )
    plot_precision_recall_curve(
        y_test,
        y_prob,
        classes=classes,
        title=f"{config['name'].capitalize()} Model Precision-Recall Curve",
        path=PLOTS_DIR / f"{config['plot_prefix']}_precision_recall.png",
    )
    plot_calibration_curve(
        y_test,
        y_prob,
        classes=classes,
        title=f"{config['name'].capitalize()} Model Calibration Curve",
        path=PLOTS_DIR / f"{config['plot_prefix']}_calibration_curve.png",
    )

    print(f"Evaluation completed for {config['name']} model.")


def main() -> None:
    for config in MODEL_CONFIGS:
        print(f"\nGenerating plots for {config['name']} model...")
        evaluate_model(config)
    print(f"\nAll evaluation plots saved under: {PLOTS_DIR}")


if __name__ == "__main__":
    main()
