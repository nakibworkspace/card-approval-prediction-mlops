# Lab 02: AWS Cloud Integration - IaC, Data Versioning & Model Storage

## Introduction

After testing your ML pipeline locally, it's time to make it production-grade by integrating with AWS cloud services. This lab transforms your local setup into a cloud-native system using Infrastructure as Code (Pulumi), data versioning (DVC), and cloud-based model storage (MLflow + S3).

## Learning Objectives

By the end of this lab, you will be able to:

1. Use Pulumi to define and deploy AWS infrastructure as code
2. Create S3 buckets for data and model storage with proper security
3. Configure DVC for cloud-based data versioning
4. Integrate MLflow with S3 for model artifact storage
5. Enable team collaboration through shared cloud resources
6. Understand production-grade ML infrastructure patterns

**Prerequisites:** Completion of Lab 01, AWS account with billing enabled, AWS CLI installed and configured.

**Estimated Time:** 3-4 hours

## Prologue: From Local to Production

Your ML pipeline works great on your laptop. You've trained models, tracked experiments with MLflow, and achieved good performance. But now you face real-world challenges:

- **Collaboration:** Teammates can't access your data or models
- **Reproducibility:** "Works on my machine" isn't good enough
- **Durability:** Data on your laptop isn't backed up
- **Scalability:** Manual infrastructure doesn't scale
- **Deployment:** Production systems need cloud storage

You need to move from local development to cloud-native infrastructure. This lab builds the foundation for production ML systems.

## Environment Setup

Install required tools:

```bash
# Activate virtual environment
source venv/bin/activate

# Install cloud dependencies
pip install pulumi pulumi-aws dvc[s3] boto3 botocore

# Install Pulumi CLI
curl -fsSL https://get.pulumi.com | sh
export PATH=$PATH:$HOME/.pulumi/bin

# Verify installations
pulumi version
dvc version
aws --version
mlflow --version
```

Configure AWS credentials:

```bash
# Configure AWS CLI
aws configure
# Enter: Access Key ID, Secret Access Key, Region (us-east-1), Output format (json)

# Verify AWS access
aws sts get-caller-identity
```

## Chapter 1: Infrastructure as Code with Pulumi

### 1.1 What You Will Build

You will use Pulumi to define AWS S3 buckets as Python code, creating reproducible infrastructure for data and model storage.

### 1.2 Think First: Why Infrastructure as Code?

**Question:** Compare two approaches to creating cloud resources:
- Approach A: Click through AWS Console manually
- Approach B: Write code that creates resources automatically

What are the trade-offs?

<details>
<summary>Click to review</summary>

**Manual (AWS Console):**
- Pros: Visual, immediate feedback, no coding required
- Cons: Not reproducible, no version control, error-prone, can't replicate environments

**Infrastructure as Code (Pulumi):**
- Pros: Reproducible, version controlled, automated, consistent across environments, self-documenting
- Cons: Initial learning curve

For production ML systems, IaC is essential. It ensures dev, staging, and production environments are identical.

</details>

### 1.3 Implementation

Initialize Pulumi project:

```bash
# Create pulumi directory
mkdir -p pulumi
cd pulumi

# Initialize Pulumi project
pulumi new aws-python \
  --name card-approval-infra \
  --description "ML infrastructure for card approval prediction"

# When prompted:
# - Stack name: dev
# - AWS region: us-east-1 (or your preferred region)
```

Create `pulumi/__main__.py`:

```python
import pulumi
import pulumi_aws as aws

# Configuration
config = pulumi.Config()
project_name = pulumi.get_project()
stack_name = pulumi.get_stack()

# ============================================
# S3 Bucket for Data Versioning (DVC)
# ============================================
data_bucket = aws.s3.Bucket(
    "ml-data-bucket",
    bucket=f"{project_name}-{stack_name}-ml-data",
    versioning=aws.s3.BucketVersioningArgs(
        enabled=True,  # Keep version history
    ),
    tags={
        "Project": project_name,
        "Stack": stack_name,
        "Purpose": "ML data versioning with DVC"
    }
)

# Block public access (security best practice)
data_bucket_public_access_block = aws.s3.BucketPublicAccessBlock(
    "ml-data-bucket-public-access-block",
    bucket=data_bucket.id,
    block_public_acls=True,
    block_public_policy=True,
    ignore_public_acls=True,
    restrict_public_buckets=True
)

# Enable server-side encryption
data_bucket_encryption = aws.s3.BucketServerSideEncryptionConfigurationV2(
    "ml-data-bucket-encryption",
    bucket=data_bucket.id,
    rules=[aws.s3.BucketServerSideEncryptionConfigurationV2RuleArgs(
        apply_server_side_encryption_by_default=aws.s3.BucketServerSideEncryptionConfigurationV2RuleApplyServerSideEncryptionByDefaultArgs(
            sse_algorithm="AES256"
        )
    )]
)

# ============================================
# S3 Bucket for MLflow Artifacts
# ============================================
mlflow_bucket = aws.s3.Bucket(
    "mlflow-artifacts-bucket",
    bucket=f"{project_name}-{stack_name}-mlflow-artifacts",
    versioning=aws.s3.BucketVersioningArgs(
        enabled=True,
    ),
    tags={
        "Project": project_name,
        "Stack": stack_name,
        "Purpose": "MLflow model artifacts"
    }
)

# Block public access
mlflow_bucket_public_access_block = aws.s3.BucketPublicAccessBlock(
    "mlflow-artifacts-bucket-public-access-block",
    bucket=mlflow_bucket.id,
    block_public_acls=True,
    block_public_policy=True,
    ignore_public_acls=True,
    restrict_public_buckets=True
)

# Enable encryption
mlflow_bucket_encryption = aws.s3.BucketServerSideEncryptionConfigurationV2(
    "mlflow-artifacts-bucket-encryption",
    bucket=mlflow_bucket.id,
    rules=[aws.s3.BucketServerSideEncryptionConfigurationV2RuleArgs(
        apply_server_side_encryption_by_default=aws.s3.BucketServerSideEncryptionConfigurationV2RuleApplyServerSideEncryptionByDefaultArgs(
            sse_algorithm="AES256"
        )
    )]
)

# Export bucket names and region
pulumi.export("data_bucket_name", data_bucket.id)
pulumi.export("mlflow_bucket_name", mlflow_bucket.id)
pulumi.export("aws_region", config.require("aws:region"))
```

### 1.4 Understanding the Infrastructure

You're creating two S3 buckets:

| Bucket | Purpose | Features |
|--------|---------|----------|
| Data Bucket | DVC data versioning | Versioning, encryption, private |
| MLflow Bucket | Model artifacts | Versioning, encryption, private |

Both buckets have:
- **Versioning:** Automatic history of all changes
- **Encryption:** Data protected at rest (AES-256)
- **Public access blocked:** No accidental exposure

### 1.5 Deploy Infrastructure

```bash
# Preview changes
pulumi preview

# Deploy (creates S3 buckets)
pulumi up
# When prompted, select "yes"
```

**Predict:** How many resources will be created?

<details>
<summary>Click to verify</summary>

Pulumi creates 6 resources:
- 2 S3 buckets
- 2 public access block configurations
- 2 encryption configurations

Output shows both bucket names. Verify in AWS Console.

</details>

### 1.6 Checkpoint

**Self-Assessment:**
- [ ] Pulumi deployment succeeds
- [ ] Both S3 buckets visible in AWS Console
- [ ] Buckets have versioning and encryption enabled
- [ ] You can retrieve bucket names: `pulumi stack output`

## Chapter 2: Data Versioning with DVC

### 2.1 What You Will Build

You will configure DVC to version control your datasets using S3 storage, enabling Git-like versioning for data.

### 2.2 Think First: Why Not Just Use Git?

**Question:** Why use DVC instead of committing data files to Git?

<details>
<summary>Click to review</summary>

**Git limitations for data:**
- Not designed for large files (>100MB)
- Slows down repository operations
- Bloats repository size
- Poor performance with binary files

**DVC advantages:**
- Designed for large datasets
- Stores data separately from code
- Lightweight metadata in Git
- Efficient for binary files
- Supports cloud storage

DVC tracks data versions using small `.dvc` files in Git, while actual data lives in S3.

</details>

### 2.3 Implementation

Initialize DVC:

```bash
# Navigate to project root
cd ..  # Back to card-approval-prediction/

# Initialize DVC
dvc init

# Get bucket name from Pulumi
cd pulumi
export DVC_S3_BUCKET=$(pulumi stack output data_bucket_name)
export AWS_REGION=$(pulumi stack output aws_region)
cd ..

# Configure DVC remote
dvc remote add -d s3storage s3://$DVC_S3_BUCKET/dvc-storage
dvc remote modify s3storage region $AWS_REGION

# Verify configuration
dvc remote list
```

### 2.4 Track Data with DVC

```bash
# Add training data to DVC tracking
dvc add training/data/raw
dvc add training/data/processed

# This creates .dvc metadata files
ls -la training/data/*.dvc

# Commit DVC metadata to Git
git add training/data/raw.dvc training/data/processed.dvc .gitignore .dvc/
git commit -m "Add data to DVC tracking"

# Push data to S3
dvc push
```

**Observe:** Data files are now in S3, while Git only tracks small `.dvc` metadata files.

### 2.5 Verify Data in S3

```bash
# List data in S3
aws s3 ls s3://$DVC_S3_BUCKET/dvc-storage/ --recursive

# Check bucket size
aws s3 ls s3://$DVC_S3_BUCKET --recursive --summarize
```

### 2.6 Test Data Pull

Simulate teammate pulling data:

```bash
# Remove local data
rm -rf training/data/raw training/data/processed

# Pull from S3
dvc pull

# Verify data restored
ls training/data/raw
ls training/data/processed
```

### 2.7 Checkpoint

**Self-Assessment:**
- [ ] DVC initialized and configured
- [ ] Data tracked with DVC
- [ ] Data pushed to S3
- [ ] Data can be pulled from S3
- [ ] You understand DVC workflow

## Chapter 3: MLflow S3 Integration

### 3.1 What You Will Build

You will configure MLflow to store model artifacts in S3, enabling team access to trained models.

### 3.2 Implementation

Create MLflow S3 configuration module `training/src/config/mlflow_s3_config.py`:

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
            return False
```

Create environment configuration:

```bash
# Get bucket names from Pulumi
cd pulumi
export MLFLOW_S3_BUCKET=$(pulumi stack output mlflow_bucket_name)
export DVC_S3_BUCKET=$(pulumi stack output data_bucket_name)
export AWS_REGION=$(pulumi stack output aws_region)
cd ..

# Create .env file
cat > .env << EOF
# MLflow Configuration
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_S3_BUCKET=${MLFLOW_S3_BUCKET}

# DVC Configuration
DVC_S3_BUCKET=${DVC_S3_BUCKET}

# AWS Configuration
AWS_REGION=${AWS_REGION}
EOF

echo "✓ Environment configuration created"
```

### 3.3 Update Training Script

Create `training/scripts/run_training_cloud.py`:

```python
import mlflow
import mlflow.sklearn
import numpy as np
from xgboost import XGBClassifier
from sklearn.metrics import f1_score, roc_auc_score, classification_report
from training.src.config.mlflow_s3_config import MLflowS3Config
import joblib
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure MLflow with S3
config = MLflowS3Config()
config.verify_bucket_access()

mlflow.set_tracking_uri(config.tracking_uri)

# Create experiment with S3 artifact location
experiment_name = "Card Approval - Cloud Production"
experiment = mlflow.get_experiment_by_name(experiment_name)

if experiment is None:
    experiment_id = mlflow.create_experiment(
        experiment_name,
        artifact_location=config.get_artifact_location()
    )
    print(f"✓ Created experiment: {experiment_name}")
else:
    experiment_id = experiment.experiment_id
    print(f"✓ Using existing experiment: {experiment_name}")

mlflow.set_experiment(experiment_name)
print(f"Artifact location: {config.get_artifact_location()}")

# Load data
print("\nLoading data...")
X_train = np.load('training/data/processed/X_train.npy')
y_train = np.load('training/data/processed/y_train.npy')
X_test = np.load('training/data/processed/X_test.npy')
y_test = np.load('training/data/processed/y_test.npy')

print(f"Training samples: {X_train.shape[0]}")
print(f"Test samples: {X_test.shape[0]}")

# Train model with cloud logging
print("\nTraining model...")
with mlflow.start_run(run_name="XGBoost_Cloud_Production"):
    # Parameters
    params = {
        "n_estimators": 100,
        "max_depth": 6,
        "learning_rate": 0.1,
        "random_state": 42,
        "eval_metric": "logloss"
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
        "roc_auc": roc_auc_score(y_test, y_pred_proba),
        "accuracy": (y_pred == y_test).mean()
    }
    mlflow.log_metrics(metrics)
    
    # Log model to S3
    mlflow.sklearn.log_model(
        model,
        "model",
        registered_model_name="card_approval_production"
    )
    
    # Log classification report
    report = classification_report(y_test, y_pred)
    with open('classification_report.txt', 'w') as f:
        f.write(report)
    mlflow.log_artifact('classification_report.txt', 'reports')
    
    # Log feature metadata
    feature_names = [f"feature_{i}" for i in range(X_train.shape[1])]
    with open('feature_names.json', 'w') as f:
        json.dump(feature_names, f)
    mlflow.log_artifact('feature_names.json', 'metadata')
    
    print(f"\n✓ Model and artifacts logged to S3")
    print(f"  F1-Score: {metrics['f1_score']:.4f}")
    print(f"  ROC-AUC: {metrics['roc_auc']:.4f}")
    print(f"  Accuracy: {metrics['accuracy']:.4f}")
    print(f"\nView in MLflow UI: {config.tracking_uri}")
```

### 3.4 Train with Cloud Storage

```bash
# Load environment
source .env

# Ensure MLflow server is running
# mlflow server --backend-store-uri sqlite:///mlflow.db --host 0.0.0.0 --port 5000

# Train model
python training/scripts/run_training_cloud.py
```

### 3.5 Verify Artifacts in S3

```bash
# List MLflow artifacts in S3
aws s3 ls s3://$MLFLOW_S3_BUCKET/mlflow-artifacts/ --recursive

# View in MLflow UI
open http://localhost:5000
```

### 3.6 Checkpoint

**Self-Assessment:**
- [ ] MLflow configured with S3
- [ ] Training completes successfully
- [ ] Artifacts visible in S3
- [ ] MLflow UI shows S3 artifact location
- [ ] You understand cloud-based MLflow architecture

## Chapter 4: Loading Models from Cloud

### 4.1 Implementation

Create `training/scripts/load_model_cloud.py`:

```python
import mlflow
import mlflow.sklearn
import numpy as np
import time
from training.src.config.mlflow_s3_config import MLflowS3Config
from dotenv import load_dotenv

# Load environment
load_dotenv()

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
print("="*60)
print("FIRST LOAD (from S3)")
print("="*60)
model, time1 = load_model_with_timing("card_approval_production")

# Test predictions
X_test = np.load('training/data/processed/X_test.npy')
predictions = model.predict(X_test[:5])
probabilities = model.predict_proba(X_test[:5])

print("\nSample Predictions:")
for i, (pred, proba) in enumerate(zip(predictions, probabilities)):
    decision = "APPROVED" if pred == 1 else "REJECTED"
    confidence = proba[1] if pred == 1 else proba[0]
    print(f"  {i+1}. {decision} (confidence: {confidence:.2%})")

# Second load (from cache)
print("\n" + "="*60)
print("SECOND LOAD (from cache)")
print("="*60)
model2, time2 = load_model_with_timing("card_approval_production")

print(f"\n✓ Caching speedup: {time1/time2:.1f}x faster")
```

Run model loading:

```bash
source .env
python training/scripts/load_model_cloud.py
```

### 4.2 Checkpoint

**Self-Assessment:**
- [ ] Model loads from S3
- [ ] Predictions work correctly
- [ ] Second load is faster (caching)
- [ ] You understand production model loading

## Epilogue: Production-Grade Infrastructure

You've built a complete cloud-native ML infrastructure:

| Component | Capability | Benefit |
|-----------|------------|---------|
| Pulumi IaC | Reproducible infrastructure | Consistent environments |
| S3 Data Bucket | Versioned data storage | Data durability & history |
| DVC | Git-like data versioning | Team collaboration |
| S3 MLflow Bucket | Model artifact storage | Shared model access |
| MLflow + S3 | Cloud-based tracking | Production-ready |

### Complete Workflow Verification

```bash
# 1. Infrastructure
cd pulumi && pulumi stack output && cd ..

# 2. Data versioning
dvc status
aws s3 ls s3://$DVC_S3_BUCKET/dvc-storage/ --recursive

# 3. Model artifacts
aws s3 ls s3://$MLFLOW_S3_BUCKET/mlflow-artifacts/ --recursive

# 4. MLflow UI
open http://localhost:5000
```

## The Principles

1. **Infrastructure as Code is essential** — Manual infrastructure doesn't scale
2. **Separate data and code** — Large files don't belong in Git
3. **Version everything** — Data, models, and infrastructure
4. **Cloud storage enables collaboration** — Team members access same resources
5. **Security by default** — Block public access, enable encryption
6. **Cache for performance** — MLflow caching makes S3 practical

## Troubleshooting

### Error: AWS credentials not found

```bash
# Configure AWS CLI
aws configure

# Verify
aws sts get-caller-identity
```

### Error: Access denied to S3

```bash
# Check IAM permissions include:
# - s3:PutObject
# - s3:GetObject
# - s3:ListBucket
# - s3:DeleteObject

# Verify access
aws s3 ls s3://$MLFLOW_S3_BUCKET
```

### Error: Pulumi deployment fails

```bash
# Check Pulumi state
pulumi stack

# Retry
pulumi up

# If persistent, destroy and recreate
pulumi destroy
pulumi up
```

### Error: DVC push fails

```bash
# Verify DVC remote
dvc remote list

# Reconfigure if needed
dvc remote modify s3storage region us-east-1
```

## Next Steps

1. **Multiple environments:** Create separate Pulumi stacks for dev/staging/prod
2. **IAM roles:** Use IAM roles instead of access keys
3. **CI/CD integration:** Automate `dvc pull` and model loading
4. **Cost optimization:** Implement S3 lifecycle policies
5. **Monitoring:** Add CloudWatch alarms for S3 access

## Additional Resources

- [Pulumi Documentation](https://www.pulumi.com/docs/)
- [DVC Documentation](https://dvc.org/doc)
- [MLflow S3 Integration](https://mlflow.org/docs/latest/tracking.html#amazon-s3-and-s3-compatible-storage)
- [AWS S3 Best Practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/best-practices.html)
