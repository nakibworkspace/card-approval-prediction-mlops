# Lab 03: MLflow + S3 Integration

This directory contains all the files and code needed for Lab 03.

## What's Included in This Lab

**From Lab 01:**
- Airflow setup and DAG definitions
- MLflow tracking configuration
- Training pipeline

**From Lab 02:**
- Pulumi Infrastructure as Code
- DVC data versioning
- S3 remote storage

**New in Lab 03:**
- MLflow S3 artifact storage configuration
- Training with S3-backed MLflow
- Model loading from S3
- Team collaboration workflow

## Directory Structure

```
lab03/
├── dags/                           # Airflow DAGs (from Lab 01)
├── training/                       # Training code (from Lab 01 + Lab 02)
│   ├── data/
│   ├── scripts/
│   │   ├── run_training_s3.py     # NEW: Training with S3 artifacts
│   │   ├── load_model_s3.py       # NEW: Load model from S3
│   │   └── query_mlflow.py        # NEW: Query MLflow programmatically
│   ├── src/
│   │   ├── config/
│   │   │   └── mlflow_s3_config.py  # NEW: MLflow S3 configuration
│   │   └── utils/
│   └── models/
├── pulumi/                         # Infrastructure (from Lab 02)
├── .dvc/                          # DVC config (from Lab 02)
├── .env.example                   # NEW: Environment variables template
├── logs/
├── plugins/
├── requirements.txt
└── README.md
```

## Setup Instructions

See the lab guide: `poridhi/lab-04-mlflow-s3-integration.md`

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Get S3 bucket name from Pulumi
cd pulumi
export MLFLOW_S3_BUCKET=$(pulumi stack output data_bucket_name)
cd ..

# 3. Create .env file
cat > .env << EOF
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_S3_BUCKET=${MLFLOW_S3_BUCKET}
AWS_REGION=us-east-1
EOF

# 4. Start MLflow with S3 backend
mlflow server \
  --backend-store-uri sqlite:///mlflow.db \
  --default-artifact-root s3://${MLFLOW_S3_BUCKET}/mlflow-artifacts \
  --host 0.0.0.0 --port 5000

# 5. Train model with S3 storage
source .env
python training/scripts/run_training_s3.py

# 6. Load model from S3
python training/scripts/load_model_s3.py
```
