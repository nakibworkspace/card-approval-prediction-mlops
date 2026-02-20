# Apache Airflow ML Pipeline

This guide explains how to use Apache Airflow to orchestrate the ML training pipeline.

## Overview

Airflow automates the entire ML workflow:
- Download data from Kaggle
- Run exploratory data analysis
- Preprocess and feature engineering
- Train multiple models
- Evaluate model quality
- Register best model to MLflow
- Trigger deployment if model improves

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Airflow Scheduler                         │
│                  (Orchestrates Pipeline)                     │
└────────────┬────────────────────────────────────────────────┘
             │
             ├─► download_data (Kaggle API)
             │
             ├─► run_eda (Optional analysis)
             │
             ├─► preprocess_data (Feature engineering)
             │
             ├─► train_models (XGBoost, LightGBM, CatBoost)
             │        │
             │        └─► Log to MLflow
             │
             ├─► evaluate_model (Quality gate: F1 > 0.75)
             │
             ├─► check_deployment (Branch decision)
             │        │
             │        ├─► trigger_deployment (GitHub Actions)
             │        │
             │        └─► skip_deployment
             │
             └─► send_notification
```

## Quick Start

### 1. Start Airflow

```bash
# Start all services including Airflow
docker-compose up -d

# Check Airflow services
docker-compose ps | grep airflow
```

### 2. Access Airflow UI

Open http://localhost:8080

- Username: `admin`
- Password: `admin` (or value from `.env`)

### 3. Configure Airflow Variables

Go to **Admin > Variables** and add:

| Key | Value | Description |
|-----|-------|-------------|
| `mlflow_tracking_uri` | `http://mlflow:5000` | MLflow server URL |
| `aws_access_key_id` | Your AWS key | AWS credentials |
| `aws_secret_access_key` | Your AWS secret | AWS credentials |
| `aws_region` | `us-east-1` | AWS region |
| `github_token` | Your GitHub token | For deployment trigger |
| `github_repo` | `username/repo` | Your repository |

### 4. Trigger the Pipeline

**Option A: Manual trigger**
- Find `credit_card_ml_pipeline` in DAGs list
- Click the play button ▶️

**Option B: CLI**
```bash
docker exec -it airflow-scheduler airflow dags trigger credit_card_ml_pipeline
```

**Option C: Wait for schedule**
- Runs automatically every Sunday at 2 AM

## DAG Tasks

### Task 1: download_data
Downloads credit card dataset from Kaggle.

**Requirements:**
- Kaggle API credentials in `~/.kaggle/kaggle.json`

**Duration:** ~2 minutes

### Task 2: run_eda
Runs exploratory data analysis (optional).

**Duration:** ~3 minutes

### Task 3: preprocess_data
Feature engineering, encoding, scaling, PCA.

**Outputs:**
- `training/data/processed/X_train.csv`
- `training/data/processed/X_test.csv`
- `training/data/processed/scaler.pkl`
- `training/data/processed/pca.pkl`

**Duration:** ~5 minutes

### Task 4: train_models
Trains multiple models and logs to MLflow.

**Models trained:**
- XGBoost
- LightGBM
- CatBoost
- Logistic Regression
- Random Forest

**Duration:** ~15-20 minutes

### Task 5: evaluate_model
Quality gate check - ensures F1 score > 0.75.

**Fails if:** Model quality below threshold

**Duration:** ~1 minute

### Task 6: check_deployment
Decides if deployment should be triggered.

**Logic:** Deploy if evaluation passed

### Task 7: trigger_deployment
Triggers GitHub Actions deployment workflow.

**Requires:** GitHub personal access token

### Task 8: send_notification
Sends completion notification.

## Monitoring

### View DAG Progress

**Grid View:**
http://localhost:8080/dags/credit_card_ml_pipeline/grid

**Graph View:**
http://localhost:8080/dags/credit_card_ml_pipeline/graph

### View Task Logs

1. Click on any task in the DAG
2. Click "Log" button
3. View real-time logs

### View MLflow Experiments

http://localhost:5000

- See all training runs
- Compare model metrics
- View artifacts

## Configuration

### Change Schedule

Edit `dags/ml_training_pipeline.py`:

```python
schedule_interval="0 2 * * 0",  # Cron expression
```

**Examples:**
- `@daily` - Every day at midnight
- `@weekly` - Every Sunday at midnight
- `0 */6 * * *` - Every 6 hours
- `0 2 * * 1` - Every Monday at 2 AM
- `0 0 1 * *` - First day of every month

### Change Model Quality Threshold

Edit the `evaluate_model` task:

```python
--min-f1 0.75  # Change to your desired threshold
```

### Enable Email Notifications

1. Configure SMTP in Airflow:

```bash
docker exec -it airflow-webserver airflow config set smtp smtp_host smtp.gmail.com
docker exec -it airflow-webserver airflow config set smtp smtp_port 587
docker exec -it airflow-webserver airflow config set smtp smtp_user your-email@gmail.com
docker exec -it airflow-webserver airflow config set smtp smtp_password your-app-password
```

2. Update DAG `default_args`:

```python
default_args = {
    "email": ["your-email@example.com"],
    "email_on_failure": True,
    "email_on_success": True,
}
```

## Troubleshooting

### DAG Not Appearing

```bash
# Check DAG syntax
docker exec -it airflow-scheduler python /opt/airflow/dags/ml_training_pipeline.py

# Check import errors
docker exec -it airflow-scheduler airflow dags list-import-errors
```

### Task Failing

```bash
# Test task locally
docker exec -it airflow-scheduler airflow tasks test credit_card_ml_pipeline download_data 2024-01-01

# View logs
docker exec -it airflow-scheduler airflow tasks logs credit_card_ml_pipeline download_data 2024-01-01
```

### Reset DAG

```bash
# Clear all task instances
docker exec -it airflow-scheduler airflow dags delete credit_card_ml_pipeline

# Restart scheduler
docker-compose restart airflow-scheduler
```

### Kaggle Credentials Not Found

Mount Kaggle credentials to Airflow containers:

```yaml
# docker-compose.yml
airflow-webserver:
  volumes:
    - ~/.kaggle:/home/airflow/.kaggle:ro
```

## Best Practices

1. **Monitor DAG runs** - Check Airflow UI regularly
2. **Set up alerts** - Configure email notifications
3. **Version control** - Keep DAGs in Git
4. **Test locally** - Use `airflow tasks test` before deploying
5. **Use variables** - Store secrets in Airflow Variables, not in code
6. **Add retries** - Configure retry logic for flaky tasks
7. **Set timeouts** - Prevent tasks from running indefinitely

## Advanced Features

### Parallel Training

Train models in parallel by modifying the DAG:

```python
from airflow.operators.python import PythonOperator

train_xgboost = PythonOperator(...)
train_lightgbm = PythonOperator(...)
train_catboost = PythonOperator(...)

preprocess_data >> [train_xgboost, train_lightgbm, train_catboost] >> evaluate_model
```

### Data Drift Detection

Add a drift detection task:

```python
check_drift = BashOperator(
    task_id="check_drift",
    bash_command="python scripts/check_drift.py",
)

download_data >> check_drift >> preprocess_data
```

### Conditional Retraining

Only retrain if drift detected:

```python
def check_drift_threshold(**context):
    # Check drift metrics
    if drift_score > 0.3:
        return "preprocess_data"
    return "skip_training"

branch_task = BranchPythonOperator(
    task_id="check_drift",
    python_callable=check_drift_threshold,
)
```

## Next Steps

- [MLflow Training Guide](02_MLflow_Training.md)
- [Monitoring Guide](05_Monitoring.md)
- [CI/CD Pipeline](.github/workflows/cd.yml)
