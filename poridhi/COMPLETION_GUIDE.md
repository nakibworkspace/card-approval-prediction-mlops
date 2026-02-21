# Lab Completion Guide

## Overview

This guide helps you track your progress through all six Poridhi MLOps labs and verify you've achieved the learning objectives.

## Lab Completion Checklist

### Lab 01: Automated ML Pipeline with Airflow & MLflow ✓

**Estimated Time:** 6-8 hours

**Completion Criteria:**
- [ ] Airflow initialized and running
- [ ] MLflow server running
- [ ] ML pipeline DAG created
- [ ] All pipeline tasks implemented (download, EDA, preprocess, train, evaluate, register)
- [ ] MLflow tracking integrated within Airflow tasks
- [ ] SMOTE balancing applied in preprocessing task
- [ ] Multiple models trained automatically
- [ ] Best model registered to MLflow Registry
- [ ] Pipeline triggered and completed successfully

**Key Deliverable:** Fully automated ML pipeline with Airflow orchestration and MLflow tracking

**Verification Command:**
```bash
# Check Airflow
curl http://localhost:8080

# Check MLflow
curl http://localhost:5000/api/2.0/mlflow/experiments/list

# Trigger pipeline
airflow dags trigger credit_card_ml_pipeline

# Check DAG status
airflow dags list | grep credit_card
```

---

### Lab 02: Infrastructure as Code (Pulumi) & S3 ✓

**Estimated Time:** 2-3 hours

**Completion Criteria:**
- [ ] Pulumi CLI installed and configured
- [ ] AWS credentials configured
- [ ] S3 bucket created with Pulumi
- [ ] Bucket versioning enabled
- [ ] Bucket encryption enabled
- [ ] Public access blocked

**Key Deliverable:** Cloud infrastructure defined as code with S3 bucket

**Verification Command:**
```bash
cd pulumi
pulumi stack output bucket_name
aws s3 ls s3://$(pulumi stack output bucket_name)/
```

---

### Lab 03: Data Versioning with DVC ✓

**Estimated Time:** 2-3 hours

**Completion Criteria:**
- [ ] DVC initialized in project
- [ ] S3 remote storage configured
- [ ] Training data tracked with DVC
- [ ] Processed data tracked with DVC
- [ ] Data pushed to S3 successfully
- [ ] Data can be pulled from S3

**Key Deliverable:** Cloud-versioned datasets with DVC tracking

**Verification Command:**
```bash
# Check DVC status
dvc status

# Verify S3 storage
aws s3 ls s3://your-bucket/dvc-storage/ --recursive

# Test pull
dvc pull
```

---

### Lab 04: MLflow + S3 Integration ✓

**Estimated Time:** 2-3 hours

**Completion Criteria:**
- [ ] MLflow configured to use S3 for artifacts
- [ ] Training runs with S3 artifact storage
- [ ] Model artifacts uploaded to S3
- [ ] Models can be loaded from S3
- [ ] Model Registry integrated with S3

**Key Deliverable:** MLflow experiments and models stored in S3

**Verification Command:**
```bash
# Train with S3 storage
python training/scripts/run_training_s3.py

# Verify in S3
aws s3 ls s3://$MLFLOW_S3_BUCKET/mlflow-artifacts/ --recursive

# Load model from S3
python training/scripts/load_model_s3.py
```

---

### Lab 05: The Prediction API (FastAPI) & Docker Hub ✓

**Estimated Time:** 3-4 hours

**Completion Criteria:**
- [ ] FastAPI application created
- [ ] Health and readiness endpoints implemented
- [ ] Pydantic models for input validation
- [ ] Model service loads from S3
- [ ] Prediction endpoint returns correct format
- [ ] Dockerfile created
- [ ] Docker image builds successfully
- [ ] Container runs locally
- [ ] Image pushed to Docker Hub

**Key Deliverable:** Containerized API on Docker Hub

**Verification Command:**
```bash
# Build and run
docker build -t card-approval-api:latest .
docker run -p 8000:8000 card-approval-api:latest

# Test
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/v1/predict -H "Content-Type: application/json" -d @test_payload.json
```

---

### Lab 06: CI/CD & Security (GitHub Actions) ✓

**Estimated Time:** 2-3 hours

**Completion Criteria:**
- [ ] GitHub repository created
- [ ] CI workflow runs on push/PR
- [ ] Linting and tests automated
- [ ] CodeQL security scanning enabled
- [ ] CD workflow triggers on version tags
- [ ] Docker image built and pushed automatically
- [ ] Trivy container scanning implemented
- [ ] Pulumi deployment automated
- [ ] Application deployed to AWS App Runner
- [ ] Deployment URL accessible

**Key Deliverable:** Live production API with automated deployment

**Verification Command:**
```bash
# Create and push tag
git tag v1.0.0
git push origin v1.0.0

# Check GitHub Actions
# Navigate to: https://github.com/your-username/card-approval-prediction/actions

# Test deployed API
curl https://your-app-runner-url.awsapprunner.com/health
```

---

### Lab 07: Observability (Prometheus & Grafana) ✓

**Estimated Time:** 3-4 hours

**Completion Criteria:**
- [ ] Prometheus metrics instrumented in API
- [ ] Metrics endpoint returns Prometheus format
- [ ] Prometheus server scraping metrics
- [ ] Grafana connected to Prometheus
- [ ] Dashboard created with key metrics
- [ ] Request rate visualized
- [ ] Latency percentiles tracked
- [ ] Prediction distribution monitored
- [ ] Data drift detection implemented
- [ ] Alert rules configured

**Key Deliverable:** Production monitoring dashboard

**Verification Command:**
```bash
# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Check metrics
curl http://localhost:8000/metrics

# Access dashboards
open http://localhost:9090  # Prometheus
open http://localhost:3000  # Grafana (admin/admin)
```

---

## Final System Verification

Once all labs are complete, verify the entire system:

### 1. Local Development Environment

```bash
# Training pipeline
python training/scripts/run_preprocessing.py
python training/scripts/run_training.py

# MLflow
curl http://localhost:5000

# API
python app/main.py
curl http://localhost:8000/docs
```

### 2. Cloud Infrastructure

```bash
# Pulumi
cd pulumi
pulumi stack output

# S3
aws s3 ls s3://$(pulumi stack output bucket_name)/

# App Runner
curl $(pulumi stack output api_url)/health
```

### 3. CI/CD Pipeline

```bash
# Check GitHub Actions status
gh run list

# View latest deployment
gh run view
```

### 4. Monitoring

```bash
# Prometheus targets
curl http://localhost:9090/api/v1/targets

# Grafana health
curl http://localhost:3000/api/health
```

## Skills Acquired

After completing all labs, you have demonstrated:

### Technical Skills
- ✅ Automated ML pipeline orchestration with Airflow
- ✅ Experiment tracking with MLflow
- ✅ Infrastructure as Code with Pulumi
- ✅ Data version control with DVC
- ✅ Cloud artifact storage with S3
- ✅ API development with FastAPI
- ✅ Container orchestration with Docker
- ✅ CI/CD pipeline implementation
- ✅ Cloud deployment on AWS
- ✅ Monitoring and observability

### MLOps Practices
- ✅ Version control for code, data, and models
- ✅ Automated testing and quality gates
- ✅ Security scanning (SAST, container scanning)
- ✅ Continuous deployment
- ✅ Production monitoring
- ✅ Data drift detection

### Cloud & DevOps
- ✅ AWS services (S3, App Runner, IAM)
- ✅ GitHub Actions workflows
- ✅ Docker containerization
- ✅ Prometheus metrics
- ✅ Grafana dashboards

## Common Issues & Solutions

### Issue: MLflow cannot connect to S3

**Solution:**
```bash
# Verify AWS credentials
aws sts get-caller-identity

# Check S3 bucket exists
aws s3 ls s3://your-bucket-name

# Verify environment variables
echo $MLFLOW_S3_BUCKET
```

### Issue: Docker container cannot access localhost services

**Solution:**
Use `host.docker.internal` instead of `localhost` in container environment variables.

### Issue: GitHub Actions workflow fails

**Solution:**
```bash
# Check secrets are configured
gh secret list

# View workflow logs
gh run view --log
```

### Issue: Prometheus not scraping metrics

**Solution:**
```bash
# Check API metrics endpoint
curl http://localhost:8000/metrics

# Verify Prometheus config
docker exec prometheus cat /etc/prometheus/prometheus.yml

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets
```

## Next Steps

### Immediate Improvements
1. Add comprehensive unit tests
2. Implement API authentication
3. Add rate limiting
4. Configure automated alerts
5. Create runbooks for common issues

### Advanced Features
1. A/B testing for model versions
2. Automated model retraining pipeline
3. Feature store integration
4. Multi-region deployment
5. Kubernetes deployment

### Production Hardening
1. Add load balancing
2. Implement caching layer
3. Set up disaster recovery
4. Configure auto-scaling
5. Add WAF for security

## Certification

You have completed the Poridhi MLOps Labs when:

- ✅ All 7 labs completed
- ✅ All checkpoints passed
- ✅ Final system verification successful
- ✅ Production API deployed and monitored
- ✅ CI/CD pipeline operational
- ✅ Automated ML pipeline running

**Congratulations!** You have built a production-grade MLOps system from scratch.

## Resources for Continued Learning

### Books
- "Designing Machine Learning Systems" by Chip Huyen
- "Machine Learning Engineering" by Andriy Burkov
- "Building Machine Learning Powered Applications" by Emmanuel Ameisen

### Online Courses
- MLOps Specialization (Coursera)
- AWS Machine Learning Engineer (AWS Training)
- Full Stack Deep Learning

### Communities
- MLOps Community Slack
- r/MachineLearning
- AWS ML Community

### Blogs & Newsletters
- MLOps.community
- The Batch (deeplearning.ai)
- AWS Machine Learning Blog

---

**Project Repository:** https://github.com/your-username/card-approval-prediction

**Documentation:** See individual lab files in the `poridhi/` directory

**Support:** Open an issue in the GitHub repository for questions or problems
