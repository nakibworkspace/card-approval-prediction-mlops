# Complete File Purpose Documentation

This document explains the purpose of every file and folder in the project.

## 📁 Root Directory Files

### Configuration Files

| File | Purpose | Required |
|------|---------|----------|
| `config-aws.env` | AWS configuration template with credentials, S3 bucket, MLflow URI, Docker Hub settings | ✅ Yes |
| `config-example.env` | Legacy GCP configuration (kept for reference) | ⚠️ Optional |
| `.gitignore` | Specifies files/folders Git should ignore (secrets, data, models, cache) | ✅ Yes |
| `.dockerignore` | Specifies files/folders Docker should ignore when building images | ✅ Yes |
| `.dvcignore` | Specifies files/folders DVC should ignore for data versioning | ✅ Yes |
| `.flake8` | Flake8 linter configuration (line length, ignore rules) | ✅ Yes |
| `.pre-commit-config.yaml` | Pre-commit hooks configuration (Black, isort, Flake8) | ✅ Yes |

### Python Configuration

| File | Purpose | Required |
|------|---------|----------|
| `requirements.txt` | Python dependencies for the entire project (AWS SDK, MLflow, FastAPI, ML libraries) | ✅ Yes |
| `pyproject.toml` | Python project metadata and tool configurations (Black, isort, pytest) | ✅ Yes |

### Docker

| File | Purpose | Required |
|------|---------|----------|
| `Dockerfile` | Container definition for FastAPI API with AWS CLI, model, and dependencies | ✅ Yes |

### Documentation

| File | Purpose | Required |
|------|---------|----------|
| `README.md` | Main project documentation with architecture, setup, and usage | ✅ Yes |
| `README-AWS.md` | Detailed AWS-specific documentation and architecture | ✅ Yes |
| `QUICK_START_AWS.md` | 30-minute quick start guide for AWS deployment | ✅ Yes |
| `TRANSFORMATION_SUMMARY.md` | Detailed GCP to AWS transformation documentation | ℹ️ Reference |
| `MIGRATION_GUIDE.md` | Step-by-step guide for migrating from GCP to AWS | ℹ️ Reference |
| `PROJECT_TRANSFORMATION_COMPLETE.md` | Transformation completion summary | ℹ️ Reference |
| `DOCUMENTATION_INDEX.md` | Index of all documentation files | ℹ️ Reference |
| `FILE_PURPOSES.md` | This file - explains every file's purpose | ℹ️ Reference |
| `Lab-plannings.md` | Original lab planning requirements (6 labs) | ℹ️ Reference |
| `LICENSE` | MIT License for the project | ✅ Yes |

### Scripts

| File | Purpose | Required |
|------|---------|----------|
| `verify_transformation.sh` | Bash script to verify AWS transformation is complete | ⚠️ Optional |

---

## 📁 app/ - FastAPI Application

### Main Application

| File | Purpose | Required |
|------|---------|----------|
| `app/main.py` | FastAPI application entrypoint, router registration, middleware, lifespan events | ✅ Yes |

### Core Configuration

| File | Purpose | Required |
|------|---------|----------|
| `app/core/config.py` | Application settings (AWS credentials, MLflow URI, model config, tracing) | ✅ Yes |
| `app/core/logging.py` | Logging configuration with Loguru (file + console output) | ✅ Yes |
| `app/core/metrics.py` | Prometheus metrics (request count, duration, active requests) | ✅ Yes |
| `app/core/tracing.py` | OpenTelemetry distributed tracing setup | ✅ Yes |

### API Routers

| File | Purpose | Required |
|------|---------|----------|
| `app/routers/health.py` | Health check endpoints (`/health`, `/health/ready`, `/health/live`) | ✅ Yes |
| `app/routers/predict.py` | Prediction endpoints (`/api/v1/predict`, `/api/v1/model-info`) | ✅ Yes |
| `app/routers/drift.py` | Drift detection endpoints (`/api/v1/drift/*`) - NEW | ✅ Yes |

### Schemas (Pydantic Models)

| File | Purpose | Required |
|------|---------|----------|
| `app/schemas/health.py` | Health check response schemas | ✅ Yes |
| `app/schemas/prediction.py` | Prediction request/response schemas | ✅ Yes |

### Services (Business Logic)

| File | Purpose | Required |
|------|---------|----------|
| `app/services/model_service.py` | Model loading from MLflow/local, inference, caching | ✅ Yes |
| `app/services/preprocessing_service.py` | Feature preprocessing (scaling, encoding, PCA) | ✅ Yes |
| `app/services/drift_detection.py` | Evidently AI drift detection service - NEW | ✅ Yes |

### Utilities

| File | Purpose | Required |
|------|---------|----------|
| `app/utils/__init__.py` | Package initialization | ✅ Yes |
| `app/utils/gcs.py` | Cloud storage helpers (works with both GCS and S3) | ✅ Yes |
| `app/utils/mlflow_helpers.py` | MLflow utilities (model download, artifact management) | ✅ Yes |

---

## 📁 training/ - ML Training Pipeline

### Scripts (Training Automation)

| File | Purpose | Required |
|------|---------|----------|
| `training/scripts/download_data.py` | Download credit card dataset from Kaggle | ✅ Yes |
| `training/scripts/run_eda.py` | Run exploratory data analysis | ⚠️ Optional |
| `training/scripts/run_preprocessing.py` | Feature engineering and preprocessing pipeline | ✅ Yes |
| `training/scripts/run_training.py` | Train multiple models, log to MLflow, register best model | ✅ Yes |

### Source Code

| File | Purpose | Required |
|------|---------|----------|
| `training/src/__init__.py` | Package initialization | ✅ Yes |
| `training/src/config/config.yaml` | Training configuration (model hyperparameters, paths) | ✅ Yes |

#### Data Loading

| File | Purpose | Required |
|------|---------|----------|
| `training/src/data/__init__.py` | Package initialization | ✅ Yes |
| `training/src/data/data_loader.py` | Load and merge application + credit record data | ✅ Yes |

#### Feature Engineering

| File | Purpose | Required |
|------|---------|----------|
| `training/src/features/__init__.py` | Package initialization | ✅ Yes |
| `training/src/features/feature_engineering.py` | Feature creation, encoding, scaling, PCA | ✅ Yes |

#### Model Training

| File | Purpose | Required |
|------|---------|----------|
| `training/src/models/__init__.py` | Package initialization | ✅ Yes |
| `training/src/models/train.py` | Model training orchestration | ✅ Yes |
| `training/src/models/evaluate.py` | Model evaluation (F1, ROC-AUC, classification report) | ✅ Yes |

#### Utilities

| File | Purpose | Required |
|------|---------|----------|
| `training/src/utils/__init__.py` | Package initialization | ✅ Yes |
| `training/src/utils/dimensionality.py` | PCA and dimensionality reduction | ✅ Yes |
| `training/src/utils/encoders.py` | Label encoding, one-hot encoding | ✅ Yes |
| `training/src/utils/helpers.py` | General helper functions | ✅ Yes |
| `training/src/utils/logger.py` | Training logger setup | ✅ Yes |
| `training/src/utils/metrics.py` | Custom metrics calculation | ✅ Yes |
| `training/src/utils/mlflow_artifacts.py` | MLflow artifact logging | ✅ Yes |
| `training/src/utils/mlflow_registry.py` | MLflow model registry operations | ✅ Yes |
| `training/src/utils/model_configs.py` | Model hyperparameter configurations | ✅ Yes |
| `training/src/utils/plotting.py` | Visualization utilities | ✅ Yes |
| `training/src/utils/resampling.py` | SMOTE and class balancing | ✅ Yes |
| `training/src/utils/scalers.py` | Feature scaling utilities | ✅ Yes |

### Data Directories

| Directory | Purpose | Required |
|-----------|---------|----------|
| `training/data/raw/` | Raw Kaggle dataset (gitignored, DVC tracked) | ✅ Yes |
| `training/data/processed/` | Processed features, scalers, PCA (DVC tracked) | ✅ Yes |
| `training/notebooks/` | Jupyter notebooks for EDA | ⚠️ Optional |
| `training/preprocessors/` | Custom preprocessor classes | ⚠️ Optional |

---

## 📁 pulumi/ - Infrastructure as Code (NEW)

| File | Purpose | Required |
|------|---------|----------|
| `pulumi/__main__.py` | Pulumi program defining AWS resources (S3, App Runner, EC2, IAM, Security Groups) | ✅ Yes |
| `pulumi/Pulumi.yaml` | Pulumi project definition (name, runtime, description) | ✅ Yes |
| `pulumi/Pulumi.dev.yaml` | Development stack configuration | ✅ Yes |
| `pulumi/Pulumi.prod.yaml` | Production stack configuration | ✅ Yes |
| `pulumi/requirements.txt` | Pulumi dependencies (pulumi, pulumi-aws) | ✅ Yes |
| `pulumi/README.md` | Pulumi deployment documentation | ✅ Yes |

**What it deploys:**
- S3 bucket for DVC, MLflow artifacts, training data
- IAM roles for App Runner and EC2
- EC2 instance (t3.medium) with Prometheus, Grafana, Nginx
- Security groups for network access

---

## 📁 .github/workflows/ - CI/CD (NEW)

| File | Purpose | Required |
|------|---------|----------|
| `.github/workflows/ci.yml` | Continuous Integration pipeline (linting, CodeQL, tests, Docker build) | ✅ Yes |
| `.github/workflows/cd.yml` | Continuous Deployment pipeline (model eval, build, push, deploy to App Runner) | ✅ Yes |

**CI Pipeline includes:**
- Code quality (Black, isort, Flake8, Pylint)
- Security scanning (CodeQL, Bandit, Safety)
- Unit tests with coverage
- Docker build test

**CD Pipeline includes:**
- Model evaluation from MLflow
- Docker build with model
- Trivy security scan
- Push to Docker Hub
- Deploy to AWS App Runner

---

## 📁 .dvc/ - Data Version Control (NEW)

| File | Purpose | Required |
|------|---------|----------|
| `.dvc/config` | DVC configuration with S3 remote storage | ✅ Yes |
| `.dvc/.gitignore` | DVC internal files to ignore | ✅ Yes |

**Purpose:** Version control for datasets and models using S3 backend

---

## 📁 scripts/ - CI/CD Helper Scripts

| File | Purpose | Required |
|------|---------|----------|
| `scripts/__init__.py` | Package initialization | ✅ Yes |
| `scripts/download_model.py` | Download model from MLflow registry (used in CD pipeline) | ✅ Yes |
| `scripts/evaluate_model.py` | Evaluate model against F1 threshold (quality gate in CD) | ✅ Yes |

---

## 📁 tests/ - Unit Tests

| File | Purpose | Required |
|------|---------|----------|
| `tests/__init__.py` | Package initialization | ✅ Yes |
| `tests/conftest.py` | Pytest fixtures and configuration | ✅ Yes |
| `tests/test_api.py` | API integration tests | ✅ Yes |
| `tests/test_main.py` | Main application tests | ✅ Yes |
| `tests/test_core_*.py` | Core module tests (config, logging, metrics) | ✅ Yes |
| `tests/test_routers_*.py` | Router tests (health, predict) | ✅ Yes |
| `tests/test_schemas.py` | Pydantic schema tests | ✅ Yes |
| `tests/test_services_*.py` | Service tests (model, preprocessing) | ✅ Yes |
| `tests/test_utils_*.py` | Utility tests (GCS, MLflow helpers) | ✅ Yes |
| `tests/test_training_*.py` | Training pipeline tests | ✅ Yes |

---

## 📁 docs/ - Documentation

### AWS Documentation (NEW)

| File | Purpose | Required |
|------|---------|----------|
| `docs/00_Setup_Guide_AWS.md` | Comprehensive AWS setup guide | ✅ Yes |

### Original Documentation (Legacy - GCP)

| File | Purpose | Required |
|------|---------|----------|
| `docs/index.md` | Documentation index | ℹ️ Reference |
| `docs/00_Setup_Guide.md` | GCP setup guide | ℹ️ Reference |
| `docs/01_Helm_Deployment.md` | Kubernetes/Helm deployment | ℹ️ Reference |
| `docs/02_MLflow_Training.md` | Model training guide (still relevant) | ✅ Yes |
| `docs/03_CICD_Pipeline.md` | Jenkins CI/CD (legacy) | ℹ️ Reference |
| `docs/04_NGINX.md` | NGINX configuration (legacy) | ℹ️ Reference |
| `docs/05_Monitoring.md` | Monitoring guide (still relevant) | ✅ Yes |

---

## 📁 models/ - Saved Models

| Directory | Purpose | Required |
|-----------|---------|----------|
| `models/` | Saved model files embedded in Docker image | ✅ Yes |
| `models/.gitkeep` | Keep empty directory in Git | ✅ Yes |

**Note:** Models are downloaded from MLflow during CI/CD and embedded in Docker image

---

## 📁 img/ - Documentation Images

| Directory | Purpose | Required |
|-----------|---------|----------|
| `img/` | Screenshots and diagrams for documentation | ⚠️ Optional |

---

## Missing or Optional Files

### What's NOT Needed (Removed)

❌ `terraform/` - Replaced by Pulumi
❌ `helm-charts/` - Replaced by App Runner (serverless)
❌ `ansible/` - No Jenkins VM needed
❌ `manifests/` - No Kubernetes needed
❌ `Jenkinsfile` - Replaced by GitHub Actions
❌ `sonar-project.properties` - Replaced by CodeQL
❌ `grafana-datasources.yml` - Configured in Pulumi
❌ `mkdocs.yml` - Not using MkDocs

### What Might Be Missing

⚠️ **GitHub Secrets** (not in repo, configure in GitHub):
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `DOCKER_HUB_USERNAME`
- `DOCKER_HUB_TOKEN`
- `MLFLOW_TRACKING_URI`

⚠️ **Kaggle API Credentials** (not in repo):
- `~/.kaggle/kaggle.json` - Required for data download

⚠️ **AWS Credentials** (not in repo):
- `~/.aws/credentials` - Required for AWS CLI

⚠️ **Environment File** (not in repo):
- `.env` - Copy from `config-aws.env` and fill in values

---

## File Status Summary

| Category | Count | Status |
|----------|-------|--------|
| **Core Application** | 15 files | ✅ Complete |
| **Training Pipeline** | 25 files | ✅ Complete |
| **Infrastructure (Pulumi)** | 6 files | ✅ Complete |
| **CI/CD (GitHub Actions)** | 2 files | ✅ Complete |
| **Tests** | 20 files | ✅ Complete |
| **Documentation** | 13 files | ✅ Complete |
| **Configuration** | 8 files | ✅ Complete |
| **Scripts** | 3 files | ✅ Complete |
| **Total** | ~92 files | ✅ Complete |

---

## Quick Checklist

Before deployment, ensure you have:

- [ ] `config-aws.env` copied to `.env` and filled
- [ ] AWS CLI configured (`aws configure`)
- [ ] Pulumi CLI installed
- [ ] DVC installed
- [ ] Docker installed and running
- [ ] GitHub secrets configured
- [ ] Kaggle API credentials (`~/.kaggle/kaggle.json`)
- [ ] Python 3.11+ installed
- [ ] All dependencies installed (`pip install -r requirements.txt`)

---

## File Dependencies

### Critical Dependencies

```
config-aws.env → .env (must copy and configure)
    ↓
pulumi/__main__.py (reads AWS credentials)
    ↓
S3 Bucket created
    ↓
.dvc/config (points to S3)
    ↓
training/scripts/*.py (uses DVC)
    ↓
MLflow (stores artifacts in S3)
    ↓
app/services/model_service.py (loads from MLflow)
    ↓
Dockerfile (embeds model)
    ↓
.github/workflows/cd.yml (builds and deploys)
    ↓
AWS App Runner (runs container)
```

---

## Conclusion

All necessary files for AWS deployment are present. The project is complete and ready for deployment following the [QUICK_START_AWS.md](QUICK_START_AWS.md) guide.

**Status**: ✅ All files accounted for and documented
