# Lab 01: Part 4 - Airflow Integration and Docker Compose

## Chapter 5: Docker Compose Setup for Lab 01

### 5.1 Understanding the Lab 01 Architecture

Before creating the Docker Compose file, understand what services we need and why.

**Lab 01 Services:**
```
┌─────────────────────────────────────────────────────────┐
│                    Lab 01 Architecture                   │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐         ┌──────────────┐             │
│  │   Airflow    │────────▶│  PostgreSQL  │             │
│  │  Webserver   │         │  (Airflow)   │             │
│  └──────────────┘         └──────────────┘             │
│         │                                                │
│         │                                                │
│  ┌──────────────┐         ┌──────────────┐             │
│  │   Airflow    │────────▶│  PostgreSQL  │             │
│  │  Scheduler   │         │  (MLflow)    │             │
│  └──────────────┘         └──────────────┘             │
│         │                         ▲                      │
│         │                         │                      │
│         ▼                         │                      │
│  ┌──────────────┐                │                      │
│  │   Training   │                │                      │
│  │    Tasks     │────────────────┘                      │
│  │  (MLflow)    │                                        │
│  └──────────────┘                                        │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Why These Services?**

1. **PostgreSQL (Airflow)**: Stores Airflow metadata (DAGs, tasks, runs)
2. **PostgreSQL (MLflow)**: Stores MLflow metadata (experiments, runs, metrics)
3. **Airflow Webserver**: Web UI for monitoring pipelines
4. **Airflow Scheduler**: Executes tasks on schedule
5. **MLflow Server**: Tracks experiments and stores models

**What's NOT in Lab 01:**
- No FastAPI (comes in Lab 02)
- No Redis (comes in Lab 02)
- No Monitoring stack (comes in Lab 03)

### 5.2 Creating the Docker Compose File

Create the Docker Compose file for Lab 01 services only.

```yaml
# docker-compose.local.lab01.yml
version: '3.8'

services:
  # ============================================
  # PostgreSQL for Airflow (Metadata)
  # ============================================
  postgres-airflow:
    image: postgres:15-alpine
    container_name: lab01-postgres-airflow
    environment:
      POSTGRES_DB: airflow
      POSTGRES_USER: airflow
      POSTGRES_PASSWORD: ${POSTGRES_AIRFLOW_PASSWORD:-airflow_password}
    ports:
      - "5434:5432"
    volumes:
      - postgres-airflow-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U airflow -d airflow"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - lab01-network
    restart: unless-stopped

  # ============================================
  # PostgreSQL for MLflow (Metadata)
  # ============================================
  postgres-mlflow:
    image: postgres:15-alpine
    container_name: lab01-postgres-mlflow
    environment:
      POSTGRES_DB: mlflow
      POSTGRES_USER: mlflow_user
      POSTGRES_PASSWORD: ${POSTGRES_MLFLOW_PASSWORD:-mlflow_password}
    ports:
      - "5433:5432"
    volumes:
      - postgres-mlflow-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mlflow_user -d mlflow"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - lab01-network
    restart: unless-stopped

  # ============================================
  # MLflow Server
  # ============================================
  mlflow:
    image: python:3.11-slim
    container_name: lab01-mlflow
    working_dir: /mlflow
    command: >
      bash -c "
      pip install mlflow psycopg2-binary boto3 &&
      mlflow server
      --backend-store-uri postgresql://mlflow_user:${POSTGRES_MLFLOW_PASSWORD:-mlflow_password}@postgres-mlflow:5432/mlflow
      --default-artifact-root /mlflow/artifacts
      --host 0.0.0.0
      --port 5000
      "
    environment:
      # For future S3 integration (Lab 04)
      AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID:-}
      AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY:-}
      AWS_DEFAULT_REGION: ${AWS_REGION:-us-east-1}
    ports:
      - "5000:5000"
    volumes:
      - mlflow-artifacts:/mlflow/artifacts
    depends_on:
      postgres-mlflow:
        condition: service_healthy
    networks:
      - lab01-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ============================================
  # Airflow Init (Database Setup)
  # ============================================
  airflow-init:
    build:
      context: ./airflow
      dockerfile: Dockerfile
    container_name: lab01-airflow-init
    entrypoint: /bin/bash
    command:
      - -c
      - |
        airflow db migrate
        airflow users create \
          --username admin \
          --firstname Admin \
          --lastname User \
          --role Admin \
          --email admin@example.com \
          --password ${AIRFLOW_ADMIN_PASSWORD:-admin}
    environment:
      AIRFLOW__CORE__EXECUTOR: LocalExecutor
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:${POSTGRES_AIRFLOW_PASSWORD:-airflow_password}@postgres-airflow/airflow
      AIRFLOW__CORE__FERNET_KEY: ${AIRFLOW_FERNET_KEY:-fb0c3f8c8b3f4c5e8d9a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e}
      AIRFLOW__CORE__LOAD_EXAMPLES: 'false'
    depends_on:
      postgres-airflow:
        condition: service_healthy
    networks:
      - lab01-network

  # ============================================
  # Airflow Webserver
  # ============================================
  airflow-webserver:
    build:
      context: ./airflow
      dockerfile: Dockerfile
    container_name: lab01-airflow-webserver
    command: webserver
    environment:
      AIRFLOW__CORE__EXECUTOR: LocalExecutor
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:${POSTGRES_AIRFLOW_PASSWORD:-airflow_password}@postgres-airflow/airflow
      AIRFLOW__CORE__FERNET_KEY: ${AIRFLOW_FERNET_KEY:-fb0c3f8c8b3f4c5e8d9a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e}
      AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION: 'true'
      AIRFLOW__CORE__LOAD_EXAMPLES: 'false'
      AIRFLOW__WEBSERVER__EXPOSE_CONFIG: 'true'
      AIRFLOW__WEBSERVER__SECRET_KEY: ${AIRFLOW_SECRET_KEY:-secret}
      # MLflow connection
      MLFLOW_TRACKING_URI: http://mlflow:5000
      # For future AWS integration (Lab 04)
      AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID:-}
      AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY:-}
      AWS_DEFAULT_REGION: ${AWS_REGION:-us-east-1}
    ports:
      - "8080:8080"
    volumes:
      - ./dags:/opt/airflow/dags
      - ./training:/opt/airflow/training
      - ./scripts:/opt/airflow/scripts
      - airflow-logs:/opt/airflow/logs
      - training-data:/opt/airflow/training/data
      - training-models:/opt/airflow/training/models
    depends_on:
      postgres-airflow:
        condition: service_healthy
      mlflow:
        condition: service_started
      airflow-init:
        condition: service_completed_successfully
    networks:
      - lab01-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "--fail", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 5

  # ============================================
  # Airflow Scheduler
  # ============================================
  airflow-scheduler:
    build:
      context: ./airflow
      dockerfile: Dockerfile
    container_name: lab01-airflow-scheduler
    command: scheduler
    environment:
      AIRFLOW__CORE__EXECUTOR: LocalExecutor
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:${POSTGRES_AIRFLOW_PASSWORD:-airflow_password}@postgres-airflow/airflow
      AIRFLOW__CORE__FERNET_KEY: ${AIRFLOW_FERNET_KEY:-fb0c3f8c8b3f4c5e8d9a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e}
      AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION: 'true'
      AIRFLOW__CORE__LOAD_EXAMPLES: 'false'
      # MLflow connection
      MLFLOW_TRACKING_URI: http://mlflow:5000
      # For future AWS integration (Lab 04)
      AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID:-}
      AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY:-}
      AWS_DEFAULT_REGION: ${AWS_REGION:-us-east-1}
    volumes:
      - ./dags:/opt/airflow/dags
      - ./training:/opt/airflow/training
      - ./scripts:/opt/airflow/scripts
      - airflow-logs:/opt/airflow/logs
      - training-data:/opt/airflow/training/data
      - training-models:/opt/airflow/training/models
    depends_on:
      postgres-airflow:
        condition: service_healthy
      airflow-init:
        condition: service_completed_successfully
    networks:
      - lab01-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "airflow jobs check --job-type SchedulerJob --hostname $(hostname)"]
      interval: 30s
      timeout: 10s
      retries: 5

# ============================================
# Networks
# ============================================
networks:
  lab01-network:
    driver: bridge
    name: lab01-network

# ============================================
# Volumes
# ============================================
volumes:
  postgres-airflow-data:
    name: lab01-postgres-airflow-data
  postgres-mlflow-data:
    name: lab01-postgres-mlflow-data
  mlflow-artifacts:
    name: lab01-mlflow-artifacts
  airflow-logs:
    name: lab01-airflow-logs
  training-data:
    name: lab01-training-data
  training-models:
    name: lab01-training-models
```

**Configuration Explanation:**

**1. Service Naming:**
- Prefix with `lab01-` to avoid conflicts with other labs
- Clear container names for easy identification

**2. Port Mapping:**
- `5434:5432` - Airflow PostgreSQL (avoid conflict with default 5432)
- `5433:5432` - MLflow PostgreSQL
- `5000:5000` - MLflow UI
- `8080:8080` - Airflow UI

**3. Health Checks:**
- PostgreSQL: `pg_isready` command
- MLflow: HTTP health endpoint
- Airflow: Built-in health endpoints
- Purpose: Ensure services are ready before dependent services start

**4. Volumes:**
- Named volumes for data persistence
- Bind mounts for code (allows live editing)
- Separate volumes for each service

**5. Dependencies:**
- `depends_on` with `condition` ensures proper startup order
- Databases must be healthy before Airflow starts
- Init must complete before webserver/scheduler start

### 5.3 Creating the Airflow Dockerfile

Create a custom Airflow image with all required dependencies.

```dockerfile
# airflow/Dockerfile
FROM apache/airflow:2.8.0-python3.11

# Switch to root to install system dependencies
USER root

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Switch back to airflow user
USER airflow

# Install Python dependencies
COPY requirements-airflow.txt /requirements-airflow.txt
RUN pip install --no-cache-dir -r /requirements-airflow.txt

# Set working directory
WORKDIR /opt/airflow
```

**Create requirements file:**

```txt
# airflow/requirements-airflow.txt
# ML Libraries
scikit-learn==1.3.2
xgboost==2.0.3
imbalanced-learn==0.11.0
pandas==2.1.4
numpy==1.26.2

# MLflow
mlflow==2.9.2
psycopg2-binary==2.9.9

# AWS (for future Lab 04)
boto3==1.34.14

# Utilities
joblib==1.3.2
```

**Dockerfile Explanation:**

1. **Base Image**: Official Airflow 2.8.0 with Python 3.11
2. **System Dependencies**: build-essential for compiling Python packages
3. **User Switching**: Root for system packages, airflow user for Python packages
4. **No Cache**: `--no-cache-dir` reduces image size
5. **Requirements File**: Separate file for easy updates

### 5.4 Environment Variables

Create an environment file for configuration.

```bash
# .env.lab01
# PostgreSQL Passwords
POSTGRES_AIRFLOW_PASSWORD=airflow_secure_password
POSTGRES_MLFLOW_PASSWORD=mlflow_secure_password

# Airflow Configuration
AIRFLOW_ADMIN_PASSWORD=admin_secure_password
AIRFLOW_FERNET_KEY=fb0c3f8c8b3f4c5e8d9a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e
AIRFLOW_SECRET_KEY=your_secret_key_here

# AWS (Optional - for Lab 04)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
```

**Security Note:**
- Never commit `.env` files to git
- Use strong passwords in production
- Rotate credentials regularly
- Use secrets management in production (AWS Secrets Manager, etc.)

### 5.5 Starting Lab 01 Services

Start all Lab 01 services with Docker Compose.

```bash
# Build images
docker-compose -f docker-compose.local.lab01.yml build

# Start services
docker-compose -f docker-compose.local.lab01.yml up -d

# View logs
docker-compose -f docker-compose.local.lab01.yml logs -f

# Check service status
docker-compose -f docker-compose.local.lab01.yml ps
```

**Expected Output:**
```
NAME                        STATUS              PORTS
lab01-postgres-airflow      Up (healthy)        0.0.0.0:5434->5432/tcp
lab01-postgres-mlflow       Up (healthy)        0.0.0.0:5433->5432/tcp
lab01-mlflow                Up (healthy)        0.0.0.0:5000->5000/tcp
lab01-airflow-webserver     Up (healthy)        0.0.0.0:8080->8080/tcp
lab01-airflow-scheduler     Up (healthy)        
```

**Access Services:**
- Airflow UI: http://localhost:8080 (admin/admin_secure_password)
- MLflow UI: http://localhost:5000

### 5.6 Checkpoint

Verify the Docker Compose setup is working correctly.

**Self-Assessment:**
- [ ] All services start without errors
- [ ] Health checks pass for all services
- [ ] Airflow UI is accessible
- [ ] MLflow UI is accessible
- [ ] You can log in to Airflow
- [ ] You understand the service dependencies

**Verification Steps:**

```bash
# Check all services are healthy
docker-compose -f docker-compose.local.lab01.yml ps

# Check Airflow database
docker exec lab01-postgres-airflow psql -U airflow -d airflow -c "\dt"

# Check MLflow database
docker exec lab01-postgres-mlflow psql -U mlflow_user -d mlflow -c "\dt"

# Test MLflow API
curl http://localhost:5000/api/2.0/mlflow/experiments/list

# Test Airflow API
curl http://localhost:8080/health
```

---

**Continue to Chapter 6 for Airflow DAG Implementation...**

## Chapter 6: Airflow DAG Implementation

### 6.1 Understanding Airflow DAGs

A DAG (Directed Acyclic Graph) defines the workflow structure and dependencies.

**DAG Concepts:**

```
DAG = Workflow Definition
├── Tasks: Individual units of work
├── Dependencies: Task execution order
├── Schedule: When to run
└── Configuration: Retries, timeouts, etc.
```

**Our ML Pipeline DAG:**

```
download_data
     ↓
run_eda
     ↓
preprocess_data
     ↓
train_models
     ↓
evaluate_models
     ↓
register_best_model
     ↓
send_notification
```

**Why This Structure?**

1. **download_data**: Get raw dataset (Kaggle, S3, or local)
2. **run_eda**: Analyze data, validate assumptions
3. **preprocess_data**: Clean, transform, balance
4. **train_models**: Train all three models with MLflow
5. **evaluate_models**: Compare performance, select best
6. **register_best_model**: Promote to MLflow Registry
7. **send_notification**: Alert team of completion

### 6.2 Creating Airflow Task Functions

Create reusable task functions that Airflow will execute.

```python
# training/scripts/airflow_tasks.py
"""
Airflow task functions for ML pipeline.

Each function represents one task in the DAG.
Functions must be idempotent (safe to run multiple times).
"""

import pandas as pd
import numpy as np
import mlflow
import mlflow.sklearn
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import f1_score, roc_auc_score, precision_score, recall_score
from imblearn.over_sampling import SMOTE
import joblib
import logging
import os

logger = logging.getLogger(__name__)

# MLflow configuration
MLFLOW_TRACKING_URI = "http://mlflow:5000"  # Docker service name
EXPERIMENT_NAME = "Credit Card Approval - Automated Pipeline"

def setup_mlflow():
    """Configure MLflow tracking."""
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT_NAME)

def download_data_task(**context):
    """
    Task 1: Download credit card approval dataset.
    
    In production, this would:
    - Download from Kaggle API
    - Pull from S3
    - Query from database
    
    For this lab, we assume data exists locally.
    
    Args:
        **context: Airflow context (provides task_instance, etc.)
    """
    logger.info("=" * 70)
    logger.info("TASK: Download Data")
    logger.info("=" * 70)
    
    data_path = '/opt/airflow/training/data/raw/application_record.csv'
    
    # Check if data exists
    if os.path.exists(data_path):
        logger.info(f"✓ Data found at {data_path}")
        
        # Load and validate
        df = pd.read_csv(data_path)
        logger.info(f"  Shape: {df.shape}")
        logger.info(f"  Columns: {list(df.columns)}")
        
        # Push metadata to XCom for downstream tasks
        context['task_instance'].xcom_push(
            key='data_path',
            value=data_path
        )
        context['task_instance'].xcom_push(
            key='n_samples',
            value=len(df)
        )
        
        return "data_downloaded"
    else:
        raise FileNotFoundError(f"Data not found at {data_path}")

def run_eda_task(**context):
    """
    Task 2: Perform exploratory data analysis.
    
    Analyzes:
    - Data types
    - Missing values
    - Class distribution
    - Basic statistics
    
    Results are logged and pushed to XCom.
    """
    logger.info("=" * 70)
    logger.info("TASK: Exploratory Data Analysis")
    logger.info("=" * 70)
    
    # Get data path from previous task
    data_path = context['task_instance'].xcom_pull(
        task_ids='download_data',
        key='data_path'
    )
    
    # Load data
    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df):,} samples")
    
    # Analyze missing values
    missing = df.isnull().sum()
    missing_pct = (missing / len(df)) * 100
    logger.info("\nMissing Values:")
    for col, pct in missing_pct[missing_pct > 0].items():
        logger.info(f"  {col}: {pct:.1f}%")
    
    # Analyze class distribution
    target_counts = df['TARGET'].value_counts()
    target_pct = (target_counts / len(df)) * 100
    logger.info("\nClass Distribution:")
    logger.info(f"  Class 0: {target_counts[0]:,} ({target_pct[0]:.1f}%)")
    logger.info(f"  Class 1: {target_counts[1]:,} ({target_pct[1]:.1f}%)")
    
    # Calculate imbalance ratio
    imbalance_ratio = target_counts.max() / target_counts.min()
    logger.info(f"  Imbalance Ratio: {imbalance_ratio:.2f}:1")
    
    # Push EDA results to XCom
    eda_results = {
        'n_samples': len(df),
        'n_features': df.shape[1],
        'class_ratio': float(imbalance_ratio),
        'missing_pct': missing_pct[missing_pct > 0].to_dict()
    }
    
    context['task_instance'].xcom_push(key='eda_results', value=eda_results)
    
    return "eda_complete"

def preprocess_data_task(**context):
    """
    Task 3: Preprocess data with SMOTE balancing.
    
    Steps:
    1. Handle missing values
    2. Feature engineering
    3. Encode categorical variables
    4. Train-test split (stratified)
    5. Feature scaling
    6. Apply SMOTE
    7. Save processed data
    """
    logger.info("=" * 70)
    logger.info("TASK: Data Preprocessing")
    logger.info("=" * 70)
    
    # Get data path
    data_path = context['task_instance'].xcom_pull(
        task_ids='download_data',
        key='data_path'
    )
    
    # Load data
    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df):,} samples")
    
    # Handle missing values
    df['OCCUPATION_TYPE'].fillna('Unknown', inplace=True)
    if 'CNT_FAM_MEMBERS' in df.columns:
        df['CNT_FAM_MEMBERS'].fillna(df['CNT_FAM_MEMBERS'].median(), inplace=True)
    logger.info("✓ Handled missing values")
    
    # Feature engineering
    df['AGE_YEARS'] = -df['DAYS_BIRTH'] / 365.25
    df['EMPLOYMENT_YEARS'] = df['DAYS_EMPLOYED'].apply(
        lambda x: -x / 365.25 if x < 0 else 0
    )
    df.drop(['DAYS_BIRTH', 'DAYS_EMPLOYED'], axis=1, inplace=True)
    logger.info("✓ Feature engineering complete")
    
    # Encode categorical variables
    label_encoders = {}
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    if 'TARGET' in categorical_cols:
        categorical_cols.remove('TARGET')
    
    for col in categorical_cols:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
        label_encoders[col] = le
    
    logger.info(f"✓ Encoded {len(categorical_cols)} categorical columns")
    
    # Split features and target
    X = df.drop('TARGET', axis=1)
    y = df['TARGET']
    
    # Stratified split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    logger.info(f"✓ Train-test split: {len(X_train):,} / {len(X_test):,}")
    
    # Feature scaling
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    logger.info("✓ Feature scaling complete")
    
    # Apply SMOTE
    smote = SMOTE(random_state=42)
    X_train_balanced, y_train_balanced = smote.fit_resample(X_train_scaled, y_train)
    logger.info(f"✓ SMOTE applied: {len(X_train):,} → {len(X_train_balanced):,}")
    
    # Save processed data
    output_dir = '/opt/airflow/training/data/processed'
    model_dir = '/opt/airflow/training/models'
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(model_dir, exist_ok=True)
    
    np.save(f'{output_dir}/X_train_balanced.npy', X_train_balanced)
    np.save(f'{output_dir}/y_train_balanced.npy', y_train_balanced)
    np.save(f'{output_dir}/X_test.npy', X_test_scaled)
    np.save(f'{output_dir}/y_test.npy', y_test)
    
    # Save preprocessing artifacts
    joblib.dump(scaler, f'{model_dir}/scaler.pkl')
    joblib.dump(label_encoders, f'{model_dir}/label_encoders.pkl')
    joblib.dump(X.columns.tolist(), f'{model_dir}/feature_names.pkl')
    
    logger.info("✓ Saved processed data and artifacts")
    
    return "preprocessing_complete"

def train_models_task(**context):
    """
    Task 4: Train multiple models with MLflow tracking.
    
    Trains:
    - Logistic Regression
    - Random Forest
    - XGBoost
    
    All experiments tracked in MLflow.
    """
    logger.info("=" * 70)
    logger.info("TASK: Model Training")
    logger.info("=" * 70)
    
    # Setup MLflow
    setup_mlflow()
    
    # Load processed data
    data_dir = '/opt/airflow/training/data/processed'
    X_train = np.load(f'{data_dir}/X_train_balanced.npy')
    y_train = np.load(f'{data_dir}/y_train_balanced.npy')
    X_test = np.load(f'{data_dir}/X_test.npy')
    y_test = np.load(f'{data_dir}/y_test.npy')
    
    logger.info(f"Loaded training data: {X_train.shape}")
    logger.info(f"Loaded test data: {X_test.shape}")
    
    # Define models
    models = {
        'Logistic_Regression': LogisticRegression(
            max_iter=1000, random_state=42, class_weight='balanced', n_jobs=-1
        ),
        'Random_Forest': RandomForestClassifier(
            n_estimators=100, max_depth=10, random_state=42,
            class_weight='balanced', n_jobs=-1
        ),
        'XGBoost': XGBClassifier(
            n_estimators=100, max_depth=6, learning_rate=0.1,
            random_state=42, eval_metric='logloss', n_jobs=-1
        )
    }
    
    results = []
    
    # Train each model
    for model_name, model in models.items():
        logger.info(f"\nTraining {model_name}...")
        
        with mlflow.start_run(run_name=f"{model_name}_airflow"):
            # Log parameters
            mlflow.log_param("model_type", model_name)
            mlflow.log_params(model.get_params())
            
            # Train
            model.fit(X_train, y_train)
            
            # Evaluate
            y_pred = model.predict(X_test)
            y_pred_proba = model.predict_proba(X_test)[:, 1]
            
            # Calculate metrics
            metrics = {
                'f1_score': f1_score(y_test, y_pred),
                'roc_auc': roc_auc_score(y_test, y_pred_proba),
                'precision': precision_score(y_test, y_pred),
                'recall': recall_score(y_test, y_pred)
            }
            
            # Log metrics
            for metric_name, metric_value in metrics.items():
                mlflow.log_metric(metric_name, metric_value)
            
            # Log model
            mlflow.sklearn.log_model(
                model,
                "model",
                registered_model_name=f"card_approval_{model_name.lower()}"
            )
            
            run_id = mlflow.active_run().info.run_id
            
            logger.info(f"  F1: {metrics['f1_score']:.4f}, ROC-AUC: {metrics['roc_auc']:.4f}")
            
            results.append({
                'model_name': model_name,
                'run_id': run_id,
                **metrics
            })
    
    # Push results to XCom
    context['task_instance'].xcom_push(key='training_results', value=results)
    
    return "training_complete"

def evaluate_models_task(**context):
    """
    Task 5: Evaluate and select best model.
    
    Compares all models and selects best by ROC-AUC.
    Implements quality gate (minimum F1 threshold).
    """
    logger.info("=" * 70)
    logger.info("TASK: Model Evaluation")
    logger.info("=" * 70)
    
    # Get training results
    results = context['task_instance'].xcom_pull(
        task_ids='train_models',
        key='training_results'
    )
    
    # Display comparison
    logger.info("\nModel Comparison:")
    logger.info(f"{'Model':<20} {'F1':<8} {'ROC-AUC':<8} {'Precision':<10} {'Recall':<8}")
    logger.info("-" * 70)
    
    for result in results:
        logger.info(
            f"{result['model_name']:<20} "
            f"{result['f1_score']:<8.4f} "
            f"{result['roc_auc']:<8.4f} "
            f"{result['precision']:<10.4f} "
            f"{result['recall']:<8.4f}"
        )
    
    # Select best model
    best_model = max(results, key=lambda x: x['roc_auc'])
    
    logger.info(f"\nBest Model: {best_model['model_name']}")
    logger.info(f"  ROC-AUC: {best_model['roc_auc']:.4f}")
    logger.info(f"  F1-Score: {best_model['f1_score']:.4f}")
    
    # Quality gate
    MIN_F1_THRESHOLD = 0.70
    if best_model['f1_score'] < MIN_F1_THRESHOLD:
        raise ValueError(
            f"Model quality below threshold! "
            f"F1: {best_model['f1_score']:.4f} < {MIN_F1_THRESHOLD}"
        )
    
    logger.info(f"✓ Quality gate passed (F1 > {MIN_F1_THRESHOLD})")
    
    # Push best model info
    context['task_instance'].xcom_push(key='best_model', value=best_model)
    
    return "evaluation_complete"

def register_best_model_task(**context):
    """
    Task 6: Register best model to MLflow Registry.
    
    Promotes best model to "Staging" stage.
    Adds description with performance metrics.
    """
    logger.info("=" * 70)
    logger.info("TASK: Register Best Model")
    logger.info("=" * 70)
    
    # Setup MLflow
    setup_mlflow()
    
    # Get best model info
    best_model = context['task_instance'].xcom_pull(
        task_ids='evaluate_models',
        key='best_model'
    )
    
    from mlflow.tracking import MlflowClient
    client = MlflowClient()
    
    # Register model
    model_name = "card_approval_production"
    model_uri = f"runs:/{best_model['run_id']}/model"
    
    logger.info(f"Registering {best_model['model_name']} as {model_name}...")
    
    model_details = mlflow.register_model(model_uri, model_name)
    
    # Transition to Staging
    client.transition_model_version_stage(
        name=model_name,
        version=model_details.version,
        stage="Staging"
    )
    
    # Add description
    description = (
        f"Model: {best_model['model_name']}\n"
        f"ROC-AUC: {best_model['roc_auc']:.4f}\n"
        f"F1-Score: {best_model['f1_score']:.4f}\n"
        f"Precision: {best_model['precision']:.4f}\n"
        f"Recall: {best_model['recall']:.4f}\n"
        f"Run ID: {best_model['run_id']}"
    )
    
    client.update_model_version(
        name=model_name,
        version=model_details.version,
        description=description
    )
    
    logger.info(f"✓ Registered as {model_name} v{model_details.version}")
    logger.info(f"✓ Promoted to Staging stage")
    
    return "registration_complete"

def send_notification_task(**context):
    """
    Task 7: Send completion notification.
    
    In production, this would:
    - Send email via SMTP
    - Post to Slack
    - Trigger webhooks
    
    For this lab, we just log the message.
    """
    logger.info("=" * 70)
    logger.info("TASK: Send Notification")
    logger.info("=" * 70)
    
    # Get best model info
    best_model = context['task_instance'].xcom_pull(
        task_ids='evaluate_models',
        key='best_model'
    )
    
    message = f"""
    ✓ ML Pipeline Completed Successfully!
    
    Best Model: {best_model['model_name']}
    ROC-AUC: {best_model['roc_auc']:.4f}
    F1-Score: {best_model['f1_score']:.4f}
    
    Model registered to MLflow Registry (Staging stage)
    
    View in MLflow: http://localhost:5000
    """
    
    logger.info(message)
    
    # In production, send actual notification:
    # send_email(to="team@company.com", subject="ML Pipeline Complete", body=message)
    # send_slack(channel="#ml-ops", message=message)
    
    return "notification_sent"
```

**Task Function Explanation:**

**1. Function Signature:**
```python
def task_name(**context):
```
- `**context` provides Airflow context (task_instance, execution_date, etc.)
- Required for accessing XCom and other Airflow features

**2. XCom (Cross-Communication):**
```python
context['task_instance'].xcom_push(key='data', value=data)
data = context['task_instance'].xcom_pull(task_ids='previous_task', key='data')
```
- Allows tasks to share data
- Stored in Airflow database
- Limited to small data (use files for large data)

**3. Idempotency:**
- Tasks should be safe to run multiple times
- Check if work is already done
- Use `os.path.exists()` before creating files

**4. Error Handling:**
- Raise exceptions for failures
- Airflow will retry based on configuration
- Log detailed error messages

---

**Continue to Chapter 7 for DAG Definition...**
