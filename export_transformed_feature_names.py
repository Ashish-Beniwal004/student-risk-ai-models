from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import joblib
from sklearn.base import TransformerMixin

ROOT = Path(__file__).resolve().parent
MODEL_CONFIGS = [
    {
        "name": "dropout",
        "model_path": ROOT / "models" / "dropout_model.pkl",
        "preprocessor_path": ROOT / "models" / "dropout_preprocessor.pkl",
        "output_path": ROOT / "models" / "dropout_transformed_feature_names.json",
    },
    {
        "name": "wellbeing",
        "model_path": ROOT / "models" / "wellbeing_model.pkl",
        "preprocessor_path": ROOT / "models" / "wellbeing_preprocessor.pkl",
        "output_path": ROOT / "models" / "wellbeing_transformed_feature_names.json",
    },
    {
        "name": "depression",
        "model_path": ROOT / "models" / "depression_model.pkl",
        "preprocessor_path": ROOT / "models" / "depression_preprocessor.pkl",
        "output_path": ROOT / "models" / "depression_transformed_feature_names.json",
    },
]


def get_transformed_feature_names(preprocessor: Any) -> List[str]:
    if hasattr(preprocessor, "get_feature_names_out"):
        try:
            return list(preprocessor.get_feature_names_out())
        except TypeError:
            if hasattr(preprocessor, "feature_names_in_"):
                try:
                    return list(preprocessor.get_feature_names_out(preprocessor.feature_names_in_))
                except Exception as exc:
                    raise RuntimeError(
                        "Failed to compute transformed feature names from preprocessor with feature_names_in_."
                    ) from exc
            raise
    if hasattr(preprocessor, "feature_names_out_"):
        return list(preprocessor.feature_names_out_)
    raise RuntimeError("Preprocessor does not support get_feature_names_out or feature_names_out_.")


def save_json(data: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)


def load_model(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"Missing model file: {path}")
    return joblib.load(path)


def main() -> None:
    for cfg in MODEL_CONFIGS:
        name = cfg["name"]
        model_path = cfg["model_path"]
        preprocessor_path = cfg["preprocessor_path"]
        output_path = cfg["output_path"]

        print(f"\nProcessing {name}")
        model = load_model(model_path)
        preprocessor = load_model(preprocessor_path)

        transformed_feature_names = get_transformed_feature_names(preprocessor)
        save_json(transformed_feature_names, output_path)

        feature_importances = getattr(model, "feature_importances_", None)
        if feature_importances is None:
            print(f"  WARNING: model {name} has no feature_importances_.")
        else:
            print(f"  Original feature count: {len(getattr(preprocessor, 'feature_names_in_', []))}")
            print(f"  Transformed feature count: {len(transformed_feature_names)}")
            print(f"  feature_importances_ count: {len(feature_importances)}")
            if len(transformed_feature_names) != len(feature_importances):
                print("  MISMATCH: transformed feature count does not equal model.feature_importances_ length")
                print("    This typically happens when the fitted preprocessor expands categorical features via OneHotEncoder.")
            else:
                print("  Validation OK: transformed feature count matches feature_importances_.")
        print(f"  Output file location: {output_path}")


if __name__ == "__main__":
    main()
