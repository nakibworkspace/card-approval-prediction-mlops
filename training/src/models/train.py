"""
Model Trainer - trains multiple models with MLflow tracking
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from loguru import logger
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from src.utils.model_configs import get_model_configs
from src.utils.resampling import Resampler

import mlflow


class ModelTrainer:
    """Train multiple ML models with MLflow experiment tracking."""

    # Metric name mapping from display names to internal keys
    METRIC_MAP = {
        "F1-Score": "f1_score",
        "Accuracy": "accuracy",
        "Precision": "precision",
        "Recall": "recall",
        "ROC-AUC": "roc_auc",
    }

    def __init__(
        self, tracking_uri: str = "http://127.0.0.1:5000", experiment_name: str = "credit_card_approval_model_training"
    ):
        self.tracking_uri = tracking_uri
        self.experiment_name = experiment_name

        mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_experiment(experiment_name)

        self.trained_models: Dict = {}
        self.results: List[Dict] = []
        self.best_model_name: Optional[str] = None
        self.best_score: Optional[float] = None
        self.best_model_run_id: Optional[str] = None

        logger.info(f"ModelTrainer initialized | MLflow: {tracking_uri} | Experiment: {experiment_name}")

    def _evaluate(self, model, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        """Evaluate a model and return metrics dict."""
        y_pred = model.predict(X)
        y_pred_proba = model.predict_proba(X)[:, 1] if hasattr(model, "predict_proba") else None

        metrics = {
            "accuracy": accuracy_score(y, y_pred),
            "precision": precision_score(y, y_pred, zero_division=0),
            "recall": recall_score(y, y_pred, zero_division=0),
            "f1_score": f1_score(y, y_pred, zero_division=0),
        }

        if y_pred_proba is not None:
            metrics["roc_auc"] = roc_auc_score(y, y_pred_proba)

        return metrics

    def _train_single_model(
        self,
        name: str,
        model_class,
        params: Dict,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_test: pd.DataFrame,
        y_test: pd.Series,
    ) -> Dict:
        """Train a single model with MLflow tracking."""
        logger.info(f"\n--- Training {name} ---")

        with mlflow.start_run(run_name=name) as run:
            run_id = run.info.run_id

            # Log parameters
            mlflow.log_param("model_name", name)
            for k, v in params.items():
                mlflow.log_param(k, v)

            # Train
            start = time.time()
            model = model_class(**params)
            model.fit(X_train, y_train)
            train_time = time.time() - start

            # Evaluate
            train_metrics = self._evaluate(model, X_train, y_train)
            test_metrics = self._evaluate(model, X_test, y_test)

            # Log metrics
            mlflow.log_metric("train_time_seconds", train_time)
            for metric_name, value in test_metrics.items():
                mlflow.log_metric(f"test_{metric_name}", value)
            for metric_name, value in train_metrics.items():
                mlflow.log_metric(f"train_{metric_name}", value)

            # Log model
            mlflow.sklearn.log_model(model, "model")

            logger.info(
                f"{name} | F1: {test_metrics['f1_score']:.4f} | Acc: {test_metrics['accuracy']:.4f} | "
                f"AUC: {test_metrics.get('roc_auc', 0):.4f} | Time: {train_time:.2f}s"
            )

        # Store results
        self.trained_models[name] = model

        result = {
            "Model": name,
            "Accuracy": test_metrics["accuracy"],
            "Precision": test_metrics["precision"],
            "Recall": test_metrics["recall"],
            "F1-Score": test_metrics["f1_score"],
            "ROC-AUC": test_metrics.get("roc_auc", 0),
            "Train Time (s)": round(train_time, 2),
            "Run ID": run_id,
        }

        return result

    def train_all_models(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        models: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Train all configured models.

        Args:
            X_train, y_train: Training data
            X_test, y_test: Test data
            models: Optional list of model names to train (defaults to all)

        Returns:
            DataFrame with comparison results
        """
        model_configs = get_model_configs(models=models)

        if not model_configs:
            raise ValueError("No model configurations found. Check config.yaml.")

        logger.info(f"Training {len(model_configs)} models: {list(model_configs.keys())}")

        self.results = []
        for name, config in model_configs.items():
            result = self._train_single_model(
                name=name,
                model_class=config["class"],
                params=config["params"],
                X_train=X_train,
                y_train=y_train,
                X_test=X_test,
                y_test=y_test,
            )
            self.results.append(result)

        results_df = pd.DataFrame(self.results)

        # Determine best model by F1-Score by default
        best_idx = results_df["F1-Score"].idxmax()
        self.best_model_name = results_df.loc[best_idx, "Model"]
        self.best_score = results_df.loc[best_idx, "F1-Score"]
        self.best_model_run_id = results_df.loc[best_idx, "Run ID"]

        logger.info(f"\nBest model: {self.best_model_name} (F1: {self.best_score:.4f})")

        return results_df

    def save_best_model(self, output_dir: str, metric: str = "F1-Score") -> Tuple[str, str]:
        """
        Save the best model to disk.

        Args:
            output_dir: Directory to save model
            metric: Metric to use for selecting best model

        Returns:
            Tuple of (model_path, metadata_path)
        """
        if not self.results:
            raise RuntimeError("No models trained yet. Call train_all_models first.")

        results_df = pd.DataFrame(self.results)

        # Resolve metric name
        col = metric if metric in results_df.columns else self.METRIC_MAP.get(metric, metric)
        if col not in results_df.columns:
            logger.warning(f"Metric '{metric}' not found, falling back to F1-Score")
            col = "F1-Score"

        best_idx = results_df[col].idxmax()
        self.best_model_name = results_df.loc[best_idx, "Model"]
        self.best_score = results_df.loc[best_idx, col]
        self.best_model_run_id = results_df.loc[best_idx, "Run ID"]

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save model
        model = self.trained_models[self.best_model_name]
        model_path = str(output_path / "best_model.pkl")
        joblib.dump(model, model_path)

        # Save metadata
        metadata = {
            "model_name": self.best_model_name,
            "best_metric": col,
            "best_score": float(self.best_score),
            "run_id": self.best_model_run_id,
            "saved_at": datetime.now().isoformat(),
        }
        metadata_path = str(output_path / "model_metadata.json")
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        return model_path, metadata_path

    def save_comparison_results(self, output_dir: str) -> str:
        """Save model comparison CSV."""
        if not self.results:
            raise RuntimeError("No models trained yet.")

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        csv_path = str(output_path / "model_comparison.csv")
        pd.DataFrame(self.results).to_csv(csv_path, index=False)
        return csv_path

    def create_training_summary(self, X_train: pd.DataFrame, X_test: pd.DataFrame, output_dir: str) -> str:
        """Create a text summary of the training run."""
        if not self.results:
            raise RuntimeError("No models trained yet.")

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        summary_path = str(output_path / "training_summary.txt")

        lines = [
            "=" * 60,
            "MODEL TRAINING SUMMARY",
            "=" * 60,
            f"Date: {datetime.now().isoformat()}",
            f"Training samples: {len(X_train)}",
            f"Test samples: {len(X_test)}",
            f"Features: {X_train.shape[1]}",
            f"Models trained: {len(self.results)}",
            "",
            "RESULTS:",
            "-" * 60,
        ]

        results_df = pd.DataFrame(self.results)
        lines.append(results_df.to_string(index=False))

        lines.extend(
            [
                "",
                "-" * 60,
                f"Best Model: {self.best_model_name}",
                f"Best Score: {self.best_score:.4f}",
                f"MLflow Run ID: {self.best_model_run_id}",
                "=" * 60,
            ]
        )

        with open(summary_path, "w") as f:
            f.write("\n".join(lines))

        return summary_path
