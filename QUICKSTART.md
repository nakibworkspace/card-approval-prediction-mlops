# Quick Start - 5 Minutes

Get the project running locally in 5 minutes.

## Step 1: Start Services (2 min)

**For local testing (no AWS):**
```bash
# Copy environment file
cp .env.example .env.local

# Start all services (local mode)
docker compose -f docker-compose.local.yml up -d

# Wait for services to be ready (check status)
docker compose -f docker-compose.local.yml ps
```

**For AWS/production testing:**
```bash
# Copy environment file
cp .env.example .env
# Edit .env with AWS credentials

# Start all services (AWS mode)
docker compose up -d

# Wait for services to be ready (check status)
docker compose ps
```

**Expected:** All services should show "Up" or "Up (healthy)" status.

## Step 2: Train a Model (2 min)

You need to train a model before the API can make predictions.

### Option A: Quick Manual Training (No Kaggle needed)

```bash
# Use the pre-processed data if available
docker compose exec api bash -c "cd /opt/airflow/training && python scripts/run_training.py --mlflow-uri http://mlflow:5000 --auto-register"
```

### Option B: Full Pipeline with Airflow

1. Open Airflow: http://localhost:8080 (admin/admin)
2. Go to Admin > Variables
3. Add these variables:
   - `mlflow_tracking_uri`: `http://mlflow:5000`
   - `aws_access_key_id`: `test`
   - `aws_secret_access_key`: `test`
   - `aws_region`: `us-east-1`
4. Find `credit_card_ml_pipeline` DAG
5. Toggle it ON
6. Click the play button ▶️
7. Wait ~25 minutes for completion

## Step 3: Test the API (1 min)

```bash
# Test health
curl http://localhost:8000/health

# Test prediction
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
```

**Expected response:**
```json
{
  "prediction": 1,
  "probability": 0.95,
  "decision": "APPROVED",
  "confidence": 0.95,
  "version": "1",
  "timestamp": "2024-01-24T10:30:00"
}
```

## Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| API Docs | http://localhost:8000/docs | None |
| Airflow | http://localhost:8080 | admin/admin |
| MLflow | http://localhost:5000 | None |
| Grafana | http://localhost:3001 | admin/admin |
| Prometheus | http://localhost:9090 | None |

## Troubleshooting

### API shows "Restarting"

This is normal if no model is trained yet. The API will start once you train a model.

```bash
# Check logs
docker compose logs api

# Should see: "API will start without a model. Train a model first..."
```

### MLflow shows "Restarting"

MLflow needs a moment to initialize the database.

```bash
# Check logs
docker compose logs mlflow

# Wait 30 seconds and check again
docker compose ps mlflow
```

### "No model loaded" error

Train a model first (see Step 2 above).

## Next Steps

- Read [LOCAL.md](LOCAL.md) for comprehensive testing guide
- Read [README_AIRFLOW.md](README_AIRFLOW.md) for Airflow usage
- Run automated tests: `./test_local.sh`
- Deploy to AWS: [docs/00_Setup_Guide_AWS.md](docs/00_Setup_Guide_AWS.md)

## Stop Services

```bash
# Stop all services
docker compose down

# Stop and remove all data
docker compose down -v
```
