# Lab Files and Folders Mapping

This document maps each lab to the specific files and folders you'll work with, so you don't get confused.

## Lab 01: Automated ML Pipeline with Airflow & MLflow

**Lab File:** `poridhi/lab-01-model-development-mlflow-tracking.md`

**Files/Folders You'll Create:**

```
training/
├── data/
│   ├── raw/
│   │   └── application_record.csv          # Downloaded dataset
│   └── processed/
│       ├── X_train_balanced.npy             # SMOTE-balanced training data
│       ├── y_train_balanced.npy             # SMOTE-balanced labels
│       ├── X_test.npy                       # Processed test features
│       └── y_test.npy                       # Test labels
│
├── scripts/
│   └── airflow_tasks.py                     # All Airflow task implementations
│
├── src/
│   └── config/
│       └── mlflow_config.py                 # MLflow configuration class
│
└── models/
    ├── scaler.pkl                           # Saved StandardScaler
    └── label_encoders.pkl                   # Saved LabelEncoders

dags/
└── ml_training_pipeline.py                  # Airflow DAG for ML pipeline

logs/                                        # Airflow task logs (auto-created)
plugins/                                     # Airflow plugins (optional)

mlruns/                                      # MLflow local artifact storage
mlflow.db                                    # MLflow SQLite database
airflow.db                                   # Airflow SQLite database
```

**Key Commands:**
```bash
# Setup environment
python3 -m venv venv && source venv/bin/activate
pip install apache-airflow==2.8.0 mlflow pandas numpy scikit-learn xgboost imbalanced-learn

# Initialize Airflow
export AIRFLOW_HOME=$(pwd)
airflow db init
airflow users create --username admin --password admin --role Admin \
  --firstname Admin --lastname User --email admin@example.com

# Start services
airflow webserver --port 8080 &
airflow scheduler &
mlflow server --backend-store-uri sqlite:///mlflow.db \
  --default-artifact-root ./mlruns --host 0.0.0.0 --port 5000 &

# Trigger pipeline
airflow dags trigger credit_card_ml_pipeline

# Access UIs
open http://localhost:8080  # Airflow (admin/admin)
open http://localhost:5000  # MLflow
```

**What Happens:**
- Airflow orchestrates the ENTIRE workflow (no manual scripts)
- Task 1: Download data
- Task 2: Run EDA (through Airflow)
- Task 3: Preprocess data with SMOTE (through Airflow)
- Task 4: Train multiple models (through Airflow)
- Task 5: Evaluate models
- Task 6: Register best model to MLflow Registry
- Task 7: Send notification
- MLflow tracks ALL experiments automatically

---

## Lab 02: Infrastructure as Code (Pulumi) & S3

**Lab File:** `poridhi/lab-02-infrastructure-as-code-pulumi-s3.md`

**Files/Folders You'll Create:**

```
pulumi/
├── __main__.py                              # Pulumi infrastructure code
├── Pulumi.yaml                              # Pulumi project config
├── Pulumi.dev.yaml                          # Dev stack config
├── requirements.txt                         # Pulumi dependencies
└── .pulumi/                                 # Pulumi state (auto-created)

.env                                         # Environment variables
```

**What Gets Created in AWS:**
- S3 bucket: `card-approval-infra-dev-ml-artifacts`
- Bucket versioning enabled
- Server-side encryption enabled
- Public access blocked

**Key Commands:**
```bash
cd pulumi

# Initialize Pulumi
pulumi new aws-python

# Deploy infrastructure
pulumi up

# Get bucket name
pulumi stack output bucket_name

# Verify in AWS
aws s3 ls s3://$(pulumi stack output bucket_name)
```

---

## Lab 03: Data Versioning with DVC

**Lab File:** `poridhi/lab-03-data-versioning-dvc-s3.md`

**Files/Folders You'll Create:**

```
.dvc/
├── config                                   # DVC configuration
├── .gitignore                               # DVC gitignore
└── cache/                                   # Local DVC cache

training/data/
├── raw.dvc                                  # DVC metadata for raw data
└── processed.dvc                            # DVC metadata for processed data

models.dvc                                   # DVC metadata for models

.dvcignore                                   # DVC ignore patterns
```

**What Gets Stored in S3:**
```
s3://your-bucket/dvc-storage/
├── ab/
│   └── cdef1234...                          # Hashed data files
├── 12/
│   └── 3456abcd...                          # Hashed data files
└── ...
```

**Key Commands:**
```bash
# Initialize DVC
dvc init

# Configure S3 remote
dvc remote add -d s3storage s3://your-bucket/dvc-storage
dvc remote modify s3storage region us-east-1

# Track data with DVC
dvc add training/data/raw
dvc add training/data/processed
dvc add models/

# Commit DVC metadata to Git
git add training/data/raw.dvc training/data/processed.dvc models.dvc .gitignore
git commit -m "Add data to DVC tracking"

# Push data to S3
dvc push

# Pull data from S3 (on another machine)
dvc pull
```

---

## Lab 04: MLflow + S3 Integration

**Lab File:** `poridhi/lab-04-mlflow-s3-integration.md`

**Files/Folders You'll Create:**

```
training/src/config/
└── mlflow_s3_config.py                      # MLflow S3 configuration class

training/scripts/
├── run_training_s3.py                       # Training with S3 artifact storage
└── load_model_s3.py                         # Load models from S3

.env                                         # Updated with S3 bucket info
```

**What Gets Stored in S3:**
```
s3://your-bucket/mlflow-artifacts/
├── 0/
│   └── abc123.../                           # Experiment artifacts
│       ├── artifacts/
│       │   ├── model/                       # Trained model
│       │   ├── preprocessors/               # Scalers, encoders
│       │   └── metadata/                    # Feature names, etc.
│       └── metrics/                         # Logged metrics
└── ...
```

**Key Commands:**
```bash
# Set environment variables
source .env

# Train with S3 storage
python training/scripts/run_training_s3.py

# Load model from S3
python training/scripts/load_model_s3.py

# Verify in S3
aws s3 ls s3://$MLFLOW_S3_BUCKET/mlflow-artifacts/ --recursive
```

---

## Lab 05: The Prediction API (FastAPI) & Docker Hub

**Lab File:** `poridhi/lab-05-prediction-api-fastapi-docker.md`

**Files/Folders You'll Create:**

```
app/
├── __init__.py
├── main.py                                  # FastAPI application entry
├── core/
│   ├── __init__.py
│   ├── config.py                            # App configuration
│   ├── logging.py                           # Logging setup
│   ├── metrics.py                           # Prometheus metrics
│   └── tracing.py                           # OpenTelemetry tracing
├── routers/
│   ├── __init__.py
│   ├── health.py                            # Health check endpoints
│   └── predict.py                           # Prediction endpoints
├── schemas/
│   ├── __init__.py
│   ├── health.py                            # Health check schemas
│   └── prediction.py                        # Prediction request/response schemas
├── services/
│   ├── __init__.py
│   ├── model_service.py                     # Model loading and inference
│   └── preprocessing_service.py             # Input preprocessing
└── utils/
    ├── __init__.py
    ├── gcs.py                               # Cloud storage helpers
    └── mlflow_helpers.py                    # MLflow utilities

Dockerfile                                   # Container definition
.dockerignore                                # Docker ignore patterns
requirements.txt                             # Python dependencies
test_payload.json                            # Sample prediction request
```

**Key Commands:**
```bash
# Run API locally
python app/main.py

# Test endpoints
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d @test_payload.json

# Build Docker image
docker build -t card-approval-api:latest .

# Run container
docker run -p 8000:8000 \
  -e MLFLOW_TRACKING_URI=http://host.docker.internal:5000 \
  card-approval-api:latest

# Push to Docker Hub
docker tag card-approval-api:latest username/card-approval-api:latest
docker push username/card-approval-api:latest
```

---

## Lab 06: CI/CD & Security (GitHub Actions)

**Lab File:** `poridhi/lab-06-cicd-security-github-actions.md`

**Files/Folders You'll Create:**

```
.github/
└── workflows/
    ├── ci.yml                               # Continuous Integration workflow
    └── cd.yml                               # Continuous Deployment workflow

pulumi/
└── __main__.py                              # Updated with App Runner deployment
```

**GitHub Secrets to Configure:**
- `DOCKER_USERNAME`
- `DOCKER_PASSWORD`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `PULUMI_CONFIG_PASSPHRASE`

**Key Commands:**
```bash
# Initialize Git repository
git init
git add .
git commit -m "Initial commit"

# Create GitHub repository
gh repo create card-approval-prediction --public --source=. --push

# Trigger deployment
git tag v1.0.0
git push origin v1.0.0

# Monitor workflows
gh run list
gh run view --log
```

---

## Lab 07: Observability (Prometheus & Grafana)

**Lab File:** `poridhi/lab-07-observability-prometheus-grafana.md`

**Files/Folders You'll Create:**

```
app/core/
└── metrics.py                               # Updated with Prometheus metrics

app/services/
└── drift_detection.py                       # Evidently AI drift detection

monitoring/
├── prometheus/
│   ├── prometheus.yml                       # Prometheus configuration
│   └── alerts.yml                           # Alert rules
├── grafana/
│   └── provisioning/
│       ├── datasources/
│       │   └── datasources.yml              # Grafana datasources
│       └── dashboards/
│           ├── dashboards.yml               # Dashboard provisioning
│           └── api_dashboard.json           # API monitoring dashboard
├── loki/
│   └── loki-config.yml                      # Loki log aggregation
├── promtail/
│   └── promtail-config.yml                  # Log shipping config
└── tempo/
    └── tempo-config.yml                     # Distributed tracing

docker-compose.monitoring.yml                # Monitoring stack compose file
```

**Key Commands:**
```bash
# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Check metrics endpoint
curl http://localhost:8000/metrics

# Access UIs
open http://localhost:9090  # Prometheus
open http://localhost:3000  # Grafana (admin/admin)

# Check drift
curl http://localhost:8000/api/v1/drift/check
```

---

## Complete Project Structure

After completing all labs, your project will look like this:

```
card-approval-prediction/
├── .dvc/                                    # Lab 03: DVC config
├── .github/workflows/                       # Lab 06: CI/CD
├── app/                                     # Lab 05: FastAPI app
├── monitoring/                              # Lab 07: Observability
├── pulumi/                                  # Lab 02: Infrastructure
├── training/                                # Lab 01: ML training
│   ├── data/
│   ├── notebooks/
│   ├── scripts/
│   ├── src/
│   └── models/
├── tests/                                   # Unit tests
├── mlruns/                                  # Lab 01: MLflow artifacts
├── mlflow.db                                # Lab 01: MLflow metadata
├── Dockerfile                               # Lab 05: Container
├── docker-compose.yml                       # Full stack
├── docker-compose.monitoring.yml            # Lab 07: Monitoring
├── requirements.txt                         # Python dependencies
├── .env                                     # Environment variables
├── .gitignore                               # Git ignore
├── .dvcignore                               # DVC ignore
└── README.md                                # Project documentation
```

---

## Quick Reference: What Each Lab Produces

| Lab | Main Output | Location |
|-----|-------------|----------|
| Lab 01 | Automated ML pipeline + MLflow tracking | `dags/`, `training/scripts/`, `mlruns/` |
| Lab 02 | S3 bucket infrastructure | AWS S3 |
| Lab 03 | Data versioned in S3 | S3 + `.dvc` files |
| Lab 04 | Models in S3 via MLflow | S3 `mlflow-artifacts/` |
| Lab 05 | Containerized API | Docker Hub |
| Lab 06 | Automated deployment | AWS App Runner |
| Lab 07 | Monitoring dashboards | Grafana |

---

## Notes

- **Lab 01** requires Airflow and MLflow (everything automated through Airflow)
- **Lab 02** requires AWS account (creates S3 bucket)
- **Lab 03** requires Lab 02 completion (uses S3 bucket)
- **Lab 04** requires Lab 02 completion (uses S3 bucket)
- **Lab 05** requires Docker Hub account
- **Lab 06** requires GitHub account + AWS
- **Lab 07** can run locally with Docker Compose

---

## Airflow-First Approach

Lab 01 follows an Airflow-first approach where:

1. **Everything runs through Airflow** - No manual script execution
2. **MLflow tracks automatically** - Integrated within Airflow tasks
3. **EDA through Airflow** - Automated exploratory analysis
4. **Preprocessing through Airflow** - SMOTE balancing automated
5. **Training through Airflow** - Multiple models trained automatically
6. **Registration through Airflow** - Best model promoted automatically
7. **Scheduling** - Pipeline runs on schedule (e.g., weekly)
8. **Monitoring** - Airflow UI shows pipeline health
9. **Retries** - Automatic retry on failures
10. **Alerts** - Notifications on completion/failure

This ensures production-ready automation from day one.
