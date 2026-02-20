## 1. Card Approval Prediction

Deadline: Monday (23.02.2026)

### Lab 01: Exploration & The "Winning" Model

**Focus:** The Data Science core.

- **Goal:** Understand the "Card Approval" dataset and find the best algorithm.
- **Tasks:**
    - Perform EDA (Exploratory Data Analysis) in a Jupyter Notebook.
    - Handle class imbalance (common in credit cards).
    - Train a baseline model (Logistic Regression) vs. a high-performer (XGBoost/RandomForest).
- **Result:** A saved `.pkl` or `.joblib` file and a clear understanding of your features.

### Lab 02: Experiment Tracking with MLflow

**Focus:** Moving from "messy notebooks" to organized experiments.

- **Goal:** Instead of just saving one model, track *every* attempt.
- **Tasks:**
    - Wrap your Lab 1 code with **MLflow** tracking.
    - Log parameters (e.g., `n_estimators`, `max_depth`) and metrics (F1-Score, ROC-AUC).
    - Compare versions in the MLflow UI.
- **Result:** An MLflow Model Registry where you can "promote" the best model to a "Production" stage.

### Lab 03: Infrastructure as Code (Pulumi) & S3

**Focus:** Building the cloud storage for your models and data.

- **Goal:** Replace your local hard drive with a professional AWS Data Lake.
- **Tasks:**
    - Use **Pulumi** to create an S3 bucket.
    - Update your MLflow configuration to use S3 as the "Artifact Store."
    - Upload your "Production" model from Lab 2 to this S3 bucket.
- **Result:** Your model is now "cloud-native"—it lives in AWS, not on your laptop.

### Lab 04: The Prediction API (FastAPI) & Docker Hub

**Focus:** Turning the model into a product.

- **Goal:** Create a service that other apps (like a bank's website) can call.
- **Tasks:**
    - Write a **FastAPI** wrapper that loads the model from S3 and predicts.
    - Create a `Dockerfile` for this API.
    - Push the image to **Docker Hub** (bypassing the ECR permission issue).
- **Result:** A containerized model ready to be deployed anywhere in the world.

### Lab 05: CI/CD & Security (GitHub Actions)

**Focus:** Automating the "Sonar" quality and the deployment.

- **Goal:** Every time you improve the model code, the API updates automatically.
- **Tasks:**
    - Set up **GitHub Actions** with **CodeQL** (the SAST tool replacing SonarQube).
    - Automate the Docker build-and-push to Docker Hub.
    - Use Pulumi within the Action to deploy/update **AWS App Runner**.
- **Result:** A live URL (Production API) that updates automatically when you push code.

### Lab 06: Observability (Prometheus & Grafana)

**Focus:** The "Safety Net."

- **Goal:** Watch the model in the wild.
- **Tasks:**
    - Add a `/metrics` endpoint to your FastAPI code using the Prometheus client.
    - Set up a **Prometheus** server to scrape those metrics.
    - Build a **Grafana** dashboard to track:
        1. **System Health:** (Is the API fast?)
        2. **Model Performance:** (Is it approving too many people? Is there Data Drift?)
- **Result:** A professional monitoring cockpit.