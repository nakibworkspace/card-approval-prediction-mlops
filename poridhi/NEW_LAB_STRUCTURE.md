# New Lab Structure - MLOps Pipeline

## Overview

This document outlines the restructured lab series for building a production-grade MLOps pipeline for credit card approval prediction. The labs progress from local development to cloud deployment with CI/CD.

## Lab Progression

### Lab 01: Airflow + MLflow (Local Development)
**Focus:** ML Pipeline Automation and Experiment Tracking

**Services (docker-compose.local.lab01.yml):**
- PostgreSQL (Airflow metadata)
- PostgreSQL (MLflow metadata)
- Airflow Webserver
- Airflow Scheduler
- MLflow Server

**What You Build:**
- Automated ML training pipeline with Airflow
- Experiment tracking with MLflow
- Model registry and versioning
- Complete data preprocessing pipeline
- Three model comparison (Logistic Regression, Random Forest, XGBoost)

**Key Files:**
- `dags/ml_training_pipeline.py` - Airflow DAG
- `training/scripts/preprocess_data.py` - Data preprocessing
- `training/scripts/train_models.py` - Model training with MLflow
- `docker-compose.local.lab01.yml` - Lab 01 services only

**Learning Outcomes:**
- Understand dataset challenges (imbalance, missing values)
- Justify model selection with clear reasoning
- Automate ML workflows with Airflow
- Track experiments systematically with MLflow
- Register and version models properly

---

### Lab 02: FastAPI Integration (Local Development)
**Focus:** Model Serving and API Development

**Services (docker-compose.local.lab02.yml):**
- All Lab 01 services +
- PostgreSQL (API database)
- Redis (caching)
- FastAPI Application

**What You Build:**
- RESTful API for model predictions
- Health and readiness endpoints
- Input validation with Pydantic
- Model loading from MLflow
- Caching layer with Redis
- Database for prediction logging

**Key Files:**
- `app/main.py` - FastAPI application
- `app/routers/predict.py` - Prediction endpoints
- `app/services/model_service.py` - Model loading and inference
- `app/services/preprocessing_service.py` - Feature preprocessing
- `docker-compose.local.lab02.yml` - Lab 01 + Lab 02 services

**Learning Outcomes:**
- Design RESTful APIs for ML models
- Implement proper input validation
- Load models from MLflow registry
- Add caching for performance
- Log predictions for monitoring

---

### Lab 03: Monitoring Stack (Local Development)
**Focus:** Observability and Monitoring

**Services (docker-compose.local.lab03.yml):**
- All Lab 02 services +
- Prometheus (metrics)
- Grafana (visualization)
- Loki (logs)
- Tempo (traces)
- Promtail (log collection)
- Nginx (reverse proxy)

**What You Build:**
- Prometheus metrics collection
- Grafana dashboards (system + ML metrics)
- Centralized logging with Loki
- Distributed tracing with Tempo
- Nginx reverse proxy for all services

**Key Files:**
- `app/core/metrics.py` - Prometheus metrics
- `app/core/tracing.py` - OpenTelemetry tracing
- `monitoring/prometheus/prometheus.yml` - Prometheus config
- `monitoring/grafana/dashboards/` - Grafana dashboards
- `nginx/nginx.conf` - Nginx configuration
- `docker-compose.local.lab03.yml` - Complete local stack

**Learning Outcomes:**
- Instrument applications with Prometheus
- Create meaningful ML dashboards
- Implement centralized logging
- Add distributed tracing
- Configure reverse proxy

---

### Lab 04: Production Containerization & Cloud Infrastructure
**Focus:** IaC, DVC, S3 Backend, Production Containers

**What You Build:**

**Part A: Pulumi Infrastructure as Code**
- S3 buckets (DVC storage, MLflow artifacts, training data)
- IAM roles and policies
- ECR repositories (optional)
- VPC and networking (for later labs)

**Part B: DVC Integration**
- Configure DVC with S3 backend
- Version control datasets
- Track data lineage
- Share data across team

**Part C: MLflow S3 Backend**
- Configure MLflow to use S3 for artifacts
- Update Airflow to use S3-backed MLflow
- Migrate existing models to S3

**Part D: Production Docker Compose Files**
- `docker-compose.airflow.yml` - Airflow + MLflow (production)
- `docker-compose.api.yml` - FastAPI service (production)
- `docker-compose.monitoring.yml` - Monitoring stack (production)

**Part E: DockerHub Push**
- Build production images
- Tag with versions
- Push to DockerHub
- Document image usage

**Key Files:**
- `pulumi/__main__.py` - Infrastructure definition
- `.dvc/config` - DVC S3 configuration
- `docker-compose.airflow.yml` - Production Airflow
- `docker-compose.api.yml` - Production API
- `docker-compose.monitoring.yml` - Production monitoring
- `.github/workflows/build-push.yml` - Docker build workflow

**Learning Outcomes:**
- Define infrastructure as code with Pulumi
- Version control data with DVC
- Configure S3 backends for MLflow
- Separate concerns with multiple compose files
- Build and publish production containers

---

### Lab 05: CI/CD with GitHub Actions
**Focus:** Automated Deployment to AWS EC2

**What You Build:**

**Part A: GitHub Actions Workflows**
- CI: Code quality, tests, security scans
- CD: Build, push to DockerHub, deploy to EC2

**Part B: EC2 Deployment**
- Provision EC2 instance with Pulumi
- Configure security groups
- Install Docker on EC2
- Set up deployment scripts

**Part C: Automated Deployment**
- Pull images from DockerHub
- Deploy with docker-compose
- Health checks and rollback
- Notifications (Slack/Email)

**Key Files:**
- `.github/workflows/ci.yml` - Continuous Integration
- `.github/workflows/cd.yml` - Continuous Deployment
- `pulumi/ec2.py` - EC2 infrastructure
- `scripts/deploy.sh` - Deployment script
- `scripts/health-check.sh` - Health verification

**Learning Outcomes:**
- Implement CI/CD pipelines with GitHub Actions
- Automate security scanning (CodeQL, Trivy)
- Deploy to EC2 from DockerHub
- Implement health checks and rollback
- Set up deployment notifications

---

## Docker Compose File Strategy

### Local Development (Labs 01-03)
**Purpose:** Incremental learning, all services on one machine

- `docker-compose.local.lab01.yml` - Airflow + MLflow only
- `docker-compose.local.lab02.yml` - Lab 01 + FastAPI + Redis + PostgreSQL
- `docker-compose.local.lab03.yml` - Lab 02 + Monitoring stack

**Usage:**
```bash
# Lab 01
docker-compose -f docker-compose.local.lab01.yml up -d

# Lab 02 (includes Lab 01 services)
docker-compose -f docker-compose.local.lab02.yml up -d

# Lab 03 (includes all services)
docker-compose -f docker-compose.local.lab03.yml up -d
```

### Production Deployment (Lab 04+)
**Purpose:** Separate concerns, independent scaling, cloud deployment

- `docker-compose.airflow.yml` - Training pipeline (can run on schedule)
- `docker-compose.api.yml` - API service (scales independently)
- `docker-compose.monitoring.yml` - Monitoring stack (separate instance)

**Usage:**
```bash
# On EC2 instance for training
docker-compose -f docker-compose.airflow.yml up -d

# On EC2 instance for API (different instance or same)
docker-compose -f docker-compose.api.yml up -d

# On EC2 instance for monitoring
docker-compose -f docker-compose.monitoring.yml up -d
```

---

## Key Principles

### 1. Incremental Complexity
Each lab builds on the previous, adding one major component at a time.

### 2. Local First, Cloud Later
Labs 01-03 run entirely locally. This allows learning without cloud costs or complexity.

### 3. Production Patterns
Even local labs follow production best practices (health checks, logging, metrics).

### 4. Clear Separation
Production compose files separate concerns (training, serving, monitoring).

### 5. Justification Required
Every decision (model choice, architecture, tool selection) must be justified.

---

## File Organization

```
card-approval-mlops/
├── dags/                           # Airflow DAGs
│   └── ml_training_pipeline.py
├── training/                       # ML training code
│   ├── data/
│   ├── scripts/
│   ├── src/
│   └── models/
├── app/                            # FastAPI application
│   ├── main.py
│   ├── core/
│   ├── routers/
│   ├── services/
│   └── schemas/
├── monitoring/                     # Monitoring configs
│   ├── prometheus/
│   ├── grafana/
│   ├── loki/
│   └── tempo/
├── pulumi/                         # Infrastructure as Code
│   ├── __main__.py
│   ├── s3.py
│   ├── ec2.py
│   └── iam.py
├── .github/workflows/              # CI/CD pipelines
│   ├── ci.yml
│   └── cd.yml
├── nginx/                          # Reverse proxy config
│   └── nginx.conf
├── scripts/                        # Utility scripts
│   ├── deploy.sh
│   └── health-check.sh
├── docker-compose.local.lab01.yml  # Lab 01 services
├── docker-compose.local.lab02.yml  # Lab 02 services
├── docker-compose.local.lab03.yml  # Lab 03 services
├── docker-compose.airflow.yml      # Production training
├── docker-compose.api.yml          # Production API
├── docker-compose.monitoring.yml   # Production monitoring
├── Dockerfile                      # API container
├── airflow/Dockerfile              # Airflow container
└── .env.example                    # Environment variables
```

---

## Lab Writing Standards

All labs follow the `standard.md` format:

### Required Sections
1. Introduction (2-3 sentences)
2. Learning Objectives (numbered, measurable)
3. Prologue: The Challenge (scenario-based motivation)
4. Environment Setup (exact commands)
5. Chapters (with subsections)
6. Epilogue: The Complete System
7. The Principles (generalizable takeaways)
8. Troubleshooting (common errors)
9. Next Steps (extensions)
10. Additional Resources (official docs only)

### Chapter Structure
- Opening Context (why this matters)
- What You Will Build
- Think First (pre-implementation questions)
- Implementation (with detailed code explanations)
- Understanding the Code (concept verification)
- Test and Verify (with predictions)
- Checkpoint (self-assessment)
- Experiment (optional failure scenarios)

### Code Explanation Requirements
- Every code block must have detailed explanations
- Explain WHY, not just WHAT
- Comment non-obvious lines
- Justify parameter choices
- Show expected output

### Active Learning
- 70% active (fill-in-blanks, predictions, exercises)
- 30% passive (explanations, complete code)
- Self-assessment at each checkpoint
- Conceptual questions with detailed answers

---

## Migration from Old Structure

### Old Labs → New Labs Mapping

**Old Lab 01 (Model Development)** → **New Lab 01 (Airflow + MLflow)**
- Adds: Airflow orchestration, automated pipeline
- Keeps: Model training, MLflow tracking

**Old Lab 02 (AWS Integration)** → **New Lab 04 (Pulumi + DVC + S3)**
- Moves cloud setup to Lab 04
- Adds: DVC, production containers

**Old Lab 05 (FastAPI)** → **New Lab 02 (FastAPI)**
- Moves earlier in sequence
- Adds: Redis caching, better structure

**Old Lab 07 (Monitoring)** → **New Lab 03 (Monitoring)**
- Moves earlier in sequence
- Adds: Complete observability stack

**Old Lab 06 (CI/CD)** → **New Lab 05 (CI/CD)**
- Stays at end
- Adds: EC2 deployment, DockerHub integration

---

## Next Steps

1. Complete Lab 01 implementation (Parts 3-4)
2. Create docker-compose.local.lab01.yml
3. Write Lab 02 (FastAPI integration)
4. Create docker-compose.local.lab02.yml
5. Write Lab 03 (Monitoring)
6. Create docker-compose.local.lab03.yml
7. Write Lab 04 (Production + Cloud)
8. Create production docker-compose files
9. Write Lab 05 (CI/CD)
10. Test complete pipeline end-to-end

---

## Success Criteria

Each lab must:
- [ ] Follow standard.md format exactly
- [ ] Include detailed code explanations
- [ ] Provide context before self-assessments
- [ ] Use active learning techniques (70/30 ratio)
- [ ] Include working code (tested)
- [ ] Have clear learning objectives
- [ ] Build incrementally on previous labs
- [ ] Justify all technical decisions
- [ ] Include troubleshooting section
- [ ] Provide next steps for extension
