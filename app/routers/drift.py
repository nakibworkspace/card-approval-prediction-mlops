"""
Drift Detection API Endpoints
"""

from typing import Dict

import pandas as pd
from fastapi import APIRouter, HTTPException
from loguru import logger

from app.services.drift_detection import get_drift_service

router = APIRouter(prefix="/api/v1/drift", tags=["Drift Detection"])


@router.post("/check")
async def check_drift(data: Dict) -> Dict:
    """
    Check for data drift in incoming prediction requests

    Args:
        data: Dictionary with prediction features

    Returns:
        Drift detection results
    """
    try:
        drift_service = get_drift_service()

        # Convert to DataFrame
        current_data = pd.DataFrame([data])

        # Detect drift
        drift_results = drift_service.detect_data_drift(current_data)

        return {
            "status": "success",
            "drift_results": drift_results,
        }

    except Exception as e:
        logger.error(f"Error checking drift: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports")
async def list_drift_reports() -> Dict:
    """
    List available drift detection reports

    Returns:
        List of drift report files
    """
    try:
        drift_service = get_drift_service()
        reports_dir = drift_service.reports_dir

        if not reports_dir.exists():
            return {"reports": []}

        reports = [
            {
                "filename": f.name,
                "timestamp": f.stat().st_mtime,
                "size": f.stat().st_size,
            }
            for f in reports_dir.glob("drift_report_*.html")
        ]

        # Sort by timestamp (newest first)
        reports.sort(key=lambda x: x["timestamp"], reverse=True)

        return {"reports": reports, "count": len(reports)}

    except Exception as e:
        logger.error(f"Error listing drift reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def drift_status() -> Dict:
    """
    Get current drift detection status

    Returns:
        Current drift status and statistics
    """
    try:
        drift_service = get_drift_service()

        # Check if reference data is loaded
        has_reference = drift_service.reference_data is not None

        # Get latest metrics if available
        metrics_files = list(drift_service.reports_dir.glob("drift_metrics_*.json"))

        if metrics_files:
            import json

            latest_metrics_file = max(metrics_files, key=lambda f: f.stat().st_mtime)
            with open(latest_metrics_file, "r") as f:
                latest_metrics = json.load(f)
        else:
            latest_metrics = None

        return {
            "status": "active" if has_reference else "inactive",
            "has_reference_data": has_reference,
            "reference_data_shape": (drift_service.reference_data.shape if has_reference else None),
            "latest_metrics": latest_metrics,
            "reports_directory": str(drift_service.reports_dir),
        }

    except Exception as e:
        logger.error(f"Error getting drift status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
