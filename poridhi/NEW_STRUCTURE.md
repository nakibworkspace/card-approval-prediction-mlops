# New Lab Structure - Updated Flow

## Overview

The labs have been restructured for better learning flow and efficiency. Labs 1 and 2 from the original plan have been merged, and a new Lab 2 focuses on data versioning.

## New Lab Sequence

### ✅ Lab 01: Model Development & MLflow Tracking (5-6h)
**File:** `lab-01-model-development-mlflow-tracking.md`

**Content:**
- Part A: Model Development (Chapters 1-3)
  - EDA and data preprocessing
  - Class imbalance handling with SMOTE
  - Model training (Logistic Regression, XGBoost, Random Forest)
  
- Part B: MLflow Experiment Tracking (Chapters 4-9)
  - MLflow setup and configuration
  - Instrumented training with automatic logging
  - Experiment comparison
  - Model Registry and lifecycle management
  - Loading models from registry
  - Hyperparameter tuning

**Key Change:** Merged original Lab 01 + Lab 02 for natural workflow

---

### ✅ Lab 02: Data Versioning with DVC & S3 (2-3h)
**File:** `lab-02-data-versioning-dvc-s3.md`

**Content:**
- Infrastructure as Code with Pulumi
- S3 bucket creation for data storage
- DVC initialization and configuration
- Tracking datasets with DVC
- Pushing/pulling data from S3
- Data versioning workflow

**Key Change:** NEW lab focusing on data versioning (not in original structure)

---

### 🔄 Lab 03: MLflow + S3 Integration (2-3h)
**File:** `lab-03-mlflow-s3-integration.md` (TO BE CREATED)

**Content:**
- Configure MLflow to use S3 for artifacts
- Update training pipeline to log to S3
- Model artifact storage in cloud
- Loading models from S3
- Team collaboration with cloud-based MLflow

**Key Change:** Split from original Lab 03, focuses only on MLflow+S3

---

### 🔄 Lab 04: The Prediction API (FastAPI) & Docker Hub (3-4h)
**File:** Rename `lab-04-prediction-api-fastapi-docker.md` (EXISTING)

**Content:** (No changes to content)
- FastAPI application development
- Input validation with Pydantic
- Model loading from S3
- Docker containerization
- Docker Hub deployment

**Key Change:** Renumbered from Lab 04 to Lab 04 (no change)

---

### 🔄 Lab 05: CI/CD & Security (GitHub Actions) (2-3h)
**File:** Rename `lab-05-cicd-security-github-actions.md` (EXISTING)

**Content:** (No changes to content)
- GitHub Actions workflows
- CodeQL security scanning
- Automated Docker build and push
- AWS App Runner deployment
- Continuous deployment pipeline

**Key Change:** Renumbered from Lab 05 to Lab 05 (no change)

---

### 🔄 Lab 06: Observability (Prometheus & Grafana) (3-4h)
**File:** Rename `lab-06-observability-prometheus-grafana.md` (EXISTING)

**Content:** (No changes to content)
- Prometheus metrics instrumentation
- Grafana dashboard creation
- System health monitoring
- Model performance tracking
- Data drift detection with Evidently AI

**Key Change:** Renumbered from Lab 06 to Lab 06 (no change)

---

## Comparison: Old vs New Structure

| Old Structure | New Structure | Change |
|---------------|---------------|--------|
| Lab 01: Exploration & Model | Lab 01: Model Development & MLflow | **MERGED** |
| Lab 02: MLflow Tracking | ↑ Merged into Lab 01 | **MERGED** |
| Lab 03: Pulumi & S3 | Lab 02: DVC & S3 (data) | **SPLIT** |
| - | Lab 03: MLflow & S3 (models) | **NEW** |
| Lab 04: FastAPI & Docker | Lab 04: FastAPI & Docker | Same |
| Lab 05: CI/CD | Lab 05: CI/CD | Same |
| Lab 06: Monitoring | Lab 06: Monitoring | Same |

## Benefits of New Structure

1. **Natural Workflow:** Train models and track experiments in one session
2. **Clear Separation:** Data versioning (Lab 02) vs Model artifacts (Lab 03)
3. **Better Learning:** See MLflow value immediately while training pain is fresh
4. **Reduced Context Switching:** No need to revisit training code in separate lab
5. **Still 6 Labs:** Maintains original lab count with better organization

## Total Time

- Lab 01: 5-6 hours
- Lab 02: 2-3 hours
- Lab 03: 2-3 hours
- Lab 04: 3-4 hours
- Lab 05: 2-3 hours
- Lab 06: 3-4 hours

**Total:** 17-23 hours (slightly more due to DVC addition, but better organized)

## Files Status

### ✅ Completed
- `lab-01-model-development-mlflow-tracking.md` - NEW merged lab
- `lab-02-data-versioning-dvc-s3.md` - NEW DVC lab

### 📝 To Be Created
- `lab-03-mlflow-s3-integration.md` - Extract from old Lab 03

### 🔄 To Be Renamed (no content changes)
- `lab-04-prediction-api-fastapi-docker.md` - Already correct number
- `lab-05-cicd-security-github-actions.md` - Already correct number
- `lab-06-observability-prometheus-grafana.md` - Already correct number

### 📦 Archived
- `archived-lab-01-exploration-winning-model.md` - Original Lab 01
- `archived-lab-02-experiment-tracking-mlflow.md` - Original Lab 02
- `poridhi/lab-03-infrastructure-as-code-pulumi-s3.md` - Will be split

## Next Steps

1. ✅ Create Lab 03 (MLflow + S3 Integration)
2. ✅ Update README.md with new structure
3. ✅ Update INDEX.md with new lab sequence
4. ✅ Update QUICK_REFERENCE.md
5. ✅ Update COMPLETION_GUIDE.md
6. ✅ Archive old Lab 03 (Pulumi & S3)

## Learning Path

```
Lab 01: Model Development + MLflow (Local)
    ↓
Lab 02: Data Versioning (DVC + S3)
    ↓
Lab 03: Model Artifacts (MLflow + S3)
    ↓
Lab 04: API Development (FastAPI + Docker)
    ↓
Lab 05: CI/CD Pipeline (GitHub Actions)
    ↓
Lab 06: Monitoring (Prometheus + Grafana)
```

This creates a logical progression from local development to full cloud deployment with proper versioning for both data and models.
