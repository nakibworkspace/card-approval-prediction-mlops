# Lab 03: MLflow + S3 Integration

## Introduction

This lab integrates MLflow with S3 for cloud-based model artifact storage. You will configure MLflow to store models in S3, update your training pipeline to log artifacts to the cloud, and enable team collaboration through shared model storage.

## Learning Objectives

By the end of this lab, you will be able to:

1. Configure MLflow to use S3 for artifact storage
2. Update training pipelines to log models to S3
3. Load models from S3 with caching
4. Understand cloud-based MLflow architecture
5. Enable team collaboration with shared model artifacts
6. Optimize model loading performance

**Prerequisites:** Completion of Lab 01 and Lab 02, MLflow tracking server running, S3 bucket created (from Lab 02), AWS credentials configured.

**Estimated Time:** 2-3 hours

## Prologue: The Challenge

Your MLflow experiments currently store artifacts locally. When a teammate wants to test your model, they cannot access it. When you deploy to production, you manually copy model files. This approach does not scale for team collaboration or production deployment.

You need MLflow artifacts in S3 so that:
- Team members can access the same models
- Production systems can load models directly
- Models are backed up automatically
- Artifact storage is durable and scalable

## Environment Setup

Ensure prerequisites are met:

```bash
# Activate virtual environment
source venv/bin/activate

# Verify MLflow is installed
mlflow --version

# Verify S3 bucket exists (from Lab 02)
cd pulumi
export MLFLOW_S3_BUCKET=$(pulumi stack output data_bucket_name)
cd ..

echo "MLflow S3 Bucket: $MLFLOW_S3_BUCKET"

# Verify AWS access
aws s3 ls s3://$MLFLOW_S3_BUCKET
```

## Chapter 1: MLflow S3 Configuration

### 1.1 What You Will Build

You will configure MLflow to store model artifacts in S3 instead of the local filesystem.

### 1.2 Think First: Local vs Cloud Storage

**Question:** What changes when MLflow artifacts move from local storage to S3? Consider access patterns, permissions, and latency.

<details>
<summary>Click to review</summary>

**Changes:**
- **Access:** Artifacts accessible from any machine with AWS credentials
- **Permissions:** Requires AWS IAM permissions for S3
- **Latency:** Slightly higher (network vs disk), but negligible
- **Durability:** S3 provides 99.999999999% durability
- **Collaboration:** Team members access the same artifacts
- **Cost:** Minimal S3 storage costs

Benefits far outweigh the minor latency increase for production ML systems.

</details>

### 1.3 Implementation

Create `training/src/config/mlflow_s3_config.py`:

```python
import os
import boto3
from botocore.exceptions import ClientError

class MLflowS3Config:
    def __init__(self):
        self.bucket_name = os.getenv("MLFLOW_S3_BUCKET")
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
        
        if not self.bucket_name:
            raise ValueError("MLFLOW_S3_BUCKET environment variable must be set")
    
    def get_artifact_location(self):
        """Get S3 artifact location URI."""
        return f"s3://{self.bucket_name}/mlflow-artifacts"
    
    def verify_bucket_access(self):
        """Verify S3 bucket is accessible."""
        s3_client = boto3.client('s3', region_name=self.region)
        try:
            s3_client.head_bucket(Bucket=self.bucket_name)
            print(f"✓ S3 bucket '{self.bucket_name}' is accessible")
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                print(f"✗ Bucket does not exist")
            elif error_code == '403':
                print(f"✗ Access denied")
            else:
                print(f"✗ Error: {e}")
            return False
```

Create environment configuration:

```bash
# Create .env file
cat > .env << EOF
# MLflow Configuration
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_S3_BUCKET=${MLFLOW_S3_BUCKET}
AWS_REGION=us-east-1
EOF

# Test configuration
python -c "from training.src.config.mlflow_s3_config import MLflowS3Config; \
  config = MLflowS3Config(); \
  print(f'Artifact location: {config.get_artifact_location()}'); \
  config.verify_bucket_access()"
```

### 1.4 Checkpoint

**Self-Assessment:**
- [ ] Configuration module created
- [ ] Environment variables set
- [ ] Bucket access verified
- [ ] You understand S3 URI format

## Chapter 2: Training with S3 Artifacts

### 2.1 What You Will Build

You will update the training script to log all artifacts (models, preprocessors, metadata) to S3.

### 2.2 Implementation

Create `training/scripts/run_training_s3.py`:

```python
import mlflow
import mlflow.sklearn
import numpy as np
from xgboost import XGBClassifier
from sklearn.metrics import f1_score, roc_auc_score
from training.src.config.mlflow_s3_config import MLflowS3Config
import joblib
import json

# Load configuration
config = MLflowS3Config()
config.verify_bucket_access()

# Configure MLflow
mlflow.set_tracking_uri(config.tracking_uri)

# Create experiment with S3 artifact location
experiment_name = "Card Approval - S3 Storage"
experiment = mlflow.get_experiment_by_name(experiment_name)

if experiment is None:
    experiment_id = mlflow.create_experiment(
        experiment_name,
        artifact_location=config.get_artifact_location()
    )
else:
    experiment_id = experiment.experiment_id

mlflow.set_experiment(experiment_name)

print(f"Experiment: {experiment_name}")
print(f"Artifact location: {config.get_artifact_location()}")

# Load data
X_train = np.load('training/data/processed/X_train_balanced.npy')
y_train = np.load('training/data/processed/y_train_balanced.npy')
X_test = np.load('training/data/processed/X_test.npy')
y_test = np.load('training/data/processed/y_test.npy')

# Train with S3 logging
with mlflow.start_run(run_name="XGBoost_S3"):
    # Parameters
    params = {
        "n_estimators": 100,
        "max_depth": 6,
        "learning_rate": 0.1,
        "random_state": 42
    }
    mlflow.log_params(params)
    
    # Train
    model = XGBClassifier(**params)
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    metrics = {
        "f1_score": f1_score(y_test, y_pred),
        "roc_auc": roc_auc_score(y_test, y_pred_proba)
    }
    mlflow.log_metrics(metrics)
    
    # Log model to S3
    mlflow.sklearn.log_model(
        model,
        "model",
        registered_model_name="card_approval_s3"
    )
    
    # Log preprocessor
    scaler = joblib.load('models/scaler.pkl')
    mlflow.log_artifact('models/scaler.pkl', 'preprocessors')
    
    # Log feature metadata
    feature_names = [f"feature_{i}" for i in range(X_train.shape[1])]
    with open('feature_names.json', 'w') as f:
        json.dump(feature_names, f)
    mlflow.log_artifact('feature_names.json', 'metadata')
    
    print(f"\n✓ Model and artifacts logged to S3")
    print(f"  F1-Score: {metrics['f1_score']:.4f}")
    print(f"  ROC-AUC: {metrics['roc_auc']:.4f}")
```

Run training:

```bash
source .env
python training/scripts/run_training_s3.py
```

Verify artifacts in S3:

```bash
aws s3 ls s3://$MLFLOW_S3_BUCKET/mlflow-artifacts/ --recursive
```

### 2.3 Checkpoint

**Self-Assessment:**
- [ ] Training completes successfully
- [ ] Artifacts appear in S3
- [ ] MLflow UI shows S3 artifact location
- [ ] You can list artifacts with AWS CLI

## Chapter 3: Loading Models from S3

### 3.1 What You Will Build

You will load models from S3 and understand caching behavior for performance optimization.

### 3.2 Implementation

Create `training/scripts/load_model_s3.py`:

```python
import mlflow
import mlflow.sklearn
import numpy as np
import time
from training.src.config.mlflow_s3_config import MLflowS3Config

# Configure
config = MLflowS3Config()
mlflow.set_tracking_uri(config.tracking_uri)

def load_model_with_timing(model_name: str, stage: str = "None"):
    """Load model from S3 and measure time."""
    model_uri = f"models:/{model_name}/{stage}"
    
    print(f"Loading: {model_name} (stage: {stage})")
    print(f"URI: {model_uri}")
    
    start_time = time.time()
    model = mlflow.sklearn.load_model(model_uri)
    load_time = time.time() - start_time
    
    print(f"✓ Loaded in {load_time:.2f} seconds")
    return model, load_time

# First load (downloads from S3)
print("First load (from S3):")
model, time1 = load_model_with_timing("card_approval_s3")

# Test prediction
X_test = np.load('training/data/processed/X_test.npy')
predictions = model.predict(X_test[:5])
probabilities = model.predict_proba(X_test[:5])

print("\nSample Predictions:")
for i, (pred, proba) in enumerate(zip(predictions, probabilities)):
    decision = "APPROVED" if pred == 1 else "REJECTED"
    confidence = proba[1] if pred == 1 else proba[0]
    print(f"  {i+1}. {decision} (confidence: {confidence:.2%})")

# Second load (from cache)
print("\n" + "="*50)
print("Second load (from cache):")
model2, time2 = load_model_with_timing("card_approval_s3")

print(f"\nSpeedup: {time1/time2:.1f}x faster")
```

Run loading:

```bash
source .env
python training/scripts/load_model_s3.py
```

### 3.3 Checkpoint

**Self-Assessment:**
- [ ] Model loads from S3
- [ ] Predictions work correctly
- [ ] Second load is faster (caching)
- [ ] You understand caching behavior

## Chapter 4: Team Collaboration Workflow

### 4.1 Understanding the Workflow

With MLflow + S3, team collaboration works as follows:

```
Data Scientist A          MLflow + S3          Data Scientist B
----------------          -----------          ----------------
Train model       -->     Store in S3
Log to MLflow     -->     
Register model    -->     
                          <--                  Pull model
                          <--                  Load from S3
                          <--                  Test/Deploy
```

### 4.2 Simulating Team Access

Simulate teammate accessing your model:

```bash
# Clear local MLflow cache (simulate teammate's machine)
rm -rf ~/.mlflow/

# Load model (downloads from S3)
python training/scripts/load_model_s3.py
```

**Observe:** Model downloads from S3 and works identically on any machine with AWS credentials.

### 4.3 Checkpoint

**Self-Assessment:**
- [ ] You understand team collaboration workflow
- [ ] Models are accessible from any machine
- [ ] You can explain the role of S3 in collaboration

## Epilogue: The Complete System

You have integrated MLflow with S3:

| Component | Capability |
|-----------|------------|
| MLflow + S3 | Cloud-based artifact storage |
| Model Registry | S3-backed model lifecycle |
| Team Access | Shared model artifacts |
| Caching | Optimized model loading |

Verify the complete workflow:

```bash
# Configure
source .env

# Train with S3
python training/scripts/run_training_s3.py

# Load from S3
python training/scripts/load_model_s3.py

# Verify in S3
aws s3 ls s3://$MLFLOW_S3_BUCKET/mlflow-artifacts/ --recursive

# View in MLflow UI
open http://localhost:5000
```

## The Principles

1. **Cloud storage enables collaboration** — Team members access the same artifacts
2. **Cache for performance** — MLflow caching makes S3 loading practical
3. **Version everything** — S3 versioning provides artifact history
4. **Separate concerns** — Data in one bucket (Lab 02), models in artifact path
5. **Configure, don't hardcode** — Use environment variables for flexibility

## Troubleshooting

### Error: Access Denied to S3

**Solution:**
```bash
# Verify AWS credentials
aws sts get-caller-identity

# Check S3 permissions
aws s3 ls s3://$MLFLOW_S3_BUCKET

# Ensure IAM user/role has:
# - s3:PutObject
# - s3:GetObject
# - s3:ListBucket
```

### Error: MLflow cannot write to S3

**Solution:**
```bash
# Restart MLflow server with AWS credentials
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret

mlflow server \
  --backend-store-uri sqlite:///mlflow.db \
  --default-artifact-root s3://$MLFLOW_S3_BUCKET/mlflow-artifacts \
  --host 0.0.0.0 --port 5000
```

### Error: Slow model loading

**Solution:**
```python
# Models are cached after first load
# For production, load at startup:
model = mlflow.sklearn.load_model(model_uri)  # Once at startup
# Then reuse 'model' for all predictions
```

## Next Steps

1. **Remote MLflow server:** Deploy MLflow on EC2 for team access
2. **Model versioning:** Implement semantic versioning for models
3. **Automated promotion:** CI/CD pipeline promotes models to Production
4. **Cross-region replication:** Replicate S3 bucket for disaster recovery
5. **Model serving:** Integrate with AWS SageMaker or custom serving

## Additional Resources

- [MLflow S3 Integration](https://mlflow.org/docs/latest/tracking.html#amazon-s3-and-s3-compatible-storage)
- [MLflow Model Registry](https://mlflow.org/docs/latest/model-registry.html)
- [AWS S3 Best Practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/best-practices.html)
- [MLflow Production Deployment](https://mlflow.org/docs/latest/tracking.html#scenario-5-mlflow-tracking-server-enabled-with-proxied-artifact-storage-access)
