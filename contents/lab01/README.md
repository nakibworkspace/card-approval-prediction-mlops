# Lab 01: Automated ML Pipeline with Airflow & MLflow

This directory contains all the files and code needed for Lab 01.

## What's Included in This Lab

- Airflow setup and DAG definitions
- MLflow tracking configuration
- Training pipeline (EDA, preprocessing, model training)
- Model comparison (Logistic Regression, Random Forest, XGBoost)

## Directory Structure

```
lab01/
├── dags/                           # Airflow DAG definitions
│   └── ml_training_pipeline.py    # Main ML pipeline DAG
├── training/                       # Training code and data
│   ├── data/
│   │   ├── raw/                   # Raw dataset
│   │   └── processed/             # Processed data
│   ├── scripts/                   # Training scripts
│   │   ├── airflow_tasks.py      # Airflow task implementations
│   │   ├── eda_analysis.py       # EDA script
│   │   ├── preprocess_data.py    # Preprocessing script
│   │   └── train_models.py       # Model training script
│   ├── src/                       # Source code
│   │   ├── config/               # Configuration
│   │   │   └── mlflow_config.py  # MLflow configuration
│   │   └── utils/                # Utility functions
│   └── models/                    # Saved models and artifacts
├── logs/                          # Airflow logs
├── plugins/                       # Airflow plugins
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## Setup Instructions

See the lab guide: `poridhi/lab-01-model-development-mlflow-tracking.md`

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize Airflow
export AIRFLOW_HOME=$(pwd)
airflow db init
airflow users create --username admin --password admin --firstname Admin --lastname User --role Admin --email admin@example.com

# Start services (in separate terminals)
airflow webserver --port 8080
airflow scheduler
mlflow server --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./mlruns --host 0.0.0.0 --port 5000

# Access UIs
# Airflow: http://localhost:8080 (admin/admin)
# MLflow: http://localhost:5000
```
