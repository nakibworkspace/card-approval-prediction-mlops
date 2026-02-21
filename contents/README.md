# Lab Contents Directory

This directory contains the complete file structure and code for each lab in the MLOps course.

## Directory Structure

Each lab directory is **cumulative** - it includes everything from previous labs plus new content for that lab.

```
contents/
├── lab01/    # Lab 01: Airflow & MLflow
├── lab02/    # Lab 01 + Lab 02: DVC & Pulumi
├── lab03/    # Lab 01-02 + Lab 03: MLflow S3
├── lab04/    # Lab 01-03 + Lab 04: FastAPI & Docker
├── lab05/    # Lab 01-04 + Lab 05: CI/CD
├── lab06/    # Lab 01-05 + Lab 06: Monitoring
└── lab07/    # Lab 01-06 (Complete System)
```

## Lab Progression

### Lab 01: Automated ML Pipeline with Airflow & MLflow
**What's included:**
- Airflow DAG definitions
- MLflow tracking setup
- Training pipeline (EDA, preprocessing, model training)
- Model comparison (Logistic Regression, Random Forest, XGBoost)

**Key files:**
- `dags/ml_training_pipeline.py`
- `training/scripts/airflow_tasks.py`
- `training/src/config/mlflow_config.py`

---

### Lab 02: Data Versioning with DVC & S3
**What's included:**
- Everything from Lab 01
- Pulumi Infrastructure as Code
- DVC data versioning
- S3 bucket creation and configuration

**New files:**
- `pulumi/__main__.py`
- `.dvc/config`
- `.dvcignore`

---

### Lab 03: MLflow + S3 Integration
**What's included:**
- Everything from Labs 01-02
- MLflow S3 artifact storage
- Cloud-based model registry
- Team collaboration setup

**New files:**
- `training/scripts/run_training_s3.py`
- `training/scripts/load_model_s3.py`
- `training/src/config/mlflow_s3_config.py`
- `.env.example`

---

### Lab 04: The Prediction API (FastAPI) & Docker Hub
**What's included:**
- Everything from Labs 01-03
- FastAPI prediction service
- Pydantic input validation
- Docker containerization
- Model serving from S3

**New files:**
- `app/main.py`
- `app/routers/predict.py`
- `app/services/model_service.py`
- `app/schemas/prediction.py`
- `Dockerfile`
- `test_payload.json`

---

### Lab 05: CI/CD & Security (GitHub Actions)
**What's included:**
- Everything from Labs 01-04
- GitHub Actions workflows
- Automated testing and linting
- Security scanning (CodeQL, Trivy)
- AWS App Runner deployment

**New files:**
- `.github/workflows/ci.yml`
- `.github/workflows/cd.yml`
- `.gitignore`
- Updated `pulumi/__main__.py` (with App Runner)

---

### Lab 06: Observability (Prometheus & Grafana)
**What's included:**
- Everything from Labs 01-05
- Prometheus metrics instrumentation
- Grafana dashboards
- Data drift detection
- Alerting rules

**New files:**
- `app/core/metrics.py`
- `app/services/drift_detection.py`
- `monitoring/prometheus/prometheus.yml`
- `monitoring/prometheus/alerts.yml`
- `monitoring/grafana/provisioning/`
- `docker-compose.monitoring.yml`

---

### Lab 07: Complete MLOps System
**What's included:**
- Everything from Labs 01-06
- Complete, production-ready system
- Full integration of all components
- Comprehensive documentation

This is the final, complete system with all features integrated.

---

## How to Use These Labs

### Option 1: Start Fresh with Each Lab
Copy the specific lab directory you're working on:
```bash
cp -r contents/lab01 my-project
cd my-project
# Follow the lab guide
```

### Option 2: Progressive Build
Start with Lab 01 and progressively add features:
```bash
# Start with Lab 01
cp -r contents/lab01 my-project
cd my-project

# When ready for Lab 02, copy new files
cp -r contents/lab02/pulumi .
cp contents/lab02/.dvcignore .
# etc.
```

### Option 3: Jump to Any Lab
Each lab is self-contained with all previous content:
```bash
# Jump directly to Lab 04
cp -r contents/lab04 my-project
cd my-project
# You have everything from Labs 01-04
```

## Lab Guides

Detailed instructions for each lab are in the `poridhi/` directory:
- `poridhi/lab-01-model-development-mlflow-tracking.md`
- `poridhi/lab-02-infrastructure-as-code-pulumi-s3.md`
- `poridhi/lab-03-data-versioning-dvc-s3.md`
- `poridhi/lab-04-mlflow-s3-integration.md`
- `poridhi/lab-05-prediction-api-fastapi-docker.md`
- `poridhi/lab-06-cicd-security-github-actions.md`
- `poridhi/lab-07-observability-prometheus-grafana.md`

## Quick Reference

| Lab | Main Focus | Key Technologies | Time Estimate |
|-----|-----------|------------------|---------------|
| 01  | ML Pipeline | Airflow, MLflow | 6-8 hours |
| 02  | Data Versioning | DVC, Pulumi, S3 | 2-3 hours |
| 03  | Cloud ML | MLflow + S3 | 2-3 hours |
| 04  | API Service | FastAPI, Docker | 3-4 hours |
| 05  | CI/CD | GitHub Actions | 3-4 hours |
| 06  | Monitoring | Prometheus, Grafana | 3-4 hours |
| 07  | Integration | All components | 1-2 hours |

## Prerequisites

- Python 3.11+
- Docker and Docker Compose
- AWS account with credentials
- GitHub account
- Docker Hub account
- Basic understanding of ML, Python, and DevOps concepts

## Support

For issues or questions:
1. Check the lab-specific README in each directory
2. Review the detailed lab guide in `poridhi/`
3. Check troubleshooting sections in lab guides

## License

This educational content is provided for learning purposes.
