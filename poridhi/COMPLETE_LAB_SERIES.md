# Complete MLOps Lab Series - Summary

## Overview

This comprehensive lab series takes you from local ML development to production-grade MLOps deployment on AWS. Each lab builds incrementally, following industry best practices and the standard.md format.

## Lab Series Structure

### Lab 01: Airflow + MLflow (Local Development)
**Files:**
- `lab-01-airflow-mlflow-local.md` - Introduction, dataset understanding, model selection
- `lab-01-airflow-mlflow-local-part2.md` - Data preprocessing
- `lab-01-part3-model-training.md` - Model training with MLflow
- `lab-01-part4-airflow-integration.md` - Docker Compose and Airflow tasks
- `lab-01-part5-dag-epilogue.md` - DAG implementation and completion

**Docker Compose:** `docker-compose.local.lab01.yml`

**What You Build:**
- Automated ML training pipeline with Apache Airflow
- Experiment tracking with MLflow
- Model registry and versioning
- Three model comparison (Logistic Regression, Random Forest, XGBoost)
- Complete data preprocessing pipeline

**Services:**
- PostgreSQL (Airflow metadata)
- PostgreSQL (MLflow metadata)
- MLflow Server
- Airflow Webserver
- Airflow Scheduler

**Access:**
- Airflow UI: http://localhost:8080
- MLflow UI: http://localhost:5000

---

### Lab 02: FastAPI Integration (Local Development)
**Files:**
- `lab-02-fastapi-integration.md` - API design, configuration, database
- `lab-02-part2-schemas-services.md` - Pydantic schemas and model service
- `lab-02-part3-preprocessing-caching.md` - Preprocessing service, Redis caching, routers

**Docker Compose:** `docker-compose.local.lab02.yml`

**What You Build:**
- RESTful API for model predictions
- Input validation with Pydantic
- Model loading from MLflow Registry
- Redis caching for performance
- PostgreSQL for prediction logging
- Health and readiness endpoints

**New Services (adds to Lab 01):**
- PostgreSQL (API database)
- Redis (caching)
- FastAPI Application

**Access:**
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- All Lab 01 services

---

### Lab 03: Monitoring Stack (Local Development)
**File:** `lab-03-monitoring-observability.md`

**Docker Compose:** `docker-compose.local.lab03.yml`

**What You Build:**
- Prometheus metrics collection
- Grafana dashboards (system + ML metrics)
- Centralized logging with Loki
- Distributed tracing with Tempo
- Nginx reverse proxy

**New Services (adds to Lab 02):**
- Prometheus (metrics)
- Grafana (visualization)
- Loki (logs)
- Tempo (traces)
- Promtail (log collection)
- Nginx (reverse proxy)

**Access:**
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090
- All services via Nginx: http://localhost/

---

### Lab 04: Production & Cloud (AWS Deployment)
**File:** `lab-04-production-cloud.md`

**Docker Compose:**
- `docker-compose.airflow.yml` - Training pipeline (production)
- `docker-compose.api.yml` - API service (production)
- `docker-compose.monitoring.yml` - Monitoring stack (production)

**What You Build:**
- Pulumi infrastructure as code (S3, IAM, VPC)
- DVC for data versioning
- MLflow with S3 artifact storage
- Production-optimized Docker images
- DockerHub image publishing
- Separated service deployments

**Key Changes:**
- Local storage → S3 buckets
- Single compose file → Multiple compose files
- Development images → Production images
- Manual deployment → Infrastructure as code

---

### Lab 05: CI/CD (GitHub Actions + EC2)
**File:** `lab-05-cicd-deployment.md`

**What You Build:**
- GitHub Actions CI workflow (tests, security, quality)
- GitHub Actions CD workflow (build, push, deploy)
- EC2 deployment automation
- Health checks and rollback
- Deployment notifications

**CI Pipeline:**
1. Code quality checks (Black, Flake8, Pylint)
2. Security scanning (CodeQL, Trivy, Bandit)
3. Unit tests with coverage
4. Docker build and scan

**CD Pipeline:**
1. Build Docker image
2. Push to DockerHub
3. Deploy to EC2
4. Health check
5. Rollback on failure
6. Notify team

---

## Complete Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         GitHub Repository                        │
│                    (Code + DVC + CI/CD)                         │
└────────────┬────────────────────────────────────────────────────┘
             │
             │ Push → CI/CD
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      GitHub Actions                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Tests   │  │ Security │  │  Build   │  │  Deploy  │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└────────────┬────────────────────────────────────────────────────┘
             │
             │ Push Images
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                         DockerHub                                │
│              (card-approval-api:latest)                          │
└────────────┬────────────────────────────────────────────────────┘
             │
             │ Pull & Deploy
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AWS EC2 Instance                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Training Pipeline (docker-compose.airflow.yml)          │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │  │
│  │  │ Airflow  │→ │  MLflow  │→ │   S3     │              │  │
│  │  └──────────┘  └──────────┘  └──────────┘              │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  API Service (docker-compose.api.yml)                    │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │  │
│  │  │ FastAPI  │→ │  Redis   │→ │PostgreSQL│              │  │
│  │  └──────────┘  └──────────┘  └──────────┘              │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Monitoring (docker-compose.monitoring.yml)              │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │  │
│  │  │Prometheus│→ │ Grafana  │→ │   Loki   │              │  │
│  │  └──────────┘  └──────────┘  └──────────┘              │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
             ▲
             │
             │ Store/Retrieve
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                          AWS S3                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ DVC Storage  │  │   MLflow     │  │   Training   │         │
│  │ (Datasets)   │  │  Artifacts   │  │    Data      │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

## Technology Stack

| Category | Technologies |
|----------|-------------|
| **Orchestration** | Apache Airflow 2.8 |
| **Experiment Tracking** | MLflow |
| **API Framework** | FastAPI, Uvicorn |
| **Data Validation** | Pydantic |
| **Caching** | Redis |
| **Database** | PostgreSQL |
| **ML Libraries** | scikit-learn, XGBoost, imbalanced-learn |
| **Data Versioning** | DVC |
| **Infrastructure** | Pulumi (Python) |
| **Cloud** | AWS (S3, EC2, IAM) |
| **Containerization** | Docker, Docker Compose |
| **Registry** | DockerHub |
| **CI/CD** | GitHub Actions |
| **Monitoring** | Prometheus, Grafana |
| **Logging** | Loki, Promtail |
| **Tracing** | Tempo, OpenTelemetry |
| **Reverse Proxy** | Nginx |

## File Structure

```
card-approval-mlops/
├── poridhi/                                    # Lab documentation
│   ├── lab-01-airflow-mlflow-local.md
│   ├── lab-01-airflow-mlflow-local-part2.md
│   ├── lab-01-part3-model-training.md
│   ├── lab-01-part4-airflow-integration.md
│   ├── lab-01-part5-dag-epilogue.md
│   ├── lab-02-fastapi-integration.md
│   ├── lab-02-part2-schemas-services.md
│   ├── lab-02-part3-preprocessing-caching.md
│   ├── lab-03-monitoring-observability.md
│   ├── lab-04-production-cloud.md
│   ├── lab-05-cicd-deployment.md
│   └── COMPLETE_LAB_SERIES.md (this file)
│
├── dags/                                       # Airflow DAGs
│   └── ml_training_pipeline.py
│
├── training/                                   # ML training code
│   ├── data/
│   │   ├── raw/
│   │   └── processed/
│   ├── scripts/
│   │   ├── preprocess_data.py
│   │   ├── train_models.py
│   │   └── airflow_tasks.py
│   ├── src/
│   │   ├── config/
│   │   └── utils/
│   └── models/
│
├── app/                                        # FastAPI application
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── logging.py
│   │   ├── metrics.py
│   │   └── tracing.py
│   ├── routers/
│   │   ├── health.py
│   │   └── predict.py
│   ├── schemas/
│   │   ├── health.py
│   │   └── prediction.py
│   ├── services/
│   │   ├── model_service.py
│   │   ├── preprocessing_service.py
│   │   └── cache_service.py
│   └── utils/
│
├── monitoring/                                 # Monitoring configs
│   ├── prometheus/
│   │   └── prometheus.yml
│   ├── grafana/
│   │   ├── provisioning/
│   │   └── dashboards/
│   ├── loki/
│   │   └── loki-config.yml
│   ├── tempo/
│   │   └── tempo-config.yml
│   └── promtail/
│       └── promtail-config.yml
│
├── pulumi/                                     # Infrastructure as Code
│   ├── __main__.py
│   ├── s3.py
│   ├── iam.py
│   ├── ec2.py
│   ├── security_group.py
│   └── Pulumi.yaml
│
├── .github/workflows/                          # CI/CD pipelines
│   ├── ci.yml
│   └── cd.yml
│
├── scripts/deployment/                         # Deployment scripts
│   ├── deploy.sh
│   ├── rollback.sh
│   └── health-check.sh
│
├── nginx/                                      # Reverse proxy
│   └── nginx.conf
│
├── airflow/                                    # Airflow Docker
│   ├── Dockerfile
│   └── requirements-airflow.txt
│
├── docker-compose.local.lab01.yml              # Lab 01 services
├── docker-compose.local.lab02.yml              # Lab 02 services
├── docker-compose.local.lab03.yml              # Lab 03 services
├── docker-compose.airflow.yml                  # Production training
├── docker-compose.api.yml                      # Production API
├── docker-compose.monitoring.yml               # Production monitoring
│
├── Dockerfile.api                              # API production image
├── requirements-api.txt                        # API dependencies
├── .env.example                                # Environment template
├── .dvcignore                                  # DVC ignore patterns
├── dvc.yaml                                    # DVC pipeline
└── README.md                                   # Project README
```

## Quick Start Guide

### Local Development (Labs 01-03)

```bash
# Lab 01: Training Pipeline
docker-compose -f docker-compose.local.lab01.yml up -d
# Access: Airflow (8080), MLflow (5000)

# Lab 02: Add API
docker-compose -f docker-compose.local.lab02.yml up -d
# Access: API (8000), API Docs (8000/docs)

# Lab 03: Add Monitoring
docker-compose -f docker-compose.local.lab03.yml up -d
# Access: Grafana (3000), Prometheus (9090)
```

### Production Deployment (Labs 04-05)

```bash
# Lab 04: Infrastructure
cd pulumi
pulumi up
cd ..

# Configure DVC
dvc remote add -d s3storage s3://your-bucket/dvc-storage
dvc push

# Build and push images
docker build -f Dockerfile.api -t yourusername/card-approval-api:latest .
docker push yourusername/card-approval-api:latest

# Lab 05: Deploy to EC2
# Push to main branch → GitHub Actions deploys automatically
git push origin main
```

## Learning Path

**Week 1: Local Development**
- Day 1-2: Lab 01 (Airflow + MLflow)
- Day 3-4: Lab 02 (FastAPI)
- Day 5: Lab 03 (Monitoring)

**Week 2: Production**
- Day 1-2: Lab 04 Part 1 (Pulumi + DVC)
- Day 3-4: Lab 04 Part 2 (Production Images)
- Day 5: Lab 05 (CI/CD)

**Week 3: Optimization**
- Tune hyperparameters
- Optimize Docker images
- Add more dashboards
- Implement alerting

## Key Principles Across All Labs

1. **Incremental Complexity** — Each lab adds one major component
2. **Local First, Cloud Later** — Master locally before cloud
3. **Production Patterns** — Even local labs follow best practices
4. **Clear Separation** — Training, serving, monitoring are independent
5. **Justification Required** — Every decision explained
6. **Active Learning** — Think First questions, self-assessments
7. **Detailed Context** — Code explained, not just shown
8. **Troubleshooting** — Common errors documented

## Success Criteria

After completing all labs, you should be able to:

✅ Build automated ML training pipelines
✅ Track experiments with MLflow
✅ Serve models via REST API
✅ Implement caching and validation
✅ Monitor system and ML metrics
✅ Aggregate logs and traces
✅ Define infrastructure as code
✅ Version control data
✅ Build production Docker images
✅ Implement CI/CD pipelines
✅ Deploy to cloud (AWS)
✅ Handle failures and rollback

## Common Issues & Solutions

**Issue: Services not starting**
```bash
# Check logs
docker-compose logs service-name

# Check ports
netstat -an | grep PORT

# Restart
docker-compose down
docker-compose up -d
```

**Issue: Model not loading**
```bash
# Check MLflow connection
curl http://localhost:5000/health

# Check model exists
docker exec container-name python -c "import mlflow; print(mlflow.search_registered_models())"
```

**Issue: Deployment failing**
```bash
# Check GitHub Actions logs
# Settings → Actions → Latest run

# SSH to EC2
ssh ubuntu@your-ec2-ip

# Check services
docker-compose ps
```

## Additional Resources

- [Apache Airflow Docs](https://airflow.apache.org/docs/)
- [MLflow Docs](https://mlflow.org/docs/latest/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Prometheus Docs](https://prometheus.io/docs/)
- [Grafana Docs](https://grafana.com/docs/)
- [Pulumi Docs](https://www.pulumi.com/docs/)
- [DVC Docs](https://dvc.org/doc)
- [GitHub Actions Docs](https://docs.github.com/en/actions)

## Contributing

To improve these labs:
1. Follow standard.md format
2. Test all code examples
3. Provide detailed explanations
4. Include troubleshooting
5. Add self-assessments

## License

MIT License - See LICENSE file

---

**🎉 Complete MLOps Lab Series**

From local development to production deployment, you now have a comprehensive guide to building production-grade ML systems. Each lab is self-contained yet builds on previous knowledge, following industry best practices throughout.

**Happy Learning! 🚀**
