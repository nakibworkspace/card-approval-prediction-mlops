# Lab 01: Part 5 - DAG Definition and Completion

## Chapter 7: Creating the Airflow DAG

### 7.1 DAG Definition

Create the DAG that orchestrates all tasks.

```python
# dags/ml_training_pipeline.py
"""
Credit Card Approval ML Training Pipeline

This DAG automates the complete ML workflow:
1. Download data
2. Perform EDA
3. Preprocess data
4. Train models
5. Evaluate models
6. Register best model
7. Send notification

Schedule: Weekly (every Sunday at 2 AM)
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
import os

# Add training scripts to Python path
sys.path.insert(0, '/opt/airflow/training/scripts')

# Import task functions
from airflow_tasks import (
    download_data_task,
    run_eda_task,
    preprocess_data_task,
    train_models_task,
    evaluate_models_task,
    register_best_model_task,
    send_notification_task
)

# ============================================
# DAG DEFAULT ARGUMENTS
# ============================================
default_args = {
    'owner': 'data-science-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email': ['ml-team@company.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=2),
}

# ============================================
# DAG DEFINITION
# ============================================
dag = DAG(
    'credit_card_ml_pipeline',
    default_args=default_args,
    description='Automated ML pipeline with Airflow and MLflow',
    schedule_interval='0 2 * * 0',  # Every Sunday at 2 AM (cron format)
    catchup=False,  # Don't run for past dates
    max_active_runs=1,  # Only one run at a time
    tags=['ml', 'training', 'automated', 'credit-approval'],
)

# ============================================
# TASK DEFINITIONS
# ============================================

# Task 1: Download Data
download_data = PythonOperator(
    task_id='download_data',
    python_callable=download_data_task,
    provide_context=True,
    dag=dag,
)

# Task 2: Exploratory Data Analysis
run_eda = PythonOperator(
    task_id='run_eda',
    python_callable=run_eda_task,
    provide_context=True,
    dag=dag,
)

# Task 3: Preprocess Data
preprocess_data = PythonOperator(
    task_id='preprocess_data',
    python_callable=preprocess_data_task,
    provide_context=True,
    dag=dag,
)

# Task 4: Train Models
train_models = PythonOperator(
    task_id='train_models',
    python_callable=train_models_task,
    provide_context=True,
    dag=dag,
)

# Task 5: Evaluate Models
evaluate_models = PythonOperator(
    task_id='evaluate_models',
    python_callable=evaluate_models_task,
    provide_context=True,
    dag=dag,
)

# Task 6: Register Best Model
register_best_model = PythonOperator(
    task_id='register_best_model',
    python_callable=register_best_model_task,
    provide_context=True,
    dag=dag,
)

# Task 7: Send Notification
send_notification = PythonOperator(
    task_id='send_notification',
    python_callable=send_notification_task,
    provide_context=True,
    dag=dag,
)

# ============================================
# TASK DEPENDENCIES
# ============================================
download_data >> run_eda >> preprocess_data >> train_models >> evaluate_models >> register_best_model >> send_notification
```

**DAG Configuration Explanation:**

**1. Default Arguments:**
```python
default_args = {
    'owner': 'data-science-team',  # Who owns this DAG
    'depends_on_past': False,       # Don't wait for previous runs
    'start_date': datetime(2024, 1, 1),  # When DAG becomes active
    'email_on_failure': True,       # Alert on failures
    'retries': 2,                   # Retry failed tasks twice
    'retry_delay': timedelta(minutes=5),  # Wait 5 min between retries
    'execution_timeout': timedelta(hours=2),  # Kill if runs > 2 hours
}
```

**2. Schedule Interval:**
```python
schedule_interval='0 2 * * 0'  # Cron format
```
- `0` - Minute (0)
- `2` - Hour (2 AM)
- `*` - Day of month (any)
- `*` - Month (any)
- `0` - Day of week (Sunday)

**Common Schedules:**
- `@daily` - Every day at midnight
- `@weekly` - Every Sunday at midnight
- `@monthly` - First day of month at midnight
- `0 */6 * * *` - Every 6 hours
- `None` - Manual trigger only

**3. Catchup:**
```python
catchup=False
```
- If `True`, Airflow runs for all past dates since `start_date`
- If `False`, only runs for current/future dates
- Set to `False` for ML pipelines (don't want to retrain for past dates)

**4. Max Active Runs:**
```python
max_active_runs=1
```
- Only one instance of this DAG can run at a time
- Prevents concurrent training (resource conflicts)

**5. Task Dependencies:**
```python
task1 >> task2 >> task3
```
- `>>` means "then" (task1, then task2, then task3)
- Can also use `task1.set_downstream(task2)`
- Can create complex dependencies: `[task1, task2] >> task3 >> [task4, task5]`

### 7.2 Testing the DAG

Before running the full pipeline, test the DAG syntax and individual tasks.

**Step 1: Validate DAG Syntax**
```bash
# Test DAG file for syntax errors
python /opt/airflow/dags/ml_training_pipeline.py

# List all DAGs
docker exec lab01-airflow-webserver airflow dags list

# Check for import errors
docker exec lab01-airflow-webserver airflow dags list-import-errors
```

**Step 2: Test Individual Task**
```bash
# Test a single task
docker exec lab01-airflow-webserver airflow tasks test \
  credit_card_ml_pipeline \
  download_data \
  2024-01-01
```

**Step 3: Trigger Full DAG**
```bash
# Trigger DAG manually
docker exec lab01-airflow-webserver airflow dags trigger credit_card_ml_pipeline

# Or use the UI:
# 1. Go to http://localhost:8080
# 2. Find "credit_card_ml_pipeline"
# 3. Toggle to "On"
# 4. Click "Trigger DAG" (play button)
```

**Step 4: Monitor Execution**

In Airflow UI (http://localhost:8080):
1. Click on DAG name
2. View "Graph" tab - see task dependencies
3. View "Grid" tab - see run history
4. Click on task to see logs

**Expected Task Colors:**
- 🟢 Green: Success
- 🔴 Red: Failed
- 🟡 Yellow: Running
- ⚪ White: Queued
- 🔵 Blue: Skipped

### 7.3 Viewing Results in MLflow

After the pipeline completes, view results in MLflow UI.

**Access MLflow:**
```bash
# Open MLflow UI
open http://localhost:5000
```

**Navigate to Experiment:**
1. Click "Experiments" in sidebar
2. Find "Credit Card Approval - Automated Pipeline"
3. See all three model runs

**Compare Models:**
1. Select all three runs (checkboxes)
2. Click "Compare" button
3. View metrics side-by-side
4. See parallel coordinates plot

**View Best Model:**
1. Click "Models" tab
2. Find "card_approval_production"
3. See version in "Staging" stage
4. View model details and metrics

### 7.4 Understanding the Complete Workflow

Let's trace a complete pipeline execution:

**Execution Flow:**
```
1. Airflow Scheduler detects it's Sunday 2 AM
   ↓
2. Creates DAG run instance
   ↓
3. Executes download_data task
   - Validates data exists
   - Pushes metadata to XCom
   ↓
4. Executes run_eda task
   - Pulls data path from XCom
   - Analyzes data
   - Pushes EDA results to XCom
   ↓
5. Executes preprocess_data task
   - Handles missing values
   - Engineers features
   - Applies SMOTE
   - Saves processed data
   ↓
6. Executes train_models task
   - Loads processed data
   - Trains 3 models
   - Logs to MLflow
   - Pushes results to XCom
   ↓
7. Executes evaluate_models task
   - Pulls training results from XCom
   - Compares models
   - Selects best by ROC-AUC
   - Checks quality gate
   - Pushes best model to XCom
   ↓
8. Executes register_best_model task
   - Pulls best model from XCom
   - Registers to MLflow Registry
   - Promotes to Staging
   ↓
9. Executes send_notification task
   - Pulls best model from XCom
   - Logs completion message
   ↓
10. DAG run marked as SUCCESS
```

**Data Flow:**
```
Raw CSV
  ↓ (download_data)
Validated Data
  ↓ (run_eda)
EDA Results (XCom)
  ↓ (preprocess_data)
Processed NumPy Arrays + Artifacts
  ↓ (train_models)
Trained Models + MLflow Runs
  ↓ (evaluate_models)
Best Model Selection (XCom)
  ↓ (register_best_model)
MLflow Registry (Staging)
  ↓ (send_notification)
Notification Sent
```

### 7.5 Checkpoint

Verify the complete pipeline is working.

**Self-Assessment:**
- [ ] DAG appears in Airflow UI without errors
- [ ] All tasks execute successfully
- [ ] MLflow shows three model runs
- [ ] Best model is registered in MLflow Registry
- [ ] You can view logs for each task
- [ ] You understand the task dependencies
- [ ] You can trigger the DAG manually

**Verification Commands:**

```bash
# Check DAG status
docker exec lab01-airflow-webserver airflow dags list | grep credit_card

# View last DAG run
docker exec lab01-airflow-webserver airflow dags list-runs -d credit_card_ml_pipeline

# Check task logs
docker exec lab01-airflow-webserver airflow tasks logs \
  credit_card_ml_pipeline train_models <execution_date>

# Query MLflow for experiments
curl http://localhost:5000/api/2.0/mlflow/experiments/list | jq

# Query MLflow for registered models
curl http://localhost:5000/api/2.0/mlflow/registered-models/list | jq
```

## Epilogue: The Complete System

You have built a fully automated ML pipeline that runs without human intervention.

### What You Built

| Component | Purpose | Technology |
|-----------|---------|------------|
| Data Pipeline | Download and validate data | Airflow Task |
| EDA | Analyze dataset characteristics | Pandas, NumPy |
| Preprocessing | Clean, transform, balance data | Scikit-learn, SMOTE |
| Model Training | Train 3 models with tracking | Scikit-learn, XGBoost, MLflow |
| Model Evaluation | Compare and select best model | Scikit-learn metrics |
| Model Registry | Version and stage models | MLflow Registry |
| Orchestration | Automate entire workflow | Apache Airflow |
| Monitoring | Track pipeline execution | Airflow UI, MLflow UI |

### Complete Workflow Verification

Run through the entire system to verify everything works:

```bash
# 1. Start all services
docker-compose -f docker-compose.local.lab01.yml up -d

# 2. Wait for services to be healthy
docker-compose -f docker-compose.local.lab01.yml ps

# 3. Access Airflow UI
open http://localhost:8080
# Login: admin / admin_secure_password

# 4. Enable and trigger DAG
# In UI: Toggle DAG on, click trigger button

# 5. Monitor execution
# Watch tasks turn green in Graph view

# 6. View MLflow results
open http://localhost:5000
# Navigate to experiment, compare runs

# 7. Check registered model
# In MLflow: Models tab → card_approval_production

# 8. View logs
docker-compose -f docker-compose.local.lab01.yml logs -f airflow-scheduler
```

### System Capabilities

Your automated pipeline now:

✅ **Runs on Schedule**: Every Sunday at 2 AM, automatically
✅ **Handles Failures**: Retries failed tasks, sends alerts
✅ **Tracks Everything**: All experiments logged to MLflow
✅ **Selects Best Model**: Automatically based on ROC-AUC
✅ **Quality Gates**: Rejects models below F1 threshold
✅ **Version Control**: Models versioned in MLflow Registry
✅ **Reproducible**: All hyperparameters and data tracked
✅ **Monitorable**: Full visibility in Airflow and MLflow UIs

## The Principles

These principles apply beyond this specific lab:

1. **Automate from Day One** — Manual processes don't scale. Automate early, even if it takes longer initially.

2. **Track Everything** — You can't improve what you don't measure. Log all parameters, metrics, and artifacts.

3. **Fail Fast with Quality Gates** — Don't deploy bad models. Implement automated quality checks.

4. **Make Failures Visible** — Silent failures are dangerous. Alert on failures, log extensively.

5. **Separate Concerns** — Data processing, training, and evaluation are separate tasks. Keep them modular.

6. **Idempotent Tasks** — Tasks should be safe to run multiple times. Check if work is done before doing it.

7. **Version Everything** — Code, data, models, and configurations. Use git, DVC, and MLflow.

8. **Design for Observability** — You will need to debug. Make logs clear and accessible.

9. **Start Simple, Add Complexity** — Begin with basic pipeline, add features incrementally.

10. **Document Decisions** — Future you (and your team) will thank you. Explain why, not just what.

## Troubleshooting

### DAG Not Appearing in UI

**Symptoms:** DAG doesn't show in Airflow UI

**Causes & Solutions:**

1. **Syntax Error in DAG File**
   ```bash
   # Check for errors
   python /opt/airflow/dags/ml_training_pipeline.py
   
   # Check import errors
   docker exec lab01-airflow-webserver airflow dags list-import-errors
   ```

2. **DAG File Not in dags/ Directory**
   ```bash
   # Verify file location
   docker exec lab01-airflow-webserver ls -la /opt/airflow/dags/
   ```

3. **Scheduler Not Running**
   ```bash
   # Check scheduler status
   docker-compose -f docker-compose.local.lab01.yml ps airflow-scheduler
   
   # Restart scheduler
   docker-compose -f docker-compose.local.lab01.yml restart airflow-scheduler
   ```

### Task Failing with Import Error

**Symptoms:** Task fails with `ModuleNotFoundError`

**Solution:**
```python
# Add to top of DAG file
import sys
sys.path.insert(0, '/opt/airflow/training/scripts')
```

### MLflow Connection Refused

**Symptoms:** Tasks fail with "Connection refused" to MLflow

**Causes & Solutions:**

1. **MLflow Not Running**
   ```bash
   # Check MLflow status
   docker-compose -f docker-compose.local.lab01.yml ps mlflow
   
   # Check MLflow logs
   docker-compose -f docker-compose.local.lab01.yml logs mlflow
   ```

2. **Wrong MLflow URI**
   ```python
   # In Docker, use service name
   MLFLOW_TRACKING_URI = "http://mlflow:5000"  # ✓ Correct
   MLFLOW_TRACKING_URI = "http://localhost:5000"  # ✗ Wrong (from container)
   ```

### SMOTE Failing

**Symptoms:** `preprocess_data` task fails with SMOTE error

**Solution:**
```bash
# Install imbalanced-learn in Airflow container
docker exec lab01-airflow-webserver pip install imbalanced-learn
```

### Out of Memory

**Symptoms:** Tasks killed with exit code 137

**Solution:**
```bash
# Increase Docker memory limit
# Docker Desktop → Settings → Resources → Memory → 8GB+

# Or reduce dataset size for testing
df = df.sample(n=10000, random_state=42)
```

### XCom Data Too Large

**Symptoms:** Warning about XCom size

**Solution:**
```python
# Don't push large data to XCom
# Instead, save to file and push file path
np.save('/tmp/data.npy', large_array)
context['task_instance'].xcom_push(key='data_path', value='/tmp/data.npy')
```

## Next Steps

Extend your ML pipeline with these enhancements:

### 1. Add Data Download from Kaggle
```python
def download_data_task(**context):
    import kaggle
    kaggle.api.dataset_download_files(
        'rikdifos/credit-card-approval-prediction',
        path='/opt/airflow/training/data/raw',
        unzip=True
    )
```

### 2. Implement Hyperparameter Tuning
```python
from sklearn.model_selection import GridSearchCV

param_grid = {
    'max_depth': [6, 8, 10],
    'learning_rate': [0.01, 0.1, 0.3],
    'n_estimators': [100, 200]
}

grid_search = GridSearchCV(XGBClassifier(), param_grid, cv=5)
grid_search.fit(X_train, y_train)
```

### 3. Add Feature Importance Analysis
```python
import matplotlib.pyplot as plt

# Get feature importance
importance = model.feature_importances_
features = feature_names

# Plot
plt.barh(features, importance)
plt.xlabel('Importance')
plt.title('Feature Importance')
plt.savefig('/tmp/feature_importance.png')

# Log to MLflow
mlflow.log_artifact('/tmp/feature_importance.png')
```

### 4. Implement Model Comparison Report
```python
import pandas as pd

# Create comparison DataFrame
comparison_df = pd.DataFrame(results)
comparison_df.to_csv('/tmp/model_comparison.csv', index=False)

# Log to MLflow
mlflow.log_artifact('/tmp/model_comparison.csv')
```

### 5. Add Email Notifications
```python
from airflow.utils.email import send_email

def send_notification_task(**context):
    best_model = context['task_instance'].xcom_pull(
        task_ids='evaluate_models',
        key='best_model'
    )
    
    send_email(
        to=['team@company.com'],
        subject='ML Pipeline Complete',
        html_content=f"""
        <h2>Pipeline Completed Successfully</h2>
        <p>Best Model: {best_model['model_name']}</p>
        <p>ROC-AUC: {best_model['roc_auc']:.4f}</p>
        """
    )
```

### 6. Add Slack Notifications
```python
from airflow.providers.slack.operators.slack_webhook import SlackWebhookOperator

send_slack = SlackWebhookOperator(
    task_id='send_slack',
    http_conn_id='slack_webhook',
    message='ML Pipeline completed! Check MLflow for results.',
    channel='#ml-ops',
    dag=dag
)
```

### 7. Implement Data Validation
```python
import great_expectations as ge

def validate_data_task(**context):
    df = pd.read_csv(data_path)
    ge_df = ge.from_pandas(df)
    
    # Define expectations
    ge_df.expect_column_values_to_not_be_null('TARGET')
    ge_df.expect_column_values_to_be_between('AGE_YEARS', 18, 100)
    
    # Validate
    results = ge_df.validate()
    
    if not results['success']:
        raise ValueError("Data validation failed!")
```

### 8. Add Model Explainability
```python
import shap

# Create SHAP explainer
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test)

# Plot
shap.summary_plot(shap_values, X_test, feature_names=feature_names)
plt.savefig('/tmp/shap_summary.png')

# Log to MLflow
mlflow.log_artifact('/tmp/shap_summary.png')
```

## Additional Resources

- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [MLflow Documentation](https://mlflow.org/docs/latest/)
- [Airflow Best Practices](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html)
- [MLflow Model Registry](https://mlflow.org/docs/latest/model-registry.html)
- [SMOTE Documentation](https://imbalanced-learn.org/stable/references/generated/imblearn.over_sampling.SMOTE.html)
- [XGBoost Documentation](https://xgboost.readthedocs.io/)
- [Scikit-learn User Guide](https://scikit-learn.org/stable/user_guide.html)

## Summary

Congratulations! You have successfully built a production-grade automated ML pipeline.

**What You Accomplished:**

✅ Understood credit card approval dataset challenges (imbalance, missing values)
✅ Justified model selection with clear reasoning (3 models, each with purpose)
✅ Implemented comprehensive preprocessing (SMOTE, scaling, encoding)
✅ Set up Docker Compose for local development (5 services)
✅ Created Airflow DAG with 7 automated tasks
✅ Integrated MLflow tracking for all experiments
✅ Registered best model to MLflow Registry
✅ Implemented quality gates and error handling
✅ Built a system that runs without human intervention

**Key Takeaways:**

1. **Automation is Essential**: Manual ML workflows don't scale
2. **Tracking is Critical**: MLflow provides experiment reproducibility
3. **Orchestration Matters**: Airflow manages complex dependencies
4. **Quality Gates Protect**: Automated checks prevent bad models
5. **Observability Enables Debugging**: Logs and UIs make troubleshooting possible

**Next Lab Preview:**

In Lab 02, you will:
- Build a FastAPI application to serve predictions
- Load models from MLflow Registry
- Implement caching with Redis
- Add health and readiness endpoints
- Log predictions to PostgreSQL

The automated training pipeline you built in this lab will provide models for the API in Lab 02.

---

**🎉 Lab 01 Complete! You're ready for Lab 02: FastAPI Integration**
