# Credit Card Approval Prediction - AWS MLOps Project

**Production-grade MLOps pipeline** for credit card approval prediction using machine learning on **Amazon Web Services (AWS)**.

> This project implements a complete MLOps lifecycle with Infrastructure as Code (Pulumi), automated CI/CD (GitHub Actions), data versioning (DVC), experiment tracking (MLflow), drift detection (Evidently AI), and comprehensive monitoring (Prometheus + Grafana).

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      GitHub Repository                           │
│                 (Code + DVC Metadata + Models)                   │
└────────────┬────────────────────────────────────────────────────┘
             │
             │ Push/PR
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     GitHub Actions CI/CD                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   CodeQL     │  │  Unit Tests  │  │ Docker Build │          │
│  │   (SAST)     │  │  + Coverage  │  │  + Trivy     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────┬────────────────────────────────────────────────────┘
             │
             │ Build & Push
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Docker Hub                                 │
│                (Container Image Registry)                        │
└────────────┬────────────────────────────────────────────────────┘
             │
             │ Deploy
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AWS App Runner                                │
│              (Serverless API Service)                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  FastAPI + MLflow Model + Drift Detection (Evidently)   │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────┬────────────────────────────────────────────────────┘
             │
             │ Metrics
             ▼
┌─────────────────────────────────────────────────────────────────┐
│            EC2 Monitoring Stack (t3.medium)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                      │
│  │  Nginx   │→ │Prometheus│→ │ Grafana  │                      │
│  │ (Proxy)  │  │(Metrics) │  │(Dashbrd) │                      │
│  └──────────┘  └──────────┘  └──────────┘                      │
└─────────────────────────────────────────────────────────────────┘
             ▲
             │
             │ Store/Retrieve
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                        AWS S3                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ DVC Storage  │  │   MLflow     │  │   Training   │          │
│  │ (Datasets)   │  │  Artifacts   │  │    Data      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

## 📑 Table of Contents

- [Credit Card Approval Prediction - MLOps Project](#credit-card-approval-prediction---mlops-project)
  - [🏗️ Architecture](#️-architecture)
  - [📑 Table of Contents](#-table-of-contents)
  - [Overview](#overview)
  - [🛠️ Tech Stack](#️-tech-stack)
  - [📁 Project Structure](#-project-structure)
  - [Quick Start](#quick-start)
    - [Prerequisites](#prerequisites)
    - [Clone \& Configure](#clone--configure)
  - [📡 API Endpoints](#-api-endpoints)
    - [Example Prediction Request](#example-prediction-request)
    - [Example Response](#example-response)
  - [Demo Video](#demo-video)
  - [📚 Documentation](#-documentation)
  - [🔮 Future Improvements](#-future-improvements)
  - [📄 License](#-license)
  - [👤 Citation](#-citation)
  - [Contact](#contact)

---

## Overview

This project is a learning-oriented MLOps playground focused on understanding the end-to-end lifecycle of machine learning model development. It includes:

- **Infrastructure as Code**: Terraform for GCP resources (GKE, GCS, Artifact Registry)
- **Kubernetes Deployment**: Helm charts for scalable, reproducible deployments
- **CI/CD Pipeline**: Jenkins with GitHub webhooks for automated builds and deployments
- **Monitoring**: Prometheus + Grafana observability stack
- **MLflow**: MLflow for experiment tracking and model versioning
- **APIs**: FastAPI service with preprocessing and real-time inference

---


## 🛠️ Tech Stack

| Layer | Technologies |
|-------|--------------|
| **Cloud & Infrastructure** | AWS (S3, App Runner, EC2), Pulumi (Python IaC) |
| **Container & Registry** | Docker, Docker Hub, Docker Compose |
| **CI/CD & Security** | GitHub Actions, CodeQL (SAST), Trivy (Container Scan), Bandit, Safety |
| **Workflow Orchestration** | Apache Airflow 2.8 (LocalExecutor) |
| **Application** | FastAPI, Python 3.11, Pydantic, Uvicorn |
| **Data Storage** | PostgreSQL (predictions + MLflow metadata), Redis (caching) |
| **Data Versioning** | DVC with S3 backend |
| **ML & Data Science** | scikit-learn, XGBoost, LightGBM, CatBoost, pandas, numpy, imbalanced-learn |
| **ML Operations** | MLflow (tracking & registry), S3 (artifacts) |
| **Drift Detection** | Evidently AI |
| **Monitoring & Observability** | Prometheus, Grafana, Loki (logs), Tempo (traces), OpenTelemetry |
| **Code Quality** | Black, isort, Flake8, Pylint, pre-commit |

---

## 📁 Project Structure

```
card-approval-prediction/
├── app/                        # FastAPI application
│   ├── main.py                 # Application entrypoint
│   ├── core/                   # Core configurations
│   │   ├── config.py           # AWS settings & environment variables
│   │   ├── logging.py          # Logging configuration
│   │   ├── metrics.py          # Prometheus metrics
│   │   └── tracing.py          # OpenTelemetry tracing
│   ├── routers/                # API route handlers
│   │   ├── health.py           # Health check endpoints
│   │   ├── predict.py          # Prediction endpoints
│   │   └── drift.py            # Drift detection endpoints (NEW)
│   ├── schemas/                # Pydantic models
│   │   ├── health.py           # Health check schemas
│   │   └── prediction.py       # Prediction schemas
│   ├── services/               # Business logic
│   │   ├── model_service.py    # Model loading & inference
│   │   ├── preprocessing_service.py # Feature preprocessing
│   │   └── drift_detection.py  # Evidently AI drift detection (NEW)
│   └── utils/                  # Utilities
│       ├── gcs.py              # Cloud storage helpers
│       └── mlflow_helpers.py   # MLflow utilities
│
├── training/                   # ML training pipeline
│   ├── data/                   # Data storage (DVC tracked)
│   │   ├── raw/                # Raw Kaggle dataset
│   │   └── processed/          # Processed features + artifacts
│   ├── scripts/                # Training automation
│   │   ├── download_data.py    # Download from Kaggle
│   │   ├── run_eda.py          # Exploratory data analysis
│   │   ├── run_preprocessing.py # Feature engineering
│   │   └── run_training.py     # Train & register models
│   ├── src/                    # Training source code
│   │   ├── data/               # Data loading
│   │   ├── features/           # Feature engineering
│   │   ├── models/             # Model training & evaluation
│   │   ├── utils/              # Training utilities
│   │   └── config/             # Training configuration
│   ├── notebooks/              # Jupyter notebooks for EDA
│   └── preprocessors/          # Custom preprocessors
│
├── pulumi/                     # Infrastructure as Code (NEW)
│   ├── __main__.py             # Pulumi program (AWS resources)
│   ├── Pulumi.yaml             # Project definition
│   ├── Pulumi.dev.yaml         # Dev stack configuration
│   ├── Pulumi.prod.yaml        # Production stack configuration
│   ├── requirements.txt        # Pulumi dependencies
│   └── README.md               # Pulumi documentation
│
├── .github/                    # GitHub Actions (NEW)
│   └── workflows/
│       ├── ci.yml              # Continuous Integration
│       └── cd.yml              # Continuous Deployment
│
├── .dvc/                       # DVC configuration (NEW)
│   └── config                  # S3 remote configuration
│
├── scripts/                    # CI/CD helper scripts
│   ├── evaluate_model.py       # Model quality gate
│   └── download_model.py       # Download from MLflow
│
├── tests/                      # Unit tests
│   ├── test_api.py             # API tests
│   ├── test_routers_*.py       # Router tests
│   ├── test_services_*.py      # Service tests
│   └── test_training_*.py      # Training tests
│
├── docs/                       # Documentation
│   ├── 00_Setup_Guide_AWS.md   # AWS setup guide (NEW)
│   ├── 00_Setup_Guide.md       # Original GCP setup guide
│   ├── 01_Helm_Deployment.md   # Kubernetes deployment (legacy)
│   ├── 02_MLflow_Training.md   # Model training guide
│   ├── 03_CICD_Pipeline.md     # Jenkins CI/CD (legacy)
│   ├── 04_NGINX.md             # NGINX configuration (legacy)
│   ├── 05_Monitoring.md        # Monitoring guide
│   └── index.md                # Documentation index
│
├── models/                     # Saved models (embedded in Docker)
├── img/                        # Images for documentation
│
├── Dockerfile                  # Container definition (AWS optimized)
├── .dockerignore               # Docker ignore patterns
├── .dvcignore                  # DVC ignore patterns (NEW)
├── pyproject.toml              # Python project configuration
├── requirements.txt            # Python dependencies (AWS)
├── config-aws.env              # AWS configuration template (NEW)
├── config-example.env          # Original GCP configuration
├── .gitignore                  # Git ignore patterns
├── .flake8                     # Flake8 configuration
├── .pre-commit-config.yaml     # Pre-commit hooks
├── verify_transformation.sh    # Transformation verification script (NEW)
│
├── test_local.sh               # Automated local testing script
├── test_payload.json           # Sample prediction payload for testing
├── README.md                   # This file
├── README_DOCKER_COMPOSE.md    # Docker Compose guide
├── README_AIRFLOW.md           # Airflow quick start
├── LOCAL.md                    # Local testing guide (NEW)
├── README-AWS.md               # Detailed AWS documentation (NEW)
├── TRANSFORMATION_SUMMARY.md   # Transformation details (NEW)
├── MIGRATION_GUIDE.md          # GCP to AWS migration guide (NEW)
├── QUICK_START_AWS.md          # Quick start guide (NEW)
├── PROJECT_TRANSFORMATION_COMPLETE.md # Transformation summary (NEW)
├── DOCUMENTATION_INDEX.md      # Documentation index (NEW)
├── Lab-plannings.md            # Lab planning requirements
└── LICENSE                     # MIT License
```

---

##   Quick Start

### Option 1: Local Development with Docker Compose (Recommended)

```bash
# Clone repository
git clone https://github.com/your-username/card-approval-prediction.git
cd card-approval-prediction

# Configure environment
cp .env.example .env
# Edit .env: Set AWS credentials, passwords

# Start all services (API, PostgreSQL, Redis, MLflow, Monitoring)
docker-compose up -d

# View logs
docker-compose logs -f

# Access services
# API: http://localhost:8000/docs
# MLflow: http://localhost:5000
# Airflow: http://localhost:8080 (admin/admin)
# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
```

> 📖 **Full Docker Compose guide**: See [README_DOCKER_COMPOSE.md](README_DOCKER_COMPOSE.md)

### Option 2: AWS Deployment with Pulumi

```bash
# Prerequisites
- Python 3.11+
- AWS Account with billing enabled
- Docker & Docker Hub account
- Pulumi CLI installed
- AWS CLI configured
- DVC installed

# Clone & Configure
git clone https://github.com/your-username/card-approval-prediction.git
cd card-approval-prediction

# Configure AWS
aws configure

# Configure environment
cp config-aws.env .env
# Edit .env: Set AWS credentials, S3 bucket, Docker Hub credentials

# Install dependencies
pip install -r requirements.txt

# Setup pre-commit hooks
pre-commit install
```

### Deploy Infrastructure

```bash
cd pulumi
pip install -r requirements.txt
pulumi login --local
pulumi stack init production
pulumi up
cd ..
```

### Setup DVC

```bash
# Configure DVC with S3
export S3_BUCKET=$(cd pulumi && pulumi stack output s3_bucket_name && cd ..)
dvc remote add -d s3storage s3://$S3_BUCKET/dvc-storage
dvc remote modify s3storage region us-east-1
```

### Train Model

```bash
cd training
python scripts/download_data.py
python scripts/run_preprocessing.py
python scripts/run_training.py
cd ..
```

### Deploy API

```bash
# Push to main branch to trigger GitHub Actions deployment
git add .
git commit -m "Deploy to AWS"
git push origin main
```

> 📖 **Full setup guide**: See [QUICK_START_AWS.md](QUICK_START_AWS.md) for 30-minute quick start or [docs/00_Setup_Guide_AWS.md](docs/00_Setup_Guide_AWS.md) for detailed instructions




## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | API info and status |
| `GET` | `/docs` | Swagger UI documentation |
| `GET` | `/health` | Health check |
| `GET` | `/health/ready` | Readiness probe |
| `GET` | `/health/live` | Liveness probe |
| `GET` | `/metrics` | Prometheus metrics |
| `POST` | `/api/v1/predict` | Credit approval prediction |
| `GET` | `/api/v1/model-info` | Current model information |
| `POST` | `/api/v1/drift/check` | Check for data drift (NEW) |
| `GET` | `/api/v1/drift/status` | Drift detection status (NEW) |
| `GET` | `/api/v1/drift/reports` | List drift reports (NEW) |

### Example Prediction Request

```bash
curl -X POST "http://localhost:8000/api/v1/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "ID": 5008804,
    "CODE_GENDER": "M",
    "FLAG_OWN_CAR": "Y",
    "FLAG_OWN_REALTY": "Y",
    "CNT_CHILDREN": 0,
    "AMT_INCOME_TOTAL": 180000.0,
    "NAME_INCOME_TYPE": "Working",
    "NAME_EDUCATION_TYPE": "Higher education",
    "NAME_FAMILY_STATUS": "Married",
    "NAME_HOUSING_TYPE": "House / apartment",
    "DAYS_BIRTH": -14000,
    "DAYS_EMPLOYED": -2500,
    "FLAG_MOBIL": 1,
    "FLAG_WORK_PHONE": 0,
    "FLAG_PHONE": 1,
    "FLAG_EMAIL": 0,
    "OCCUPATION_TYPE": "Managers",
    "CNT_FAM_MEMBERS": 2.0
  }'
```

### Example Response

```json
{
  "prediction": 1,
  "probability": 1.0,
  "decision": "APPROVED",
  "confidence": 1.0,
  "version": "1",
  "timestamp": "2025-01-24T15:47:00"
}
```

---

## Demo Video

[▶ Watch the demo video on Google Drive](https://drive.google.com/drive/folders/1ZjPjfBKeP1AoTEvL-5GgAoK9CSbr1KBx?usp=sharing)



## 📚 Documentation

| Document | Description |
|----------|-------------|
| [QUICKSTART.md](QUICKSTART.md) | **5-minute quick start** - Get running fast |
| [README.md](README.md) | **Main documentation** - Start here |
| [README_DOCKER_SETUP.md](README_DOCKER_SETUP.md) | **Docker Compose guide** - Local vs AWS modes |
| [LOCAL.md](LOCAL.md) | **Local testing guide** - Test with Docker before deployment |
| [README_DOCKER_COMPOSE.md](README_DOCKER_COMPOSE.md) | Run locally with Docker Compose (detailed) |
| [README_AIRFLOW.md](README_AIRFLOW.md) | Airflow ML pipeline quick start |
| [FILE_PURPOSES.md](FILE_PURPOSES.md) | Purpose of every file in the project |
| [Lab-plannings.md](Lab-plannings.md) | Lab requirements (6 labs) |
| [docs/00_Setup_Guide_AWS.md](docs/00_Setup_Guide_AWS.md) | AWS setup guide |
| [docs/02_MLflow_Training.md](docs/02_MLflow_Training.md) | Model training guide |
| [docs/05_Monitoring.md](docs/05_Monitoring.md) | Monitoring guide |
| [docs/06_Airflow_Pipeline.md](docs/06_Airflow_Pipeline.md) | Airflow ML pipeline orchestration |

---

## 🔮 Future Improvements

- [ ] **AWS Lambda**: Batch predictions
- [ ] **AWS SageMaker**: Model training and hosting
- [ ] **AWS Step Functions**: ML pipeline orchestration
- [ ] **AWS EventBridge**: Event-driven model retraining
- [ ] **Unit Tests in CI/CD**: Integrate comprehensive unit tests
- [ ] **A/B Testing**: Canary deployments for model versions
- [ ] **Feature Store**: Centralized feature management
- [ ] **Model Explainability**: SHAP/LIME integration

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👤 Citation

If you use Card Approval Prediction in your research, please cite it as follows:
```
@software{CardApprovalPrediction2025,
  author = {Thanh Phat},
  title = {Card Approval Prediction: End-to-end MLOps pipeline for credit card approval prediction using machine learning on Google Cloud Platform.},
  year = {2025},
  url = {https://github.com/thanhphat-19/card-approval-prediction}
}
```

## Contact

For questions, issues, or collaborations, please open an issue or contact thanhphat352@gmail.com
