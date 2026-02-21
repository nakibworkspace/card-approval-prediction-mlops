# Lab 02: Data Versioning with DVC & S3

## Introduction

This lab establishes cloud-based data versioning using DVC (Data Version Control) and AWS S3. You will use Pulumi to create cloud infrastructure, initialize DVC for dataset versioning, and push your data to S3. This prevents "I lost the data" disasters and enables team collaboration.

## Learning Objectives

By the end of this lab, you will be able to:

1. Install and configure Pulumi for AWS infrastructure management
2. Define cloud resources using Python code (Infrastructure as Code)
3. Create and configure S3 buckets with appropriate permissions
4. Initialize DVC for data version control
5. Configure DVC to use S3 as remote storage
6. Version control datasets with DVC
7. Push and pull data from cloud storage
8. Understand the benefits of data versioning for ML projects

**Prerequisites:** Completion of Lab 01, AWS account with billing enabled, AWS CLI installed and configured, basic understanding of version control (Git).

**Estimated Time:** 2-3 hours

## Prologue: The Challenge

Your ML models depend on training data stored on your laptop. When a teammate asks "Can I reproduce your results?", you email them a 2GB CSV file. When you accidentally delete the processed data, you lose hours of preprocessing work. When the data changes, nobody knows which model was trained on which version.

You need cloud storage that:
- Versions datasets automatically (like Git for data)
- Is accessible from anywhere
- Integrates with your ML workflow
- Prevents data loss disasters

DVC provides Git-like versioning for data, while S3 provides durable cloud storage. Pulumi ensures your infrastructure is reproducible.

## Environment Setup

Install required tools:

```bash
# Activate virtual environment
source venv/bin/activate

# Install Pulumi and DVC
pip install pulumi pulumi-aws dvc[s3] boto3

# Install Pulumi CLI
curl -fsSL https://get.pulumi.com | sh
export PATH=$PATH:$HOME/.pulumi/bin

# Verify installations
pulumi version
dvc version
aws --version
```

Configure AWS credentials:

```bash
# Configure AWS CLI (if not already done)
aws configure

# Verify AWS access
aws sts get-caller-identity
```

## Chapter 1: Infrastructure as Code with Pulumi

### 1.1 What You Will Build

You will use Pulumi to create an S3 bucket for data storage, defining infrastructure as Python code for reproducibility.

### 1.2 Think First: Manual vs Automated Infrastructure

**Question:** Compare two approaches:
- Approach A: Click through AWS Console to create S3 bucket
- Approach B: Write Python code that creates the bucket automatically

What are the advantages of each?

<details>
<summary>Click to review</summary>

**Manual (AWS Console):**
- Pros: Visual, immediate feedback, no coding
- Cons: Not reproducible, no version control, error-prone, difficult to replicate

**Infrastructure as Code (Pulumi):**
- Pros: Reproducible, version controlled, automated, consistent across environments
- Cons: Initial learning curve, requires coding knowledge

For production ML systems, IaC is essential. It ensures dev, staging, and production environments are identical, and infrastructure changes are reviewed like code.

</details>

### 1.3 Implementation

Create Pulumi project:

```bash
# Create pulumi directory
mkdir -p pulumi
cd pulumi

# Initialize Pulumi project
pulumi new aws-python \
  --name card-approval-infra \
  --description "ML infrastructure for card approval prediction"

# When prompted:
# - Project name: card-approval-infra
# - Stack name: dev
# - AWS region: us-east-1 (or your preferred region)
```

Update `pulumi/__main__.py`:

```python
import pulumi
import pulumi_aws as aws

# Configuration
config = pulumi.Config()
project_name = pulumi.get_project()
stack_name = pulumi.get_stack()

# Create S3 bucket for data versioning
data_bucket = aws.s3.Bucket(
    "ml-data-bucket",
    bucket=f"{project_name}-{stack_name}-ml-data",
    versioning=aws.s3.BucketVersioningArgs(
        enabled=True,  # Enable versioning for data history
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

# Export bucket name and region
pulumi.export("data_bucket_name", data_bucket.id)
pulumi.export("data_bucket_arn", data_bucket.arn)
pulumi.export("aws_region", config.require("aws:region"))
```

### 1.4 Understanding the Code

Pulumi infrastructure components:

| Component | Purpose |
|-----------|---------|
| Bucket versioning | Keeps history of all data versions |
| Public access block | Prevents accidental public exposure |
| Server-side encryption | Protects data at rest |
| Tags | Organizes resources and tracks costs |

### 1.5 Test and Verify

Deploy the infrastructure:

```bash
# Preview changes
pulumi preview

# Deploy (creates S3 bucket)
pulumi up

# When prompted, select "yes"
```

**Predict:** What resources will be created?

<details>
<summary>Click to verify</summary>

Pulumi will create 3 resources:
1. S3 bucket with versioning enabled
2. Public access block configuration
3. Server-side encryption configuration

The output shows the bucket name and ARN. Verify in AWS Console that the bucket exists.

</details>

### 1.6 Checkpoint

**Self-Assessment:**
- [ ] Pulumi deployment completes successfully
- [ ] S3 bucket visible in AWS Console
- [ ] Bucket has versioning enabled
- [ ] You can retrieve bucket name: `pulumi stack output data_bucket_name`

## Chapter 2: DVC Initialization

### 2.1 What You Will Build

You will initialize DVC in your project to track datasets with Git-like versioning.

### 2.2 Think First: Git vs DVC

**Question:** Why not just use Git to version control your datasets?

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
- Supports cloud storage (S3, GCS, Azure)

DVC tracks data versions using small `.dvc` files in Git, while actual data lives in S3.

</details>

### 2.3 Implementation

Initialize DVC:

```bash
# Navigate to project root
cd ..  # Back to card-approval-prediction/

# Initialize DVC
dvc init

# Verify DVC initialization
ls -la .dvc/
```

This creates:
- `.dvc/` directory with DVC configuration
- `.dvcignore` file (like `.gitignore` for DVC)
- `.dvc/config` file for remote storage configuration

### 2.4 Understanding DVC Structure

```
.dvc/
├── config          # DVC configuration (remotes, cache)
├── .gitignore      # Ignores cache directory
└── cache/          # Local cache of data files
```

### 2.5 Checkpoint

**Self-Assessment:**
- [ ] DVC initialized successfully
- [ ] `.dvc/` directory exists
- [ ] You understand DVC vs Git differences

## Chapter 3: Configuring DVC Remote Storage

### 3.1 What You Will Build

You will configure DVC to use your S3 bucket as remote storage for datasets.

### 3.2 Implementation

Get bucket name from Pulumi:

```bash
cd pulumi
export DVC_S3_BUCKET=$(pulumi stack output data_bucket_name)
export AWS_REGION=$(pulumi stack output aws_region)
cd ..

echo "Bucket: $DVC_S3_BUCKET"
echo "Region: $AWS_REGION"
```

Configure DVC remote:

```bash
# Add S3 as DVC remote storage
dvc remote add -d s3storage s3://$DVC_S3_BUCKET/dvc-storage

# Configure AWS region
dvc remote modify s3storage region $AWS_REGION

# Verify configuration
dvc remote list
cat .dvc/config
```

The `.dvc/config` file should now contain:

```ini
[core]
    remote = s3storage
['remote "s3storage"']
    url = s3://your-bucket-name/dvc-storage
    region = us-east-1
```

### 3.3 Understanding the Configuration

| Setting | Purpose |
|---------|---------|
| `remote add -d` | Adds remote and sets as default |
| `s3://bucket/path` | S3 location for data storage |
| `region` | AWS region for S3 bucket |

### 3.4 Checkpoint

**Self-Assessment:**
- [ ] DVC remote configured successfully
- [ ] `.dvc/config` contains S3 remote
- [ ] You can list remotes: `dvc remote list`

## Chapter 4: Tracking Data with DVC

### 4.1 What You Will Build

You will add your datasets to DVC tracking and push them to S3.

### 4.2 Think First: What to Track

**Question:** Which files should be tracked with DVC vs Git?

<details>
<summary>Click to review</summary>

**Track with DVC:**
- Raw datasets (CSV, Parquet, images)
- Processed datasets
- Trained models (large binary files)
- Feature engineering artifacts
- Any file >10MB

**Track with Git:**
- Code (Python scripts, notebooks)
- Configuration files
- DVC metadata files (`.dvc` files)
- Documentation
- Small reference files

Rule of thumb: Code and metadata in Git, data and models in DVC.

</details>

### 4.3 Implementation

Add raw data to DVC:

```bash
# Add raw data directory to DVC tracking
dvc add training/data/raw

# This creates training/data/raw.dvc file
ls -la training/data/

# Add processed data
dvc add training/data/processed

# Add trained models
dvc add models/
```

What happened:
1. DVC computed MD5 hash of data
2. Created `.dvc` metadata files
3. Added data to `.gitignore` (data not tracked by Git)
4. Data files moved to DVC cache

### 4.4 Understanding DVC Files

Example `training/data/raw.dvc`:

```yaml
outs:
- md5: a1b2c3d4e5f6g7h8i9j0
  size: 52428800
  path: raw
```

This small file (tracked by Git) contains:
- MD5 hash of data (for integrity)
- Size in bytes
- Path to data directory

### 4.5 Commit DVC metadata to Git

```bash
# Add DVC files to Git
git add training/data/raw.dvc training/data/processed.dvc models.dvc .gitignore

# Commit
git commit -m "Add data and models to DVC tracking"
```

### 4.6 Checkpoint

**Self-Assessment:**
- [ ] Data directories tracked by DVC
- [ ] `.dvc` files created
- [ ] Data added to `.gitignore`
- [ ] DVC metadata committed to Git

## Chapter 5: Pushing Data to S3

### 5.1 What You Will Build

You will push your versioned data to S3 for cloud backup and team access.

### 5.2 Implementation

Push data to S3:

```bash
# Push all DVC-tracked data to S3
dvc push

# This uploads:
# - training/data/raw/
# - training/data/processed/
# - models/
```

**Predict:** How long will the push take?

<details>
<summary>Click to verify</summary>

Push time depends on:
- Data size (typically 100MB-2GB for this project)
- Network speed
- AWS region proximity

First push takes longest (uploads everything). Subsequent pushes are incremental (only changed files).

</details>

Verify data in S3:

```bash
# List files in S3
aws s3 ls s3://$DVC_S3_BUCKET/dvc-storage/ --recursive

# Check bucket size
aws s3 ls s3://$DVC_S3_BUCKET --recursive --summarize
```

### 5.3 Checkpoint

**Self-Assessment:**
- [ ] `dvc push` completes successfully
- [ ] Data visible in S3 bucket
- [ ] You can list S3 contents with AWS CLI

## Chapter 6: Pulling Data from S3

### 6.1 What You Will Build

You will simulate a teammate pulling your data from S3 to reproduce your work.

### 6.2 Implementation

Simulate fresh clone:

```bash
# Remove local data (simulate teammate's machine)
rm -rf training/data/raw training/data/processed models/

# Verify data is gone
ls training/data/

# Pull data from S3
dvc pull

# Verify data restored
ls training/data/raw
ls training/data/processed
ls models/
```

**Observe:** DVC downloads data from S3 and restores it exactly as it was.

### 6.3 Understanding DVC Workflow

```
Developer A                    S3 Remote                    Developer B
-----------                    ---------                    -----------
dvc add data/          -->                                  
git commit .dvc files  -->                                  
dvc push               -->     Upload data      -->         
git push               -->                                  
                                                  <--        git pull
                                                  <--        dvc pull
                                                             (data restored)
```

### 6.4 Checkpoint

**Self-Assessment:**
- [ ] Data removed successfully
- [ ] `dvc pull` restores data from S3
- [ ] You understand DVC workflow for team collaboration

## Chapter 7: Data Versioning in Practice

### 7.1 Experiment: Updating Data

Simulate data update:

```bash
# Modify processed data (simulate reprocessing)
python training/scripts/run_preprocessing.py

# Check DVC status
dvc status

# DVC detects changes
# Output: training/data/processed.dvc:
#   changed outs:
#     modified: training/data/processed

# Add updated data
dvc add training/data/processed

# Commit new version
git add training/data/processed.dvc
git commit -m "Update processed data with new preprocessing"

# Push new version to S3
dvc push
```

### 7.2 Experiment: Switching Versions

```bash
# View Git history
git log --oneline training/data/processed.dvc

# Checkout previous version
git checkout HEAD~1 training/data/processed.dvc

# Pull old data version
dvc checkout

# Verify old data restored
ls training/data/processed/

# Return to latest version
git checkout main training/data/processed.dvc
dvc checkout
```

**Observe:** DVC enables time-travel for datasets, just like Git for code.

### 7.3 Checkpoint

**Self-Assessment:**
- [ ] You can update and version data
- [ ] You can switch between data versions
- [ ] You understand DVC + Git workflow

## Epilogue: The Complete System

You have built cloud-based data versioning:

| Component | Capability |
|-----------|------------|
| Pulumi IaC | Reproducible S3 bucket creation |
| S3 Bucket | Durable cloud storage with versioning |
| DVC | Git-like versioning for datasets |
| DVC Remote | S3-backed data storage |
| Version Control | Time-travel for datasets |

Verify the complete workflow:

```bash
# Infrastructure
cd pulumi && pulumi stack output && cd ..

# DVC status
dvc status
dvc remote list

# Data in S3
aws s3 ls s3://$DVC_S3_BUCKET/dvc-storage/ --recursive

# Git + DVC workflow
git log --oneline -- '*.dvc'
```

## The Principles

1. **Infrastructure as Code is essential** — Manual infrastructure is not reproducible
2. **Version data like code** — DVC provides Git-like versioning for datasets
3. **Separate data from code** — Large files don't belong in Git
4. **Cloud storage enables collaboration** — Team members access the same data
5. **Track metadata in Git** — `.dvc` files are small and belong in version control
6. **Push early, push often** — Regular `dvc push` prevents data loss

## Troubleshooting

### Error: AWS credentials not found

**Solution:**
```bash
# Configure AWS CLI
aws configure

# Verify
aws sts get-caller-identity
```

### Error: DVC push fails with access denied

**Solution:**
```bash
# Verify S3 bucket permissions
aws s3 ls s3://$DVC_S3_BUCKET

# Check IAM permissions include:
# - s3:PutObject
# - s3:GetObject
# - s3:ListBucket
```

### Error: Pulumi deployment fails

**Solution:**
```bash
# Check Pulumi state
pulumi stack

# Retry deployment
pulumi up

# If persistent, destroy and recreate
pulumi destroy
pulumi up
```

### Error: DVC remote not configured

**Solution:**
```bash
# List remotes
dvc remote list

# If empty, reconfigure
dvc remote add -d s3storage s3://your-bucket/dvc-storage
dvc remote modify s3storage region us-east-1
```

## Next Steps

1. **Automate data updates:** Create scripts to automatically version new data
2. **Data pipelines:** Use DVC pipelines to track data transformations
3. **Multiple remotes:** Configure separate remotes for different environments
4. **Data registry:** Implement data catalog for dataset discovery
5. **CI/CD integration:** Automate `dvc pull` in deployment pipelines

## Additional Resources

- [DVC Documentation](https://dvc.org/doc)
- [DVC with S3](https://dvc.org/doc/user-guide/data-management/remote-storage/amazon-s3)
- [Pulumi Documentation](https://www.pulumi.com/docs/)
- [Pulumi AWS Provider](https://www.pulumi.com/registry/packages/aws/)
- [AWS S3 Best Practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/best-practices.html)
- [Data Versioning for ML](https://dvc.org/doc/use-cases/versioning-data-and-model-files)
