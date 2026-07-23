from __future__ import annotations

import numpy as np
import pandas as pd
import shap
import matplotlib.pyplot as plt
from sklearn.feature_selection import RFE
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.base import BaseEstimator
from typing import Any, Dict, List


def compute_classification_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: np.ndarray,
) -> Dict[str, Any]:
    metrics: Dict[str, Any] = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, average="macro", zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, average="macro", zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "classification_report": classification_report(y_true, y_pred, output_dict=True),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
    }
    if y_prob is not None:
        if y_prob.ndim == 1 or y_prob.shape[1] == 2:
            metrics["roc_auc"] = float(roc_auc_score(y_true, y_prob[:, 1] if y_prob.ndim > 1 else y_prob))
        else:
            metrics["roc_auc"] = float(roc_auc_score(y_true, y_prob, average="macro", multi_class="ovr"))
    return metrics


def select_features_rfe(
    estimator: BaseEstimator,
    X: pd.DataFrame,
    y: pd.Series,
    n_features: int = 15,
) -> List[str]:
    selector = RFE(estimator=estimator, n_features_to_select=min(n_features, X.shape[1]), step=1)
    selector = selector.fit(X.fillna(X.median()), y)
    return X.columns[selector.support_].tolist()


def get_transformed_feature_names(preprocessor: Any, original_features: List[str]) -> List[str]:
    try:
        return preprocessor.get_feature_names_out(original_features).tolist()
    except Exception:
        return original_features


def get_top_feature_importances(model: Any, feature_names: List[str], top_k: int = 15) -> pd.DataFrame:
    importances = getattr(model, "feature_importances_", None)
    if importances is None:
        raise AttributeError("Model does not expose feature_importances_.")
    df = pd.DataFrame(
        {"feature": feature_names, "importance": importances}
    ).sort_values(by="importance", ascending=False)
    return df.head(top_k)


def save_shap_summary(
    model: Any,
    X: Any,
    feature_names: List[str],
    path: str,
    sample_size: int = 5000,
) -> None:
    if hasattr(X, "shape") and X.shape[0] > sample_size:
        X_sample = X[:sample_size]
    else:
        X_sample = X
    explainer = shap.TreeExplainer(model)
    shap_values = explainer(X_sample)
    plt.figure(figsize=(10, 7))
    shap.summary_plot(shap_values, feature_names=feature_names, show=False)
    plt.tight_layout()
    plt.savefig(path, dpi=200)
    plt.close()
