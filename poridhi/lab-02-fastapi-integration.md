# Lab 02: FastAPI Model Serving with MLflow Integration

## Introduction

This lab builds a production-ready REST API for serving credit card approval predictions. You will create a FastAPI application that loads models from MLflow Registry, implements proper input validation, adds caching for performance, and logs predictions to a database. The API integrates seamlessly with the automated training pipeline from Lab 01.

By the end of this lab, you will have a scalable, monitored API that serves real-time predictions with sub-second response times.

## Learning Objectives

By the end of this lab, you will be able to:

1. Design RESTful APIs for machine learning model serving
2. Load models dynamically from MLflow Model Registry
3. Implement input validation using Pydantic schemas
4. Add Redis caching to improve response times
5. Log predictions to PostgreSQL for audit trails
6. Create health and readiness endpoints for orchestration
7. Handle preprocessing consistently between training and inference
8. Implement proper error handling and status codes
9. Structure FastAPI applications following best practices
10. Integrate multiple services using Docker Compose

**Prerequisites:** Completed Lab 01, basic FastAPI knowledge, understanding of REST APIs

**Estimated Time:** 6-8 hours

## Prologue: The Challenge

Your automated ML pipeline from Lab 01 is working perfectly. Every Sunday at 2 AM, it trains models and registers the best one to MLflow. But there's a problem: the models just sit in MLflow Registry. Nobody can use them.

The business team asks: "How do we actually approve credit card applications using these models?"

You need to build an API that:
- Loads the latest production model from MLflow
- Accepts credit card applications via HTTP
- Returns approval decisions in milliseconds
- Handles thousands of requests per second
- Logs every prediction for compliance
- Validates input data (reject malformed requests)
- Caches frequent requests (same applicant, same result)
- Reports health status to load balancers

The API must be production-ready: fast, reliable, observable, and secure.

## Environment Setup

Continue from Lab 01 project structure.

```bash
# Navigate to project directory
cd card-approval-mlops

# Create API directory structure
mkdir -p app/{core,routers,schemas,services,utils}

# Create __init__.py files
touch app/__init__.py
touch app/core/__init__.py
touch app/routers/__init__.py
touch app/schemas/__init__.py
touch app/services/__init__.py
touch app/utils/__init__.py

# Install additional dependencies
pip install fastapi uvicorn redis pydantic-settings asyncpg
```

**New Directory Structure:**
```
card-approval-mlops/
├── app/                        # FastAPI application
│   ├── __init__.py
│   ├── main.py                 # Application entry point
│   ├── core/                   # Core configurations
│   │   ├── __init__.py
│   │   ├── config.py           # Settings and environment
│   │   ├── logging.py          # Logging configuration
│   │   └── database.py         # Database connection
│   ├── routers/                # API endpoints
│   │   ├── __init__.py
│   │   ├── health.py           # Health checks
│   │   └── predict.py          # Prediction endpoints
│   ├── schemas/                # Pydantic models
│   │   ├── __init__.py
│   │   ├── health.py           # Health schemas
│   │   └── prediction.py       # Prediction schemas
│   ├── services/               # Business logic
│   │   ├── __init__.py
│   │   ├── model_service.py    # Model loading
│   │   └── preprocessing_service.py  # Feature preprocessing
│   └── utils/                  # Utilities
│       ├── __init__.py
│       └── mlflow_helpers.py   # MLflow utilities
├── dags/                       # (from Lab 01)
├── training/                   # (from Lab 01)
└── docker-compose.local.lab02.yml  # Lab 02 services
```

## Chapter 1: Understanding API Design for ML Models

### 1.1 REST API Principles for ML

Before coding, understand how to design APIs for machine learning models.

**Key Principles:**

```
1. STATELESS
   ├── Each request contains all information needed
   ├── No session state on server
   └── Enables horizontal scaling

2. RESOURCE-ORIENTED
   ├── /predict - prediction resource
   ├── /health - health resource
   └── /model-info - model metadata resource

3. STANDARD HTTP METHODS
   ├── GET - retrieve information (health, model info)
   ├── POST - create prediction
   └── Avoid PUT/DELETE for ML APIs (predictions are immutable)

4. PROPER STATUS CODES
   ├── 200 - Success
   ├── 400 - Bad request (invalid input)
   ├── 422 - Validation error (Pydantic)
   ├── 500 - Server error
   └── 503 - Service unavailable (model not loaded)

5. VERSIONING
   ├── /api/v1/predict
   └── Allows breaking changes without affecting clients
```

### 1.2 Think First: API Design Decisions

**Question 1:** Should predictions be GET or POST requests?

<details>
<parameter name="summary">Click to review


**Answer:**

**POST is correct for predictions. Here's why:**

**Why POST:**
- Predictions create a new resource (prediction record)
- Request body can contain complex data (18+ features)
- Not idempotent (each prediction is logged separately)
- Sensitive data shouldn't be in URL (GET parameters are logged)

**Why NOT GET:**
- GET is for retrieving existing resources
- URL length limits (can't fit 18 features)
- GET requests are cached by browsers/proxies (unwanted for predictions)
- Query parameters appear in logs (security risk)

**Example:**
```python
# ✓ Correct
POST /api/v1/predict
Body: {"income": 50000, "age": 35, ...}

# ✗ Wrong
GET /api/v1/predict?income=50000&age=35&...
```

</details>

**Question 2:** Should the API load the model on every request or once at startup?

<details>
<parameter name="summary">Click to review


**Answer:**

**Load once at startup (with reload mechanism).**

**Why Load at Startup:**
- Model loading is expensive (seconds)
- Loading on every request would be too slow (timeout)
- Memory efficient (one model in memory, not N copies)

**Why Not Load Per Request:**
- Latency: 2-5 seconds per request (unacceptable)
- Memory: Each request would load a new model copy
- MLflow API calls: Rate limiting issues

**Best Practice:**
```python
# Application startup
@app.on_event("startup")
async def load_model():
    global model
    model = mlflow.sklearn.load_model("models:/card_approval_production/Production")

# Request handling
@app.post("/predict")
async def predict(data: PredictionInput):
    prediction = model.predict(data)  # Fast (milliseconds)
    return prediction
```

**Reload Strategy:**
- Load at startup
- Provide `/reload-model` endpoint for manual reload
- Or: Check MLflow for new versions periodically (background task)

</details>

**Question 3:** How should we handle preprocessing? Duplicate code or reuse from training?

<details>
<parameter name="summary">Click to review


**Answer:**

**Reuse preprocessing artifacts from training.**

**The Problem:**
If you duplicate preprocessing code, training and inference will drift:
- Training uses StandardScaler with mean=50000
- Inference accidentally uses mean=48000
- Model receives different inputs → wrong predictions

**The Solution:**
Save preprocessing artifacts during training, load during inference:

```python
# Training (Lab 01)
scaler = StandardScaler()
scaler.fit(X_train)
joblib.dump(scaler, 'models/scaler.pkl')

# Inference (Lab 02)
scaler = joblib.load('models/scaler.pkl')
X_scaled = scaler.transform(X_new)  # Uses SAME mean/std as training
```

**Critical Artifacts to Save:**
1. `scaler.pkl` - StandardScaler (mean, std for each feature)
2. `label_encoders.pkl` - LabelEncoder mappings (categorical → numeric)
3. `feature_names.pkl` - Feature order (must match training)

**Why This Matters:**
- Training-serving skew is a top cause of ML failures in production
- Subtle differences cause silent failures (wrong predictions, no errors)
- Reusing artifacts guarantees consistency

</details>

### 1.3 API Endpoint Design

Design the complete API surface before implementation.

**Endpoint Specification:**

```
1. Health Endpoints (Orchestration)
   GET /health
   └── Returns: {"status": "healthy"}
   └── Purpose: Liveness check (is process running?)
   
   GET /health/ready
   └── Returns: {"status": "ready", "model_loaded": true}
   └── Purpose: Readiness check (can serve requests?)

2. Model Information
   GET /api/v1/model-info
   └── Returns: Model metadata (name, version, metrics)
   └── Purpose: Transparency (which model is serving?)

3. Prediction
   POST /api/v1/predict
   └── Input: Application data (18 features)
   └── Returns: Prediction + probability + decision
   └── Purpose: Core business logic

4. Batch Prediction (Optional)
   POST /api/v1/predict/batch
   └── Input: Array of applications
   └── Returns: Array of predictions
   └── Purpose: Bulk processing
```

**Why These Endpoints?**

**Health Endpoints:**
- Load balancers need to know if service is healthy
- Kubernetes uses readiness probes before routing traffic
- Liveness vs. Readiness: Process running vs. Ready to serve

**Model Info:**
- Debugging: "Which model version is deployed?"
- Compliance: "What model made this decision?"
- Monitoring: Track model versions in production

**Prediction:**
- Core business value
- Single prediction for real-time use cases

**Batch Prediction:**
- Efficiency for bulk processing
- Reduces HTTP overhead
- Useful for batch jobs

### 1.4 Input Validation Strategy

Pydantic provides automatic validation. Design schemas carefully.

**Validation Levels:**

```
1. TYPE VALIDATION
   ├── income: float (not string)
   ├── age: int (not float)
   └── Automatic with Pydantic

2. RANGE VALIDATION
   ├── age: 18-100 (reject impossible values)
   ├── income: > 0 (no negative income)
   └── Use Field(ge=, le=)

3. BUSINESS LOGIC VALIDATION
   ├── employment_years <= age - 18
   ├── family_members >= children
   └── Custom validators

4. REQUIRED vs OPTIONAL
   ├── All features required for prediction
   ├── Optional: request_id, metadata
   └── Use Optional[type]
```

**Example Schema:**

```python
from pydantic import BaseModel, Field, validator

class PredictionInput(BaseModel):
    # Demographics
    CODE_GENDER: str = Field(..., pattern="^[MF]$")
    CNT_CHILDREN: int = Field(..., ge=0, le=20)
    
    # Financial
    AMT_INCOME_TOTAL: float = Field(..., gt=0, le=10000000)
    
    # Temporal (in years, not days)
    AGE_YEARS: float = Field(..., ge=18, le=100)
    EMPLOYMENT_YEARS: float = Field(..., ge=0, le=80)
    
    @validator('EMPLOYMENT_YEARS')
    def validate_employment(cls, v, values):
        if 'AGE_YEARS' in values:
            if v > values['AGE_YEARS'] - 18:
                raise ValueError('Employment years cannot exceed age - 18')
        return v
```

**Why Strict Validation?**
- Garbage in, garbage out (bad input → bad predictions)
- Security (prevent injection attacks)
- User experience (clear error messages)
- Data quality (enforce business rules)

### 1.5 Checkpoint

Verify your understanding of API design before implementation.

**Self-Assessment:**
- [ ] You understand why predictions use POST, not GET
- [ ] You know why models are loaded at startup, not per request
- [ ] You understand training-serving skew and how to prevent it
- [ ] You can explain the difference between liveness and readiness
- [ ] You know why input validation is critical
- [ ] You understand the purpose of each endpoint

**Conceptual Question:**

**Q:** A client sends a request with `AGE_YEARS: "35"` (string instead of float). What happens?

<details>
<parameter name="summary">Click to review


**Answer:**

**Pydantic will automatically convert it to float (if possible).**

**Behavior:**
```python
# Input
{"AGE_YEARS": "35"}

# Pydantic processing
AGE_YEARS: float = Field(...)
# "35" → 35.0 (automatic coercion)

# Result: Success (converted)
```

**However:**
```python
# Input
{"AGE_YEARS": "thirty-five"}

# Pydantic processing
# Cannot convert "thirty-five" to float

# Result: 422 Validation Error
{
  "detail": [
    {
      "loc": ["body", "AGE_YEARS"],
      "msg": "value is not a valid float",
      "type": "type_error.float"
    }
  ]
}
```

**Key Point:**
- Pydantic tries to coerce types (string → number)
- If coercion fails, returns 422 with clear error message
- This is good UX (accept "35" as 35, reject "abc")

</details>

## Chapter 2: Configuration and Core Setup

### 2.1 Application Configuration

Create a centralized configuration using Pydantic Settings.

```python
# app/core/config.py
"""
Application configuration using Pydantic Settings.

Loads configuration from environment variables with validation.
Provides type-safe access to settings throughout the application.
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Environment variables are automatically loaded and validated.
    Prefix: None (use exact variable names)
    """
    
    # ========================================
    # APPLICATION SETTINGS
    # ========================================
    APP_NAME: str = "Credit Card Approval API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # ========================================
    # DATABASE SETTINGS (PostgreSQL)
    # ========================================
    POSTGRES_HOST: str = "postgres-api"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "card_approval_api"
    POSTGRES_USER: str = "api_user"
    POSTGRES_PASSWORD: str
    
    @property
    def DATABASE_URL(self) -> str:
        """
        Construct PostgreSQL connection URL.
        
        Format: postgresql://user:password@host:port/database
        """
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    # ========================================
    # REDIS SETTINGS (Caching)
    # ========================================
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    CACHE_TTL: int = 3600  # Cache time-to-live in seconds (1 hour)
    
    @property
    def REDIS_URL(self) -> str:
        """
        Construct Redis connection URL.
        
        Format: redis://:password@host:port/db
        """
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # ========================================
    # MLFLOW SETTINGS
    # ========================================
    MLFLOW_TRACKING_URI: str = "http://mlflow:5000"
    MODEL_NAME: str = "card_approval_production"
    MODEL_STAGE: str = "Production"  # or "Staging" for testing
    
    # ========================================
    # MODEL ARTIFACTS
    # ========================================
    MODEL_DIR: str = "/app/models"
    SCALER_PATH: str = "/app/models/scaler.pkl"
    ENCODERS_PATH: str = "/app/models/label_encoders.pkl"
    FEATURES_PATH: str = "/app/models/feature_names.pkl"
    
    # ========================================
    # API SETTINGS
    # ========================================
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list = ["*"]  # In production, specify exact origins
    
    # ========================================
    # LOGGING
    # ========================================
    LOG_LEVEL: str = "INFO"
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        case_sensitive = True

# Create global settings instance
settings = Settings()
```

**Configuration Explanation:**

**1. Pydantic Settings:**
- Automatically loads from environment variables
- Type validation (POSTGRES_PORT must be int)
- Required vs. optional (POSTGRES_PASSWORD required, REDIS_PASSWORD optional)

**2. Property Methods:**
```python
@property
def DATABASE_URL(self) -> str:
```
- Computed properties (construct URLs from components)
- Cleaner than storing full URLs in env vars
- Easier to override individual components

**3. Defaults:**
```python
REDIS_PORT: int = 6379
```
- Sensible defaults for optional settings
- Can be overridden via environment variables

**4. Type Safety:**
```python
POSTGRES_PORT: int = 5432
```
- IDE autocomplete
- Type checking
- Runtime validation

**Why Centralized Configuration?**
- Single source of truth
- Easy to test (mock settings)
- Environment-specific configs (dev, staging, prod)
- No hardcoded values scattered in code

### 2.2 Database Connection Setup

Create database connection management for logging predictions.

```python
# app/core/database.py
"""
Database connection management.

Provides async database connection pool for PostgreSQL.
Used for logging predictions and audit trails.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean
from datetime import datetime
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# ========================================
# DATABASE ENGINE
# ========================================

# Convert postgresql:// to postgresql+asyncpg://
# asyncpg is the async PostgreSQL driver
ASYNC_DATABASE_URL = settings.DATABASE_URL.replace(
    "postgresql://",
    "postgresql+asyncpg://"
)

# Create async engine
# pool_size: Number of connections to maintain
# max_overflow: Additional connections when pool is full
# pool_pre_ping: Test connections before using (detect stale connections)
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

# Create async session factory
# expire_on_commit=False: Don't expire objects after commit (allows access)
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for models
Base = declarative_base()

# ========================================
# DATABASE MODELS
# ========================================

class Prediction(Base):
    """
    Prediction log table.
    
    Stores every prediction for:
    - Audit trail (compliance)
    - Model monitoring (drift detection)
    - Analytics (approval rates, etc.)
    """
    __tablename__ = "predictions"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Model information
    model_name = Column(String, nullable=False)
    model_version = Column(String, nullable=False)
    
    # Prediction results
    prediction = Column(Integer, nullable=False)  # 0 or 1
    probability = Column(Float, nullable=False)   # 0.0 to 1.0
    decision = Column(String, nullable=False)     # "APPROVED" or "REJECTED"
    
    # Input features (store for audit/debugging)
    # In production, consider storing as JSONB for flexibility
    income = Column(Float)
    age_years = Column(Float)
    employment_years = Column(Float)
    
    # Request metadata
    request_id = Column(String, index=True)  # For tracing
    response_time_ms = Column(Float)         # Performance monitoring
    
    # Cache information
    from_cache = Column(Boolean, default=False)

# ========================================
# DATABASE UTILITIES
# ========================================

async def get_db():
    """
    Dependency for getting database session.
    
    Usage in FastAPI:
        @app.post("/predict")
        async def predict(db: AsyncSession = Depends(get_db)):
            # Use db here
    
    Automatically closes session after request.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """
    Initialize database tables.
    
    Creates all tables defined in Base.metadata.
    Called during application startup.
    """
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("✓ Database tables initialized")

async def close_db():
    """
    Close database connections.
    
    Called during application shutdown.
    """
    await engine.dispose()
    logger.info("✓ Database connections closed")
```

**Database Code Explanation:**

**1. Async Database:**
```python
from sqlalchemy.ext.asyncio import create_async_engine
```
- FastAPI is async (non-blocking I/O)
- Async database driver (asyncpg) allows concurrent requests
- Synchronous database would block the event loop

**2. Connection Pool:**
```python
pool_size=10, max_overflow=20
```
- Maintains 10 persistent connections
- Can create 20 more if needed (total 30)
- Reuses connections (faster than creating new ones)

**3. pool_pre_ping:**
```python
pool_pre_ping=True
```
- Tests connection before using
- Detects stale connections (database restart, network issues)
- Automatically reconnects if needed

**4. Dependency Injection:**
```python
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```
- FastAPI dependency
- Automatically provides database session to endpoints
- Ensures session is closed after request

**5. Prediction Model:**
```python
class Prediction(Base):
```
- Stores every prediction
- Audit trail for compliance
- Data for monitoring and analytics
- Includes model version (track which model made prediction)

**Why Log Predictions?**
- **Compliance**: Regulatory requirements (explain decisions)
- **Monitoring**: Detect model drift (approval rate changes)
- **Debugging**: Investigate incorrect predictions
- **Analytics**: Business insights (approval rates by demographics)

### 2.3 Logging Configuration

Set up structured logging for observability.

```python
# app/core/logging.py
"""
Logging configuration.

Provides structured logging with consistent format.
Logs to stdout (captured by Docker/Kubernetes).
"""

import logging
import sys
from app.core.config import settings

def setup_logging():
    """
    Configure application logging.
    
    Format: [TIMESTAMP] [LEVEL] [MODULE] MESSAGE
    Output: stdout (Docker captures this)
    """
    
    # Create formatter
    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL)
    
    # Remove existing handlers
    root_logger.handlers = []
    
    # Add stdout handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Reduce noise from libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    logging.info("✓ Logging configured")
```

**Logging Explanation:**

**1. Structured Format:**
```
[2024-01-15 10:30:45] [INFO] [app.services.model_service] Model loaded successfully
```
- Timestamp: When event occurred
- Level: INFO, WARNING, ERROR
- Module: Which part of code logged
- Message: What happened

**2. Stdout Output:**
- Docker captures stdout
- Kubernetes collects logs
- Log aggregation systems (Loki, ELK) ingest stdout

**3. Library Noise Reduction:**
```python
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
```
- Uvicorn logs every request (too verbose)
- SQLAlchemy logs every query (too verbose)
- Reduce to WARNING level

### 2.4 Checkpoint

Verify your understanding of the core setup.

**Self-Assessment:**
- [ ] You understand why we use Pydantic Settings
- [ ] You know why database connections are async
- [ ] You understand connection pooling
- [ ] You know why we log predictions to database
- [ ] You understand structured logging
- [ ] You can explain the purpose of each configuration setting

**Practical Exercise:**

Create a `.env.lab02` file with all required settings:

```bash
# .env.lab02
# PostgreSQL
POSTGRES_PASSWORD=secure_api_password

# Redis
REDIS_PASSWORD=secure_redis_password

# MLflow
MLFLOW_TRACKING_URI=http://mlflow:5000
MODEL_NAME=card_approval_production
MODEL_STAGE=Production

# Logging
LOG_LEVEL=INFO
DEBUG=false
```

---

**Continue to Chapter 3 for Pydantic Schemas...**
