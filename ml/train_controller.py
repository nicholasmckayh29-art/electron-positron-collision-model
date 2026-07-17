"""Train a first-pass quantum controller model from flattened telemetry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    r2_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

try:
    import mlflow
    import mlflow.sklearn
except ImportError:  # pragma: no cover - Azure/local installs may omit mlflow early on.
    mlflow = None


DEFAULT_DATA = Path("data/quantum_databank/controller_training.csv")
DEFAULT_MODEL_DIR = Path("outputs/quantum_controller_model")
DEFAULT_TARGET = "final_error_abs"
FEATURE_SETS = {"pre_run", "first_iteration", "full"}


def _is_classifier_target(target: str, series: pd.Series) -> bool:
    if target == "converged":
        return True
    return series.dropna().isin([0, 1, True, False]).all()


def _split_columns(
    frame: pd.DataFrame,
    target: str,
    feature_set: str,
) -> tuple[list[str], list[str]]:
    excluded = {
        target,
        "saved_at_utc",
        "runtime_job_id",
        "job_id",
        "final_error",
        "final_error_abs",
        "final_error_corrected",
        "final_error_abs_corrected",
        "converged",
        "stopping_reason",
    }

    # The default controller should make decisions before the quantum job has
    # produced an estimate. Keep run outcomes out unless an explicit later
    # horizon is requested.
    outcome_columns = {
        "estimate",
        "standard_error",
        "good_counts",
        "discretization_error",
        "quantum_vs_exact",
        "quantum_vs_binned",
        "quantum_vs_exact_sigma",
        "within_2sigma_of_exact",
        "first_iteration_error_abs",
        "best_iteration_error_abs",
        "mean_iteration_error_abs",
        "last_iteration_error_abs",
        "error_improvement_abs",
        "max_iteration_shots",
        "total_iteration_shots",
        "iterations_run",
        "distinct_bins_observed",
    }
    first_iteration_allowed = {
        "estimate",
        "standard_error",
        "good_counts",
        "first_iteration_error_abs",
    }
    if feature_set == "pre_run":
        excluded.update(outcome_columns)
    elif feature_set == "first_iteration":
        excluded.update(outcome_columns - first_iteration_allowed)

    features = [col for col in frame.columns if col not in excluded]
    categorical = [
        col
        for col in features
        if frame[col].dtype == "object" or str(frame[col].dtype) == "bool"
    ]
    numeric = [col for col in features if col not in categorical]
    return numeric, categorical


def _make_preprocessor(numeric: list[str], categorical: list[str]) -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("num", SimpleImputer(strategy="median"), numeric),
            (
                "cat",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical,
            ),
        ],
        remainder="drop",
    )


def _regression_metrics(y_test: pd.Series, preds: Any) -> dict[str, float]:
    return {
        "mae": float(mean_absolute_error(y_test, preds)),
        "r2": float(r2_score(y_test, preds)) if len(y_test) > 1 else 0.0,
    }


def _classification_metrics(y_test: pd.Series, preds: Any, probabilities: Any) -> dict[str, float]:
    metrics = {
        "accuracy": float(accuracy_score(y_test, preds)),
        "f1": float(f1_score(y_test, preds, zero_division=0)),
    }
    if probabilities is not None and len(set(y_test)) > 1:
        metrics["roc_auc"] = float(roc_auc_score(y_test, probabilities))
    return metrics


def train(
    data_path: Path,
    target: str,
    model_dir: Path,
    n_estimators: int,
    max_depth: int | None,
    min_samples_leaf: int,
    test_size: float,
    random_state: int,
    registered_model_name: str | None,
    feature_set: str,
) -> dict[str, Any]:
    if feature_set not in FEATURE_SETS:
        raise ValueError(f"feature_set must be one of {sorted(FEATURE_SETS)}")

    frame = pd.read_csv(data_path)
    if target not in frame.columns:
        raise ValueError(f"Target '{target}' not found. Columns: {list(frame.columns)}")

    frame = frame.dropna(subset=[target])
    if len(frame) < 3:
        raise ValueError(
            f"Need at least 3 training rows after filtering target '{target}', found {len(frame)}"
        )

    y = frame[target]
    is_classifier = _is_classifier_target(target, y)
    if is_classifier:
        y = y.astype(int)

    numeric, categorical = _split_columns(frame, target, feature_set)
    X = frame[numeric + categorical]
    stratify = y if is_classifier and y.nunique() > 1 and len(frame) >= 10 else None
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=stratify,
    )

    estimator: Any
    if is_classifier:
        estimator = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_leaf=min_samples_leaf,
            random_state=random_state,
            n_jobs=-1,
            class_weight="balanced",
        )
    else:
        estimator = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_leaf=min_samples_leaf,
            random_state=random_state,
            n_jobs=-1,
        )

    pipeline = Pipeline(
        steps=[
            ("preprocess", _make_preprocessor(numeric, categorical)),
            ("model", estimator),
        ]
    )

    if mlflow:
        mlflow.sklearn.autolog(log_models=False)

    pipeline.fit(X_train, y_train)
    preds = pipeline.predict(X_test)

    if is_classifier:
        probabilities = None
        if hasattr(pipeline, "predict_proba"):
            probabilities = pipeline.predict_proba(X_test)[:, 1]
        metrics = _classification_metrics(y_test, preds, probabilities)
    else:
        metrics = _regression_metrics(y_test, preds)

    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / "model.joblib"
    metrics_path = model_dir / "metrics.json"
    metadata_path = model_dir / "metadata.json"

    joblib.dump(pipeline, model_path)
    metadata = {
        "target": target,
        "task": "classification" if is_classifier else "regression",
        "feature_set": feature_set,
        "rows": int(len(frame)),
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "numeric_features": numeric,
        "categorical_features": categorical,
        "model_path": str(model_path),
    }
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    if mlflow:
        for key, value in metrics.items():
            mlflow.log_metric(key, value)
        mlflow.log_params(
            {
                "target": target,
                "task": metadata["task"],
                "feature_set": feature_set,
                "n_estimators": n_estimators,
                "max_depth": max_depth or "none",
                "min_samples_leaf": min_samples_leaf,
                "rows": len(frame),
            }
        )
        mlflow.log_artifact(str(metrics_path))
        mlflow.log_artifact(str(metadata_path))
        mlflow.sklearn.log_model(
            sk_model=pipeline,
            artifact_path="model",
            registered_model_name=registered_model_name,
        )

    return {"metrics": metrics, "metadata": metadata}


def main() -> int:
    parser = argparse.ArgumentParser(description="Train quantum controller model")
    parser.add_argument("--data", default=str(DEFAULT_DATA), help="Flattened training CSV")
    parser.add_argument("--target", default=DEFAULT_TARGET)
    parser.add_argument("--model-dir", default=str(DEFAULT_MODEL_DIR))
    parser.add_argument("--n-estimators", type=int, default=300)
    parser.add_argument("--max-depth", type=int, default=0, help="0 means no limit")
    parser.add_argument("--min-samples-leaf", type=int, default=1)
    parser.add_argument("--test-size", type=float, default=0.25)
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--registered-model-name", default=None)
    parser.add_argument(
        "--feature-set",
        choices=sorted(FEATURE_SETS),
        default="pre_run",
        help="Prediction horizon: pre_run avoids outcome leakage.",
    )
    args = parser.parse_args()

    result = train(
        data_path=Path(args.data),
        target=args.target,
        model_dir=Path(args.model_dir),
        n_estimators=args.n_estimators,
        max_depth=args.max_depth or None,
        min_samples_leaf=args.min_samples_leaf,
        test_size=args.test_size,
        random_state=args.random_state,
        registered_model_name=args.registered_model_name,
        feature_set=args.feature_set,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
