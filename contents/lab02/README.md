# Lab 02: Data Versioning with DVC & S3

This directory contains all the files and code needed for Lab 02.

## What's Included in This Lab

**From Lab 01:**
- Airflow setup and DAG definitions
- MLflow tracking configuration
- Training pipeline (EDA, preprocessing, model training)

**New in Lab 02:**
- Pulumi Infrastructure as Code (S3 bucket creation)
- DVC data versioning setup
- S3 remote storage configuration
- Data versioning workflow

## Directory Structure

```
lab02/
├── dags/                           # Airflow DAG definitions (from Lab 01)
├── training/                       # Training code and data (from Lab 01)
│   ├── data/
│   │   ├── raw/                   # Raw dataset (DVC tracked)
│   │   └── processed/             # Processed data (DVC tracked)
│   ├── scripts/
│   ├── src/
│   └── models/                    # Trained models (DVC tracked)
├── pulumi/                         # NEW: Infrastructure as Code
│   ├── __main__.py                # Pulumi infrastructure definition
│   ├── Pulumi.yaml                # Pulumi project configuration
│   ├── Pulumi.dev.yaml            # Dev stack configuration
│   └── requirements.txt           # Pulumi dependencies
├── .dvc/                          # NEW: DVC configuration
├── .dvcignore                     # NEW: DVC ignore file
├── logs/
├── plugins/
├── requirements.txt               # Updated with DVC and Pulumi
└── README.md
```

## Setup Instructions

See the lab guide: `poridhi/lab-02-infrastructure-as-code-pulumi-s3.md` and `poridhi/lab-03-data-versioning-dvc-s3.md`

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Install Pulumi CLI
curl -fsSL https://get.pulumi.com | sh
export PATH=$PATH:$HOME/.pulumi/bin

# 3. Configure AWS
aws configure

# 4. Deploy infrastructure
cd pulumi
pulumi up
cd ..

# 5. Initialize DVC
dvc init

# 6. Configure DVC remote
export DVC_S3_BUCKET=$(cd pulumi && pulumi stack output data_bucket_name && cd ..)
dvc remote add -d s3storage s3://$DVC_S3_BUCKET/dvc-storage
dvc remote modify s3storage region us-east-1

# 7. Track data with DVC
dvc add training/data/raw
dvc add training/data/processed
dvc add training/models

# 8. Push to S3
dvc push
```
