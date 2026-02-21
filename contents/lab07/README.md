# Lab 07: Complete MLOps System

This directory contains the complete, production-ready MLOps system with all components from Labs 01-06.

## Complete System Overview

This is the culmination of all previous labs, providing a fully integrated MLOps platform.

**From Lab 01: ML Pipeline Foundation**
- Airflow orchestration
- MLflow experiment tracking
- Model training (Logistic Regression, Random Forest, XGBoost)
- Automated pipeline execution

**From Lab 02: Infrastructure & Data Versioning**
- Pulumi Infrastructure as Code
- DVC data versioning
- S3 storage for data

**From Lab 03: Cloud-Native ML**
- MLflow S3 integration
- Cloud-based artifact storage
- Team collaboration

**From Lab 04: Production API**
- FastAPI prediction service
- Pydantic validation
- Docker containerization
- Docker Hub deployment

**From Lab 05: CI/CD & Security**
- GitHub Actions workflows
- Automated testing
- Security scanning (CodeQL, Trivy)
- AWS App Runner deployment

**From Lab 06: Observability**
- Prometheus metrics
- Grafana dashboards
- Data drift detection
- Alerting

## Complete Directory Structure

```
lab07/
├── dags/                           # Airflow DAG definitions
│   └── ml_training_pipeline.py
├── training/                       # ML training code
│   ├── data/
│   │   ├── raw/                   # Raw data (DVC tracked)
│   │   └── processed/             # Processed data (DVC tracked)
│   ├── scripts/
│   │   ├── airflow_tasks.py
│   │   ├── eda_analysis.py
│   │   ├── preprocess_data.py
│   │   ├── train_models.py
│   │   ├── run_training_s3.py
│   │   ├── load_model_s3.py
│   │   └── query_mlflow.py
│   ├── src/
│   │   ├── config/
│   │   │   ├── mlflow_config.py
│   │   │   └── mlflow_s3_config.py
│   │   └── utils/
│   └── models/                    # Trained models (DVC tracked)
├── pulumi/                         # Infrastructure as Code
│   ├── __main__.py                # S3, App Runner, IAM
│   ├── Pulumi.yaml
│   ├── Pulumi.dev.yaml
│   ├── Pulumi.prod.yaml
│   └── requirements.txt
├── app/                           # FastAPI application
│   ├── routers/
│   │   ├── health.py
│   │   └── predict.py
│   ├── services/
│   │   ├── model_service.py
│   │   └── drift_detection.py
│   ├── schemas/
│   │   ├── health.py
│   │   └── prediction.py
│   ├── core/
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── metrics.py
│   ├── utils/
│   ├── main.py
│   └── __init__.py
├── tests/                         # Test suite
│   ├── test_api.py
│   ├── test_model_service.py
│   ├── test_drift_detection.py
│   └── conftest.py
├── .github/                       # CI/CD workflows
│   └── workflows/
│       ├── ci.yml
│       └── cd.yml
├── monitoring/                    # Observability stack
│   ├── prometheus/
│   │   ├── prometheus.yml
│   │   └── alerts.yml
│   ├── grafana/
│   │   └── provisioning/
│   │       ├── datasources/
│   │       └── dashboards/
│   └── dashboards/
│       └── api-dashboard.json
├── logs/                          # Airflow logs
├── plugins/                       # Airflow plugins
├── .dvc/                          # DVC configuration
├── .github/                       # GitHub Actions
├── Dockerfile                     # API container
├── .dockerignore
├── docker-compose.monitoring.yml  # Monitoring stack
├── .env.example
├── .gitignore
├── .dvcignore
├── test_payload.json
├── requirements.txt
└── README.md
```

## Complete Setup Guide

### 1. Prerequisites
- Python 3.11+
- Docker and Docker Compose
- AWS account with credentials configured
- GitHub account
- Docker Hub account
- Pulumi CLI

### 2. Installation

```bash
# Clone repository
git clone https://github.com/your-username/card-approval-prediction.git
cd card-approval-prediction

# Install dependencies
pip install -r requirements.txt

# Install Pulumi
curl -fsSL https://get.pulumi.com | sh
export PATH=$PATH:$HOME/.pulumi/bin
```

### 3. Infrastructure Setup

```bash
# Deploy AWS infrastructure
cd pulumi
pulumi up
export DVC_S3_BUCKET=$(pulumi stack output data_bucket_name)
export MLFLOW_S3_BUCKET=$(pulumi stack output data_bucket_name)
cd ..
```

### 4. Data Versioning

```bash
# Initialize DVC
dvc init
dvc remote add -d s3storage s3://$DVC_S3_BUCKET/dvc-storage
dvc remote modify s3storage region us-east-1

# Track data
dvc add training/data/raw
dvc add training/data/processed
dvc add training/models

# Push to S3
dvc push
```

### 5. ML Pipeline

```bash
# Initialize Airflow
export AIRFLOW_HOME=$(pwd)
airflow db init
airflow users create --username admin --password admin \
  --firstname Admin --lastname User --role Admin --email admin@example.com

# Start Airflow (separate terminals)
airflow webserver --port 8080
airflow scheduler

# Start MLflow with S3
mlflow server \
  --backend-store-uri sqlite:///mlflow.db \
  --default-artifact-root s3://$MLFLOW_S3_BUCKET/mlflow-artifacts \
  --host 0.0.0.0 --port 5000

# Trigger pipeline
airflow dags trigger credit_card_ml_pipeline
```

### 6. API Deployment

```bash
# Build Docker image
docker build -t card-approval-api:latest .

# Run locally
docker run -p 8000:8000 \
  -e MLFLOW_TRACKING_URI=http://host.docker.internal:5000 \
  -e MODEL_NAME=card_approval_production \
  -e MODEL_STAGE=Production \
  card-approval-api:latest

# Push to Docker Hub
docker login
docker tag card-approval-api:latest your-username/card-approval-api:latest
docker push your-username/card-approval-api:latest
```

### 7. Monitoring

```bash
# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Access UIs
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin)
```

### 8. CI/CD

```bash
# Create GitHub repository
gh repo create card-approval-prediction --public --source=. --remote=origin --push

# Configure secrets in GitHub
# Settings > Secrets and variables > Actions

# Push code
git add .
git commit -m "Complete MLOps system"
git push origin main

# Create release
git tag v1.0.0
git push origin v1.0.0
```

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Development Phase                        │
├─────────────────────────────────────────────────────────────┤
│  Airflow → EDA → Preprocessing → Training → MLflow → S3     │
│     ↓                                           ↓            │
│  DVC (Data Versioning)                    Model Registry    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     CI/CD Pipeline                           │
├─────────────────────────────────────────────────────────────┤
│  GitHub → Actions → Tests → Security Scan → Docker Build    │
│                              ↓                               │
│                        Docker Hub                            │
│                              ↓                               │
│                    Pulumi → AWS App Runner                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     Production Phase                         │
├─────────────────────────────────────────────────────────────┤
│  FastAPI → Load Model from S3 → Predict → Return Result     │
│     ↓                                         ↓              │
│  Prometheus Metrics                    Drift Detection      │
│     ↓                                         ↓              │
│  Grafana Dashboards                    Alerts               │
└─────────────────────────────────────────────────────────────┘
```

## Access Points

- **Airflow UI**: http://localhost:8080 (admin/admin)
- **MLflow UI**: http://localhost:5000
- **API Docs**: http://localhost:8000/docs
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)
- **Production API**: [AWS App Runner URL from Pulumi output]

## Testing the Complete System

```bash
# 1. Test API health
curl http://localhost:8000/health

# 2. Test prediction
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d @test_payload.json

# 3. Generate traffic for monitoring
for i in {1..200}; do
  curl -X POST http://localhost:8000/api/v1/predict \
    -H "Content-Type: application/json" \
    -d @test_payload.json
done

# 4. Check metrics
curl http://localhost:8000/metrics

# 5. Check drift
curl http://localhost:8000/api/v1/drift/check

# 6. View in Grafana
open http://localhost:3000
```

## Maintenance & Operations

### Retraining Pipeline
```bash
# Trigger manual retraining
airflow dags trigger credit_card_ml_pipeline

# Or schedule automatic retraining (already configured for weekly)
```

### Model Promotion
```bash
# Promote model to production
python -c "
from mlflow.tracking import MlflowClient
client = MlflowClient()
client.transition_model_version_stage(
    name='card_approval_production',
    version=2,
    stage='Production'
)
"
```

### Monitoring Alerts
- Check Prometheus alerts: http://localhost:9090/alerts
- Configure alert notifications in Grafana

### Data Updates
```bash
# Update data
# ... add new data to training/data/raw/

# Version with DVC
dvc add training/data/raw
git add training/data/raw.dvc
git commit -m "Update training data"
dvc push
git push
```

## Troubleshooting

See individual lab guides for detailed troubleshooting:
- Lab 01: Airflow and MLflow issues
- Lab 02: Pulumi and DVC issues
- Lab 03: S3 integration issues
- Lab 04: API and Docker issues
- Lab 05: CI/CD and deployment issues
- Lab 06: Monitoring and drift detection issues

## Production Checklist

- [ ] All tests passing
- [ ] Security scans clean
- [ ] Monitoring dashboards configured
- [ ] Alerts set up and tested
- [ ] Documentation complete
- [ ] Backup strategy in place
- [ ] Disaster recovery plan documented
- [ ] Performance benchmarks established
- [ ] Cost monitoring enabled
- [ ] Team trained on system operations

## Next Steps

1. **Scale**: Add horizontal scaling with Kubernetes
2. **Advanced Monitoring**: Add distributed tracing with Jaeger
3. **A/B Testing**: Implement multi-model serving
4. **Feature Store**: Add Feast for feature management
5. **Model Explainability**: Integrate SHAP for model interpretability
6. **Advanced Drift**: Implement concept drift detection
7. **Cost Optimization**: Add auto-scaling and spot instances
8. **Multi-Region**: Deploy to multiple AWS regions
9. **Advanced Security**: Add OAuth2, rate limiting, WAF
10. **ML Governance**: Implement model cards and lineage tracking

## Resources

- [Complete Lab Guide](../../poridhi/)
- [Architecture Diagrams](./docs/architecture/)
- [API Documentation](http://localhost:8000/docs)
- [Runbooks](./docs/runbooks/)
