# Lab 04: The Prediction API (FastAPI) & Docker Hub

## Introduction

This lab transforms your trained model into a production-ready API service. You will build a FastAPI application that loads models from S3, validates input data, and serves predictions. The application will be containerized with Docker and pushed to Docker Hub for deployment.

## Learning Objectives

By the end of this lab, you will be able to:

1. Create a FastAPI application with health and prediction endpoints
2. Implement input validation using Pydantic models
3. Load ML models from S3 and cache them for performance
4. Handle errors gracefully with appropriate HTTP status codes
5. Create a production-ready Dockerfile
6. Build and push Docker images to Docker Hub
7. Test the containerized API locally

**Prerequisites:** Completion of Lab 03, basic understanding of REST APIs, Docker installed, Docker Hub account.

## Prologue: The Challenge

Your ML model currently lives in notebooks and scripts. A bank's loan application system needs to call your model to make approval decisions in real-time. They cannot run Python notebooks—they need an API endpoint they can call with HTTP requests.

You need to build a service that:
- Accepts credit application data as JSON
- Validates input to prevent errors
- Loads the production model from S3
- Returns predictions with confidence scores
- Handles thousands of requests per day reliably
- Can be deployed anywhere (cloud, on-premises, Kubernetes)

Docker containerization ensures the API runs identically in development, testing, and production environments.

## Environment Setup

Install FastAPI and related dependencies:

```bash
# Activate virtual environment
source venv/bin/activate

# Install FastAPI dependencies
pip install fastapi uvicorn pydantic python-dotenv redis

# Install testing tools
pip install httpx pytest pytest-asyncio

# Create API directory structure
mkdir -p app/routers app/services app/schemas app/core app/utils
touch app/__init__.py
touch app/routers/__init__.py
touch app/services/__init__.py
touch app/schemas/__init__.py
touch app/core/__init__.py
touch app/utils/__init__.py
```

## Chapter 1: FastAPI Fundamentals


### 1.1 What You Will Build

You will create a basic FastAPI application with health check endpoints to verify the service is running correctly.

### 1.2 Think First: API Design

**Question:** A production API needs both `/health` and `/ready` endpoints. What is the difference between them?

<details>
<summary>Click to review</summary>

**Health endpoint (`/health`):**
- Checks if the process is running
- Returns 200 if the server can respond to requests
- Used by orchestrators to restart crashed containers

**Readiness endpoint (`/ready`):**
- Checks if the service can handle requests
- Verifies dependencies (database, model loaded, etc.)
- Returns 200 only when fully operational
- Used by load balancers to route traffic

A service can be healthy but not ready (e.g., model still loading from S3). Load balancers should only send traffic when the service is ready.

</details>

### 1.3 Implementation

Create `app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Card Approval Prediction API",
    description="ML-powered credit card approval prediction service",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Card Approval Prediction API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    # TODO: Add model loading check
    return {"status": "ready"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 1.4 Understanding the Code

Match each FastAPI component to its purpose:

| Component | Purpose (A-D) |
|-----------|---------------|
| FastAPI() | ___ |
| CORSMiddleware | ___ |
| @app.get() | ___ |
| uvicorn.run() | ___ |

**Options:**
- A: Defines HTTP GET endpoint
- B: Creates the application instance
- C: Allows cross-origin requests from browsers
- D: Starts the ASGI server

<details>
<summary>Click to review</summary>

- FastAPI(): B (Creates application instance)
- CORSMiddleware: C (Allows cross-origin requests)
- @app.get(): A (Defines GET endpoint)
- uvicorn.run(): D (Starts ASGI server)

</details>

### 1.5 Test and Verify

Start the API server:

```bash
python app/main.py
```

Test the endpoints:

```bash
# Test root endpoint
curl http://localhost:8000/

# Test health endpoint
curl http://localhost:8000/health

# Test readiness endpoint
curl http://localhost:8000/ready

# View interactive documentation
open http://localhost:8000/docs
```

**Predict:** What will the interactive documentation show?

<details>
<summary>Click to verify</summary>

The `/docs` endpoint shows Swagger UI with all available endpoints, their parameters, and response schemas. You can test endpoints directly from the browser. This is automatically generated by FastAPI from your code and type hints.

</details>

### 1.6 Checkpoint

**Self-Assessment:**
- [ ] API starts without errors
- [ ] All three endpoints return expected responses
- [ ] Interactive documentation is accessible
- [ ] You understand the difference between health and readiness checks

## Chapter 2: Input Validation with Pydantic

### 2.1 What You Will Build

You will create Pydantic models to validate credit application input data, ensuring only valid requests reach the model.

### 2.2 Think First: Validation Strategy

**Question:** What happens if the API receives invalid input (e.g., negative income, missing required fields)? Should validation happen before or after loading the model?

<details>
<summary>Click to review</summary>

Validation must happen before model inference:

**Benefits of early validation:**
- Prevents model errors from invalid input
- Saves computational resources (no need to load/run model)
- Provides clear error messages to clients
- Protects against malicious input

Pydantic validates at the API boundary, rejecting invalid requests with 422 status code before they reach business logic.

</details>

### 2.3 Implementation

Create `app/schemas/prediction.py`:


```python
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class PredictionRequest(BaseModel):
    """Credit card application data for prediction."""
    
    ID: int = Field(..., description="Application ID")
    CODE_GENDER: str = Field(..., description="Gender (M/F)")
    FLAG_OWN_CAR: str = Field(..., description="Owns car (Y/N)")
    FLAG_OWN_REALTY: str = Field(..., description="Owns realty (Y/N)")
    CNT_CHILDREN: int = Field(..., ge=0, description="Number of children")
    AMT_INCOME_TOTAL: float = Field(..., gt=0, description="Annual income")
    NAME_INCOME_TYPE: str = Field(..., description="Income type")
    NAME_EDUCATION_TYPE: str = Field(..., description="Education level")
    NAME_FAMILY_STATUS: str = Field(..., description="Family status")
    NAME_HOUSING_TYPE: str = Field(..., description="Housing type")
    DAYS_BIRTH: int = Field(..., lt=0, description="Age in days (negative)")
    DAYS_EMPLOYED: int = Field(..., description="Employment days (negative)")
    FLAG_MOBIL: int = Field(..., ge=0, le=1, description="Mobile phone flag")
    FLAG_WORK_PHONE: int = Field(..., ge=0, le=1, description="Work phone flag")
    FLAG_PHONE: int = Field(..., ge=0, le=1, description="Phone flag")
    FLAG_EMAIL: int = Field(..., ge=0, le=1, description="Email flag")
    OCCUPATION_TYPE: Optional[str] = Field(None, description="Occupation")
    CNT_FAM_MEMBERS: float = Field(..., gt=0, description="Family members")
    
    @validator('CODE_GENDER')
    def validate_gender(cls, v):
        if v not in ['M', 'F']:
            raise ValueError('Gender must be M or F')
        return v
    
    @validator('FLAG_OWN_CAR', 'FLAG_OWN_REALTY')
    def validate_yes_no(cls, v):
        if v not in ['Y', 'N']:
            raise ValueError('Must be Y or N')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "ID": 5008804,
                "CODE_GENDER": "M",
                "FLAG_OWN_CAR": "Y",
                "FLAG_OWN_REALTY": "Y",
                "CNT_CHILDREN": 0,
                "AMT_INCOME_TOTAL": 180000.0,
                "NAME_INCOME_TYPE": "Working",
                "NAME_EDUCATION_TYPE": "Higher education",
                "NAME_FAMILY_STATUS": "Married",
                "NAME_HOUSING_TYPE": "House / apartment",
                "DAYS_BIRTH": -14000,
                "DAYS_EMPLOYED": -2500,
                "FLAG_MOBIL": 1,
                "FLAG_WORK_PHONE": 0,
                "FLAG_PHONE": 1,
                "FLAG_EMAIL": 0,
                "OCCUPATION_TYPE": "Managers",
                "CNT_FAM_MEMBERS": 2.0
            }
        }

class PredictionResponse(BaseModel):
    """Prediction result."""
    
    prediction: int = Field(..., description="Prediction (0=Rejected, 1=Approved)")
    probability: float = Field(..., ge=0, le=1, description="Approval probability")
    decision: str = Field(..., description="Human-readable decision")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")
    version: str = Field(..., description="Model version")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        schema_extra = {
            "example": {
                "prediction": 1,
                "probability": 0.85,
                "decision": "APPROVED",
                "confidence": 0.85,
                "version": "1.0.0",
                "timestamp": "2025-02-21T10:30:00"
            }
        }
```

### 2.4 Understanding the Code

Pydantic validation features:

```python
# Field constraints
Field(..., ge=0)           # Greater than or equal to 0
Field(..., gt=0)           # Greater than 0
Field(..., le=1)           # Less than or equal to 1
Field(..., lt=0)           # Less than 0

# Custom validators
@validator('field_name')   # Validates specific field
def validate_field(cls, v):
    if condition:
        raise ValueError('Error message')
    return v
```

### 2.5 Test and Verify

Create a test file `test_payload.json`:

```json
{
  "ID": 5008804,
  "CODE_GENDER": "M",
  "FLAG_OWN_CAR": "Y",
  "FLAG_OWN_REALTY": "Y",
  "CNT_CHILDREN": 0,
  "AMT_INCOME_TOTAL": 180000.0,
  "NAME_INCOME_TYPE": "Working",
  "NAME_EDUCATION_TYPE": "Higher education",
  "NAME_FAMILY_STATUS": "Married",
  "NAME_HOUSING_TYPE": "House / apartment",
  "DAYS_BIRTH": -14000,
  "DAYS_EMPLOYED": -2500,
  "FLAG_MOBIL": 1,
  "FLAG_WORK_PHONE": 0,
  "FLAG_PHONE": 1,
  "FLAG_EMAIL": 0,
  "OCCUPATION_TYPE": "Managers",
  "CNT_FAM_MEMBERS": 2.0
}
```

Test validation with invalid data:

```json
{
  "ID": 5008804,
  "CODE_GENDER": "X",
  "AMT_INCOME_TOTAL": -1000
}
```

**Predict:** What error will Pydantic return for the invalid data?

<details>
<summary>Click to verify</summary>

Pydantic will return a 422 Unprocessable Entity response with detailed validation errors:
- `CODE_GENDER`: "Gender must be M or F"
- `AMT_INCOME_TOTAL`: "ensure this value is greater than 0"
- Missing required fields will also be listed

This provides clear feedback to API clients about what needs to be fixed.

</details>

### 2.6 Checkpoint

**Self-Assessment:**
- [ ] Pydantic models are defined correctly
- [ ] You understand Field constraints (ge, gt, le, lt)
- [ ] Custom validators work for categorical fields
- [ ] You can explain why validation happens at the API boundary

## Chapter 3: Model Service

### 3.1 What You Will Build

You will create a service that loads the production model from S3, caches it in memory, and provides prediction functionality.

### 3.2 Think First: Model Loading Strategy

**Question:** Should the model be loaded:
- A: On every prediction request
- B: Once at application startup
- C: On the first prediction request, then cached

What are the trade-offs?

<details>
<summary>Click to review</summary>

**Option A (per-request):** 
- Pros: Always uses latest model
- Cons: Extremely slow (S3 download per request), not practical

**Option B (at startup):**
- Pros: Fast predictions, predictable startup time
- Cons: Startup fails if S3 is unavailable, longer startup time

**Option C (lazy loading with cache):**
- Pros: Fast startup, model loads only when needed, cached for subsequent requests
- Cons: First request is slow, requires cache invalidation strategy

Best practice: Option B for production (fail fast if model unavailable). Option C for development (faster iteration).

</details>

### 3.3 Implementation

Create `app/services/model_service.py`:


```python
import mlflow
import mlflow.sklearn
import numpy as np
from typing import Optional
import logging
import os

logger = logging.getLogger(__name__)

class ModelService:
    """Service for loading and using ML models."""
    
    def __init__(self):
        self.model = None
        self.model_version = None
        self.mlflow_tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
        self.model_name = os.getenv("MODEL_NAME", "card_approval_production")
        self.model_stage = os.getenv("MODEL_STAGE", "Production")
        
    def load_model(self):
        """Load model from MLflow registry."""
        try:
            mlflow.set_tracking_uri(self.mlflow_tracking_uri)
            model_uri = f"models:/{self.model_name}/{self.model_stage}"
            
            logger.info(f"Loading model from {model_uri}")
            self.model = mlflow.sklearn.load_model(model_uri)
            
            # Get model version
            from mlflow.tracking import MlflowClient
            client = MlflowClient()
            model_versions = client.get_latest_versions(self.model_name, stages=[self.model_stage])
            if model_versions:
                self.model_version = model_versions[0].version
            
            logger.info(f"Model loaded successfully (version: {self.model_version})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
    
    def predict(self, features: np.ndarray) -> dict:
        """Make prediction using loaded model."""
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        try:
            prediction = self.model.predict(features)[0]
            probability = self.model.predict_proba(features)[0]
            
            return {
                "prediction": int(prediction),
                "probability": float(probability[1]),
                "confidence": float(max(probability))
            }
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise

# Global model service instance
model_service = ModelService()
```

Create `app/core/config.py`:

```python
from pydantic import BaseSettings

class Settings(BaseSettings):
    """Application settings."""
    
    # API Settings
    API_TITLE: str = "Card Approval Prediction API"
    API_VERSION: str = "1.0.0"
    
    # MLflow Settings
    MLFLOW_TRACKING_URI: str = "http://localhost:5000"
    MODEL_NAME: str = "card_approval_production"
    MODEL_STAGE: str = "Production"
    
    # AWS Settings
    AWS_REGION: str = "us-east-1"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### 3.4 Understanding the Code

The model service implements the singleton pattern:
- One instance created at module import
- Model loaded once and reused
- Thread-safe for concurrent requests

### 3.5 Test and Verify

Update `app/main.py` to include model loading:

```python
from contextlib import asynccontextmanager
from app.services.model_service import model_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup: Load model
    logger.info("Loading ML model...")
    success = model_service.load_model()
    if not success:
        logger.error("Failed to load model at startup")
    yield
    # Shutdown: Cleanup
    logger.info("Shutting down...")

app = FastAPI(
    title="Card Approval Prediction API",
    description="ML-powered credit card approval prediction service",
    version="1.0.0",
    lifespan=lifespan
)
```

**Predict:** What happens if the model fails to load at startup?

<details>
<summary>Click to verify</summary>

The application will start but log an error. The `/ready` endpoint should return an error status to prevent traffic routing. In production, you might want to exit the application if the model cannot be loaded (fail-fast principle).

</details>

### 3.6 Checkpoint

**Self-Assessment:**
- [ ] Model service loads model from MLflow registry
- [ ] Model is cached in memory after first load
- [ ] You understand the lifespan context manager
- [ ] Logging provides visibility into model loading

## Chapter 4: Prediction Endpoint

### 4.1 What You Will Build

You will create the prediction endpoint that accepts credit applications and returns approval decisions.

### 4.2 Implementation

Create `app/routers/predict.py`:

```python
from fastapi import APIRouter, HTTPException
from app.schemas.prediction import PredictionRequest, PredictionResponse
from app.services.model_service import model_service
import numpy as np
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["predictions"])

@router.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """Predict credit card approval."""
    
    if model_service.model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Convert request to feature array
        features = np.array([[
            request.ID,
            1 if request.CODE_GENDER == "M" else 0,
            1 if request.FLAG_OWN_CAR == "Y" else 0,
            1 if request.FLAG_OWN_REALTY == "Y" else 0,
            request.CNT_CHILDREN,
            request.AMT_INCOME_TOTAL,
            # Add other features...
        ]])
        
        # Make prediction
        result = model_service.predict(features)
        
        # Format response
        decision = "APPROVED" if result["prediction"] == 1 else "REJECTED"
        
        return PredictionResponse(
            prediction=result["prediction"],
            probability=result["probability"],
            decision=decision,
            confidence=result["confidence"],
            version=model_service.model_version or "unknown"
        )
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Register router in main.py
# app.include_router(predict.router)
```

Update `app/main.py`:

```python
from app.routers import predict

app.include_router(predict.router)
```

### 4.3 Test and Verify

Test the prediction endpoint:

```bash
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d @test_payload.json
```

### 4.4 Checkpoint

**Self-Assessment:**
- [ ] Prediction endpoint accepts valid requests
- [ ] Invalid requests return 422 with validation errors
- [ ] Predictions return expected format
- [ ] Error handling works correctly

## Chapter 5: Dockerization

### 5.1 What You Will Build

You will create a Dockerfile that packages the API into a container image.

### 5.2 Think First: Docker Best Practices

**Question:** What should be included in a production Docker image? What should be excluded?

<details>
<summary>Click to review</summary>

**Include:**
- Application code
- Production dependencies
- Runtime environment (Python)
- Configuration files

**Exclude:**
- Development dependencies (pytest, jupyter)
- Source data files
- Local environment files (.env)
- Git history
- IDE configurations

Use `.dockerignore` to exclude unnecessary files, reducing image size and build time.

</details>

### 5.3 Implementation

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Create `.dockerignore`:

```
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.env
.git
.gitignore
*.md
tests/
.pytest_cache
.coverage
htmlcov/
dist/
build/
*.egg-info
.DS_Store
```

### 5.4 Build and Test

Build the Docker image:

```bash
docker build -t card-approval-api:latest .
```

Run the container:

```bash
docker run -p 8000:8000 \
  -e MLFLOW_TRACKING_URI=http://host.docker.internal:5000 \
  -e MODEL_NAME=card_approval_production \
  -e MODEL_STAGE=Production \
  card-approval-api:latest
```

Test the containerized API:

```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d @test_payload.json
```

### 5.5 Checkpoint

**Self-Assessment:**
- [ ] Docker image builds successfully
- [ ] Container runs without errors
- [ ] API is accessible from host machine
- [ ] Predictions work in containerized environment

## Chapter 6: Docker Hub Deployment

### 6.1 Implementation

Tag and push to Docker Hub:

```bash
# Login to Docker Hub
docker login

# Tag image
docker tag card-approval-api:latest your-username/card-approval-api:latest
docker tag card-approval-api:latest your-username/card-approval-api:v1.0.0

# Push to Docker Hub
docker push your-username/card-approval-api:latest
docker push your-username/card-approval-api:v1.0.0
```

### 6.2 Checkpoint

**Self-Assessment:**
- [ ] Image is pushed to Docker Hub
- [ ] You can pull the image from another machine
- [ ] Version tags are applied correctly

## Epilogue: The Complete System

You have built a production-ready API:

| Component | Capability |
|-----------|------------|
| FastAPI | High-performance async API framework |
| Pydantic | Automatic input validation |
| Model Service | Cached model loading from S3 |
| Docker | Portable containerized deployment |
| Docker Hub | Public image registry |

## The Principles

1. **Validate at the boundary** — Reject invalid input before it reaches business logic
2. **Load expensive resources once** — Cache models in memory, not per-request
3. **Fail fast** — Load model at startup to detect issues immediately
4. **Use appropriate status codes** — 422 for validation, 503 for unavailable service
5. **Container everything** — Docker ensures consistency across environments

## Troubleshooting

### Error: Model not found in registry

**Solution:** Ensure model is registered and promoted to Production stage in MLflow.

### Error: Connection refused to MLflow

**Solution:** Use `host.docker.internal` instead of `localhost` in Docker.

### Error: Permission denied pushing to Docker Hub

**Solution:** Run `docker login` and verify credentials.

## Next Steps

1. Add authentication and authorization
2. Implement rate limiting
3. Add caching with Redis
4. Create comprehensive test suite
5. Add API documentation

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
