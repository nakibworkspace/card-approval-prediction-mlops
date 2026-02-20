# Airflow DAGs

This directory contains Apache Airflow DAGs for orchestrating ML pipelines.

## Available DAGs

### `ml_training_pipeline.py`
End-to-end ML training pipeline for credit card approval prediction.

**Schedule**: Every Sunday at 2 AM (configurable)

**Tasks**:
1. `download_data` - Download dataset from Kaggle
2. `run_eda` - Run exploratory data analysis
3. `preprocess_data` - Feature engineering and preprocessing
4. `train_models` - Train multiple models (XGBoost, LightGBM, CatBoost)
5. `evaluate_model` - Quality gate check (F1 score threshold)
6. `check_deployment` - Decide if deployment is needed
7. `trigger_deployment` - Trigger GitHub Actions deployment
8. `send_notification` - Send completion notification

## Setup

### 1. Configure Airflow Variables

Access Airflow UI at http://localhost:8080 (admin/admin) and set these variables:

```
Admin > Variables > Add
```

Required variables:
- `mlflow_tracking_uri`: http://mlflow:5000
- `aws_access_key_id`: Your AWS access key
- `aws_secret_access_key`: Your AWS secret key
- `aws_region`: us-east-1
- `github_token`: Your GitHub personal access token (for deployment trigger)
- `github_repo`: your-username/card-approval-prediction

### 2. Configure Kaggle Credentials

Create a Kaggle API token and mount it to Airflow:

```bash
# Create kaggle.json with your credentials
mkdir -p ~/.kaggle
echo '{"username":"your-username","key":"your-api-key"}' > ~/.kaggle/kaggle.json
chmod 600 ~/.kaggle/kaggle.json
```

Update `docker-compose.yml` to mount Kaggle credentials:
```yaml
airflow-webserver:
  volumes:
    - ~/.kaggle:/home/airflow/.kaggle:ro
```

### 3. Start Airflow

```bash
docker-compose up -d airflow-webserver airflow-scheduler
```

### 4. Trigger DAG

**Option 1: Manual trigger**
- Go to http://localhost:8080
- Find `credit_card_ml_pipeline`
- Click the play button

**Option 2: CLI**
```bash
docker exec -it airflow-scheduler airflow dags trigger credit_card_ml_pipeline
```

**Option 3: Wait for schedule**
- DAG runs automatically every Sunday at 2 AM

## Monitoring

### View DAG runs
- Airflow UI: http://localhost:8080/dags/credit_card_ml_pipeline/grid
- Task logs: Click on any task > Log

### View MLflow experiments
- MLflow UI: http://localhost:5000

### View metrics
- Grafana: http://localhost:3000

## Customization

### Change schedule
Edit `schedule_interval` in `ml_training_pipeline.py`:
```python
schedule_interval="0 2 * * 0",  # Cron expression
```

Examples:
- `@daily` - Every day at midnight
- `@weekly` - Every Sunday at midnight
- `0 */6 * * *` - Every 6 hours
- `0 2 * * 1` - Every Monday at 2 AM

### Change model quality threshold
Edit `evaluate_model` task:
```python
--min-f1 0.75  # Change to your desired F1 threshold
```

### Add email notifications
Update `default_args` in DAG:
```python
default_args = {
    "email": ["your-email@example.com"],
    "email_on_failure": True,
    "email_on_success": True,
}
```

Configure SMTP in Airflow:
```bash
docker exec -it airflow-webserver airflow config set smtp smtp_host smtp.gmail.com
docker exec -it airflow-webserver airflow config set smtp smtp_port 587
docker exec -it airflow-webserver airflow config set smtp smtp_user your-email@gmail.com
docker exec -it airflow-webserver airflow config set smtp smtp_password your-app-password
```

## Troubleshooting

### DAG not appearing
```bash
# Check DAG syntax
docker exec -it airflow-scheduler python /opt/airflow/dags/ml_training_pipeline.py

# Check DAG import errors
docker exec -it airflow-scheduler airflow dags list-import-errors
```

### Task failing
```bash
# View logs
docker exec -it airflow-scheduler airflow tasks test credit_card_ml_pipeline download_data 2024-01-01
```

### Reset DAG
```bash
# Clear all task instances
docker exec -it airflow-scheduler airflow dags delete credit_card_ml_pipeline
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Airflow Scheduler                         │
│                  (Orchestrates Pipeline)                     │
└────────────┬────────────────────────────────────────────────┘
             │
             ├─► Download Data (Kaggle API)
             │
             ├─► Run EDA (Optional)
             │
             ├─► Preprocess Data (Feature Engineering)
             │
             ├─► Train Models (XGBoost, LightGBM, CatBoost)
             │        │
             │        └─► Log to MLflow
             │
             ├─► Evaluate Model (Quality Gate)
             │
             ├─► Check Deployment (Branch)
             │        │
             │        ├─► Trigger Deployment (GitHub Actions)
             │        │
             │        └─► Skip Deployment
             │
             └─► Send Notification
```
