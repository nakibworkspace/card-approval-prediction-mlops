# Lab Restructuring Summary

## What Has Been Done

I've started restructuring the labs according to your requirements. Here's what's been created:

### 1. New Lab Structure Document
**File:** `poridhi/NEW_LAB_STRUCTURE.md`

This document outlines the complete new lab structure:
- Lab 01: Airflow + MLflow (Local)
- Lab 02: FastAPI Integration (Local)
- Lab 03: Monitoring Stack (Local)
- Lab 04: Production Containerization + Cloud (Pulumi, DVC, S3, DockerHub)
- Lab 05: CI/CD with GitHub Actions (EC2 Deployment)

### 2. Lab 01 - Part 1 (Completed)
**File:** `poridhi/lab-01-airflow-mlflow-local.md`

**Content:**
- Introduction and learning objectives
- Prologue with real-world scenario
- Environment setup
- Chapter 1: Understanding the Dataset
  - Dataset characteristics
  - Think First questions with detailed answers
  - EDA implementation with full code explanations
  - Preprocessing strategy development
  - Checkpoint with self-assessment
- Chapter 2: Model Selection Strategy
  - Why multiple models (No Free Lunch Theorem)
  - Three-model approach with justifications
  - Evaluation metrics strategy
  - Think First questions
  - Checkpoint with self-assessment

**Key Features:**
- Detailed code explanations for every block
- Context provided before self-assessments
- Active learning with Think First questions
- Justification for every decision
- Follows standard.md format

### 3. Lab 01 - Part 2 (Completed)
**File:** `poridhi/lab-01-airflow-mlflow-local-part2.md`

**Content:**
- Chapter 3: Data Preprocessing Implementation
  - Complete preprocessing pipeline with detailed explanations
  - Step-by-step code walkthrough
  - Explanation of each preprocessing decision
  - Testing instructions
  - Checkpoint with practical exercises

**Key Features:**
- Line-by-line code explanations
- Rationale for each preprocessing step
- Data leakage prevention explained
- SMOTE strategy justified
- Verification steps included

## What Still Needs to Be Done

### Lab 01 - Remaining Parts

**Part 3: Model Training Implementation**
- Complete training script with MLflow integration
- Detailed explanation of each model
- Hyperparameter justification
- Metrics calculation and interpretation
- Model comparison logic

**Part 4: Airflow Integration**
- Docker Compose setup for Lab 01
- Airflow DAG implementation
- Task definitions with MLflow tracking
- Pipeline testing and verification
- MLflow UI walkthrough
- Complete epilogue and principles

**Part 5: Docker Compose File**
- `docker-compose.local.lab01.yml` with only:
  - PostgreSQL (Airflow)
  - PostgreSQL (MLflow)
  - Airflow Webserver
  - Airflow Scheduler
  - Airflow Init
  - MLflow Server

### Lab 02: FastAPI Integration

**Content Needed:**
- Introduction and prologue
- Chapter 1: API Design
  - RESTful principles
  - Endpoint design
  - Input validation strategy
- Chapter 2: FastAPI Implementation
  - Application structure
  - Health endpoints
  - Prediction endpoints
  - Model loading from MLflow
- Chapter 3: Caching and Database
  - Redis integration
  - PostgreSQL for predictions
  - Performance optimization
- Chapter 4: Testing and Verification
- Docker Compose file: `docker-compose.local.lab02.yml`

### Lab 03: Monitoring Stack

**Content Needed:**
- Introduction and prologue
- Chapter 1: Prometheus Metrics
  - Instrumentation
  - Custom metrics
  - ML-specific metrics
- Chapter 2: Grafana Dashboards
  - Dashboard design
  - System metrics
  - ML metrics
- Chapter 3: Logging with Loki
  - Log aggregation
  - Query language
- Chapter 4: Tracing with Tempo
  - OpenTelemetry integration
  - Distributed tracing
- Chapter 5: Nginx Reverse Proxy
- Docker Compose file: `docker-compose.local.lab03.yml`

### Lab 04: Production & Cloud

**Content Needed:**
- Introduction and prologue
- Chapter 1: Pulumi Infrastructure
  - S3 buckets
  - IAM roles
  - VPC setup
- Chapter 2: DVC Integration
  - Configuration
  - Data versioning
  - Team collaboration
- Chapter 3: MLflow S3 Backend
  - Configuration
  - Migration
- Chapter 4: Production Containers
  - Dockerfile optimization
  - Multi-stage builds
  - Security hardening
- Chapter 5: DockerHub Publishing
  - Build process
  - Tagging strategy
  - Push workflow
- Docker Compose files:
  - `docker-compose.airflow.yml`
  - `docker-compose.api.yml`
  - `docker-compose.monitoring.yml`

### Lab 05: CI/CD

**Content Needed:**
- Introduction and prologue
- Chapter 1: GitHub Actions CI
  - Code quality checks
  - Security scanning
  - Unit tests
- Chapter 2: GitHub Actions CD
  - Build and push
  - Deployment workflow
- Chapter 3: EC2 Deployment
  - Infrastructure setup
  - Deployment scripts
  - Health checks
- Chapter 4: Monitoring Deployment
  - Rollback strategy
  - Notifications

## Key Principles Being Followed

### 1. Standard.md Compliance
- All required sections included
- Chapter structure followed
- Active learning techniques used

### 2. Code Explanations
- Every code block has detailed explanations
- WHY explained, not just WHAT
- Parameter choices justified
- Expected outputs shown

### 3. Context Before Assessment
- Self-assessments come after substantial content
- Conceptual questions with detailed answers
- Practical exercises included

### 4. Active Learning (70/30 Ratio)
- Think First questions
- Prediction exercises
- Fill-in-the-blank code (to be added)
- Matching exercises (to be added)
- Scenario questions

### 5. Incremental Complexity
- Lab 01: Local Airflow + MLflow
- Lab 02: Add FastAPI
- Lab 03: Add Monitoring
- Lab 04: Move to Cloud
- Lab 05: Add CI/CD

## Docker Compose Strategy

### Local Development (Labs 01-03)
Each lab has its own compose file that includes all previous services:

```bash
# Lab 01: Just training pipeline
docker-compose -f docker-compose.local.lab01.yml up -d

# Lab 02: Training + API
docker-compose -f docker-compose.local.lab02.yml up -d

# Lab 03: Training + API + Monitoring
docker-compose -f docker-compose.local.lab03.yml up -d
```

### Production (Lab 04+)
Separate compose files for independent deployment:

```bash
# Training pipeline (can run on schedule)
docker-compose -f docker-compose.airflow.yml up -d

# API service (scales independently)
docker-compose -f docker-compose.api.yml up -d

# Monitoring (separate instance)
docker-compose -f docker-compose.monitoring.yml up -d
```

## Next Steps

### Immediate (Complete Lab 01)
1. Write Lab 01 Part 3 (Model Training)
2. Write Lab 01 Part 4 (Airflow Integration)
3. Create `docker-compose.local.lab01.yml`
4. Test Lab 01 end-to-end

### Short Term (Labs 02-03)
5. Write Lab 02 (FastAPI)
6. Create `docker-compose.local.lab02.yml`
7. Write Lab 03 (Monitoring)
8. Create `docker-compose.local.lab03.yml`

### Medium Term (Labs 04-05)
9. Write Lab 04 (Production + Cloud)
10. Create production docker-compose files
11. Write Lab 05 (CI/CD)
12. Test complete pipeline

### Final
13. Review all labs for standard.md compliance
14. Verify code explanations are detailed
15. Test all docker-compose files
16. Create lab index and navigation

## Questions to Address

1. **Dataset Source:** Where should students get the credit card approval dataset?
   - Kaggle API?
   - Provided CSV?
   - S3 download?

2. **AWS Costs:** Should we provide cost estimates for Lab 04-05?

3. **Prerequisites:** Should we create a "Lab 00" for Docker/Python setup?

4. **Lab Length:** Current Lab 01 is quite long. Should we split further?

5. **Code Repository:** Should students fork a template repo or build from scratch?

## Estimated Completion Time

- Lab 01 completion: 4-6 hours
- Lab 02: 6-8 hours
- Lab 03: 6-8 hours
- Lab 04: 8-10 hours
- Lab 05: 6-8 hours
- Testing and refinement: 4-6 hours

**Total: 34-46 hours of work**

## How to Continue

To continue this restructuring:

1. Review the completed Lab 01 parts
2. Provide feedback on structure and explanations
3. Confirm the docker-compose strategy
4. I'll continue with Lab 01 Parts 3-4
5. Then proceed to Labs 02-05

Would you like me to:
- Continue with Lab 01 Part 3 (Model Training)?
- Adjust anything in the current structure?
- Focus on a specific lab first?
