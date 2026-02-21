# Lab 03: Infrastructure as Code (Pulumi) & S3

## Introduction

This lab transitions from local development to cloud infrastructure. You will use Pulumi to define AWS resources as code, create an S3 bucket for model storage, and configure MLflow to use S3 as the artifact store. This establishes the foundation for cloud-native ML operations.

## Learning Objectives

By the end of this lab, you will be able to:

1. Install and configure Pulumi for AWS infrastructure management
2. Define cloud resources using Python code
3. Create and configure S3 buckets with appropriate permissions
4. Configure MLflow to use S3 for artifact storage
5. Upload and retrieve models from cloud storage
6. Understand Infrastructure as Code principles and benefits

**Prerequisites:** Completion of Lab 02, AWS account with billing enabled, basic understanding of cloud storage concepts, AWS CLI installed and configured.

## Prologue: The Challenge

Your ML models currently live on your laptop. When a teammate asks "Can I test the latest model?", you email them a 200MB file. When the model needs to run in production, you manually copy it to a server. This approach does not scale.

You need cloud storage that is accessible from anywhere, versioned automatically, and integrated with your ML workflow. Additionally, your infrastructure should be defined as code so that creating a new environment (development, staging, production) is as simple as running a command.

## Environment Setup

Install Pulumi and AWS dependencies:

```bash
# Install Pulumi CLI
curl -fsSL https://get.pulumi.com | sh

# Add Pulumi to PATH (add to ~/.bashrc or ~/.zshrc for persistence)
export PATH=$PATH:$HOME/.pulumi/bin

# Verify installation
pulumi version

# Install Python dependencies
pip install pulumi pulumi-aws boto3
```

Configure AWS credentials:

```bash
# Configure AWS CLI (if not already done)
aws configure

# Verify AWS access
aws sts get-caller-identity
```

Create Pulumi project directory:

```bash
mkdir -p pulumi
cd pulumi
```

## Chapter 1: Infrastructure as Code Fundamentals

### 1.1 What You Will Build

You will understand Infrastructure as Code (IaC) principles and initialize a Pulumi project for managing AWS resources.

### 1.2 Think First: Manual vs Automated Infrastructure

**Question:** Compare two approaches to creating an S3 bucket:
- Approach A: Click through AWS Console, configure settings manually
- Approach B: Write code that creates the bucket automatically

What are the advantages and disadvantages of each?

<details>
<summary>Click to review</summary>

**Manual (AWS Console):**
- Pros: Visual, immediate feedback, no coding required
- Cons: Not reproducible, no version control, error-prone for complex setups, difficult to replicate across environments

**Infrastructure as Code:**
- Pros: Reproducible, version controlled, automated, consistent across environments, self-documenting
- Cons: Initial learning curve, requires coding knowledge

For production systems, IaC is essential. It ensures development, staging, and production environments are identical, and infrastructure changes are reviewed like code changes.

</details>

### 1.3 Implementation

Initialize a Pulumi project:

```bash
# Create new Pulumi project
pulumi new aws-python --name card-approval-infra --description "ML infrastructure for card approval prediction"

# This creates:
# - Pulumi.yaml (project configuration)
# - __main__.py (infrastructure code)
# - requirements.txt (Python dependencies)
```

When prompted:
- Project name: `card-approval-infra`
- Project description: `ML infrastructure for card approval prediction`
- Stack name: `dev`
- AWS region: `us-east-1` (or your preferred region)

### 1.4 Understanding the Code

Pulumi organizes infrastructure into projects and stacks:

| Concept | Purpose |
|---------|---------|
| Project | Collection of infrastructure code (one per application) |
| Stack | Instance of the project (dev, staging, production) |
| Resource | Individual cloud component (S3 bucket, EC2 instance) |
| State | Current status of deployed infrastructure |

### 1.5 Test and Verify

Verify the Pulumi project:

```bash
# List stacks
pulumi stack ls

# View current stack
pulumi stack

# Preview changes (should show no changes yet)
pulumi preview
```

**Predict:** What will `pulumi preview` show?

<details>
<summary>Click to verify</summary>

`pulumi preview` shows no changes because the default `__main__.py` creates no resources. The output should indicate "0 to create, 0 to update, 0 to delete". This is the baseline before adding infrastructure code.

</details>

### 1.6 Checkpoint

**Self-Assessment:**
- [ ] Pulumi CLI is installed and accessible
- [ ] AWS credentials are configured correctly
- [ ] Pulumi project is initialized
- [ ] You understand the difference between projects and stacks

## Chapter 2: Creating an S3 Bucket

### 2.1 What You Will Build

You will define an S3 bucket using Pulumi Python code, configure it for ML artifact storage, and deploy it to AWS.

### 2.2 Think First: Bucket Configuration

**Question:** For storing ML models and artifacts, what S3 bucket features are important? Consider versioning, access control, and lifecycle policies.

<details>
<summary>Click to review</summary>

**Important features for ML artifacts:**
- **Versioning:** Automatically keeps old versions of models, enabling rollback
- **Access control:** Restrict access to authorized users/services only
- **Encryption:** Protect sensitive model data at rest
- **Lifecycle policies:** Automatically archive or delete old artifacts to reduce costs
- **Tags:** Organize resources and track costs by project

For this lab, we will focus on versioning and access control. Lifecycle policies can be added later as artifacts accumulate.

</details>

### 2.3 Implementation

Replace the contents of `pulumi/__main__.py`:

```python
import pulumi
import pulumi_aws as aws

# Configuration
config = pulumi.Config()
project_name = pulumi.get_project()
stack_name = pulumi.get_stack()

# Create S3 bucket for ML artifacts
bucket = aws.s3.Bucket(
    "ml-artifacts-bucket",
    bucket=f"{project_name}-{stack_name}-ml-artifacts",
    versioning=aws.s3.BucketVersioningArgs(
        enabled=___,  # Q1: Should versioning be enabled?
    ),
    tags={
        "Project": project_name,
        "Stack": stack_name,
        "Purpose": "ML model artifacts and data"
    }
)

# Block public access (security best practice)
bucket_public_access_block = aws.s3.BucketPublicAccessBlock(
    "ml-artifacts-bucket-public-access-block",
    bucket=bucket.id,
    block_public_acls=___,       # Q2: Block public ACLs?
    block_public_policy=___,     # Q3: Block public policies?
    ignore_public_acls=___,      # Q4: Ignore public ACLs?
    restrict_public_buckets=___  # Q5: Restrict public buckets?
)

# Enable server-side encryption
bucket_encryption = aws.s3.BucketServerSideEncryptionConfigurationV2(
    "ml-artifacts-bucket-encryption",
    bucket=bucket.id,
    rules=[aws.s3.BucketServerSideEncryptionConfigurationV2RuleArgs(
        apply_server_side_encryption_by_default=aws.s3.BucketServerSideEncryptionConfigurationV2RuleApplyServerSideEncryptionByDefaultArgs(
            sse_algorithm="AES256"
        )
    )]
)

# Export bucket name and ARN
pulumi.export("bucket_name", bucket.id)
pulumi.export("bucket_arn", bucket.arn)
pulumi.export("bucket_region", config.require("aws:region"))
```

**Hints:**
- Q1: Versioning should be True for model artifact history
- Q2-Q5: All should be True to prevent public access (security best practice)

<details>
<summary>Click to see solution</summary>

```python
versioning=aws.s3.BucketVersioningArgs(
    enabled=True,  # Keep version history of all artifacts
),

# All public access blocks should be True
block_public_acls=True,
block_public_policy=True,
ignore_public_acls=True,
restrict_public_buckets=True
```

</details>

### 2.4 Understanding the Code

Match each security feature to its purpose:

| Feature | Purpose (A-D) |
|---------|---------------|
| Versioning | ___ |
| Public access block | ___ |
| Server-side encryption | ___ |
| Tags | ___ |

**Options:**
- A: Prevents accidental public exposure of data
- B: Protects data at rest from unauthorized access
- C: Enables rollback to previous model versions
- D: Organizes resources and tracks costs

<details>
<summary>Click to review</summary>

- Versioning: C (Enables rollback)
- Public access block: A (Prevents public exposure)
- Server-side encryption: B (Protects data at rest)
- Tags: D (Organizes and tracks costs)

</details>

### 2.5 Test and Verify

Deploy the infrastructure:

```bash
# Preview changes
pulumi preview

# Deploy (creates the S3 bucket)
pulumi up

# When prompted, select "yes" to proceed
```

**Predict:** What resources will be created? How many?

<details>
<summary>Click to verify</summary>

Pulumi will create 3 resources:
1. S3 bucket
2. Public access block configuration
3. Server-side encryption configuration

The output will show the bucket name and ARN. Verify in AWS Console that the bucket exists with versioning and encryption enabled.

</details>

### 2.6 Checkpoint

**Self-Assessment:**
- [ ] Pulumi deployment completes successfully
- [ ] S3 bucket is visible in AWS Console
- [ ] Bucket has versioning enabled
- [ ] Bucket has public access blocked
- [ ] You can retrieve the bucket name using `pulumi stack output bucket_name`

### 2.7 Experiment: Infrastructure Changes

Modify the bucket configuration to add a lifecycle rule:

```python
# Add lifecycle rule to archive old artifacts
bucket_lifecycle = aws.s3.BucketLifecycleConfigurationV2(
    "ml-artifacts-bucket-lifecycle",
    bucket=bucket.id,
    rules=[aws.s3.BucketLifecycleConfigurationV2RuleArgs(
        id="archive-old-artifacts",
        status="Enabled",
        transitions=[aws.s3.BucketLifecycleConfigurationV2RuleTransitionArgs(
            days=90,
            storage_class="GLACIER"
        )]
    )]
)
```

Run `pulumi up` again.

**Observe:** Pulumi detects the change and updates only the lifecycle configuration, leaving the bucket and other settings unchanged.

**Question:** What happens to existing objects in the bucket when you add a lifecycle rule?

<details>
<summary>Click to review</summary>

Existing objects are not immediately affected. The lifecycle rule applies to objects based on their age from the time the rule is created. Objects older than 90 days will transition to Glacier storage class on their next evaluation cycle (typically within 24 hours).

</details>

## Chapter 3: Configuring MLflow with S3

### 3.1 What You Will Build

You will configure MLflow to store artifacts in S3 instead of the local filesystem, enabling team collaboration and production deployment.

### 3.2 Think First: Local vs Cloud Storage

**Question:** What changes when MLflow artifacts move from local storage to S3? Consider access patterns, permissions, and latency.

<details>
<summary>Click to review</summary>

**Changes:**
- **Access:** Artifacts accessible from any machine with AWS credentials (not just your laptop)
- **Permissions:** Requires AWS IAM permissions to read/write S3
- **Latency:** Slightly higher latency for artifact upload/download (network vs disk)
- **Durability:** S3 provides 99.999999999% durability vs local disk risk
- **Collaboration:** Team members can access the same artifacts
- **Cost:** S3 storage costs vs free local disk (but minimal for ML artifacts)

The benefits far outweigh the minor latency increase for production ML systems.

</details>

### 3.3 Implementation

Update MLflow configuration to use S3. Create `training/src/config/mlflow_config.py`:

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
                print(f"✗ S3 bucket '{self.bucket_name}' does not exist")
            elif error_code == '403':
                print(f"✗ Access denied to S3 bucket '{self.bucket_name}'")
            else:
                print(f"✗ Error accessing S3 bucket: {e}")
            return False

# Usage example
if __name__ == "__main__":
    config = MLflowS3Config()
    print(f"Artifact location: {config.get_artifact_location()}")
    config.verify_bucket_access()
```

Create environment configuration file `.env`:

```bash
# Get bucket name from Pulumi
cd pulumi
export MLFLOW_S3_BUCKET=$(pulumi stack output bucket_name)
cd ..

# Create .env file
cat > .env << EOF
# MLflow Configuration
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_S3_BUCKET=${MLFLOW_S3_BUCKET}
AWS_REGION=us-east-1

# AWS Credentials (if not using AWS CLI default profile)
# AWS_ACCESS_KEY_ID=your_access_key
# AWS_SECRET_ACCESS_KEY=your_secret_key
EOF

echo "Environment configuration created in .env"
```

### 3.4 Understanding the Code

The MLflow S3 integration requires:

1. **Bucket name:** Where to store artifacts
2. **AWS credentials:** How to authenticate
3. **Artifact location URI:** S3 path in format `s3://bucket-name/path`

MLflow automatically handles:
- Uploading artifacts to S3 during `log_model()`
- Downloading artifacts from S3 during `load_model()`
- Versioning (using S3 bucket versioning)

### 3.5 Test and Verify

Test S3 access:

```bash
# Load environment variables
source .env

# Verify bucket access
python training/src/config/mlflow_config.py
```

**Predict:** What will happen if AWS credentials are not configured?

<details>
<summary>Click to verify</summary>

The script will fail with an authentication error. AWS credentials must be configured either through:
- AWS CLI (`aws configure`)
- Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
- IAM role (if running on EC2)

The error message will indicate "Unable to locate credentials" or "Access Denied".

</details>

### 3.6 Checkpoint

**Self-Assessment:**
- [ ] Environment variables are configured correctly
- [ ] Bucket access verification succeeds
- [ ] You understand the S3 URI format
- [ ] You can explain how MLflow uses S3 for artifacts

## Chapter 4: Training with S3 Artifact Storage

### 4.1 What You Will Build

You will modify the training script to log artifacts to S3 and verify that models are stored in the cloud.

### 4.2 Think First: Artifact Storage Strategy

**Question:** Should you store only the final model in S3, or also intermediate artifacts like preprocessors, feature names, and evaluation plots?

<details>
<summary>Click to review</summary>

**Store all artifacts in S3:**
- Final trained model
- Preprocessors (scalers, encoders)
- Feature names and metadata
- Evaluation plots and reports
- Training data checksums

This ensures complete reproducibility. Anyone can load the model and understand exactly how it was trained, what preprocessing was applied, and how it performed. The storage cost is minimal compared to the value of reproducibility.

</details>

### 4.3 Implementation

Update `training/scripts/run_training.py` to use S3:

```python
import mlflow
import mlflow.sklearn
import os
from training.src.config.mlflow_config import MLflowS3Config

# Load configuration
config = MLflowS3Config()
config.verify_bucket_access()

# Configure MLflow
mlflow.set_tracking_uri(config.tracking_uri)
mlflow.set_experiment("Card Approval - S3 Storage")

# Set artifact location for the experiment
experiment = mlflow.get_experiment_by_name("Card Approval - S3 Storage")
if experiment is None:
    experiment_id = mlflow.create_experiment(
        "Card Approval - S3 Storage",
        artifact_location=config.get_artifact_location()
    )
else:
    experiment_id = experiment.experiment_id

print(f"Experiment ID: {experiment_id}")
print(f"Artifact location: {config.get_artifact_location()}")

# Load data (same as before)
X_train = np.load('data/processed/X_train_balanced.npy')
y_train = np.load('data/processed/y_train_balanced.npy')
X_test = np.load('data/processed/X_test.npy')
y_test = np.load('data/processed/y_test.npy')

# Train model with S3 artifact logging
with mlflow.start_run(run_name="XGBoost_S3_Test"):
    # Log parameters
    params = {
        "n_estimators": 100,
        "max_depth": 6,
        "learning_rate": 0.1,
        "random_state": 42
    }
    mlflow.log_params(params)
    
    # Train model
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
    
    # Log additional artifacts
    import joblib
    import json
    
    # Save and log preprocessor
    scaler = joblib.load('models/scaler.pkl')
    mlflow.log_artifact('models/scaler.pkl', 'preprocessors')
    
    # Save and log feature names
    feature_names = list(X_train.columns) if hasattr(X_train, 'columns') else [f"feature_{i}" for i in range(X_train.shape[1])]
    with open('feature_names.json', 'w') as f:
        json.dump(feature_names, f)
    mlflow.log_artifact('feature_names.json', 'metadata')
    
    print(f"\n✓ Model and artifacts logged to S3")
    print(f"  F1-Score: {metrics['f1_score']:.4f}")
    print(f"  ROC-AUC: {metrics['roc_auc']:.4f}")
```

### 4.4 Understanding the Code

The key changes for S3 storage:

1. **Experiment artifact location:** Set when creating the experiment
2. **Automatic upload:** MLflow handles S3 upload transparently
3. **Additional artifacts:** Use `log_artifact()` for preprocessors and metadata

No changes needed to `log_model()` or `log_metrics()` calls.

### 4.5 Test and Verify

Run the training script with S3 storage:

```bash
# Ensure environment variables are loaded
source .env

# Run training
python training/scripts/run_training.py
```

Verify artifacts in S3:

```bash
# List artifacts in S3
aws s3 ls s3://$(pulumi stack output bucket_name --cwd pulumi)/mlflow-artifacts/ --recursive
```

**Predict:** How long will artifact upload take compared to local storage?

<details>
<summary>Click to verify</summary>

Artifact upload to S3 typically adds 2-5 seconds for a model file (depending on size and network speed). This is negligible compared to training time. The MLflow UI will show the S3 artifact location in the run details.

</details>

### 4.6 Checkpoint

**Self-Assessment:**
- [ ] Training completes successfully with S3 storage
- [ ] Artifacts appear in S3 bucket
- [ ] MLflow UI shows S3 artifact location
- [ ] You can list artifacts using AWS CLI

## Chapter 5: Loading Models from S3

### 5.1 What You Will Build

You will create a script that loads models from S3, demonstrating that models are accessible from any machine with AWS credentials.

### 5.2 Think First: Model Loading Performance

**Question:** Loading a model from S3 requires downloading it first. How can you optimize this for production systems that need low latency?

<details>
<summary>Click to review</summary>

**Optimization strategies:**
1. **Caching:** Download model once, cache locally, reload from cache
2. **Model size:** Use model compression techniques to reduce download time
3. **Regional deployment:** Deploy models in the same AWS region as the application
4. **Lazy loading:** Load model at startup, not per-request
5. **Model serving:** Use dedicated model serving infrastructure (e.g., AWS SageMaker)

For this lab, we will implement basic caching. Production systems typically use strategy 4 (load at startup) combined with strategy 3 (regional deployment).

</details>

### 5.3 Implementation

Create `training/scripts/load_model_from_s3.py`:

```python
import mlflow
import mlflow.sklearn
import os
import time
from training.src.config.mlflow_config import MLflowS3Config

# Load configuration
config = MLflowS3Config()
mlflow.set_tracking_uri(config.tracking_uri)

def load_model_with_timing(model_name: str, stage: str):
    """Load model from S3 and measure time."""
    model_uri = f"models:/{model_name}/{stage}"
    
    print(f"Loading model: {model_name} (stage: {stage})")
    print(f"Model URI: {model_uri}")
    
    start_time = time.time()
    model = mlflow.sklearn.load_model(model_uri)
    load_time = time.time() - start_time
    
    print(f"✓ Model loaded in {load_time:.2f} seconds")
    return model

# Load model from S3
model = load_model_with_timing("card_approval_s3", "None")

# Test prediction
import numpy as np
X_test = np.load('data/processed/X_test.npy')

print("\nTesting predictions...")
predictions = model.predict(X_test[:5])
probabilities = model.predict_proba(X_test[:5])

print("\nSample Predictions:")
for i, (pred, proba) in enumerate(zip(predictions, probabilities)):
    decision = "APPROVED" if pred == 1 else "REJECTED"
    confidence = proba[1] if pred == 1 else proba[0]
    print(f"  Sample {i+1}: {decision} (confidence: {confidence:.2%})")

# Demonstrate caching benefit
print("\n" + "="*50)
print("Loading model again (should be faster due to caching)...")
model2 = load_model_with_timing("card_approval_s3", "None")
```

### 5.4 Understanding the Code

MLflow caches downloaded models in `~/.mlflow/` by default. Subsequent loads of the same model version use the cached copy, avoiding repeated S3 downloads.

### 5.5 Test and Verify

Run the model loading script:

```bash
source .env
python training/scripts/load_model_from_s3.py
```

**Predict:** Will the second load be faster than the first?

<details>
<summary>Click to verify</summary>

Yes, the second load should be significantly faster (often 10-100x) because MLflow uses the cached model. The first load downloads from S3, while the second load reads from local cache. This demonstrates why production systems load models at startup rather than per-request.

</details>

### 5.6 Checkpoint

**Self-Assessment:**
- [ ] Model loads successfully from S3
- [ ] Predictions work correctly
- [ ] Second load is faster due to caching
- [ ] You understand model caching behavior

## Epilogue: The Complete System

You have built a cloud-native ML infrastructure:

| Component | Capability |
|-----------|------------|
| Pulumi IaC | Reproducible infrastructure deployment |
| S3 Bucket | Versioned, encrypted artifact storage |
| MLflow + S3 | Cloud-based experiment tracking |
| Model Registry | S3-backed model lifecycle management |
| Model Loading | Cached loading from S3 |

Verify the complete workflow:

```bash
# Deploy infrastructure
cd pulumi && pulumi up && cd ..

# Configure environment
source .env

# Train with S3 storage
python training/scripts/run_training.py

# Load from S3
python training/scripts/load_model_from_s3.py

# Verify in S3
aws s3 ls s3://$(pulumi stack output bucket_name --cwd pulumi)/mlflow-artifacts/ --recursive
```

## The Principles

1. **Infrastructure as Code is essential** — Manual infrastructure is not reproducible or scalable
2. **Version everything** — Enable S3 versioning for automatic artifact history
3. **Security by default** — Block public access and enable encryption from the start
4. **Cloud storage enables collaboration** — Team members access the same artifacts
5. **Cache for performance** — MLflow caching makes S3 loading practical for production

## Troubleshooting

### Error: Access Denied to S3 bucket

**Cause:** AWS credentials lack S3 permissions.

**Solution:**
```bash
# Verify AWS identity
aws sts get-caller-identity

# Check S3 access
aws s3 ls s3://your-bucket-name

# If access denied, add S3 permissions to your IAM user/role
```

### Error: Bucket does not exist

**Cause:** Pulumi deployment failed or bucket name is incorrect.

**Solution:**
```bash
# Verify Pulumi deployment
cd pulumi
pulumi stack output bucket_name

# If empty, redeploy
pulumi up
```

### Error: MLflow cannot write to S3

**Cause:** MLflow server does not have AWS credentials.

**Solution:**
```bash
# Set environment variables before starting MLflow server
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_REGION=us-east-1

mlflow server --backend-store-uri sqlite:///mlflow.db \
  --default-artifact-root s3://your-bucket/mlflow-artifacts \
  --host 0.0.0.0 --port 5000
```

## Next Steps

1. **Multiple environments:** Create separate Pulumi stacks for dev, staging, production
2. **IAM roles:** Use IAM roles instead of access keys for better security
3. **Cross-region replication:** Replicate S3 bucket for disaster recovery
4. **Cost optimization:** Implement lifecycle policies to archive old artifacts
5. **Monitoring:** Add CloudWatch alarms for S3 access patterns

## Additional Resources

- [Pulumi Documentation](https://www.pulumi.com/docs/)
- [Pulumi AWS Provider](https://www.pulumi.com/registry/packages/aws/)
- [MLflow S3 Integration](https://mlflow.org/docs/latest/tracking.html#amazon-s3-and-s3-compatible-storage)
- [AWS S3 Best Practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/best-practices.html)
