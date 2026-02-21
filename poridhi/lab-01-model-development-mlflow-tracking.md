# Lab 01: Automated ML Pipeline with Airflow & MLflow

## Introduction

This lab builds a production-grade automated ML pipeline from the ground up. You will set up Apache Airflow to orchestrate the entire workflow (EDA, preprocessing, training) and MLflow to track all experiments. Everything runs through Airflow—no manual script execution.

## Learning Objectives

By the end of this lab, you will be able to:

1. Set up Apache Airflow for ML pipeline orchestration
2. Create Airflow DAGs to automate data processing and model training
3. Integrate MLflow tracking within Airflow tasks
4. Perform EDA, preprocessing, and training through Airflow
5. Handle class imbalance using SMOTE in automated pipelines
6. Train and compare multiple models automatically
7. Register best models to MLflow Model Registry
8. Schedule and monitor automated pipeline execution
9. Handle failures with automatic retries

**Prerequisites:** Basic Python, pandas, scikit-learn knowledge

**Estimated Time:** 6-8 hours

## Prologue: The Challenge

You join a fintech startup building an automated credit card approval system. The data science team runs training scripts manually, often forgetting to retrain models or track experiments properly. Models are saved with names like `model_v2_final_FINAL.pkl`. Nobody knows which hyperparameters produced which results.

You need a system that:
- Automatically downloads and processes data
- Trains models on a schedule (weekly)
- Tracks every experiment automatically
- Retries on failures
- Sends alerts when something breaks
- Requires zero manual intervention

Apache Airflow orchestrates the workflow. MLflow tracks every experiment. Together, they create a production-grade ML pipeline.

## Environment Setup

```bash
# Create project structure
mkdir -p card-approval-prediction
cd card-approval-prediction

# Create directories
mkdir -p dags training/{data/{raw,processed},scripts,src/{config,utils}} logs plugins

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install apache-airflow==2.8.0 \
  apache-airflow-providers-amazon \
  mlflow pandas numpy scikit-learn xgboost lightgbm \
  imbalanced-learn matplotlib seaborn boto3
```

## Chapter 1: Airflow Setup

### 1.1 What You Will Build

You will set up Apache Airflow as the orchestration engine for your ML pipeline.

### 1.2 Think First: Why Airflow First?

**Question:** Why set up Airflow before writing any ML code?

<details>
<summary>Click to review</summary>

**Airflow-first approach:**
- Defines workflow structure upfront
- Ensures all code is orchestrated (no manual scripts)
- Built-in scheduling, retries, monitoring
- Forces modular, reusable code
- Production-ready from day one

**Manual-first approach (what we're avoiding):**
- Scripts work locally but hard to productionize
- No scheduling or monitoring
- Manual execution required
- Difficult to add orchestration later

Starting with Airflow ensures everything is automated from the beginning.

</details>

### 1.3 Implementation

Initialize Airflow:

```bash
# Set Airflow home
export AIRFLOW_HOME=$(pwd)

# Initialize database
airflow db init

# Create admin user
airflow users create \
  --username admin \
  --firstname Admin \
  --lastname User \
  --role Admin \
  --email admin@example.com \
  --password admin
```

Start Airflow services:

```bash
# Terminal 1: Start webserver
airflow webserver --port 8080

# Terminal 2: Start scheduler
airflow scheduler
```

Access Airflow UI at `http://localhost:8080` (admin/admin)

### 1.4 Checkpoint

**Self-Assessment:**
- [ ] Airflow initialized successfully
- [ ] Airflow UI accessible at localhost:8080
- [ ] You can login with admin credentials
- [ ] Scheduler is running

## Chapter 2: MLflow Setup

### 2.1 What You Will Build

You will set up MLflow to track all experiments that Airflow executes.

### 2.2 Implementation

Start MLflow server:

```bash
# Terminal 3: Start MLflow
mlflow server \
  --backend-store-uri sqlite:///mlflow.db \
  --default-artifact-root ./mlruns \
  --host 0.0.0.0 \
  --port 5000
```

Access MLflow UI at `http://localhost:5000`

Create MLflow configuration:

```python
# training/src/config/mlflow_config.py
import mlflow
import os

class MLflowConfig:
    def __init__(self):
        self.tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
        self.experiment_name = "Card Approval - Automated Pipeline"
        
    def setup(self):
        """Configure MLflow for Airflow tasks."""
        mlflow.set_tracking_uri(self.tracking_uri)
        mlflow.set_experiment(self.experiment_name)
        return mlflow.get_experiment_by_name(self.experiment_name)
```

### 2.3 Checkpoint

**Self-Assessment:**
- [ ] MLflow server running
- [ ] MLflow UI accessible at localhost:5000
- [ ] Configuration module created

## Chapter 3: Creating the ML Pipeline DAG

### 3.1 What You Will Build

You will create an Airflow DAG that orchestrates the entire ML workflow: download data → EDA → preprocess → train → evaluate → register.

### 3.2 Think First: Task Dependencies

**Question:** What's the correct order for ML pipeline tasks?

<details>
<summary>Click to review</summary>

```
download_data
     ↓
run_eda
     ↓
preprocess_data
     ↓
train_models (can run in parallel for different algorithms)
     ↓
evaluate_models
     ↓
register_best_model
     ↓
send_notification
```

Each task depends on the previous one completing successfully.

</details>

### 3.3 Implementation

Create the DAG:

```python
# dags/ml_training_pipeline.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
import os

# Add project to path
sys.path.insert(0, os.path.abspath('.'))

default_args = {
    'owner': 'data-science-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'credit_card_ml_pipeline',
    default_args=default_args,
    description='Automated ML pipeline with Airflow and MLflow',
    schedule_interval='0 2 * * 0',  # Every Sunday at 2 AM
    catchup=False,
    tags=['ml', 'training', 'automated'],
)

# Import task functions (we'll create these next)
from training.scripts.airflow_tasks import (
    download_data_task,
    run_eda_task,
    preprocess_data_task,
    train_models_task,
    evaluate_models_task,
    register_best_model_task,
    send_notification_task
)

# Define tasks
download_data = PythonOperator(
    task_id='download_data',
    python_callable=download_data_task,
    dag=dag,
)

run_eda = PythonOperator(
    task_id='run_eda',
    python_callable=run_eda_task,
    dag=dag,
)

preprocess_data = PythonOperator(
    task_id='preprocess_data',
    python_callable=preprocess_data_task,
    dag=dag,
)

train_models = PythonOperator(
    task_id='train_models',
    python_callable=train_models_task,
    dag=dag,
)

evaluate_models = PythonOperator(
    task_id='evaluate_models',
    python_callable=evaluate_models_task,
    dag=dag,
)

register_best_model = PythonOperator(
    task_id='register_best_model',
    python_callable=register_best_model_task,
    dag=dag,
)

send_notification = PythonOperator(
    task_id='send_notification',
    python_callable=send_notification_task,
    dag=dag,
)

# Define dependencies
download_data >> run_eda >> preprocess_data >> train_models >> evaluate_models >> register_best_model >> send_notification
```

### 3.4 Checkpoint

**Self-Assessment:**
- [ ] DAG file created
- [ ] Task dependencies defined
- [ ] You understand the workflow order

## Chapter 4: Implementing Pipeline Tasks

### 4.1 What You Will Build

You will implement each task that Airflow will execute, with MLflow tracking integrated.

### 4.2 Implementation

Create task implementations:

```python
# training/scripts/airflow_tasks.py
import pandas as pd
import numpy as np
import mlflow
import mlflow.sklearn
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import f1_score, roc_auc_score, classification_report
from imblearn.over_sampling import SMOTE
import joblib
import logging
from training.src.config.mlflow_config import MLflowConfig

logger = logging.getLogger(__name__)

def download_data_task(**context):
    """Task 1: Download credit card approval dataset."""
    logger.info("Downloading dataset...")
    
    # TODO: Add actual download logic (Kaggle API, S3, etc.)
    # For now, assume data exists
    logger.info("Dataset downloaded successfully")
    return "data_downloaded"

def run_eda_task(**context):
    """Task 2: Perform exploratory data analysis."""
    logger.info("Running EDA...")
    
    # Load data
    df = pd.read_csv('training/data/raw/application_record.csv')
    
    # Basic analysis
    logger.info(f"Dataset shape: {df.shape}")
    logger.info(f"Missing values:\n{df.isnull().sum()}")
    
    # Class distribution
    target_counts = df['TARGET'].value_counts()
    logger.info(f"Class distribution:\n{target_counts}")
    logger.info(f"Class ratio: {target_counts[0] / target_counts[1]:.2f}:1")
    
    # Save EDA results
    eda_results = {
        'n_samples': len(df),
        'n_features': df.shape[1],
        'class_ratio': float(target_counts[0] / target_counts[1]),
        'missing_values': df.isnull().sum().to_dict()
    }
    
    context['task_instance'].xcom_push(key='eda_results', value=eda_results)
    logger.info("EDA completed")
    return "eda_complete"

def preprocess_data_task(**context):
    """Task 3: Preprocess data with SMOTE balancing."""
    logger.info("Preprocessing data...")
    
    # Load data
    df = pd.read_csv('training/data/raw/application_record.csv')
    
    # Handle missing values
    df['OCCUPATION_TYPE'].fillna('Unknown', inplace=True)
    df['CNT_FAM_MEMBERS'].fillna(df['CNT_FAM_MEMBERS'].median(), inplace=True)
    
    # Encode categorical variables
    label_encoders = {}
    for col in df.select_dtypes(include=['object']).columns:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col])
        label_encoders[col] = le
    
    # Split features and target
    X = df.drop('TARGET', axis=1)
    y = df['TARGET']
    
    # Stratified split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Apply SMOTE
    smote = SMOTE(random_state=42)
    X_train_balanced, y_train_balanced = smote.fit_resample(X_train_scaled, y_train)
    
    # Save processed data
    np.save('training/data/processed/X_train_balanced.npy', X_train_balanced)
    np.save('training/data/processed/y_train_balanced.npy', y_train_balanced)
    np.save('training/data/processed/X_test.npy', X_test_scaled)
    np.save('training/data/processed/y_test.npy', y_test)
    
    # Save preprocessing artifacts
    joblib.dump(scaler, 'training/models/scaler.pkl')
    joblib.dump(label_encoders, 'training/models/label_encoders.pkl')
    
    logger.info(f"Preprocessing complete. Balanced training set: {X_train_balanced.shape}")
    return "preprocessing_complete"

def train_models_task(**context):
    """Task 4: Train multiple models with MLflow tracking."""
    logger.info("Training models with MLflow tracking...")
    
    # Setup MLflow
    mlflow_config = MLflowConfig()
    mlflow_config.setup()
    
    # Load data
    X_train = np.load('training/data/processed/X_train_balanced.npy')
    y_train = np.load('training/data/processed/y_train_balanced.npy')
    X_test = np.load('training/data/processed/X_test.npy')
    y_test = np.load('training/data/processed/y_test.npy')
    
    models = {
        'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
        'XGBoost': XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42),
        'Random Forest': RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    }
    
    results = []
    
    for model_name, model in models.items():
        with mlflow.start_run(run_name=f"{model_name}_airflow"):
            logger.info(f"Training {model_name}...")
            
            # Log parameters
            mlflow.log_param("model_type", model_name)
            mlflow.log_params(model.get_params())
            
            # Train
            model.fit(X_train, y_train)
            
            # Evaluate
            y_pred = model.predict(X_test)
            y_pred_proba = model.predict_proba(X_test)[:, 1]
            
            f1 = f1_score(y_test, y_pred)
            roc_auc = roc_auc_score(y_test, y_pred_proba)
            
            # Log metrics
            mlflow.log_metric("f1_score", f1)
            mlflow.log_metric("roc_auc", roc_auc)
            
            # Log model
            mlflow.sklearn.log_model(
                model,
                "model",
                registered_model_name=f"card_approval_{model_name.lower().replace(' ', '_')}"
            )
            
            results.append({
                'model_name': model_name,
                'f1_score': f1,
                'roc_auc': roc_auc,
                'run_id': mlflow.active_run().info.run_id
            })
            
            logger.info(f"{model_name} - F1: {f1:.4f}, ROC-AUC: {roc_auc:.4f}")
    
    # Store results in XCom
    context['task_instance'].xcom_push(key='training_results', value=results)
    logger.info("All models trained successfully")
    return "training_complete"

def evaluate_models_task(**context):
    """Task 5: Evaluate and select best model."""
    logger.info("Evaluating models...")
    
    # Get training results from XCom
    results = context['task_instance'].xcom_pull(task_ids='train_models', key='training_results')
    
    # Find best model by ROC-AUC
    best_model = max(results, key=lambda x: x['roc_auc'])
    
    logger.info(f"Best model: {best_model['model_name']}")
    logger.info(f"ROC-AUC: {best_model['roc_auc']:.4f}")
    logger.info(f"F1-Score: {best_model['f1_score']:.4f}")
    
    # Store best model info
    context['task_instance'].xcom_push(key='best_model', value=best_model)
    
    # Quality gate: F1 score must be > 0.75
    if best_model['f1_score'] < 0.75:
        raise ValueError(f"Model quality below threshold. F1: {best_model['f1_score']:.4f} < 0.75")
    
    logger.info("Model evaluation passed quality gate")
    return "evaluation_complete"

def register_best_model_task(**context):
    """Task 6: Register best model to MLflow Registry."""
    logger.info("Registering best model...")
    
    # Get best model info
    best_model = context['task_instance'].xcom_pull(task_ids='evaluate_models', key='best_model')
    
    # Setup MLflow
    mlflow_config = MLflowConfig()
    mlflow_config.setup()
    
    from mlflow.tracking import MlflowClient
    client = MlflowClient()
    
    # Get model from run
    run_id = best_model['run_id']
    model_name = "card_approval_production"
    
    # Register model
    model_uri = f"runs:/{run_id}/model"
    model_details = mlflow.register_model(model_uri, model_name)
    
    # Promote to Staging
    client.transition_model_version_stage(
        name=model_name,
        version=model_details.version,
        stage="Staging"
    )
    
    # Add description
    client.update_model_version(
        name=model_name,
        version=model_details.version,
        description=f"Best model: {best_model['model_name']}. ROC-AUC: {best_model['roc_auc']:.4f}"
    )
    
    logger.info(f"Model registered: {model_name} v{model_details.version}")
    return "registration_complete"

def send_notification_task(**context):
    """Task 7: Send completion notification."""
    logger.info("Sending notification...")
    
    best_model = context['task_instance'].xcom_pull(task_ids='evaluate_models', key='best_model')
    
    message = f"""
    ML Pipeline Completed Successfully!
    
    Best Model: {best_model['model_name']}
    ROC-AUC: {best_model['roc_auc']:.4f}
    F1-Score: {best_model['f1_score']:.4f}
    
    Model registered to MLflow Registry (Staging stage)
    """
    
    logger.info(message)
    # TODO: Add email/Slack notification
    
    return "notification_sent"
```

### 4.3 Checkpoint

**Self-Assessment:**
- [ ] All task functions implemented
- [ ] MLflow tracking integrated
- [ ] Tasks use XCom for data passing
- [ ] Quality gate implemented

## Chapter 5: Running the Pipeline

### 5.1 Test and Verify

Trigger the pipeline:

```bash
# Test DAG syntax
python dags/ml_training_pipeline.py

# List DAGs
airflow dags list | grep credit_card

# Trigger manually
airflow dags trigger credit_card_ml_pipeline
```

Monitor in Airflow UI:
1. Go to `http://localhost:8080`
2. Find `credit_card_ml_pipeline`
3. Click to view Graph/Grid
4. Watch tasks turn green as they complete

View results in MLflow:
1. Go to `http://localhost:5000`
2. See experiment "Card Approval - Automated Pipeline"
3. Compare runs from different models

### 5.2 Checkpoint

**Self-Assessment:**
- [ ] Pipeline triggers successfully
- [ ] All tasks complete (green in Airflow)
- [ ] Experiments appear in MLflow
- [ ] Best model registered in MLflow Registry

## Epilogue: The Complete System

You have built a fully automated ML pipeline:

| Component | Capability |
|-----------|------------|
| Airflow | Orchestrates entire workflow |
| MLflow | Tracks all experiments automatically |
| Automated EDA | Runs through Airflow |
| Automated Preprocessing | SMOTE balancing via Airflow |
| Automated Training | Multiple models trained automatically |
| Quality Gate | Ensures F1 > 0.75 before registration |
| Model Registry | Best model promoted to Staging |
| Scheduling | Runs every Sunday at 2 AM |

Verify the complete workflow:

```bash
# Check Airflow
open http://localhost:8080

# Check MLflow
open http://localhost:5000

# View logs
airflow tasks logs credit_card_ml_pipeline download_data 2024-01-01
```

## The Principles

1. **Automate from day one** — No manual script execution
2. **Orchestration first** — Airflow defines the workflow
3. **Track everything** — MLflow logs all experiments automatically
4. **Quality gates** — Automated checks prevent bad models
5. **Fail fast** — Retries and alerts on failures
6. **Schedule intelligently** — Weekly retraining without manual intervention
7. **Monitor continuously** — Airflow UI shows pipeline health

## Troubleshooting

### Error: DAG not appearing

**Solution:**
```bash
# Check syntax
python dags/ml_training_pipeline.py

# Check import errors
airflow dags list-import-errors
```

### Error: Task failing with import errors

**Solution:**
```python
# Add to DAG file
import sys
sys.path.insert(0, os.path.abspath('.'))
```

### Error: MLflow connection refused

**Solution:**
```bash
# Ensure MLflow is running
mlflow server --backend-store-uri sqlite:///mlflow.db \
  --default-artifact-root ./mlruns --host 0.0.0.0 --port 5000
```

## Next Steps

1. **Add data download:** Integrate Kaggle API or S3 download
2. **Email alerts:** Configure SMTP for failure notifications
3. **Slack integration:** Send pipeline status to Slack
4. **Parallel training:** Train models simultaneously
5. **Data validation:** Add Great Expectations checks
6. **Model comparison:** Generate comparison reports
7. **Auto-promotion:** Promote to Production if metrics improve

## Additional Resources

- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [MLflow Documentation](https://mlflow.org/docs/latest/)
- [Airflow Best Practices](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html)
- [MLflow with Airflow](https://mlflow.org/docs/latest/tracking.html)
