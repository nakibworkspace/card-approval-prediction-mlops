# Lab 01: Automated ML Pipeline with Airflow & MLflow

## Introduction

This lab builds a production-grade automated ML pipeline from the ground up. You will understand the credit card approval dataset, train multiple models with proper justification, integrate Apache Airflow to orchestrate the entire workflow, and use MLflow to track all experiments. Everything runs through Airflow—no manual script execution.

## Learning Objectives

By the end of this lab, you will be able to:

1. Analyze and understand credit card approval dataset characteristics
2. Approach dataset challenges (class imbalance, missing values, categorical features)
3. Select appropriate ML models based on dataset properties
4. Train and compare multiple models (Logistic Regression, XGBoost, Random Forest)
5. Set up Apache Airflow for ML pipeline orchestration
6. Create Airflow DAGs to automate the complete ML workflow
7. Integrate MLflow tracking within Airflow tasks
8. Register best models to MLflow Model Registry
9. Schedule and monitor automated pipeline execution

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

## Chapter 1: Understanding the Dataset and Approach

### 1.1 The Credit Card Approval Dataset

The credit card approval dataset contains information about credit card applicants and their approval status. Understanding this dataset is crucial before building any ML pipeline.

**Dataset Overview:**
- **Source:** Credit card application records
- **Target Variable:** Approval status (0 = Rejected, 1 = Approved)
- **Features:** Demographic, financial, and employment information

**Sample Features:**
```python
# Typical features in credit card approval dataset
- CODE_GENDER: Gender of applicant
- FLAG_OWN_CAR: Car ownership
- FLAG_OWN_REALTY: Property ownership
- CNT_CHILDREN: Number of children
- AMT_INCOME_TOTAL: Annual income
- NAME_INCOME_TYPE: Income source
- NAME_EDUCATION_TYPE: Education level
- NAME_FAMILY_STATUS: Marital status
- NAME_HOUSING_TYPE: Housing situation
- DAYS_BIRTH: Age (in days)
- DAYS_EMPLOYED: Employment duration
- FLAG_MOBIL: Mobile phone ownership
- FLAG_WORK_PHONE: Work phone availability
- FLAG_PHONE: Phone availability
- FLAG_EMAIL: Email availability
- OCCUPATION_TYPE: Job category
- CNT_FAM_MEMBERS: Family size
```

### 1.2 Think First: Dataset Challenges

Before jumping into model training, identify the key challenges this dataset presents.

**Question:** What are the main challenges you expect with credit card approval data?

<details>
<summary>Click to review</summary>

**Challenge 1: Class Imbalance**
- Credit card approvals are typically imbalanced
- More rejections than approvals (or vice versa)
- Models may bias toward majority class
- **Solution:** SMOTE (Synthetic Minority Over-sampling Technique)

**Challenge 2: Missing Values**
- Real-world data has gaps (e.g., OCCUPATION_TYPE)
- Cannot simply drop rows (lose valuable data)
- **Solution:** Strategic imputation (median for numeric, mode/category for categorical)

**Challenge 3: Categorical Features**
- Many features are categorical (gender, education, occupation)
- ML models need numeric inputs
- **Solution:** Label encoding or one-hot encoding

**Challenge 4: Feature Scaling**
- Income ranges from thousands to millions
- Age in days vs. binary flags (0/1)
- Different scales affect model performance
- **Solution:** StandardScaler normalization

**Challenge 5: Temporal Features**
- DAYS_BIRTH and DAYS_EMPLOYED are negative (days before application)
- Need conversion to meaningful units (years)
- **Solution:** Feature engineering

</details>

### 1.3 Exploratory Data Analysis (EDA)

Let's explore the dataset to validate our assumptions.

```python
# training/scripts/eda_analysis.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def load_and_explore_data():
    """Perform initial data exploration."""
    
    # Load dataset
    df = pd.read_csv('training/data/raw/application_record.csv')
    
    print("=" * 60)
    print("DATASET OVERVIEW")
    print("=" * 60)
    print(f"Shape: {df.shape}")
    print(f"Samples: {df.shape[0]:,}")
    print(f"Features: {df.shape[1]}")
    print()
    
    # Data types
    print("=" * 60)
    print("DATA TYPES")
    print("=" * 60)
    print(df.dtypes)
    print()
    
    # Missing values
    print("=" * 60)
    print("MISSING VALUES")
    print("=" * 60)
    missing = df.isnull().sum()
    missing_pct = (missing / len(df)) * 100
    missing_df = pd.DataFrame({
        'Missing Count': missing,
        'Percentage': missing_pct
    })
    print(missing_df[missing_df['Missing Count'] > 0].sort_values('Percentage', ascending=False))
    print()
    
    # Target distribution
    print("=" * 60)
    print("TARGET DISTRIBUTION")
    print("=" * 60)
    target_counts = df['TARGET'].value_counts()
    print(target_counts)
    print(f"\nClass Ratio (0:1): {target_counts[0] / target_counts[1]:.2f}:1")
    print(f"Imbalance: {(abs(target_counts[0] - target_counts[1]) / len(df)) * 100:.1f}%")
    print()
    
    # Numeric features summary
    print("=" * 60)
    print("NUMERIC FEATURES SUMMARY")
    print("=" * 60)
    print(df.describe())
    print()
    
    # Categorical features
    print("=" * 60)
    print("CATEGORICAL FEATURES")
    print("=" * 60)
    categorical_cols = df.select_dtypes(include=['object']).columns
    for col in categorical_cols:
        print(f"\n{col}:")
        print(df[col].value_counts().head())
    
    return df

if __name__ == "__main__":
    df = load_and_explore_data()
```

**Expected Findings:**
- Class imbalance: ~70:30 or 80:20 ratio
- Missing values in OCCUPATION_TYPE (~30%)
- Categorical features need encoding
- Income and age features need scaling

### 1.4 How to Think About This Dataset

**Mental Model for Approach:**

```
1. DATA QUALITY
   ├── Handle missing values (imputation strategy)
   ├── Validate data types
   └── Check for outliers

2. FEATURE ENGINEERING
   ├── Convert temporal features (days → years)
   ├── Encode categorical variables
   ├── Create interaction features (optional)
   └── Scale numeric features

3. CLASS IMBALANCE
   ├── Analyze distribution
   ├── Choose balancing technique (SMOTE)
   └── Validate balanced dataset

4. TRAIN-TEST SPLIT
   ├── Stratified split (preserve class ratio)
   ├── 80-20 or 70-30 split
   └── Set random seed for reproducibility

5. MODEL SELECTION
   ├── Start simple (Logistic Regression)
   ├── Add complexity (Tree-based models)
   └── Compare performance
```

**Key Principle:** Understand your data before building models. Every preprocessing decision should be justified by data characteristics.

### 1.5 Checkpoint

**Self-Assessment:**
- [ ] You understand the dataset structure
- [ ] You identified class imbalance challenge
- [ ] You know which features need encoding
- [ ] You understand why scaling is necessary
- [ ] You have a preprocessing strategy

## Chapter 2: Training the Model and Model Selection

### 2.1 Why These Models?

Before training, understand why we choose specific models for credit card approval prediction.

**Question:** Why not just use one "best" model?

<details>
<summary>Click to review</summary>

**Reason 1: No Free Lunch Theorem**
- No single model works best for all datasets
- Must compare multiple approaches
- Dataset characteristics determine best model

**Reason 2: Different Model Strengths**
- Logistic Regression: Interpretable, fast, linear relationships
- Random Forest: Handles non-linearity, feature importance
- XGBoost: State-of-the-art performance, handles imbalance

**Reason 3: Business Requirements**
- Interpretability vs. Performance trade-off
- Regulatory requirements (explainability)
- Inference speed constraints

</details>

### 2.2 Model Selection Strategy

**Our Three-Model Approach:**

```
1. LOGISTIC REGRESSION (Baseline)
   ├── Why: Simple, interpretable, fast
   ├── Strength: Linear relationships, probability outputs
   ├── Weakness: Cannot capture complex patterns
   └── Use Case: Baseline performance, regulatory compliance

2. RANDOM FOREST (Ensemble)
   ├── Why: Handles non-linearity, robust to outliers
   ├── Strength: Feature importance, no scaling needed
   ├── Weakness: Slower inference, less interpretable
   └── Use Case: Capture complex interactions

3. XGBOOST (Gradient Boosting)
   ├── Why: State-of-the-art performance
   ├── Strength: Handles imbalance, regularization
   ├── Weakness: Hyperparameter tuning required
   └── Use Case: Maximum performance
```

### 2.3 Think First: Model Characteristics

**Question:** Which model characteristics matter for credit card approval?

<details>
<summary>Click to review</summary>

**Critical Characteristics:**

1. **Handles Class Imbalance**
   - XGBoost: Built-in `scale_pos_weight` parameter
   - Random Forest: `class_weight='balanced'`
   - Logistic Regression: `class_weight='balanced'`

2. **Interpretability**
   - Logistic Regression: Coefficients show feature impact
   - Random Forest: Feature importance scores
   - XGBoost: SHAP values for explanations

3. **Training Speed**
   - Logistic Regression: Fastest (seconds)
   - Random Forest: Moderate (minutes)
   - XGBoost: Slower (minutes to hours)

4. **Inference Speed**
   - Logistic Regression: Fastest (microseconds)
   - XGBoost: Fast (milliseconds)
   - Random Forest: Slower (milliseconds)

5. **Handles Missing Values**
   - XGBoost: Native support
   - Random Forest: Requires imputation
   - Logistic Regression: Requires imputation

</details>

### 2.4 Data Preprocessing for Training

Before training models, prepare the data properly.

```python
# training/scripts/preprocess_data.py
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from imblearn.over_sampling import SMOTE
import joblib

def preprocess_data():
    """Preprocess credit card approval data."""
    
    # Load data
    df = pd.read_csv('training/data/raw/application_record.csv')
    
    print("Step 1: Handle Missing Values")
    print("-" * 60)
    # Strategy: Impute with mode for categorical, median for numeric
    df['OCCUPATION_TYPE'].fillna('Unknown', inplace=True)
    df['CNT_FAM_MEMBERS'].fillna(df['CNT_FAM_MEMBERS'].median(), inplace=True)
    print("✓ Missing values handled")
    print()
    
    print("Step 2: Feature Engineering")
    print("-" * 60)
    # Convert days to years (more interpretable)
    df['AGE_YEARS'] = -df['DAYS_BIRTH'] / 365
    df['EMPLOYMENT_YEARS'] = -df['DAYS_EMPLOYED'] / 365
    df.drop(['DAYS_BIRTH', 'DAYS_EMPLOYED'], axis=1, inplace=True)
    print("✓ Temporal features converted")
    print()
    
    print("Step 3: Encode Categorical Variables")
    print("-" * 60)
    label_encoders = {}
    categorical_cols = df.select_dtypes(include=['object']).columns
    
    for col in categorical_cols:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col])
        label_encoders[col] = le
        print(f"✓ Encoded {col}")
    
    # Save encoders for inference
    joblib.dump(label_encoders, 'training/models/label_encoders.pkl')
    print()
    
    print("Step 4: Split Features and Target")
    print("-" * 60)
    X = df.drop('TARGET', axis=1)
    y = df['TARGET']
    print(f"Features shape: {X.shape}")
    print(f"Target shape: {y.shape}")
    print(f"Target distribution: {y.value_counts().to_dict()}")
    print()
    
    print("Step 5: Train-Test Split (Stratified)")
    print("-" * 60)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, 
        test_size=0.2, 
        random_state=42, 
        stratify=y  # Preserve class distribution
    )
    print(f"Train set: {X_train.shape[0]} samples")
    print(f"Test set: {X_test.shape[0]} samples")
    print()
    
    print("Step 6: Feature Scaling")
    print("-" * 60)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Save scaler for inference
    joblib.dump(scaler, 'training/models/scaler.pkl')
    print("✓ Features scaled (StandardScaler)")
    print()
    
    print("Step 7: Handle Class Imbalance (SMOTE)")
    print("-" * 60)
    print(f"Before SMOTE: {dict(zip(*np.unique(y_train, return_counts=True)))}")
    
    smote = SMOTE(random_state=42)
    X_train_balanced, y_train_balanced = smote.fit_resample(X_train_scaled, y_train)
    
    print(f"After SMOTE: {dict(zip(*np.unique(y_train_balanced, return_counts=True)))}")
    print("✓ Classes balanced")
    print()
    
    # Save processed data
    np.save('training/data/processed/X_train_balanced.npy', X_train_balanced)
    np.save('training/data/processed/y_train_balanced.npy', y_train_balanced)
    np.save('training/data/processed/X_test.npy', X_test_scaled)
    np.save('training/data/processed/y_test.npy', y_test)
    
    print("=" * 60)
    print("PREPROCESSING COMPLETE")
    print("=" * 60)
    print(f"Balanced training set: {X_train_balanced.shape}")
    print(f"Test set: {X_test_scaled.shape}")
    
    return X_train_balanced, y_train_balanced, X_test_scaled, y_test

if __name__ == "__main__":
    preprocess_data()
```

### 2.5 Model Training Implementation

Now train all three models and compare performance.

```python
# training/scripts/train_models.py
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import (
    f1_score, 
    roc_auc_score, 
    precision_score, 
    recall_score,
    classification_report,
    confusion_matrix
)
import joblib
import time

def train_and_evaluate_models():
    """Train multiple models and compare performance."""
    
    # Load preprocessed data
    X_train = np.load('training/data/processed/X_train_balanced.npy')
    y_train = np.load('training/data/processed/y_train_balanced.npy')
    X_test = np.load('training/data/processed/X_test.npy')
    y_test = np.load('training/data/processed/y_test.npy')
    
    print("=" * 80)
    print("MODEL TRAINING AND EVALUATION")
    print("=" * 80)
    print()
    
    # Define models with justification
    models = {
        'Logistic Regression': {
            'model': LogisticRegression(
                max_iter=1000,
                random_state=42,
                class_weight='balanced'  # Handle any remaining imbalance
            ),
            'rationale': 'Baseline model: Fast, interpretable, linear relationships'
        },
        'Random Forest': {
            'model': RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                class_weight='balanced',
                n_jobs=-1  # Use all CPU cores
            ),
            'rationale': 'Ensemble model: Captures non-linear patterns, feature importance'
        },
        'XGBoost': {
            'model': XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
                eval_metric='logloss',
                use_label_encoder=False
            ),
            'rationale': 'Gradient boosting: State-of-the-art performance, handles complexity'
        }
    }
    
    results = []
    
    for model_name, model_info in models.items():
        print("=" * 80)
        print(f"TRAINING: {model_name}")
        print("=" * 80)
        print(f"Rationale: {model_info['rationale']}")
        print()
        
        model = model_info['model']
        
        # Train
        print("Training...")
        start_time = time.time()
        model.fit(X_train, y_train)
        training_time = time.time() - start_time
        print(f"✓ Training completed in {training_time:.2f} seconds")
        print()
        
        # Predict
        print("Evaluating...")
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        
        # Calculate metrics
        f1 = f1_score(y_test, y_pred)
        roc_auc = roc_auc_score(y_test, y_pred_proba)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        
        # Display results
        print(f"F1 Score:    {f1:.4f}")
        print(f"ROC-AUC:     {roc_auc:.4f}")
        print(f"Precision:   {precision:.4f}")
        print(f"Recall:      {recall:.4f}")
        print()
        
        print("Classification Report:")
        print(classification_report(y_test, y_pred))
        
        print("Confusion Matrix:")
        print(confusion_matrix(y_test, y_pred))
        print()
        
        # Save model
        model_path = f'training/models/{model_name.lower().replace(" ", "_")}.pkl'
        joblib.dump(model, model_path)
        print(f"✓ Model saved: {model_path}")
        print()
        
        results.append({
            'model_name': model_name,
            'f1_score': f1,
            'roc_auc': roc_auc,
            'precision': precision,
            'recall': recall,
            'training_time': training_time
        })
    
    # Compare models
    print("=" * 80)
    print("MODEL COMPARISON")
    print("=" * 80)
    print(f"{'Model':<20} {'F1':<10} {'ROC-AUC':<10} {'Precision':<12} {'Recall':<10} {'Time (s)':<10}")
    print("-" * 80)
    
    for result in results:
        print(f"{result['model_name']:<20} "
              f"{result['f1_score']:<10.4f} "
              f"{result['roc_auc']:<10.4f} "
              f"{result['precision']:<12.4f} "
              f"{result['recall']:<10.4f} "
              f"{result['training_time']:<10.2f}")
    
    # Select best model
    best_model = max(results, key=lambda x: x['roc_auc'])
    print()
    print("=" * 80)
    print(f"BEST MODEL: {best_model['model_name']}")
    print(f"ROC-AUC: {best_model['roc_auc']:.4f}")
    print("=" * 80)
    
    return results

if __name__ == "__main__":
    results = train_and_evaluate_models()
```

### 2.6 Why Each Model Matters

**Logistic Regression:**
- Provides interpretable coefficients
- Fast training and inference
- Regulatory compliance (explainable AI)
- Baseline to beat

**Random Forest:**
- Captures feature interactions
- Provides feature importance
- Robust to outliers
- No feature scaling needed (but we scaled anyway)

**XGBoost:**
- Often achieves best performance
- Handles missing values natively
- Built-in regularization
- Industry standard for tabular data

### 2.7 Checkpoint

**Self-Assessment:**
- [ ] You understand why we chose these three models
- [ ] You know the strengths/weaknesses of each model
- [ ] You implemented proper preprocessing (SMOTE, scaling, encoding)
- [ ] You can train and evaluate all models
- [ ] You understand the evaluation metrics (F1, ROC-AUC)

## Chapter 3: Integrating Airflow to Automate the Training Pipeline

### 3.1 Why Airflow for ML Pipelines?

**Question:** Why not just run Python scripts manually or with cron jobs?

<details>
<summary>Click to review</summary>

**Airflow Advantages:**
- **Orchestration:** Manages task dependencies automatically
- **Scheduling:** Built-in cron-like scheduling with backfilling
- **Monitoring:** Web UI shows pipeline status in real-time
- **Retries:** Automatic retry on failures with exponential backoff
- **Logging:** Centralized logs for debugging
- **Scalability:** Can distribute tasks across workers
- **Alerting:** Email/Slack notifications on failures

**Manual Scripts Problems:**
- No dependency management (must run in correct order)
- No automatic retries
- No centralized monitoring
- Hard to debug failures
- No scheduling (requires external cron)

</details>

### 3.2 Airflow Setup

Initialize Airflow for ML pipeline orchestration.

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

# Start services (in separate terminals)
# Terminal 1: Webserver
airflow webserver --port 8080

# Terminal 2: Scheduler
airflow scheduler
```

Access Airflow UI at `http://localhost:8080` (admin/admin)

### 3.3 Creating the ML Pipeline DAG

A DAG (Directed Acyclic Graph) defines the workflow structure.

**Pipeline Flow:**
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

**DAG Implementation:**

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

# Import task functions
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

### 3.4 Implementing Airflow Tasks with MLflow Integration

Each task integrates MLflow tracking automatically.

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

logger = logging.getLogger(__name__)

# MLflow configuration
MLFLOW_TRACKING_URI = "http://localhost:5000"
EXPERIMENT_NAME = "Card Approval - Automated Pipeline"

def setup_mlflow():
    """Configure MLflow tracking."""
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT_NAME)

def download_data_task(**context):
    """Task 1: Download credit card approval dataset."""
    logger.info("Downloading dataset...")
    
    # TODO: Add actual download logic (Kaggle API, S3, etc.)
    # For now, assume data exists at training/data/raw/application_record.csv
    
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
    
    # Save EDA results to XCom
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
    
    # Feature engineering
    df['AGE_YEARS'] = -df['DAYS_BIRTH'] / 365
    df['EMPLOYMENT_YEARS'] = -df['DAYS_EMPLOYED'] / 365
    df.drop(['DAYS_BIRTH', 'DAYS_EMPLOYED'], axis=1, inplace=True)
    
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
    setup_mlflow()
    
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
    logger.info("Registering best model to MLflow Registry...")
    
    # Setup MLflow
    setup_mlflow()
    
    # Get best model info
    best_model = context['task_instance'].xcom_pull(task_ids='evaluate_models', key='best_model')
    
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

### 3.5 Running the Automated Pipeline

Trigger and monitor the pipeline:

```bash
# Test DAG syntax
python dags/ml_training_pipeline.py

# List DAGs
airflow dags list | grep credit_card

# Trigger manually
airflow dags trigger credit_card_ml_pipeline

# View task logs
airflow tasks logs credit_card_ml_pipeline download_data 2024-01-01
```

Monitor in Airflow UI:
1. Go to `http://localhost:8080`
2. Find `credit_card_ml_pipeline`
3. Click to view Graph/Grid
4. Watch tasks turn green as they complete

### 3.6 Checkpoint

**Self-Assessment:**
- [ ] Airflow initialized and running
- [ ] DAG created with proper task dependencies
- [ ] All task functions implemented
- [ ] MLflow tracking integrated in training task
- [ ] Pipeline triggers successfully
- [ ] Tasks complete in correct order

## Chapter 4: MLflow Setup and Viewing Output

### 4.1 What is MLflow?

MLflow is an open-source platform for managing the ML lifecycle, including experimentation, reproducibility, and deployment.

**MLflow Components:**
- **Tracking:** Log parameters, metrics, and artifacts
- **Projects:** Package ML code in reusable format
- **Models:** Deploy models to various platforms
- **Registry:** Centralized model store with versioning

### 4.2 MLflow Setup

Start MLflow tracking server:

```bash
# Terminal 3: Start MLflow
mlflow server \
  --backend-store-uri sqlite:///mlflow.db \
  --default-artifact-root ./mlruns \
  --host 0.0.0.0 \
  --port 5000
```

**Configuration Explained:**
- `--backend-store-uri`: Where to store experiment metadata (SQLite database)
- `--default-artifact-root`: Where to store model artifacts and files
- `--host 0.0.0.0`: Allow connections from any IP
- `--port 5000`: MLflow UI port

Access MLflow UI at `http://localhost:5000`

### 4.3 Understanding MLflow Tracking

When Airflow runs the training task, MLflow automatically logs:

**Parameters (Inputs):**
```python
mlflow.log_param("model_type", "XGBoost")
mlflow.log_param("n_estimators", 100)
mlflow.log_param("max_depth", 6)
mlflow.log_param("learning_rate", 0.1)
```

**Metrics (Outputs):**
```python
mlflow.log_metric("f1_score", 0.8542)
mlflow.log_metric("roc_auc", 0.9123)
mlflow.log_metric("precision", 0.8234)
mlflow.log_metric("recall", 0.8876)
```

**Artifacts (Files):**
```python
mlflow.sklearn.log_model(model, "model")
mlflow.log_artifact("confusion_matrix.png")
mlflow.log_artifact("feature_importance.csv")
```

### 4.4 Viewing Experiments in MLflow UI

After running the Airflow pipeline, view results in MLflow:

**Step 1: Access MLflow UI**
```bash
# Open browser
open http://localhost:5000
```

**Step 2: Navigate to Experiment**
1. You'll see "Card Approval - Automated Pipeline" experiment
2. Click to view all runs

**Step 3: Compare Runs**
- See all three models (Logistic Regression, XGBoost, Random Forest)
- Compare metrics side-by-side
- Sort by ROC-AUC to find best model

**Step 4: View Run Details**
Click on any run to see:
- Parameters used
- Metrics achieved
- Artifacts (model files)
- System information (Python version, packages)
- Tags and notes

**Step 5: Compare Multiple Runs**
1. Select multiple runs (checkboxes)
2. Click "Compare" button
3. View parallel coordinates plot
4. See metric differences

### 4.5 MLflow Model Registry

The best model is automatically registered to MLflow Registry.

**View Registered Models:**
1. Click "Models" tab in MLflow UI
2. Find "card_approval_production"
3. See version history

**Model Stages:**
- **None:** Initial registration
- **Staging:** Ready for testing (our best model goes here)
- **Production:** Deployed to production
- **Archived:** Old versions

**Promote Model to Production:**
```python
from mlflow.tracking import MlflowClient

client = MlflowClient()
client.transition_model_version_stage(
    name="card_approval_production",
    version=1,
    stage="Production"
)
```

### 4.6 Understanding the Complete Output

After pipeline completes, you'll see:

**In Airflow UI (`http://localhost:8080`):**
```
✓ download_data (green)
✓ run_eda (green)
✓ preprocess_data (green)
✓ train_models (green)
✓ evaluate_models (green)
✓ register_best_model (green)
✓ send_notification (green)
```

**In MLflow UI (`http://localhost:5000`):**
```
Experiment: Card Approval - Automated Pipeline
├── Run 1: Logistic Regression
│   ├── F1: 0.7823
│   ├── ROC-AUC: 0.8456
│   └── Model: card_approval_logistic_regression
├── Run 2: XGBoost
│   ├── F1: 0.8542
│   ├── ROC-AUC: 0.9123  ← BEST
│   └── Model: card_approval_xgboost
└── Run 3: Random Forest
    ├── F1: 0.8234
    ├── ROC-AUC: 0.8987
    └── Model: card_approval_random_forest

Registered Models:
└── card_approval_production (v1)
    ├── Stage: Staging
    ├── Model: XGBoost
    └── ROC-AUC: 0.9123
```

### 4.7 Querying MLflow Programmatically

Access MLflow data from Python:

```python
# training/scripts/query_mlflow.py
import mlflow
from mlflow.tracking import MlflowClient

# Setup
mlflow.set_tracking_uri("http://localhost:5000")
client = MlflowClient()

# Get experiment
experiment = mlflow.get_experiment_by_name("Card Approval - Automated Pipeline")
print(f"Experiment ID: {experiment.experiment_id}")

# Get all runs
runs = mlflow.search_runs(experiment_ids=[experiment.experiment_id])
print("\nAll Runs:")
print(runs[['run_id', 'params.model_type', 'metrics.f1_score', 'metrics.roc_auc']])

# Get best run
best_run = runs.loc[runs['metrics.roc_auc'].idxmax()]
print(f"\nBest Model: {best_run['params.model_type']}")
print(f"ROC-AUC: {best_run['metrics.roc_auc']:.4f}")

# Load best model
model_uri = f"runs:/{best_run['run_id']}/model"
model = mlflow.sklearn.load_model(model_uri)
print(f"\nModel loaded: {type(model)}")

# Get registered models
registered_models = client.search_registered_models()
for rm in registered_models:
    print(f"\nRegistered Model: {rm.name}")
    for version in rm.latest_versions:
        print(f"  Version {version.version}: {version.current_stage}")
```

### 4.8 MLflow Best Practices

**1. Consistent Naming:**
```python
# Good: Descriptive experiment names
mlflow.set_experiment("Card Approval - Automated Pipeline")

# Bad: Generic names
mlflow.set_experiment("experiment1")
```

**2. Log Everything:**
```python
# Log hyperparameters
mlflow.log_params(model.get_params())

# Log metrics
mlflow.log_metric("f1_score", f1)
mlflow.log_metric("roc_auc", roc_auc)

# Log artifacts
mlflow.log_artifact("confusion_matrix.png")
```

**3. Use Tags:**
```python
mlflow.set_tag("team", "data-science")
mlflow.set_tag("project", "credit-approval")
mlflow.set_tag("environment", "production")
```

**4. Add Descriptions:**
```python
client.update_model_version(
    name="card_approval_production",
    version=1,
    description="XGBoost model trained on balanced dataset with SMOTE"
)
```

### 4.9 Checkpoint

**Self-Assessment:**
- [ ] MLflow server running at localhost:5000
- [ ] You can view experiments in MLflow UI
- [ ] You understand the difference between runs and experiments
- [ ] You can compare multiple runs
- [ ] You can view registered models
- [ ] You understand model stages (Staging, Production)
- [ ] You can query MLflow programmatically

## Epilogue: The Complete System

You have built a fully automated ML pipeline with proper understanding and justification at each step:

| Chapter | What You Built | Why It Matters |
|---------|----------------|----------------|
| Chapter 1 | Dataset understanding and approach | Foundation for all decisions |
| Chapter 2 | Model selection and training | Justified model choices |
| Chapter 3 | Airflow automation | Zero manual intervention |
| Chapter 4 | MLflow tracking and registry | Complete experiment tracking |

**Complete Workflow:**
```
1. Understand Dataset
   ├── Identify class imbalance
   ├── Find missing values
   └── Plan preprocessing strategy

2. Select Models
   ├── Logistic Regression (baseline)
   ├── Random Forest (ensemble)
   └── XGBoost (performance)

3. Automate with Airflow
   ├── Download data
   ├── Run EDA
   ├── Preprocess (SMOTE, scaling, encoding)
   ├── Train all models
   ├── Evaluate and select best
   ├── Register to MLflow
   └── Send notification

4. Track with MLflow
   ├── Log all parameters
   ├── Log all metrics
   ├── Compare runs
   └── Register best model
```

**Verify the Complete System:**

```bash
# Check Airflow
open http://localhost:8080

# Check MLflow
open http://localhost:5000

# View pipeline logs
airflow tasks logs credit_card_ml_pipeline train_models 2024-01-01

# Query MLflow
python training/scripts/query_mlflow.py
```

## The Principles

1. **Understand before building** — Know your data challenges first
2. **Justify model selection** — Each model serves a purpose
3. **Automate from day one** — No manual script execution
4. **Track everything** — MLflow logs all experiments automatically
5. **Quality gates** — Automated checks prevent bad models
6. **Fail fast** — Retries and alerts on failures
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

### Error: SMOTE failing

**Solution:**
```bash
# Install imbalanced-learn
pip install imbalanced-learn
```

### Error: XGBoost not found

**Solution:**
```bash
# Install XGBoost
pip install xgboost
```

## Next Steps

1. **Add data download:** Integrate Kaggle API or S3 download
2. **Hyperparameter tuning:** Add GridSearchCV or Optuna
3. **Feature importance:** Log feature importance plots
4. **Model explainability:** Add SHAP values
5. **Email alerts:** Configure SMTP for failure notifications
6. **Slack integration:** Send pipeline status to Slack
7. **Parallel training:** Train models simultaneously
8. **Data validation:** Add Great Expectations checks
9. **A/B testing:** Compare new models against production
10. **Auto-promotion:** Promote to Production if metrics improve

## Additional Resources

- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [MLflow Documentation](https://mlflow.org/docs/latest/)
- [Airflow Best Practices](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html)
- [MLflow with Airflow](https://mlflow.org/docs/latest/tracking.html)
- [SMOTE Documentation](https://imbalanced-learn.org/stable/references/generated/imblearn.over_sampling.SMOTE.html)
- [XGBoost Documentation](https://xgboost.readthedocs.io/)

## Summary

You have successfully built an automated ML pipeline that:
- Understands the credit card approval dataset and its challenges
- Trains three justified models (Logistic Regression, Random Forest, XGBoost)
- Automates the entire workflow with Apache Airflow
- Tracks all experiments with MLflow
- Registers the best model to MLflow Registry
- Runs on a schedule without manual intervention

This is a production-ready system that can be deployed and maintained with confidence.
