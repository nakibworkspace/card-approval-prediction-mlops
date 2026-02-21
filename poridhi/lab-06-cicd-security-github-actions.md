# Lab 05: CI/CD & Security (GitHub Actions)

## Introduction

This lab automates your deployment pipeline using GitHub Actions. Every code change will trigger automated testing, security scanning, Docker image building, and deployment to AWS App Runner. This ensures code quality and enables rapid, reliable releases.

## Learning Objectives

By the end of this lab, you will be able to:

1. Create GitHub Actions workflows for CI/CD
2. Implement security scanning with CodeQL (SAST)
3. Automate Docker image building and pushing
4. Deploy to AWS App Runner using Pulumi
5. Configure secrets management in GitHub
6. Implement automated quality gates
7. Understand continuous deployment principles

**Prerequisites:** Completion of Lab 04, GitHub account, GitHub repository for the project, AWS credentials, Docker Hub account.

## Prologue: The Challenge

Currently, deploying your API requires manual steps:
1. Run tests locally
2. Build Docker image
3. Push to Docker Hub
4. Deploy to AWS manually
5. Verify deployment

This process is error-prone and time-consuming. A teammate might forget to run tests, push an untagged image, or deploy to the wrong environment. You need automation that ensures every deployment follows the same reliable process.

GitHub Actions provides CI/CD automation that runs on every code push, ensuring consistent quality and deployment.

## Environment Setup

Prepare your GitHub repository:

```bash
# Initialize git if not already done
git init
git add .
git commit -m "Initial commit"

# Create GitHub repository and push
gh repo create card-approval-prediction --public --source=. --remote=origin --push

# Or manually create on GitHub and push
git remote add origin https://github.com/your-username/card-approval-prediction.git
git push -u origin main
```

Create workflow directory:

```bash
mkdir -p .github/workflows
```

## Chapter 1: Continuous Integration Workflow


### 1.1 What You Will Build

You will create a CI workflow that runs tests and security scans on every pull request and push to main branch.

### 1.2 Think First: CI/CD Pipeline Stages

**Question:** In what order should CI/CD stages run? Why?

<details>
<summary>Click to review</summary>

**Optimal order:**
1. **Lint/Format Check** — Fast, catches syntax errors
2. **Security Scan** — Identifies vulnerabilities early
3. **Unit Tests** — Verifies code correctness
4. **Build** — Creates artifacts (Docker image)
5. **Integration Tests** — Tests with dependencies
6. **Deploy** — Only if all previous stages pass

This order follows the "fail fast" principle: expensive operations (build, deploy) only run if cheap checks (lint, tests) pass.

</details>

### 1.3 Implementation

Create `.github/workflows/ci.yml`:

```yaml
name: Continuous Integration

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov flake8 black
    
    - name: Lint with flake8
      run: |
        flake8 app/ --count --select=E9,F63,F7,F82 --show-source --statistics
        flake8 app/ --count --max-complexity=10 --max-line-length=127 --statistics
    
    - name: Format check with black
      run: black --check app/
    
    - name: Run tests
      run: |
        pytest tests/ -v --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: false

  security-scan:
    runs-on: ubuntu-latest
    permissions:
      security-events: write
      actions: read
      contents: read
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Initialize CodeQL
      uses: github/codeql-action/init@v2
      with:
        languages: python
    
    - name: Perform CodeQL Analysis
      uses: github/codeql-action/analyze@v2
```

### 1.4 Understanding the Code

GitHub Actions workflow components:

| Component | Purpose |
|-----------|---------|
| `on:` | Defines trigger events |
| `jobs:` | Defines parallel or sequential tasks |
| `steps:` | Individual commands within a job |
| `uses:` | Reusable actions from marketplace |
| `run:` | Shell commands to execute |

### 1.5 Test and Verify

Push the workflow to GitHub:

```bash
git add .github/workflows/ci.yml
git commit -m "Add CI workflow"
git push origin main
```

**Predict:** What will happen when you push this commit?

<details>
<summary>Click to verify</summary>

GitHub Actions will automatically:
1. Detect the new workflow file
2. Trigger the workflow on push to main
3. Run lint, tests, and security scan
4. Display results in the Actions tab

Navigate to your repository's Actions tab to see the workflow running.

</details>

### 1.6 Checkpoint

**Self-Assessment:**
- [ ] CI workflow runs automatically on push
- [ ] All jobs complete successfully
- [ ] CodeQL security scan completes
- [ ] You can view workflow logs in GitHub Actions tab

## Chapter 2: Continuous Deployment Workflow

### 2.1 What You Will Build

You will create a CD workflow that builds Docker images, pushes to Docker Hub, and deploys to AWS App Runner.

### 2.2 Think First: Deployment Strategy

**Question:** Should deployment happen on every commit, or only on specific events (tags, releases)?

<details>
<summary>Click to review</summary>

**Deployment strategies:**

**Continuous Deployment (every commit):**
- Pros: Fastest feedback, smallest changes
- Cons: Higher risk, requires excellent testing

**Tag-based deployment:**
- Pros: Controlled releases, semantic versioning
- Cons: Manual tagging required

**Release-based deployment:**
- Pros: Formal release process, changelog
- Cons: Slower feedback cycle

For this lab, we will use tag-based deployment: pushing a version tag (e.g., `v1.0.0`) triggers deployment.

</details>

### 2.3 Implementation

Create `.github/workflows/cd.yml`:

```yaml
name: Continuous Deployment

on:
  push:
    tags:
      - 'v*'

env:
  DOCKER_IMAGE: ${{ secrets.DOCKER_USERNAME }}/card-approval-api
  AWS_REGION: us-east-1

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Login to Docker Hub
      uses: docker/login-action@v2
      with:
        username: ${{ secrets.DOCKER_USERNAME }}
        password: ${{ secrets.DOCKER_PASSWORD }}
    
    - name: Extract version from tag
      id: version
      run: echo "VERSION=${GITHUB_REF#refs/tags/v}" >> $GITHUB_OUTPUT
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v4
      with:
        context: .
        push: true
        tags: |
          ${{ env.DOCKER_IMAGE }}:latest
          ${{ env.DOCKER_IMAGE }}:${{ steps.version.outputs.VERSION }}
        cache-from: type=registry,ref=${{ env.DOCKER_IMAGE }}:buildcache
        cache-to: type=registry,ref=${{ env.DOCKER_IMAGE }}:buildcache,mode=max
    
    - name: Run Trivy security scan
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: ${{ env.DOCKER_IMAGE }}:${{ steps.version.outputs.VERSION }}
        format: 'sarif'
        output: 'trivy-results.sarif'
    
    - name: Upload Trivy results to GitHub Security
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: 'trivy-results.sarif'

  deploy-to-aws:
    needs: build-and-push
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ${{ env.AWS_REGION }}
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install Pulumi
      run: |
        curl -fsSL https://get.pulumi.com | sh
        echo "$HOME/.pulumi/bin" >> $GITHUB_PATH
    
    - name: Install dependencies
      run: |
        cd pulumi
        pip install -r requirements.txt
    
    - name: Deploy with Pulumi
      run: |
        cd pulumi
        pulumi login --local
        pulumi stack select production --create
        pulumi up --yes
      env:
        PULUMI_CONFIG_PASSPHRASE: ${{ secrets.PULUMI_CONFIG_PASSPHRASE }}
```

### 2.4 Understanding the Code

The CD workflow:
1. Triggers only on version tags (`v*`)
2. Builds and pushes Docker image with version tag
3. Scans image for vulnerabilities with Trivy
4. Deploys to AWS using Pulumi

### 2.5 Configure GitHub Secrets

Add secrets to your GitHub repository:

```bash
# Navigate to: Settings > Secrets and variables > Actions > New repository secret

# Add these secrets:
DOCKER_USERNAME=your-docker-username
DOCKER_PASSWORD=your-docker-password
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
PULUMI_CONFIG_PASSPHRASE=your-pulumi-passphrase
```

### 2.6 Test and Verify

Create and push a version tag:

```bash
git add .github/workflows/cd.yml
git commit -m "Add CD workflow"
git push origin main

# Create version tag
git tag v1.0.0
git push origin v1.0.0
```

**Predict:** What will happen when you push the tag?

<details>
<summary>Click to verify</summary>

The CD workflow will:
1. Build Docker image with tags `latest` and `1.0.0`
2. Push to Docker Hub
3. Scan image for vulnerabilities
4. Deploy to AWS App Runner using Pulumi
5. Provide deployment URL in workflow logs

Check the Actions tab to monitor progress.

</details>

### 2.7 Checkpoint

**Self-Assessment:**
- [ ] CD workflow triggers on version tags
- [ ] Docker image builds and pushes successfully
- [ ] Trivy security scan completes
- [ ] Pulumi deployment succeeds
- [ ] Application is accessible at AWS App Runner URL

## Chapter 3: AWS App Runner Deployment

### 3.1 What You Will Build

You will update your Pulumi code to deploy the Docker image to AWS App Runner.

### 3.2 Implementation

Update `pulumi/__main__.py`:

```python
import pulumi
import pulumi_aws as aws

# Configuration
config = pulumi.Config()
project_name = pulumi.get_project()
stack_name = pulumi.get_stack()

# S3 bucket (from Lab 03)
bucket = aws.s3.Bucket(
    "ml-artifacts-bucket",
    bucket=f"{project_name}-{stack_name}-ml-artifacts",
    versioning=aws.s3.BucketVersioningArgs(enabled=True),
)

# IAM role for App Runner
app_runner_role = aws.iam.Role(
    "app-runner-role",
    assume_role_policy="""{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "tasks.apprunner.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }"""
)

# Attach S3 read policy
s3_policy = aws.iam.RolePolicy(
    "app-runner-s3-policy",
    role=app_runner_role.id,
    policy=pulumi.Output.all(bucket.arn).apply(
        lambda args: f"""{{
            "Version": "2012-10-17",
            "Statement": [{{
                "Effect": "Allow",
                "Action": ["s3:GetObject", "s3:ListBucket"],
                "Resource": ["{args[0]}", "{args[0]}/*"]
            }}]
        }}"""
    )
)

# App Runner service
docker_image = config.get("docker_image") or "your-username/card-approval-api:latest"

app_runner_service = aws.apprunner.Service(
    "card-approval-api",
    service_name=f"{project_name}-{stack_name}-api",
    source_configuration=aws.apprunner.ServiceSourceConfigurationArgs(
        image_repository=aws.apprunner.ServiceSourceConfigurationImageRepositoryArgs(
            image_identifier=docker_image,
            image_repository_type="ECR_PUBLIC",
            image_configuration=aws.apprunner.ServiceSourceConfigurationImageRepositoryImageConfigurationArgs(
                port="8000",
                runtime_environment_variables={
                    "MLFLOW_TRACKING_URI": config.get("mlflow_tracking_uri") or "http://localhost:5000",
                    "MODEL_NAME": "card_approval_production",
                    "MODEL_STAGE": "Production",
                    "AWS_REGION": "us-east-1",
                },
            ),
        ),
        auto_deployments_enabled=True,
    ),
    instance_configuration=aws.apprunner.ServiceInstanceConfigurationArgs(
        cpu="1024",
        memory="2048",
        instance_role_arn=app_runner_role.arn,
    ),
)

# Export outputs
pulumi.export("bucket_name", bucket.id)
pulumi.export("bucket_arn", bucket.arn)
pulumi.export("api_url", app_runner_service.service_url)
pulumi.export("app_runner_service_arn", app_runner_service.arn)
```

### 3.3 Checkpoint

**Self-Assessment:**
- [ ] Pulumi code includes App Runner service
- [ ] IAM role has S3 access permissions
- [ ] Environment variables are configured
- [ ] API URL is exported

## Epilogue: The Complete System

You have built a complete CI/CD pipeline:

| Component | Capability |
|-----------|------------|
| GitHub Actions | Automated workflows |
| CodeQL | Security scanning (SAST) |
| Trivy | Container vulnerability scanning |
| Docker Hub | Image registry |
| Pulumi | Infrastructure deployment |
| AWS App Runner | Serverless container hosting |

## The Principles

1. **Automate everything** — Manual processes are error-prone
2. **Fail fast** — Run cheap checks before expensive operations
3. **Security by default** — Scan code and containers automatically
4. **Version everything** — Use semantic versioning for releases
5. **Infrastructure as Code** — Deploy infrastructure with code, not clicks

## Troubleshooting

### Error: Docker push unauthorized

**Solution:** Verify Docker Hub credentials in GitHub secrets.

### Error: AWS credentials invalid

**Solution:** Check AWS access keys have correct permissions.

### Error: Pulumi deployment fails

**Solution:** Verify Pulumi passphrase is set correctly.

## Next Steps

1. Add automated rollback on deployment failure
2. Implement blue-green deployment
3. Add smoke tests after deployment
4. Configure deployment notifications (Slack, email)
5. Add deployment approval gates

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [CodeQL Documentation](https://codeql.github.com/docs/)
- [AWS App Runner Documentation](https://docs.aws.amazon.com/apprunner/)
- [Pulumi AWS Guide](https://www.pulumi.com/docs/clouds/aws/)
