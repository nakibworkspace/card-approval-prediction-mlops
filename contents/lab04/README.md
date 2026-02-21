# Lab 04: The Prediction API (FastAPI) & Docker Hub

This directory contains all the files and code needed for Lab 04.

## What's Included in This Lab

**From Lab 01:**
- Airflow setup and DAG definitions
- MLflow tracking configuration
- Training pipeline

**From Lab 02:**
- Pulumi Infrastructure as Code
- DVC data versioning

**From Lab 03:**
- MLflow S3 integration

**New in Lab 04:**
- FastAPI prediction API
- Pydantic input validation
- Model service with S3 loading
- Docker containerization
- Docker Hub deployment

## Directory Structure

```
lab04/
├── dags/                           # Airflow (from Lab 01)
├── training/                       # Training (from Labs 01-03)
├── pulumi/                         # Infrastructure (from Lab 02)
├── app/                           # NEW: FastAPI application
│   ├── routers/
│   │   └── predict.py            # Prediction endpoint
│   ├── services/
│   │   └── model_service.py      # Model loading and prediction
│   ├── schemas/
│   │   ├── health.py             # Health check schemas
│   │   └── prediction.py         # Prediction request/response
│   ├── core/
│   │   ├── config.py             # Application configuration
│   │   └── logging.py            # Logging configuration
│   ├── utils/
│   ├── main.py                   # FastAPI entry point
│   └── __init__.py
├── tests/                         # NEW: Test suite
│   ├── test_api.py
│   └── test_model_service.py
├── Dockerfile                     # NEW: Docker image definition
├── .dockerignore                  # NEW: Docker ignore file
├── test_payload.json              # NEW: Sample test payload
├── .dvc/
├── .env.example
├── logs/
├── plugins/
├── requirements.txt
└── README.md
```

## Setup Instructions

See the lab guide: `poridhi/lab-05-prediction-api-fastapi-docker.md`

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create .env file
cp .env.example .env
# Edit .env with your configuration

# 3. Run API locally
python app/main.py

# 4. Test API
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d @test_payload.json

# 5. Build Docker image
docker build -t card-approval-api:latest .

# 6. Run Docker container
docker run -p 8000:8000 \
  -e MLFLOW_TRACKING_URI=http://host.docker.internal:5000 \
  card-approval-api:latest

# 7. Push to Docker Hub
docker login
docker tag card-approval-api:latest your-username/card-approval-api:latest
docker push your-username/card-approval-api:latest
```
