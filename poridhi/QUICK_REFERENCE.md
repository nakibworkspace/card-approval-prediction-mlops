# Poridhi Labs - Quick Reference Card

## Lab Overview

| # | Lab | Focus | Time | Key Deliverable |
|---|-----|-------|------|-----------------|
| 1 | Automated ML Pipeline | Airflow + MLflow | 6-8h | Automated pipeline |
| 2 | Pulumi & S3 | Cloud Infrastructure | 2-3h | S3 buckets |
| 3 | DVC | Data Versioning | 2-3h | Versioned datasets |
| 4 | MLflow + S3 | Cloud Experiments | 2-3h | S3 artifact storage |
| 5 | FastAPI & Docker | API Development | 3-4h | Containerized API |
| 6 | GitHub Actions | CI/CD Pipeline | 2-3h | Automated deployment |
| 7 | Prometheus & Grafana | Monitoring | 3-4h | Observability dashboard |

## Essential Commands

### Lab 01: Airflow + MLflow
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
open http://localhost:8080  # Airflow
open http://localhost:5000  # MLflow
```

### Lab 02: Pulumi & S3
```bash
# Initialize
pulumi new aws-python

# Deploy
pulumi up

# Get outputs
pulumi stack output bucket_name

# Verify S3
aws s3 ls s3://$(pulumi stack output bucket_name)/
```

### Lab 03: DVC
```bash
# Initialize DVC
dvc init

# Configure S3 remote
dvc remote add -d s3storage s3://your-bucket/dvc-storage
dvc remote modify s3storage region us-east-1

# Track data
dvc add training/data/raw
dvc add training/data/processed

# Push to S3
dvc push

# Pull from S3
dvc pull
```

### Lab 04: MLflow + S3
```bash
# Set environment variables
export MLFLOW_S3_BUCKET=your-bucket-name
export AWS_REGION=us-east-1

# Train with S3 storage
python training/scripts/run_training_s3.py

# Verify in S3
aws s3 ls s3://$MLFLOW_S3_BUCKET/mlflow-artifacts/ --recursive
```

### Lab 05: FastAPI & Docker
```bash
# Run locally
python app/main.py

# Build image
docker build -t card-approval-api:latest .

# Run container
docker run -p 8000:8000 card-approval-api:latest

# Test
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" -d @test_payload.json

# Push to Docker Hub
docker tag card-approval-api:latest username/card-approval-api:latest
docker push username/card-approval-api:latest
```

### Lab 06: GitHub Actions
```bash
# Setup repository
git init && git add . && git commit -m "Initial commit"
gh repo create card-approval-prediction --public --source=. --push

# Trigger deployment
git tag v1.0.0 && git push origin v1.0.0

# Monitor
gh run list
gh run view --log
```

### Lab 07: Monitoring
```bash
# Start monitoring
docker-compose -f docker-compose.monitoring.yml up -d

# Check metrics
curl http://localhost:8000/metrics

# Access dashboards
open http://localhost:9090  # Prometheus
open http://localhost:3000  # Grafana (admin/admin)

# Check drift
curl http://localhost:8000/api/v1/drift/check
```

## Key Endpoints

### API Endpoints (Lab 04)
```
GET  /                      # API info
GET  /health                # Health check
GET  /ready                 # Readiness check
GET  /docs                  # Swagger UI
GET  /metrics               # Prometheus metrics
POST /api/v1/predict        # Make prediction
GET  /api/v1/model-info     # Model information
POST /api/v1/drift/check    # Check data drift
```

### MLflow Endpoints (Lab 02)
```
http://localhost:5000       # MLflow UI
http://localhost:5000/api/2.0/mlflow/experiments/list
```

### Monitoring Endpoints (Lab 06)
```
http://localhost:9090       # Prometheus UI
http://localhost:3000       # Grafana UI
http://localhost:8000/metrics  # Application metrics
```

## Configuration Files

### Environment Variables (.env)
```bash
# MLflow
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_S3_BUCKET=your-bucket-name
MODEL_NAME=card_approval_production
MODEL_STAGE=Production

# AWS
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret

# Docker Hub
DOCKER_USERNAME=your-username
DOCKER_PASSWORD=your-password
```

### GitHub Secrets (Lab 05)
```
DOCKER_USERNAME
DOCKER_PASSWORD
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
PULUMI_CONFIG_PASSPHRASE
```

## Test Payload

### Sample Prediction Request
```json
{
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
}
```

## Common Issues & Quick Fixes

### Issue: Port already in use
```bash
# Find and kill process
lsof -ti:8000 | xargs kill -9
```

### Issue: Docker cannot access localhost
```bash
# Use host.docker.internal instead of localhost
MLFLOW_TRACKING_URI=http://host.docker.internal:5000
```

### Issue: AWS credentials not found
```bash
# Configure AWS CLI
aws configure

# Verify
aws sts get-caller-identity
```

### Issue: MLflow model not found
```bash
# List registered models
python -c "from mlflow.tracking import MlflowClient; \
  client = MlflowClient(); \
  [print(m.name) for m in client.search_registered_models()]"
```

### Issue: Prometheus not scraping
```bash
# Check targets
curl http://localhost:9090/api/v1/targets

# Verify metrics endpoint
curl http://localhost:8000/metrics
```

## Verification Checklist

### Lab 01 ✓
- [ ] Airflow initialized and running
- [ ] MLflow server running
- [ ] DAG created and triggered
- [ ] All tasks completed successfully
- [ ] Models tracked in MLflow
- [ ] Best model registered

### Lab 02 ✓
- [ ] Pulumi installed and configured
- [ ] S3 bucket created
- [ ] Bucket versioning enabled
- [ ] Bucket encryption enabled

### Lab 03 ✓
- [ ] DVC initialized
- [ ] S3 remote configured
- [ ] Data tracked with DVC
- [ ] Data pushed to S3

### Lab 04 ✓
- [ ] MLflow configured with S3
- [ ] Artifacts uploaded to S3
- [ ] Model loads from S3

### Lab 05 ✓
- [ ] API responds to requests
- [ ] Docker image builds
- [ ] Container runs successfully

### Lab 06 ✓
- [ ] CI workflow passes
- [ ] CD workflow deploys
- [ ] App accessible on AWS

### Lab 07 ✓
- [ ] Metrics collected
- [ ] Grafana dashboard created
- [ ] Drift detection works

## Performance Benchmarks

### Expected Metrics
- **Model Training:** 2-5 minutes
- **Model Loading:** 2-5 seconds (first time), <1s (cached)
- **Prediction Latency:** <100ms (p95)
- **Docker Build:** 3-5 minutes
- **Deployment:** 5-10 minutes

### Resource Requirements
- **Development:** 8GB RAM, 20GB disk
- **Production:** 2GB RAM (API), 4GB RAM (monitoring)

## Important URLs

### Local Development
- MLflow: http://localhost:5000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

### Production (after Lab 05)
- API: https://your-app.awsapprunner.com
- GitHub Actions: https://github.com/username/repo/actions

## File Structure

```
card-approval-prediction/
├── training/           # Lab 01-03: ML pipeline
├── app/               # Lab 04: FastAPI application
├── pulumi/            # Lab 03, 05: Infrastructure
├── .github/workflows/ # Lab 05: CI/CD
├── monitoring/        # Lab 06: Observability
├── tests/             # Unit tests
└── poridhi/          # This documentation
```

## Next Steps After Completion

1. **Immediate:**
   - Add unit tests
   - Implement authentication
   - Configure alerts

2. **Short-term:**
   - A/B testing
   - Automated retraining
   - Multi-region deployment

3. **Long-term:**
   - Feature store
   - Model explainability
   - Advanced monitoring

## Support Resources

- **Documentation:** See individual lab files
- **Troubleshooting:** Check each lab's troubleshooting section
- **Issues:** Open GitHub issue
- **Questions:** Review COMPLETION_GUIDE.md

---

**Quick Start:** Begin with [Lab 01](./lab-01-model-development-mlflow-tracking.md)

**Full Index:** See [INDEX.md](./INDEX.md)

**Progress Tracking:** See [COMPLETION_GUIDE.md](./COMPLETION_GUIDE.md)
