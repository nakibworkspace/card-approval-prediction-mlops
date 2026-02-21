# Local Testing Guide

This guide shows you how to test the entire project locally with Docker before deploying to AWS.

## Prerequisites

- Docker and Docker Compose installed
- At least 8GB RAM available for Docker
- 10GB free disk space
- Kaggle API credentials (for training)

## Quick Start

### 1. Clone and Configure

```bash
# Clone repository
git clone https://github.com/your-username/card-approval-prediction.git
cd card-approval-prediction

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env  # or vim, code, etc.
```

**Minimum required variables in `.env`:**
```bash
# AWS (can use dummy values for local testing)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
S3_BUCKET_NAME=local-test-bucket

# Databases
POSTGRES_API_PASSWORD=api_password
POSTGRES_MLFLOW_PASSWORD=mlflow_password
POSTGRES_AIRFLOW_PASSWORD=airflow_password

# Redis
REDIS_PASSWORD=redis_password

# MLflow
MLFLOW_TRACKING_URI=http://localhost:5000

# Grafana
GRAFANA_ADMIN_PASSWORD=admin

# Airflow
AIRFLOW_ADMIN_PASSWORD=admin
AIRFLOW_FERNET_KEY=fb0c3f8c8b3f4c5e8d9a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e
AIRFLOW_SECRET_KEY=secret
```

### 2. Build and Start Services

```bash
# Build the API image
docker compose build api

# Start all services
docker compose up -d

# Check all services are running
docker compose ps
```

**Expected services:**
- ✅ postgres-api (port 5432)
- ✅ postgres-mlflow (port 5433)
- ✅ postgres-airflow (port 5434)
- ✅ redis (port 6379)
- ✅ mlflow (port 5000)
- ✅ card-approval-api (port 8000)
- ✅ airflow-webserver (port 8080)
- ✅ airflow-scheduler
- ✅ prometheus (port 9090)
- ✅ grafana (port 3000)
- ✅ loki (port 3100)
- ✅ tempo (port 3200)
- ✅ promtail

### 3. Wait for Services to be Ready

```bash
# Watch logs until all services are healthy
docker compose logs -f

# Press Ctrl+C when you see:
# - "Application startup complete" (API)
# - "Listening at: http://0.0.0.0:5000" (MLflow)
# - "Airflow webserver is ready" (Airflow)
```

**Or check health individually:**
```bash
# API health
curl http://localhost:8000/health

# MLflow health
curl http://localhost:5000/health

# Airflow health
curl http://localhost:8080/health
```

## Testing the ML Pipeline

### Option 1: Train Model with Airflow (Recommended)

```bash
# 1. Access Airflow UI
open http://localhost:8080  # or visit in browser
# Login: admin/admin

# 2. Configure Airflow Variables
# Go to Admin > Variables and add:
# - mlflow_tracking_uri: http://mlflow:5000
# - aws_access_key_id: test
# - aws_secret_access_key: test
# - aws_region: us-east-1

# 3. Enable and trigger the DAG
# Find "credit_card_ml_pipeline"
# Toggle it ON
# Click the play button ▶️

# 4. Monitor progress
# Watch the DAG graph turn green as tasks complete
```

### Option 2: Train Model Manually

```bash
# 1. Download data (requires Kaggle credentials)
docker compose exec api bash -c "cd /opt/airflow/training && python scripts/download_data.py"

# 2. Preprocess data
docker compose exec api bash -c "cd /opt/airflow/training && python scripts/run_preprocessing.py"

# 3. Train models
docker compose exec api bash -c "cd /opt/airflow/training && python scripts/run_training.py --mlflow-uri http://mlflow:5000 --auto-register"

# 4. Check MLflow for trained models
open http://localhost:5000
```

## API Testing

### Test 1: Health Check

```bash
# Basic health check
curl http://localhost:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "timestamp": "2024-01-24T10:30:00",
#   "version": "1.0.0"
# }
```

### Test 2: Readiness Check

```bash
# Check if API is ready to serve requests
curl http://localhost:8000/health/ready

# Expected response:
# {
#   "status": "ready",
#   "checks": {
#     "database": "ok",
#     "redis": "ok",
#     "model": "loaded"
#   }
# }
```

### Test 3: Liveness Check

```bash
# Check if API is alive
curl http://localhost:8000/health/live

# Expected response:
# {
#   "status": "alive"
# }
```

### Test 4: Model Info

```bash
# Get current model information
curl http://localhost:8000/api/v1/model-info

# Expected response:
# {
#   "model_name": "card_approval_model",
#   "version": "1",
#   "stage": "Production",
#   "run_id": "abc123...",
#   "source": "mlflow"
# }
```

### Test 5: Prediction - Approved Case

```bash
# Test case that should be APPROVED
curl -X POST http://localhost:8000/api/v1/predict \
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

# Expected response:
# {
#   "prediction": 1,
#   "probability": 0.95,
#   "decision": "APPROVED",
#   "confidence": 0.95,
#   "version": "1",
#   "timestamp": "2024-01-24T10:30:00"
# }
```

### Test 6: Prediction - Rejected Case

```bash
# Test case that should be REJECTED
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "ID": 5008805,
    "CODE_GENDER": "F",
    "FLAG_OWN_CAR": "N",
    "FLAG_OWN_REALTY": "N",
    "CNT_CHILDREN": 3,
    "AMT_INCOME_TOTAL": 45000.0,
    "NAME_INCOME_TYPE": "Working",
    "NAME_EDUCATION_TYPE": "Secondary / secondary special",
    "NAME_FAMILY_STATUS": "Single / not married",
    "NAME_HOUSING_TYPE": "Rented apartment",
    "DAYS_BIRTH": -7000,
    "DAYS_EMPLOYED": -500,
    "FLAG_MOBIL": 1,
    "FLAG_WORK_PHONE": 0,
    "FLAG_PHONE": 0,
    "FLAG_EMAIL": 0,
    "OCCUPATION_TYPE": "Laborers",
    "CNT_FAM_MEMBERS": 4.0
  }'

# Expected response:
# {
#   "prediction": 0,
#   "probability": 0.25,
#   "decision": "REJECTED",
#   "confidence": 0.75,
#   "version": "1",
#   "timestamp": "2024-01-24T10:30:00"
# }
```

### Test 7: Batch Predictions

```bash
# Test multiple predictions
for i in {1..5}; do
  curl -X POST http://localhost:8000/api/v1/predict \
    -H "Content-Type: application/json" \
    -d '{
      "ID": 500880'$i',
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
    }' | jq '.decision'
  echo ""
done
```

### Test 8: Invalid Input Validation

```bash
# Test with missing required field
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "ID": 5008804,
    "CODE_GENDER": "M"
  }'

# Expected response:
# {
#   "detail": [
#     {
#       "loc": ["body", "FLAG_OWN_CAR"],
#       "msg": "field required",
#       "type": "value_error.missing"
#     }
#   ]
# }
```

### Test 9: Prometheus Metrics

```bash
# Check metrics endpoint
curl http://localhost:8000/metrics

# Should see metrics like:
# api_requests_total{endpoint="/api/v1/predict",method="POST",status="200"} 5
# api_request_duration_seconds_bucket{endpoint="/api/v1/predict",method="POST",le="0.5"} 5
# api_active_requests 0
```

### Test 10: API Documentation

```bash
# Open interactive API docs
open http://localhost:8000/docs

# Or get OpenAPI schema
curl http://localhost:8000/openapi.json | jq
```

## Monitoring Testing

### Test Prometheus

```bash
# Access Prometheus UI
open http://localhost:9090

# Run queries:
# - api_requests_total
# - rate(api_requests_total[5m])
# - api_request_duration_seconds_bucket
```

### Test Grafana

```bash
# Access Grafana
open http://localhost:3000
# Login: admin/admin

# Check datasources:
# - Prometheus (should be green)
# - Loki (should be green)
# - Tempo (should be green)

# Import dashboard:
# 1. Go to Dashboards > Import
# 2. Upload monitoring/grafana/dashboards/*.json
```

### Test MLflow

```bash
# Access MLflow UI
open http://localhost:5000

# Check:
# - Experiments list
# - Runs with metrics
# - Registered models
# - Model versions
```

### Test Airflow

```bash
# Access Airflow UI
open http://localhost:8080
# Login: admin/admin

# Check:
# - DAGs list shows "credit_card_ml_pipeline"
# - DAG can be toggled ON
# - Variables are configured
```

## Load Testing

### Test 11: Performance Test

```bash
# Install Apache Bench (if not installed)
# Ubuntu/Debian: sudo apt-get install apache2-utils
# macOS: brew install apache2-utils

# Run load test (100 requests, 10 concurrent)
ab -n 100 -c 10 -p test_payload.json -T application/json http://localhost:8000/api/v1/predict

# Create test payload first:
cat > test_payload.json << 'EOF'
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
EOF
```

### Test 12: Stress Test

```bash
# Use hey for better load testing
# Install: go install github.com/rakyll/hey@latest

# Run stress test (1000 requests, 50 concurrent)
hey -n 1000 -c 50 -m POST \
  -H "Content-Type: application/json" \
  -d @test_payload.json \
  http://localhost:8000/api/v1/predict
```

## Database Testing

### Test 13: Check Predictions in Database

```bash
# Connect to API database
docker compose exec postgres-api psql -U api_user -d card_approval_api

# Run queries:
# List predictions
SELECT * FROM predictions ORDER BY created_at DESC LIMIT 10;

# Count predictions by decision
SELECT decision, COUNT(*) FROM predictions GROUP BY decision;

# Exit
\q
```

### Test 14: Check MLflow Metadata

```bash
# Connect to MLflow database
docker compose exec postgres-mlflow psql -U mlflow_user -d mlflow

# List experiments
SELECT * FROM experiments;

# List runs
SELECT * FROM runs ORDER BY start_time DESC LIMIT 10;

# Exit
\q
```

## Troubleshooting Tests

### Check Service Logs

```bash
# API logs
docker compose logs -f api

# MLflow logs
docker compose logs -f mlflow

# Airflow scheduler logs
docker compose logs -f airflow-scheduler

# All logs
docker compose logs -f
```

### Check Service Health

```bash
# Check all container status
docker compose ps

# Check specific service
docker compose ps api

# Restart unhealthy service
docker compose restart api
```

### Check Resource Usage

```bash
# Check Docker resource usage
docker stats

# Check disk usage
docker system df
```

### Common Issues

**Issue 1: API returns 503 Service Unavailable**
```bash
# Check if model is loaded
docker compose logs api | grep "Model loaded"

# If not, train a model first (see "Testing the ML Pipeline" section)
```

**Issue 2: Airflow DAG not showing**
```bash
# Check DAG syntax
docker compose exec airflow-scheduler python /opt/airflow/dags/ml_training_pipeline.py

# Check import errors
docker compose exec airflow-scheduler airflow dags list-import-errors
```

**Issue 3: Database connection errors**
```bash
# Check database is running
docker compose ps postgres-api

# Check database logs
docker compose logs postgres-api

# Restart database
docker compose restart postgres-api
```

**Issue 4: Out of memory**
```bash
# Check Docker memory limit
docker info | grep Memory

# Increase Docker memory in Docker Desktop settings
# Recommended: 8GB minimum
```

## Cleanup

### Stop Services

```bash
# Stop all services
docker compose down

# Stop and remove volumes (WARNING: deletes all data)
docker compose down -v

# Stop and remove images
docker compose down --rmi all
```

### Clean Docker System

```bash
# Remove unused containers, networks, images
docker system prune -a

# Remove unused volumes
docker volume prune
```

## Test Checklist

Before deploying to AWS, ensure all tests pass:

- [ ] All services start successfully
- [ ] Health checks return 200 OK
- [ ] Model can be trained via Airflow
- [ ] Predictions return valid responses
- [ ] Approved cases return decision="APPROVED"
- [ ] Rejected cases return decision="REJECTED"
- [ ] Invalid input returns validation errors
- [ ] Metrics are collected in Prometheus
- [ ] Logs appear in Grafana/Loki
- [ ] MLflow shows experiments and models
- [ ] Airflow DAG runs successfully
- [ ] Database stores predictions
- [ ] Load test completes without errors

## Next Steps

Once all tests pass locally:

1. Review [README_DOCKER_COMPOSE.md](README_DOCKER_COMPOSE.md) for detailed Docker Compose guide
2. Review [README_AIRFLOW.md](README_AIRFLOW.md) for Airflow usage
3. Follow [docs/00_Setup_Guide_AWS.md](docs/00_Setup_Guide_AWS.md) for AWS deployment
4. Set up CI/CD with GitHub Actions

## Quick Test Script

Save this as `test_local.sh` for automated testing:

```bash
#!/bin/bash
set -e

echo "🧪 Testing Card Approval Prediction API"
echo "========================================"

# Test 1: Health Check
echo "✓ Test 1: Health Check"
curl -s http://localhost:8000/health | jq

# Test 2: Model Info
echo "✓ Test 2: Model Info"
curl -s http://localhost:8000/api/v1/model-info | jq

# Test 3: Approved Prediction
echo "✓ Test 3: Approved Prediction"
curl -s -X POST http://localhost:8000/api/v1/predict \
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
  }' | jq

# Test 4: Metrics
echo "✓ Test 4: Metrics"
curl -s http://localhost:8000/metrics | grep api_requests_total | head -5

echo ""
echo "✅ All tests passed!"
```

Run with:
```bash
chmod +x test_local.sh
./test_local.sh
```
