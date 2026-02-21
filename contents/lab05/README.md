# Lab 05: CI/CD & Security (GitHub Actions)

This directory contains all the files and code needed for Lab 05.

## What's Included in This Lab

**From Lab 01:**
- Airflow and MLflow setup
- Training pipeline

**From Lab 02:**
- Pulumi Infrastructure as Code
- DVC data versioning

**From Lab 03:**
- MLflow S3 integration

**From Lab 04:**
- FastAPI prediction API
- Docker containerization

**New in Lab 05:**
- GitHub Actions CI/CD workflows
- Automated testing and linting
- Security scanning (CodeQL, Trivy)
- Automated Docker image building
- AWS App Runner deployment
- Secrets management

## Directory Structure

```
lab05/
├── dags/                           # Airflow (from Lab 01)
├── training/                       # Training (from Labs 01-03)
├── pulumi/                         # Infrastructure (from Lab 02, updated)
│   └── __main__.py                # Updated with App Runner
├── app/                           # FastAPI (from Lab 04)
├── tests/                         # Tests (from Lab 04)
├── .github/                       # NEW: GitHub Actions
│   └── workflows/
│       ├── ci.yml                 # Continuous Integration
│       └── cd.yml                 # Continuous Deployment
├── Dockerfile                     # Docker (from Lab 04)
├── .dockerignore
├── .dvc/
├── .env.example
├── .gitignore                     # NEW: Git ignore file
├── test_payload.json
├── requirements.txt
└── README.md
```

## Setup Instructions

See the lab guide: `poridhi/lab-06-cicd-security-github-actions.md`

## Quick Start

```bash
# 1. Create GitHub repository
gh repo create card-approval-prediction --public --source=. --remote=origin --push

# 2. Configure GitHub Secrets
# Go to: Settings > Secrets and variables > Actions
# Add:
#   - DOCKER_USERNAME
#   - DOCKER_PASSWORD
#   - AWS_ACCESS_KEY_ID
#   - AWS_SECRET_ACCESS_KEY
#   - PULUMI_CONFIG_PASSPHRASE

# 3. Push code to trigger CI
git add .
git commit -m "Add CI/CD workflows"
git push origin main

# 4. Create version tag to trigger CD
git tag v1.0.0
git push origin v1.0.0

# 5. Monitor workflows
# Go to repository Actions tab
```

## Workflows

### CI Workflow (ci.yml)
- Triggers: Push to main/develop, Pull requests
- Jobs:
  - Lint with flake8 and black
  - Run tests with pytest
  - Security scan with CodeQL

### CD Workflow (cd.yml)
- Triggers: Version tags (v*)
- Jobs:
  - Build and push Docker image
  - Security scan with Trivy
  - Deploy to AWS App Runner with Pulumi
