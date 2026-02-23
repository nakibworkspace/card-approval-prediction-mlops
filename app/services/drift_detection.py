"""
Drift Detection Service using Evidently AI

Monitors data drift and model performance degradation in production.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import pandas as pd
from evidently import ColumnMapping
from evidently.metric_preset import DataDriftPreset, DataQualityPreset
from evidently.report import Report
from loguru import logger


class DriftDetectionService:
    """Service for detecting data and model drift"""

    def __init__(
        self,
        reference_data_path: Optional[str] = None,
        reports_dir: str = "reports/drift",
    ):
        """
        Initialize drift detection service

        Args:
            reference_data_path: Path to reference dataset (training data)
            reports_dir: Directory to save drift reports
        """
        self.reference_data_path = reference_data_path
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # Load reference data if provided
        self.reference_data = None
        if reference_data_path and Path(reference_data_path).exists():
            self.reference_data = pd.read_csv(reference_data_path)
            logger.info(f"Loaded reference data: {self.reference_data.shape}")

    def detect_data_drift(
        self,
        current_data: pd.DataFrame,
        column_mapping: Optional[ColumnMapping] = None,
    ) -> Dict:
        """
        Detect data drift between reference and current data

        Args:
            current_data: Current production data
            column_mapping: Evidently column mapping configuration

        Returns:
            Dictionary with drift detection results
        """
        if self.reference_data is None:
            logger.warning("No reference data available for drift detection")
            return {"error": "No reference data available"}

        try:
            # Create drift report
            report = Report(metrics=[DataDriftPreset(), DataQualityPreset()])

            report.run(
                reference_data=self.reference_data,
                current_data=current_data,
                column_mapping=column_mapping,
            )

            # Save report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = self.reports_dir / f"drift_report_{timestamp}.html"
            report.save_html(str(report_path))

            # Extract metrics
            report_dict = report.as_dict()
            drift_metrics = self._extract_drift_metrics(report_dict)

            # Save metrics as JSON
            metrics_path = self.reports_dir / f"drift_metrics_{timestamp}.json"
            with open(metrics_path, "w") as f:
                json.dump(drift_metrics, f, indent=2)

            logger.info(f"Drift report saved: {report_path}")
            logger.info(f"Drift metrics: {drift_metrics}")

            return drift_metrics

        except Exception as e:
            logger.error(f"Error detecting drift: {e}")
            return {"error": str(e)}

    def _extract_drift_metrics(self, report_dict: Dict) -> Dict:
        """Extract key metrics from Evidently report"""
        try:
            metrics = report_dict.get("metrics", [])

            # Find data drift metrics
            drift_share = 0
            drifted_features = []

            for metric in metrics:
                if metric.get("metric") == "DatasetDriftMetric":
                    result = metric.get("result", {})
                    drift_share = result.get("drift_share", 0)
                    drifted_features = [
                        col
                        for col, info in result.get("drift_by_columns", {}).items()
                        if info.get("drift_detected", False)
                    ]
                    break

            return {
                "timestamp": datetime.now().isoformat(),
                "drift_detected": drift_share > 0,
                "drift_share": drift_share,
                "drifted_features": drifted_features,
                "num_drifted_features": len(drifted_features),
            }

        except Exception as e:
            logger.error(f"Error extracting drift metrics: {e}")
            return {"error": str(e)}

    def check_prediction_drift(
        self,
        predictions: pd.DataFrame,
        threshold: float = 0.3,
    ) -> Dict:
        """
        Check if prediction distribution has drifted

        Args:
            predictions: DataFrame with prediction results
            threshold: Drift threshold (0-1)

        Returns:
            Dictionary with drift status
        """
        try:
            # Calculate prediction statistics
            approval_rate = predictions["prediction"].mean()
            avg_confidence = predictions["probability"].mean()

            # Load historical statistics if available
            stats_path = self.reports_dir / "prediction_stats.json"
            if stats_path.exists():
                with open(stats_path, "r") as f:
                    historical_stats = json.load(f)

                # Compare with historical
                approval_drift = abs(approval_rate - historical_stats.get("approval_rate", approval_rate))
                confidence_drift = abs(avg_confidence - historical_stats.get("avg_confidence", avg_confidence))

                drift_detected = approval_drift > threshold or confidence_drift > threshold

                return {
                    "timestamp": datetime.now().isoformat(),
                    "drift_detected": drift_detected,
                    "current_approval_rate": float(approval_rate),
                    "historical_approval_rate": historical_stats.get("approval_rate"),
                    "approval_drift": float(approval_drift),
                    "current_confidence": float(avg_confidence),
                    "historical_confidence": historical_stats.get("avg_confidence"),
                    "confidence_drift": float(confidence_drift),
                }

            # Save current statistics as baseline
            current_stats = {
                "approval_rate": float(approval_rate),
                "avg_confidence": float(avg_confidence),
                "timestamp": datetime.now().isoformat(),
            }

            with open(stats_path, "w") as f:
                json.dump(current_stats, f, indent=2)

            return {
                "timestamp": datetime.now().isoformat(),
                "drift_detected": False,
                "message": "Baseline statistics saved",
                "approval_rate": float(approval_rate),
                "avg_confidence": float(avg_confidence),
            }

        except Exception as e:
            logger.error(f"Error checking prediction drift: {e}")
            return {"error": str(e)}


# Singleton instance
_drift_service: Optional[DriftDetectionService] = None


def get_drift_service() -> DriftDetectionService:
    """Get or create drift detection service instance"""
    global _drift_service
    if _drift_service is None:
        _drift_service = DriftDetectionService(reference_data_path="training/data/processed/X_train.csv")
    return _drift_service
