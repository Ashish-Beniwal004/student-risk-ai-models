from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

import joblib
import pandas as pd


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    return logger


def ensure_directory(path: str) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


def save_json(data: Any, path: str) -> None:
    ensure_directory(str(Path(path).parent))
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)


def save_pickle(path: str, obj: Any) -> None:
    ensure_directory(str(Path(path).parent))
    joblib.dump(obj, path)


def load_pickle(path: str) -> Any:
    return joblib.load(path)


def save_feature_importance_csv(feature_names: List[str], importances: List[float], path: str) -> None:
    ensure_directory(str(Path(path).parent))
    df = pd.DataFrame({"feature": feature_names, "importance": importances})
    df = df.sort_values(by="importance", ascending=False)
    df.to_csv(path, index=False)
