# Poridhi MLOps Labs - Card Approval Prediction

## Overview

This documentation series guides you through building a production-grade MLOps system for credit card approval prediction. The labs progress from data science fundamentals to full cloud deployment with monitoring.

**Project Deadline:** Monday, February 23, 2026

## Lab Structure

Each lab builds on the previous one, creating a complete MLOps pipeline:

### [Lab 01: Automated ML Pipeline with Airflow & MLflow](./lab-01-model-development-mlflow-tracking.md)
**Focus:** Automated ML Orchestration

Build a production-grade automated ML pipeline where Airflow orchestrates everything (EDA, preprocessing, training) and MLflow tracks all experiments. No manual script execution.

**Key Topics:**
- Apache Airflow setup and DAG creation
- MLflow tracking integration within Airflow tasks
- Automated EDA, preprocessing, and training through Airflow
- Class imbalance handling with SMOTE in automated pipelines
- Multiple model training and comparison
- Model Registry and automated promotion
- Scheduling and monitoring pipeline execution

**Deliverable:** Fully automated ML pipeline with Airflow orchestration and MLflow tracking

---

### [Lab 02: Infrastructure as Code (Pulumi) & S3](./lab-02-infrastructure-as-code-pulumi-s3.md)
**Focus:** Cloud Storage Foundation

Replace local storage with professional AWS infrastructure defined as code.

**Key Topics:**
- Pulumi for Infrastructure as Code
- S3 bucket creation and configuration
- MLflow integration with S3
- Cloud-native artifact storage

**Deliverable:** Cloud-hosted models in S3 with versioning and encryption

---

### [Lab 03: Data Versioning with DVC](./lab-03-data-versioning-dvc-s3.md)
**Focus:** Data Version Control

Version your datasets in the cloud using DVC with S3 backend, preventing "I lost the data" disasters.

**Key Topics:**
- DVC initialization and configuration
- S3 remote storage setup
- Data tracking and versioning
- Pushing and pulling data from cloud
- Collaboration with versioned datasets

**Deliverable:** Cloud-versioned datasets with DVC tracking

---

### [Lab 04: MLflow + S3 Integration](./lab-04-mlflow-s3-integration.md)
**Focus:** Cloud-Native Experiment Tracking

Integrate MLflow with S3 for cloud-based artifact storage, enabling team collaboration and scalability.

**Key Topics:**
- MLflow S3 backend configuration
- Cloud artifact storage
- Model versioning in S3
- Loading models from cloud storage

**Deliverable:** MLflow experiments and models stored in S3

---

### [Lab 05: The Prediction API (FastAPI) & Docker Hub](./lab-05-prediction-api-fastapi-docker.md)
**Focus:** Model as a Service

Turn the model into a production API that other applications can consume.

**Key Topics:**
- FastAPI application development
- Model loading from S3
- Input validation with Pydantic
- Docker containerization
- Docker Hub deployment

**Deliverable:** Containerized API ready for deployment

---

### [Lab 06: CI/CD & Security (GitHub Actions)](./lab-06-cicd-security-github-actions.md)
**Focus:** Automated Deployment

Automate quality checks and deployment with every code change.

**Key Topics:**
- GitHub Actions workflows
- CodeQL security scanning (SAST)
- Automated Docker build and push
- AWS App Runner deployment with Pulumi
- Continuous deployment pipeline

**Deliverable:** Live production API with automated updates

---

### [Lab 07: Observability (Prometheus & Grafana)](./lab-07-observability-prometheus-grafana.md)
**Focus:** Production Monitoring

Watch the model in production and detect issues before users do.

**Key Topics:**
- Prometheus metrics collection
- Grafana dashboard creation
- System health monitoring
- Model performance tracking
- Data drift detection with Evidently AI

**Deliverable:** Professional monitoring dashboard

---

## Learning Path

```
Lab 01: Automated ML Pipeline (Airflow + MLflow)
    ↓
Lab 02: Cloud Infrastructure (Pulumi + S3)
    ↓
Lab 03: Data Versioning (DVC)
    ↓
Lab 04: MLflow + S3 Integration
    ↓
Lab 05: API Development (FastAPI + Docker)
    ↓
Lab 06: CI/CD Pipeline (GitHub Actions)
    ↓
Lab 07: Monitoring (Prometheus + Grafana)
```

## Prerequisites

### Required Knowledge
- Python programming (intermediate level)
- Basic machine learning concepts
- Command line proficiency
- Git version control

### Required Tools
- Python 3.11+
- AWS Account (with billing enabled)
- Docker Desktop
- Git
- Code editor (VS Code recommended)

### Recommended Background
- REST API concepts
- Basic cloud computing knowledge
- Understanding of DevOps principles

## Getting Started

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/card-approval-prediction.git
   cd card-approval-prediction
   ```

2. **Start with Lab 01:**
   - Read the lab documentation thoroughly
   - Complete each chapter in sequence
   - Test your work at each checkpoint
   - Complete self-assessments before moving forward

3. **Follow the active learning approach:**
   - Predict outcomes before running code
   - Complete fill-in-the-blank exercises
   - Experiment with deliberate failures
   - Answer conceptual questions

## Lab Standards

All labs follow the Poridhi standards for technical education:

- **Active Learning:** 70% active exercises, 30% passive reading
- **Think First:** Predict outcomes before seeing results
- **Checkpoints:** Self-assessment at each chapter
- **Experiments:** Deliberate failures to understand why patterns matter
- **Professional Tone:** Technical, precise, no emojis or clichés

## Testing Approach

Each lab includes:

1. **Local Testing:** Test components locally before cloud deployment
2. **Integration Testing:** Verify components work together
3. **End-to-End Testing:** Test complete workflows
4. **Troubleshooting:** Common errors and solutions

## Project Structure

```
card-approval-prediction/
├── training/              # ML training pipeline (Labs 01-03)
│   ├── data/             # Datasets (DVC tracked)
│   ├── scripts/          # Training automation
│   ├── src/              # Training source code
│   └── notebooks/        # Jupyter notebooks
├── app/                  # FastAPI application (Lab 04)
│   ├── routers/          # API endpoints
│   ├── services/         # Business logic
│   └── schemas/          # Pydantic models
├── pulumi/               # Infrastructure as Code (Lab 03, 05)
├── .github/workflows/    # CI/CD pipelines (Lab 05)
├── monitoring/           # Prometheus & Grafana (Lab 06)
└── tests/                # Unit and integration tests
```

## Support and Resources

### Documentation
- Each lab includes comprehensive troubleshooting sections
- Additional resources linked at the end of each lab
- Architecture diagrams in the main README

### Common Issues
- Check the Troubleshooting section in each lab
- Verify prerequisites are installed correctly
- Ensure AWS credentials are configured
- Check environment variables are set

### Best Practices
- Complete labs in order (each builds on previous)
- Don't skip checkpoints or self-assessments
- Test locally before deploying to cloud
- Keep notes on what you learn

## Timeline

| Lab | Estimated Time | Deadline |
|-----|----------------|----------|
| Lab 01 | 6-8 hours | Day 1-2 |
| Lab 02 | 2-3 hours | Day 3 |
| Lab 03 | 2-3 hours | Day 3 |
| Lab 04 | 2-3 hours | Day 4 |
| Lab 05 | 3-4 hours | Day 5 |
| Lab 06 | 2-3 hours | Day 6 |
| Lab 07 | 3-4 hours | Day 7 |

**Total:** 22-30 hours over 7 days

## Success Criteria

By completing all labs, you will have:

- ✅ Built automated ML pipeline with Airflow orchestration
- ✅ Integrated MLflow tracking within Airflow tasks
- ✅ Deployed infrastructure as code with Pulumi
- ✅ Versioned datasets with DVC and S3
- ✅ Configured MLflow with S3 artifact storage
- ✅ Built a production FastAPI service
- ✅ Containerized the application with Docker
- ✅ Implemented CI/CD with GitHub Actions
- ✅ Deployed to AWS App Runner
- ✅ Set up comprehensive monitoring with Prometheus and Grafana

## Next Steps After Completion

1. **Extend the system:**
   - Add A/B testing for model versions
   - Implement automated retraining
   - Add feature store integration

2. **Improve monitoring:**
   - Add alerting rules
   - Implement log aggregation
   - Create custom dashboards

3. **Enhance security:**
   - Implement API authentication
   - Add rate limiting
   - Set up AWS WAF

4. **Scale the system:**
   - Add load balancing
   - Implement caching
   - Optimize model serving

## Contributing

Found an issue or have a suggestion? Please open an issue in the repository.

## License

This documentation is part of the Card Approval Prediction MLOps project, licensed under MIT License.

---

**Ready to start?** Begin with [Lab 01: Automated ML Pipeline with Airflow & MLflow](./lab-01-model-development-mlflow-tracking.md)
