# Airflow ML Pipeline - Quick Start

This guide shows you how to use Apache Airflow to automate your ML training pipeline.

## What is Airflow?

Apache Airflow is a workflow orchestration platform that automates your ML pipeline:
- Schedules training runs (daily, weekly, monthly)
- Monitors task execution
- Retries failed tasks automatically
- Sends alerts on failures
- Provides visual DAG monitoring

## Quick Start

### 1. Start Airflow

```bash
# Start all services (includes Airflow)
docker-compose up -d

# Verify Airflow is running
docker-compose ps | grep airflow
```

You should see:
- `airflow-webserver` - Web UI
- `airflow-scheduler` - Task scheduler
- `airflow-init` - Database initialization (exits after setup)
- `postgres-airflow` - Airflow metadata database

### 2. Access Airflow UI

Open http://localhost:8080

**Login:**
- Username: `admin`
- Password: `admin` (or from `.env` file)

### 3. Configure Airflow Variables

Before running the pipeline, set up required variables:

1. Go to **Admin > Variables**
2. Click **+** to add new variables
3. Add these variables:

| Key | Value | Example |
|-----|-------|---------|
| `mlflow_tracking_uri` | `http://mlflow:5000` | MLflow server URL |
| `aws_access_key_id` | Your AWS key | From your `.env` file |
| `aws_secret_access_key` | Your AWS secret | From your `.env` file |
| `aws_region` | `us-east-1` | Your AWS region |
| `github_token` | Your GitHub PAT | Optional, for deployment |
| `github_repo` | `username/repo` | Optional, for deployment |

### 4. Trigger the Pipeline

**Option A: Manual Trigger (Recommended for first run)**

1. Find `credit_card_ml_pipeline` in the DAGs list
2. Toggle the DAG to "On" (switch on the left)
3. Click the ▶️ play button
4. Select "Trigger DAG"

**Option B: CLI**

```bash
docker exec -it airflow-scheduler airflow dags trigger credit_card_ml_pipeline
```

**Option C: Scheduled (Automatic)**

The DAG runs automatically every Sunday at 2 AM. No action needed.

### 5. Monitor Progress

**Grid View:**
- Shows task status over time
- Green = Success, Red = Failed, Yellow = Running

**Graph View:**
- Shows task dependencies
- Click tasks to view logs

**Task Logs:**
1. Click on any task box
2. Click "Log" button
3. View real-time execution logs

## Pipeline Tasks

The DAG executes these tasks in order:

```
download_data → run_eda → preprocess_data → train_models → evaluate_model
                                                                    ↓
                                                            check_deployment
                                                                    ↓
                                                    ┌───────────────┴───────────────┐
                                                    ↓                               ↓
                                            trigger_deployment              skip_deployment
                                                    ↓                               ↓
                                                    └───────────────┬───────────────┘
                                                                    ↓
                                                            send_notification
```

**Estimated total runtime:** 25-30 minutes

## What Each Task Does

1. **download_data** (2 min) - Downloads dataset from Kaggle
2. **run_eda** (3 min) - Exploratory data analysis
3. **preprocess_data** (5 min) - Feature engineering, scaling, PCA
4. **train_models** (15-20 min) - Trains XGBoost, LightGBM, CatBoost
5. **evaluate_model** (1 min) - Quality gate check (F1 > 0.75)
6. **check_deployment** (<1 min) - Decides if deployment needed
7. **trigger_deployment** (<1 min) - Triggers GitHub Actions
8. **send_notification** (<1 min) - Completion notification

## Accessing Services

| Service | URL | Credentials |
|---------|-----|-------------|
| Airflow UI | http://localhost:8080 | admin/admin |
| MLflow UI | http://localhost:5000 | None |
| API Docs | http://localhost:8000/docs | None |
| Grafana | http://localhost:3000 | admin/admin |
| Prometheus | http://localhost:9090 | None |

## Common Tasks

### View All DAG Runs

```bash
docker exec -it airflow-scheduler airflow dags list-runs -d credit_card_ml_pipeline
```

### Test a Single Task

```bash
docker exec -it airflow-scheduler airflow tasks test credit_card_ml_pipeline download_data 2024-01-01
```

### Clear Failed Tasks

```bash
docker exec -it airflow-scheduler airflow tasks clear credit_card_ml_pipeline
```

### Pause/Unpause DAG

```bash
# Pause
docker exec -it airflow-scheduler airflow dags pause credit_card_ml_pipeline

# Unpause
docker exec -it airflow-scheduler airflow dags unpause credit_card_ml_pipeline
```

## Customization

### Change Schedule

Edit `dags/ml_training_pipeline.py`:

```python
schedule_interval="0 2 * * 0",  # Every Sunday at 2 AM
```

**Common schedules:**
- `@daily` - Every day at midnight
- `@weekly` - Every Sunday at midnight
- `0 */6 * * *` - Every 6 hours
- `0 2 * * 1` - Every Monday at 2 AM

### Change Model Quality Threshold

Edit the `evaluate_model` task:

```python
--min-f1 0.75  # Change to 0.80 for stricter quality gate
```

### Disable Deployment Trigger

Comment out the deployment tasks in the DAG:

```python
# trigger_deployment = BashOperator(...)
```

## Troubleshooting

### DAG Not Showing Up

```bash
# Check for syntax errors
docker exec -it airflow-scheduler python /opt/airflow/dags/ml_training_pipeline.py

# Check import errors
docker exec -it airflow-scheduler airflow dags list-import-errors
```

### Task Failing

1. Click on the failed task (red box)
2. Click "Log" to see error details
3. Fix the issue
4. Click "Clear" to retry

### Kaggle Credentials Error

Ensure Kaggle credentials are mounted:

```yaml
# docker-compose.yml
airflow-webserver:
  volumes:
    - ~/.kaggle:/home/airflow/.kaggle:ro
```

### MLflow Connection Error

Check that MLflow is running:

```bash
docker-compose ps mlflow
curl http://localhost:5000/health
```

## Benefits of Using Airflow

✅ **Automated scheduling** - No manual training runs
✅ **Retry logic** - Auto-retry failed tasks
✅ **Monitoring** - Visual DAG and task logs
✅ **Alerting** - Email notifications on failures
✅ **Dependency management** - Tasks run in correct order
✅ **Parallel execution** - Train multiple models simultaneously
✅ **Version control** - DAGs stored in Git

## Next Steps

- Read the full guide: [docs/06_Airflow_Pipeline.md](docs/06_Airflow_Pipeline.md)
- Configure email alerts
- Add data drift detection
- Set up parallel model training
- Integrate with CI/CD

## Architecture

```
┌──────────────┐
│   Kaggle     │
│   Dataset    │
└──────┬───────┘
       │
       ↓
┌──────────────────────────────────────────┐
│         Airflow Scheduler                │
│  (Orchestrates ML Pipeline)              │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │  DAG: credit_card_ml_pipeline      │ │
│  │                                    │ │
│  │  Tasks:                            │ │
│  │  1. Download data                  │ │
│  │  2. Preprocess                     │ │
│  │  3. Train models                   │ │
│  │  4. Evaluate                       │ │
│  │  5. Deploy                         │ │
│  └────────────────────────────────────┘ │
└──────────────┬───────────────────────────┘
               │
               ↓
┌──────────────────────────────────────────┐
│            MLflow Server                 │
│  (Experiment Tracking & Model Registry)  │
└──────────────┬───────────────────────────┘
               │
               ↓
┌──────────────────────────────────────────┐
│         AWS App Runner                   │
│  (Production API with Best Model)        │
└──────────────────────────────────────────┘
```

## Support

For detailed documentation, see:
- [Airflow Pipeline Guide](docs/06_Airflow_Pipeline.md)
- [MLflow Training Guide](docs/02_MLflow_Training.md)
- [Monitoring Guide](docs/05_Monitoring.md)
