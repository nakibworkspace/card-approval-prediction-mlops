# Poridhi Labs - Complete Documentation Index

## Quick Navigation

| Lab | Title | Time | Status |
|-----|-------|------|--------|
| [Lab 01](./lab-01-model-development-mlflow-tracking.md) | Automated ML Pipeline with Airflow & MLflow | 6-8h | ✅ |
| [Lab 02](./lab-02-infrastructure-as-code-pulumi-s3.md) | Infrastructure as Code (Pulumi) & S3 | 2-3h | ✅ |
| [Lab 03](./lab-03-data-versioning-dvc-s3.md) | Data Versioning with DVC | 2-3h | ✅ |
| [Lab 04](./lab-04-mlflow-s3-integration.md) | MLflow + S3 Integration | 2-3h | ✅ |
| [Lab 05](./lab-05-prediction-api-fastapi-docker.md) | The Prediction API (FastAPI) & Docker Hub | 3-4h | ✅ |
| [Lab 06](./lab-06-cicd-security-github-actions.md) | CI/CD & Security (GitHub Actions) | 2-3h | ✅ |
| [Lab 07](./lab-07-observability-prometheus-grafana.md) | Observability (Prometheus & Grafana) | 3-4h | ✅ |

**Total Time:** 22-30 hours over 7 days

## Documentation Files

### Main Documentation
- **[README.md](./README.md)** - Overview, learning path, prerequisites, and getting started
- **[COMPLETION_GUIDE.md](./COMPLETION_GUIDE.md)** - Progress tracking, verification commands, and troubleshooting
- **[INDEX.md](./INDEX.md)** - This file - complete documentation index

### Lab Documentation

#### Lab 01: Automated ML Pipeline with Airflow & MLflow
**File:** [lab-01-model-development-mlflow-tracking.md](./lab-01-model-development-mlflow-tracking.md)

**Chapters:**
1. Airflow Setup
2. MLflow Setup
3. Creating the ML Pipeline DAG
4. Implementing Pipeline Tasks
5. Running the Pipeline

**Key Concepts:**
- Apache Airflow orchestration
- MLflow tracking integration
- Automated EDA, preprocessing, training
- SMOTE balancing in pipelines
- Model Registry and automated promotion
- Scheduling and monitoring

---

#### Lab 02: Infrastructure as Code (Pulumi) & S3
**File:** [lab-02-infrastructure-as-code-pulumi-s3.md](./lab-02-infrastructure-as-code-pulumi-s3.md)

**Chapters:**
1. Infrastructure as Code Fundamentals
2. Creating an S3 Bucket
3. Configuring Bucket Security
4. Verifying Infrastructure

**Key Concepts:**
- Pulumi projects and stacks
- S3 bucket configuration (versioning, encryption)
- Infrastructure as Code principles

---

#### Lab 03: Data Versioning with DVC
**File:** [lab-03-data-versioning-dvc-s3.md](./lab-03-data-versioning-dvc-s3.md)

**Chapters:**
1. DVC Fundamentals
2. DVC Setup and Configuration
3. Tracking Data with DVC
4. Pushing and Pulling Data
5. Collaboration Workflows

**Key Concepts:**
- Data version control
- DVC with S3 backend
- Data tracking and versioning
- Team collaboration with versioned data

---

#### Lab 04: MLflow + S3 Integration
**File:** [lab-04-mlflow-s3-integration.md](./lab-04-mlflow-s3-integration.md)

**Chapters:**
1. MLflow S3 Configuration
2. Training with S3 Artifact Storage
3. Loading Models from S3
4. Model Registry with S3

**Key Concepts:**
- MLflow S3 integration
- Cloud artifact storage
- Model versioning in S3
- Loading models from cloud

---

#### Lab 05: The Prediction API (FastAPI) & Docker Hub
**File:** [lab-05-prediction-api-fastapi-docker.md](./lab-05-prediction-api-fastapi-docker.md)

**Chapters:**
1. FastAPI Fundamentals
2. Input Validation with Pydantic
3. Model Service
4. Prediction Endpoint
5. Dockerization
6. Docker Hub Deployment

**Key Concepts:**
- FastAPI application structure
- Pydantic validation
- Model loading and caching
- Docker best practices
- Container registry

---

#### Lab 06: CI/CD & Security (GitHub Actions)
**File:** [lab-06-cicd-security-github-actions.md](./lab-06-cicd-security-github-actions.md)

**Chapters:**
1. Continuous Integration Workflow
2. Continuous Deployment Workflow
3. AWS App Runner Deployment

**Key Concepts:**
- GitHub Actions workflows
- CodeQL security scanning
- Trivy container scanning
- Automated deployment
- Secrets management

---

#### Lab 07: Observability (Prometheus & Grafana)
**File:** [lab-07-observability-prometheus-grafana.md](./lab-07-observability-prometheus-grafana.md)

**Chapters:**
1. Prometheus Metrics
2. Prometheus Setup
3. Grafana Dashboards
4. Data Drift Detection
5. Alerting

**Key Concepts:**
- Prometheus metric types (Counter, Gauge, Histogram)
- Grafana visualization
- Evidently AI drift detection
- Alert rules and thresholds

---

## Learning Objectives by Lab

### Lab 01 Learning Objectives
1. Set up Apache Airflow for ML pipeline orchestration
2. Create Airflow DAGs to automate data processing and model training
3. Integrate MLflow tracking within Airflow tasks
4. Perform EDA, preprocessing, and training through Airflow
5. Handle class imbalance using SMOTE in automated pipelines
6. Train and compare multiple models automatically
7. Register best models to MLflow Model Registry
8. Schedule and monitor automated pipeline execution

### Lab 02 Learning Objectives
1. Install and configure Pulumi for AWS infrastructure management
2. Define cloud resources using Python code
3. Create and configure S3 buckets with appropriate permissions
4. Understand Infrastructure as Code principles and benefits

### Lab 03 Learning Objectives
1. Initialize and configure DVC for data version control
2. Set up S3 as DVC remote storage
3. Track datasets with DVC
4. Push and pull data from cloud storage
5. Collaborate with versioned datasets

### Lab 04 Learning Objectives
1. Configure MLflow to use S3 for artifact storage
2. Upload and retrieve models from cloud storage
3. Integrate MLflow with S3 backend
4. Load models from S3 for inference

### Lab 05 Learning Objectives
1. Create a FastAPI application with health and prediction endpoints
2. Implement input validation using Pydantic models
3. Load ML models from S3 and cache them for performance
4. Handle errors gracefully with appropriate HTTP status codes
5. Create a production-ready Dockerfile
6. Build and push Docker images to Docker Hub
7. Test the containerized API locally

### Lab 06 Learning Objectives
1. Create GitHub Actions workflows for CI/CD
2. Implement security scanning with CodeQL (SAST)
3. Automate Docker image building and pushing
4. Deploy to AWS App Runner using Pulumi
5. Configure secrets management in GitHub
6. Implement automated quality gates
7. Understand continuous deployment principles

### Lab 07 Learning Objectives
1. Instrument FastAPI with Prometheus metrics
2. Set up Prometheus for metrics collection
3. Create Grafana dashboards for visualization
4. Monitor system health (latency, throughput, errors)
5. Track model performance metrics
6. Implement data drift detection with Evidently AI
7. Configure alerting rules for critical issues

---

## Key Technologies by Lab

### Lab 01
- Apache Airflow
- MLflow (tracking, registry)
- Python, pandas, numpy
- scikit-learn, XGBoost
- imbalanced-learn (SMOTE)
- SQLite (backend stores)

### Lab 02
- Pulumi (Python)
- AWS S3
- AWS CLI

### Lab 03
- DVC (Data Version Control)
- AWS S3
- Git

### Lab 04
- MLflow
- AWS S3
- boto3

### Lab 05
- FastAPI
- Pydantic
- Uvicorn
- Docker
- Docker Hub

### Lab 06
- GitHub Actions
- CodeQL
- Trivy
- AWS App Runner
- Pulumi

### Lab 07
- Prometheus
- Grafana
- Evidently AI
- Docker Compose

---

## Prerequisites by Lab

### Lab 01
- Basic Python knowledge
- Familiarity with pandas and scikit-learn
- Understanding of classification metrics
- Basic understanding of workflow orchestration

### Lab 02
- Completion of Lab 01
- AWS account with billing enabled
- Basic understanding of cloud storage concepts
- AWS CLI installed and configured

### Lab 03
- Completion of Lab 02
- Understanding of version control (Git)
- S3 bucket from Lab 02

### Lab 04
- Completion of Lab 02 and Lab 03
- Understanding of MLflow basics
- S3 bucket from Lab 02

### Lab 05
- Completion of Lab 03
- Basic understanding of REST APIs
- Docker installed
- Docker Hub account

### Lab 06
- Completion of Lab 05
- GitHub account
- GitHub repository for the project
- AWS credentials
- Docker Hub account

### Lab 07
- Completion of Lab 05
- Understanding of monitoring concepts
- Deployed API on AWS App Runner

---

## Common Commands Reference

### Lab 01 Commands
```bash
# Setup
python3 -m venv venv
source venv/bin/activate
pip install pandas numpy scikit-learn xgboost imbalanced-learn

# Run training
python training/scripts/run_preprocessing.py
python training/scripts/run_training.py
```

### Lab 02 Commands
```bash
# Start MLflow server
mlflow server --backend-store-uri sqlite:///mlflow.db \
  --default-artifact-root ./mlruns --host 0.0.0.0 --port 5000

# Run training with tracking
python training/scripts/run_training.py

# Compare experiments
python training/scripts/compare_experiments.py
```

### Lab 03 Commands
```bash
# Initialize Pulumi
pulumi new aws-python

# Deploy infrastructure
pulumi up

# Configure DVC
dvc remote add -d s3storage s3://bucket-name/dvc-storage
```

### Lab 04 Commands
```bash
# Run API locally
python app/main.py

# Build Docker image
docker build -t card-approval-api:latest .

# Run container
docker run -p 8000:8000 card-approval-api:latest

# Push to Docker Hub
docker push username/card-approval-api:latest
```

### Lab 05 Commands
```bash
# Create and push tag
git tag v1.0.0
git push origin v1.0.0

# View GitHub Actions
gh run list
gh run view
```

### Lab 06 Commands
```bash
# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# View metrics
curl http://localhost:8000/metrics

# Access UIs
open http://localhost:9090  # Prometheus
open http://localhost:3000  # Grafana
```

---

## Troubleshooting Index

Each lab includes a comprehensive troubleshooting section. Common issues:

### Lab 01
- SMOTE requires more samples
- XGBoost installation fails
- Model overfitting

### Lab 02
- Connection refused to MLflow server
- Model not found in registry
- Multiple models in Production stage

### Lab 03
- Access Denied to S3 bucket
- Bucket does not exist
- MLflow cannot write to S3

### Lab 04
- Model not found in registry
- Connection refused to MLflow
- Permission denied pushing to Docker Hub

### Lab 05
- Docker push unauthorized
- AWS credentials invalid
- Pulumi deployment fails

### Lab 06
- Prometheus cannot scrape metrics
- Grafana shows no data
- Drift detection fails

---

## Additional Resources

### Official Documentation
- [scikit-learn](https://scikit-learn.org/stable/)
- [XGBoost](https://xgboost.readthedocs.io/)
- [MLflow](https://mlflow.org/docs/latest/)
- [Pulumi](https://www.pulumi.com/docs/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [GitHub Actions](https://docs.github.com/en/actions)
- [Prometheus](https://prometheus.io/docs/)
- [Grafana](https://grafana.com/docs/)

### AWS Documentation
- [AWS S3](https://docs.aws.amazon.com/s3/)
- [AWS App Runner](https://docs.aws.amazon.com/apprunner/)
- [AWS IAM](https://docs.aws.amazon.com/iam/)

### Best Practices
- [MLOps Principles](https://ml-ops.org/)
- [12-Factor App](https://12factor.net/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Monitoring Best Practices](https://sre.google/sre-book/monitoring-distributed-systems/)

---

## Support

- **Issues:** Open an issue in the GitHub repository
- **Questions:** Check the troubleshooting section in each lab
- **Improvements:** Submit a pull request with suggested changes

---

**Last Updated:** February 21, 2026

**Version:** 1.0.0

**Maintainer:** Poridhi MLOps Team
