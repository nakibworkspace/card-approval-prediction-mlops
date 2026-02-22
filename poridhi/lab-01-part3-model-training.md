# Lab 01: Part 3 - Model Training with MLflow

## Chapter 4: Model Training Implementation

### 4.1 Setting Up MLflow Tracking

Before training models, configure MLflow to track experiments systematically.

**MLflow Architecture:**
```
MLflow Server
├── Backend Store (PostgreSQL)
│   └── Stores: experiments, runs, parameters, metrics
└── Artifact Store (Local/S3)
    └── Stores: models, plots, files
```

**Why PostgreSQL for Backend?**
- SQLite (default) doesn't support concurrent writes
- Multiple Airflow tasks may log simultaneously
- PostgreSQL handles concurrent connections
- Production-ready and scalable

**Configuration Script:**

```python
# training/scripts/setup_mlflow.py
import mlflow
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MLflow configuration
MLFLOW_TRACKING_URI = "http://localhost:5000"
EXPERIMENT_NAME = "Credit Card Approval - Automated Pipeline"

def setup_mlflow_experiment():
    """
    Configure MLflow tracking and create experiment.
    
    This function:
    1. Sets the tracking URI (where MLflow server is running)
    2. Creates or retrieves the experiment
    3. Returns experiment ID for use in training
    
    Returns:
        str: Experiment ID
    """
    
    logger.info("=" * 70)
    logger.info("MLFLOW SETUP")
    logger.info("=" * 70)
    
    # Set tracking URI
    # This tells MLflow where to send tracking data
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    logger.info(f"✓ Tracking URI: {MLFLOW_TRACKING_URI}")
    
    # Create or get experiment
    # Experiments group related runs together
    try:
        experiment_id = mlflow.create_experiment(EXPERIMENT_NAME)
        logger.info(f"✓ Created new experiment: {EXPERIMENT_NAME}")
    except Exception:
        # Experiment already exists
        experiment = mlflow.get_experiment_by_name(EXPERIMENT_NAME)
        experiment_id = experiment.experiment_id
        logger.info(f"✓ Using existing experiment: {EXPERIMENT_NAME}")
    
    logger.info(f"  Experiment ID: {experiment_id}")
    logger.info("")
    
    return experiment_id

if __name__ == "__main__":
    experiment_id = setup_mlflow_experiment()
    print(f"Experiment ID: {experiment_id}")
```

**Code Explanation:**

1. **Tracking URI**: Points to MLflow server. All tracking data goes here.
2. **Experiment**: Groups related runs. One experiment = one project/problem.
3. **Error Handling**: If experiment exists, retrieve it instead of failing.

### 4.2 Model Training Script

Create a comprehensive training script that trains all three models with MLflow tracking.

```python
# training/scripts/train_models.py
import numpy as np
import mlflow
import mlflow.sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import (
    f1_score,
    roc_auc_score,
    precision_score,
    recall_score,
    accuracy_score,
    classification_report,
    confusion_matrix
)
import joblib
import logging
import time
import os
from setup_mlflow import setup_mlflow_experiment, MLFLOW_TRACKING_URI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def train_and_evaluate_models(
    data_dir='training/data/processed',
    model_dir='training/models',
    experiment_name='Credit Card Approval - Automated Pipeline'
):
    """
    Train multiple models and track with MLflow.
    
    This function:
    1. Loads preprocessed data
    2. Defines three models with justification
    3. Trains each model
    4. Evaluates with multiple metrics
    5. Logs everything to MLflow
    6. Saves models locally
    7. Compares performance
    
    Args:
        data_dir: Directory containing processed data
        model_dir: Directory to save trained models
        experiment_name: MLflow experiment name
        
    Returns:
        list: Training results for all models
    """
    
    logger.info("=" * 80)
    logger.info("MODEL TRAINING WITH MLFLOW TRACKING")
    logger.info("=" * 80)
    logger.info("")
    
    # ========================================
    # STEP 1: SETUP MLFLOW
    # ========================================
    logger.info("STEP 1: Setting up MLflow")
    logger.info("-" * 80)
    
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(experiment_name)
    
    logger.info(f"✓ MLflow tracking URI: {MLFLOW_TRACKING_URI}")
    logger.info(f"✓ Experiment: {experiment_name}")
    logger.info("")
    
    # ========================================
    # STEP 2: LOAD PREPROCESSED DATA
    # ========================================
    logger.info("STEP 2: Loading Preprocessed Data")
    logger.info("-" * 80)
    
    X_train = np.load(os.path.join(data_dir, 'X_train_balanced.npy'))
    y_train = np.load(os.path.join(data_dir, 'y_train_balanced.npy'))
    X_test = np.load(os.path.join(data_dir, 'X_test.npy'))
    y_test = np.load(os.path.join(data_dir, 'y_test.npy'))
    
    logger.info(f"✓ Training set: {X_train.shape}")
    logger.info(f"✓ Test set:     {X_test.shape}")
    
    # Verify class balance in training
    train_dist = dict(zip(*np.unique(y_train, return_counts=True)))
    logger.info(f"  Training classes: {train_dist}")
    logger.info("")
```

Let me continue with the model definitions:


    # ========================================
    # STEP 3: DEFINE MODELS
    # ========================================
    logger.info("STEP 3: Defining Models")
    logger.info("-" * 80)
    
    # Model definitions with clear justification
    models = {
        'Logistic_Regression': {
            'model': LogisticRegression(
                max_iter=1000,           # Sufficient iterations for convergence
                random_state=42,         # Reproducibility
                class_weight='balanced', # Handle any remaining imbalance
                solver='lbfgs',          # Efficient for small-medium datasets
                n_jobs=-1                # Use all CPU cores
            ),
            'rationale': 'Baseline model: Fast, interpretable, regulatory compliant',
            'strengths': 'Linear relationships, probability calibration, explainable',
            'use_case': 'Regulatory compliance, baseline performance'
        },
        'Random_Forest': {
            'model': RandomForestClassifier(
                n_estimators=100,        # Number of trees (balance speed/performance)
                max_depth=10,            # Prevent overfitting
                min_samples_split=20,    # Minimum samples to split node
                min_samples_leaf=10,     # Minimum samples in leaf
                random_state=42,         # Reproducibility
                class_weight='balanced', # Handle imbalance
                n_jobs=-1,               # Use all CPU cores
                max_features='sqrt'      # Feature sampling (prevents correlation)
            ),
            'rationale': 'Ensemble model: Captures non-linear patterns, robust',
            'strengths': 'Feature importance, handles outliers, no scaling needed',
            'use_case': 'Feature analysis, robust predictions'
        },
        'XGBoost': {
            'model': XGBClassifier(
                n_estimators=100,        # Number of boosting rounds
                max_depth=6,             # Tree depth (XGBoost default)
                learning_rate=0.1,       # Step size shrinkage (prevents overfitting)
                subsample=0.8,           # Row sampling (prevents overfitting)
                colsample_bytree=0.8,    # Column sampling (prevents overfitting)
                random_state=42,         # Reproducibility
                eval_metric='logloss',   # Optimization metric
                use_label_encoder=False, # Avoid deprecation warning
                n_jobs=-1                # Use all CPU cores
            ),
            'rationale': 'Gradient boosting: State-of-the-art performance',
            'strengths': 'Handles complexity, built-in regularization, fast',
            'use_case': 'Maximum performance, production deployment'
        }
    }
    
    logger.info(f"Defined {len(models)} models:")
    for name, info in models.items():
        logger.info(f"  • {name}: {info['rationale']}")
    logger.info("")
    
    # ========================================
    # STEP 4: TRAIN AND EVALUATE EACH MODEL
    # ========================================
    logger.info("STEP 4: Training and Evaluating Models")
    logger.info("-" * 80)
    logger.info("")
    
    results = []
    
    for model_name, model_info in models.items():
        logger.info("=" * 80)
        logger.info(f"TRAINING: {model_name}")
        logger.info("=" * 80)
        logger.info(f"Rationale: {model_info['rationale']}")
        logger.info(f"Strengths: {model_info['strengths']}")
        logger.info(f"Use Case:  {model_info['use_case']}")
        logger.info("")
        
        model = model_info['model']
        
        # Start MLflow run
        # Each model gets its own run within the experiment
        with mlflow.start_run(run_name=model_name):
            
            # ========================================
            # LOG MODEL METADATA
            # ========================================
            logger.info("Logging metadata to MLflow...")
            
            # Log model type and rationale
            mlflow.set_tag("model_type", model_name)
            mlflow.set_tag("rationale", model_info['rationale'])
            mlflow.set_tag("use_case", model_info['use_case'])
            
            # Log all hyperparameters
            # This allows comparing different configurations later
            params = model.get_params()
            mlflow.log_params(params)
            logger.info(f"✓ Logged {len(params)} hyperparameters")
            
            # ========================================
            # TRAIN MODEL
            # ========================================
            logger.info("Training model...")
            start_time = time.time()
            
            model.fit(X_train, y_train)
            
            training_time = time.time() - start_time
            logger.info(f"✓ Training completed in {training_time:.2f} seconds")
            
            # Log training time
            mlflow.log_metric("training_time_seconds", training_time)
            
            # ========================================
            # EVALUATE MODEL
            # ========================================
            logger.info("Evaluating model...")
            
            # Predictions
            y_pred = model.predict(X_test)
            y_pred_proba = model.predict_proba(X_test)[:, 1]
            
            # Calculate metrics
            # Multiple metrics give different perspectives on performance
            metrics = {
                'accuracy': accuracy_score(y_test, y_pred),
                'f1_score': f1_score(y_test, y_pred),
                'roc_auc': roc_auc_score(y_test, y_pred_proba),
                'precision': precision_score(y_test, y_pred),
                'recall': recall_score(y_test, y_pred)
            }
            
            # Log all metrics to MLflow
            for metric_name, metric_value in metrics.items():
                mlflow.log_metric(metric_name, metric_value)
            
            # Display metrics
            logger.info("Metrics:")
            logger.info(f"  Accuracy:  {metrics['accuracy']:.4f}")
            logger.info(f"  F1-Score:  {metrics['f1_score']:.4f}")
            logger.info(f"  ROC-AUC:   {metrics['roc_auc']:.4f}")
            logger.info(f"  Precision: {metrics['precision']:.4f}")
            logger.info(f"  Recall:    {metrics['recall']:.4f}")
            logger.info("")
            
            # ========================================
            # DETAILED CLASSIFICATION REPORT
            # ========================================
            logger.info("Classification Report:")
            report = classification_report(y_test, y_pred)
            logger.info(report)
            
            # Save report as artifact
            report_path = os.path.join(model_dir, f'{model_name}_classification_report.txt')
            with open(report_path, 'w') as f:
                f.write(report)
            mlflow.log_artifact(report_path)
            
            # ========================================
            # CONFUSION MATRIX
            # ========================================
            cm = confusion_matrix(y_test, y_pred)
            logger.info("Confusion Matrix:")
            logger.info(f"  TN: {cm[0,0]:>6}  FP: {cm[0,1]:>6}")
            logger.info(f"  FN: {cm[1,0]:>6}  TP: {cm[1,1]:>6}")
            logger.info("")
            
            # Log confusion matrix values
            mlflow.log_metric("true_negatives", int(cm[0,0]))
            mlflow.log_metric("false_positives", int(cm[0,1]))
            mlflow.log_metric("false_negatives", int(cm[1,0]))
            mlflow.log_metric("true_positives", int(cm[1,1]))
            
            # ========================================
            # SAVE AND LOG MODEL
            # ========================================
            logger.info("Saving model...")
            
            # Save locally
            model_path = os.path.join(model_dir, f'{model_name}.pkl')
            joblib.dump(model, model_path)
            logger.info(f"✓ Saved to {model_path}")
            
            # Log model to MLflow
            # This allows loading the model later by run_id
            mlflow.sklearn.log_model(
                model,
                "model",
                registered_model_name=f"card_approval_{model_name.lower()}"
            )
            logger.info(f"✓ Logged to MLflow Model Registry")
            
            # Get run ID for later reference
            run_id = mlflow.active_run().info.run_id
            logger.info(f"  Run ID: {run_id}")
            logger.info("")
            
            # ========================================
            # STORE RESULTS
            # ========================================
            results.append({
                'model_name': model_name,
                'run_id': run_id,
                'training_time': training_time,
                **metrics  # Unpack all metrics
            })
    
    # ========================================
    # STEP 5: COMPARE MODELS
    # ========================================
    logger.info("")
    logger.info("=" * 80)
    logger.info("MODEL COMPARISON")
    logger.info("=" * 80)
    
    # Create comparison table
    logger.info(f"{'Model':<20} {'F1':<8} {'ROC-AUC':<8} {'Precision':<10} {'Recall':<8} {'Time(s)':<8}")
    logger.info("-" * 80)
    
    for result in results:
        logger.info(
            f"{result['model_name']:<20} "
            f"{result['f1_score']:<8.4f} "
            f"{result['roc_auc']:<8.4f} "
            f"{result['precision']:<10.4f} "
            f"{result['recall']:<8.4f} "
            f"{result['training_time']:<8.2f}"
        )
    
    # ========================================
    # STEP 6: SELECT BEST MODEL
    # ========================================
    logger.info("")
    logger.info("=" * 80)
    logger.info("BEST MODEL SELECTION")
    logger.info("=" * 80)
    
    # Select best by ROC-AUC (threshold-independent metric)
    best_model = max(results, key=lambda x: x['roc_auc'])
    
    logger.info(f"Best Model: {best_model['model_name']}")
    logger.info(f"  ROC-AUC:   {best_model['roc_auc']:.4f}")
    logger.info(f"  F1-Score:  {best_model['f1_score']:.4f}")
    logger.info(f"  Precision: {best_model['precision']:.4f}")
    logger.info(f"  Recall:    {best_model['recall']:.4f}")
    logger.info(f"  Run ID:    {best_model['run_id']}")
    logger.info("")
    
    # Save best model info
    best_model_path = os.path.join(model_dir, 'best_model_info.txt')
    with open(best_model_path, 'w') as f:
        f.write(f"Best Model: {best_model['model_name']}\n")
        f.write(f"ROC-AUC: {best_model['roc_auc']:.4f}\n")
        f.write(f"F1-Score: {best_model['f1_score']:.4f}\n")
        f.write(f"Run ID: {best_model['run_id']}\n")
    
    logger.info("=" * 80)
    logger.info("TRAINING COMPLETE")
    logger.info("=" * 80)
    
    return results, best_model

if __name__ == "__main__":
    results, best_model = train_and_evaluate_models()
    
    print(f"\n✓ Trained {len(results)} models")
    print(f"✓ Best model: {best_model['model_name']} (ROC-AUC: {best_model['roc_auc']:.4f})")
```

**Code Explanation - Key Concepts:**

**1. MLflow Run Context:**
```python
with mlflow.start_run(run_name=model_name):
    # Everything here is logged to this run
```
- Creates a new run within the experiment
- All logging happens within this context
- Run automatically ends when context exits

**2. Hyperparameter Logging:**
```python
mlflow.log_params(model.get_params())
```
- Logs ALL model hyperparameters
- Allows comparing different configurations
- Essential for reproducibility

**3. Metric Logging:**
```python
mlflow.log_metric("f1_score", f1)
```
- Logs a single numeric value
- Can be compared across runs
- Used for model selection

**4. Model Logging:**
```python
mlflow.sklearn.log_model(model, "model", registered_model_name="...")
```
- Saves the trained model
- Registers in Model Registry
- Can be loaded later for inference

**5. Artifact Logging:**
```python
mlflow.log_artifact(report_path)
```
- Logs files (reports, plots, etc.)
- Stored in artifact store
- Accessible from MLflow UI

### 4.3 Understanding the Metrics

Each metric tells a different story about model performance.

**Accuracy:**
```python
accuracy = (TP + TN) / (TP + TN + FP + FN)
```
- Overall correctness
- Misleading for imbalanced data
- Example: 80% accuracy might mean "predict reject for everyone"

**Precision:**
```python
precision = TP / (TP + FP)
```
- Of all predicted approvals, how many were correct?
- High precision = low false positive rate
- Business: "When we approve, we're usually right"

**Recall:**
```python
recall = TP / (TP + FN)
```
- Of all actual approvals, how many did we catch?
- High recall = low false negative rate
- Business: "We approve most good applicants"

**F1-Score:**
```python
f1 = 2 * (precision * recall) / (precision + recall)
```
- Harmonic mean of precision and recall
- Balances both metrics
- Good for imbalanced datasets

**ROC-AUC:**
- Area under ROC curve
- Measures discrimination ability
- Threshold-independent
- Best for model comparison

**Business Trade-offs:**

```
High Precision, Low Recall:
├── Few false positives (low credit risk)
├── Many false negatives (reject good customers)
└── Conservative strategy

Low Precision, High Recall:
├── Many false positives (high credit risk)
├── Few false negatives (approve most good customers)
└── Aggressive strategy

Balanced (High F1):
├── Balance both concerns
└── Optimal for most cases
```

### 4.4 Testing the Training Script

Run the training script locally to verify it works.

```bash
# Ensure preprocessing is done
python training/scripts/preprocess_data.py

# Run training
python training/scripts/train_models.py
```

**Expected Output:**
```
================================================================================
MODEL TRAINING WITH MLFLOW TRACKING
================================================================================

STEP 1: Setting up MLflow
--------------------------------------------------------------------------------
✓ MLflow tracking URI: http://localhost:5000
✓ Experiment: Credit Card Approval - Automated Pipeline

STEP 2: Loading Preprocessed Data
--------------------------------------------------------------------------------
✓ Training set: (56000, 17)
✓ Test set:     (10000, 17)
  Training classes: {0: 28000, 1: 28000}

...

================================================================================
TRAINING: XGBoost
================================================================================
Rationale: Gradient boosting: State-of-the-art performance
Strengths: Handles complexity, built-in regularization, fast
Use Case:  Maximum performance, production deployment

Logging metadata to MLflow...
✓ Logged 15 hyperparameters
Training model...
✓ Training completed in 12.34 seconds
Evaluating model...
Metrics:
  Accuracy:  0.8542
  F1-Score:  0.8234
  ROC-AUC:   0.9123
  Precision: 0.8456
  Recall:    0.8023

...

================================================================================
MODEL COMPARISON
================================================================================
Model                F1       ROC-AUC  Precision  Recall   Time(s)
--------------------------------------------------------------------------------
Logistic_Regression  0.7823   0.8456   0.7654     0.8012   2.34
Random_Forest        0.8123   0.8987   0.8234     0.8023   45.67
XGBoost              0.8234   0.9123   0.8456     0.8023   12.34

================================================================================
BEST MODEL SELECTION
================================================================================
Best Model: XGBoost
  ROC-AUC:   0.9123
  F1-Score:  0.8234
  Precision: 0.8456
  Recall:    0.8023
  Run ID:    abc123def456
```

### 4.5 Checkpoint

Verify your understanding before moving to Airflow integration.

**Self-Assessment:**
- [ ] You understand what MLflow logs (params, metrics, artifacts, models)
- [ ] You can explain why we use `with mlflow.start_run()`
- [ ] You know the difference between F1-score and ROC-AUC
- [ ] You understand the precision-recall trade-off
- [ ] You can interpret the confusion matrix
- [ ] You know why we select the best model by ROC-AUC

**Conceptual Questions:**

**Q1:** Why log hyperparameters to MLflow?

<details>
<summary>Click to review</summary>

Logging hyperparameters is essential for:

1. **Reproducibility**: Can recreate exact model later
2. **Comparison**: See which hyperparameters work best
3. **Debugging**: Understand why a model performed poorly
4. **Documentation**: No need to remember settings
5. **Collaboration**: Team members see your configuration

Example: If XGBoost performs well, you can see it used `max_depth=6, learning_rate=0.1`. You can then try `max_depth=8` and compare.

</details>

**Q2:** A stakeholder asks: "Our model has 85% accuracy. Is that good?"

<details>
<summary>Click to review</summary>

The answer depends on context:

**If dataset is 80% rejected, 20% approved:**
- 85% accuracy could mean: predict "reject" for everyone (80% accuracy) + correctly predict some approvals (5% improvement)
- Need to check precision and recall

**Better response:**
"85% accuracy is a starting point. Let me show you the complete picture:
- Precision: 84% (when we approve, we're right 84% of the time)
- Recall: 80% (we approve 80% of good applicants)
- F1-Score: 82% (balanced performance)
- ROC-AUC: 91% (excellent discrimination ability)

The model performs well, but we're missing 20% of good applicants (recall=80%). Depending on business goals, we might tune the threshold to approve more applicants."

</details>

---

**Continue to Part 4 for Airflow Integration...**
