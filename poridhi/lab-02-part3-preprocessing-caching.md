# Lab 02: Part 3 - Preprocessing Service and Redis Caching

## Chapter 5: Preprocessing Service

### 5.1 Understanding Training-Serving Consistency

The preprocessing service ensures identical transformations between training and inference.

**The Problem:**
```
Training:
  Raw Data → Preprocess → Model → Prediction
  
Inference (Wrong):
  Raw Data → Different Preprocess → Model → Wrong Prediction
  
Inference (Correct):
  Raw Data → Same Preprocess → Model → Correct Prediction
```

**Training-Serving Skew:**
- Training uses StandardScaler with mean=50000
- Inference accidentally uses mean=48000
- Model receives different inputs
- Predictions are wrong (silently!)

**The Solution:**
- Save preprocessing artifacts during training
- Load same artifacts during inference
- Apply identical transformations

### 5.2 Preprocessing Service Implementation

Create a service that applies the same preprocessing as training.

```python
# app/services/preprocessing_service.py
"""
Preprocessing service for feature transformation.

Applies the same preprocessing as training:
1. Encode categorical variables (using saved encoders)
2. Scale numeric features (using saved scaler)
3. Ensure feature order matches training

Critical: Uses artifacts from training to ensure consistency.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
import logging
from app.schemas.prediction import PredictionInput
from app.services.model_service import model_service

logger = logging.getLogger(__name__)

class PreprocessingService:
    """
    Service for preprocessing input features.
    
    Responsibilities:
    - Convert Pydantic model to DataFrame
    - Encode categorical variables
    - Scale numeric features
    - Ensure feature order
    - Validate preprocessing
    """
    
    def __init__(self):
        """Initialize preprocessing service."""
        pass
    
    def preprocess(self, input_data: PredictionInput) -> np.ndarray:
        """
        Preprocess input data for prediction.
        
        Steps:
        1. Convert Pydantic model to dict
        2. Create DataFrame
        3. Encode categorical variables
        4. Ensure feature order
        5. Scale features
        6. Validate output
        
        Args:
            input_data: Validated input from Pydantic
        
        Returns:
            np.ndarray: Preprocessed features ready for model
        
        Raises:
            ValueError: If preprocessing fails
        """
        try:
            # ========================================
            # STEP 1: CONVERT TO DICT
            # ========================================
            # Exclude optional fields (request_id)
            data_dict = input_data.model_dump(exclude={'request_id'})
            
            logger.debug(f"Input features: {list(data_dict.keys())}")
            
            # ========================================
            # STEP 2: CREATE DATAFRAME
            # ========================================
            # DataFrame with single row
            df = pd.DataFrame([data_dict])
            
            logger.debug(f"DataFrame shape: {df.shape}")
            
            # ========================================
            # STEP 3: ENCODE CATEGORICAL VARIABLES
            # ========================================
            # Use the same label encoders from training
            label_encoders = model_service.label_encoders
            
            if label_encoders is None:
                raise ValueError("Label encoders not loaded")
            
            for col, encoder in label_encoders.items():
                if col in df.columns:
                    try:
                        # Transform using saved encoder
                        df[col] = encoder.transform(df[col].astype(str))
                        logger.debug(f"Encoded {col}: {df[col].values[0]}")
                    except ValueError as e:
                        # Handle unknown categories
                        # This happens if inference sees a category not in training
                        logger.warning(f"Unknown category in {col}: {df[col].values[0]}")
                        
                        # Strategy: Use most frequent category from training
                        # Or: Use a default "Unknown" category
                        # For now, raise error (fail fast)
                        raise ValueError(
                            f"Unknown category '{df[col].values[0]}' in column '{col}'. "
                            f"Valid categories: {list(encoder.classes_)}"
                        )
            
            logger.debug("✓ Categorical encoding complete")
            
            # ========================================
            # STEP 4: ENSURE FEATURE ORDER
            # ========================================
            # Model expects features in specific order (from training)
            feature_names = model_service.feature_names
            
            if feature_names is None:
                raise ValueError("Feature names not loaded")
            
            # Reorder columns to match training
            df = df[feature_names]
            
            logger.debug(f"Feature order: {list(df.columns)}")
            
            # ========================================
            # STEP 5: SCALE FEATURES
            # ========================================
            # Use the same scaler from training
            scaler = model_service.scaler
            
            if scaler is None:
                raise ValueError("Scaler not loaded")
            
            # Transform using saved scaler
            # This uses the SAME mean and std as training
            features_scaled = scaler.transform(df)
            
            logger.debug(f"Scaled features shape: {features_scaled.shape}")
            logger.debug(f"Scaled features sample: {features_scaled[0][:3]}...")
            
            # ========================================
            # STEP 6: VALIDATE OUTPUT
            # ========================================
            self._validate_preprocessed_features(features_scaled)
            
            logger.debug("✓ Preprocessing complete")
            
            return features_scaled
            
        except Exception as e:
            logger.error(f"Preprocessing failed: {e}")
            raise
    
    def _validate_preprocessed_features(self, features: np.ndarray):
        """
        Validate preprocessed features.
        
        Checks:
        - Shape is correct (1 row, N features)
        - No NaN values
        - No infinite values
        - Values are in reasonable range
        
        Args:
            features: Preprocessed feature array
        
        Raises:
            ValueError: If validation fails
        """
        # Check shape
        if features.shape[0] != 1:
            raise ValueError(f"Expected 1 row, got {features.shape[0]}")
        
        expected_features = len(model_service.feature_names)
        if features.shape[1] != expected_features:
            raise ValueError(
                f"Expected {expected_features} features, got {features.shape[1]}"
            )
        
        # Check for NaN
        if np.isnan(features).any():
            raise ValueError("Preprocessed features contain NaN values")
        
        # Check for infinite values
        if np.isinf(features).any():
            raise ValueError("Preprocessed features contain infinite values")
        
        # Check range (scaled features should be roughly -3 to +3)
        # This is a sanity check, not a hard requirement
        if np.abs(features).max() > 10:
            logger.warning(
                f"Scaled features have large values (max: {np.abs(features).max():.2f}). "
                "This might indicate preprocessing issues."
            )
        
        logger.debug("✓ Preprocessed features validated")

# Global preprocessing service instance
preprocessing_service = PreprocessingService()
```

**Preprocessing Service Explanation:**

**1. Artifact Reuse:**
```python
label_encoders = model_service.label_encoders
scaler = model_service.scaler
feature_names = model_service.feature_names
```
- Uses exact same artifacts from training
- Guarantees consistency
- Prevents training-serving skew

**2. Unknown Category Handling:**
```python
except ValueError as e:
    # Handle unknown categories
    raise ValueError(f"Unknown category '{value}' in column '{col}'")
```
- Training saw: ["Manager", "Driver", "Laborer"]
- Inference sees: "Pilot" (unknown)
- Options:
  - Fail fast (current approach)
  - Map to "Unknown" category
  - Use most frequent category
- Choice depends on business requirements

**3. Feature Order:**
```python
df = df[feature_names]
```
- Model expects features in specific order
- If order is wrong, model gets wrong inputs
- Example: Model expects [age, income], gets [income, age] → wrong predictions

**4. Validation:**
```python
def _validate_preprocessed_features(self, features: np.ndarray):
```
- Sanity checks on preprocessed data
- Catches preprocessing bugs early
- Prevents garbage from reaching model

**5. Logging:**
```python
logger.debug(f"Encoded {col}: {df[col].values[0]}")
```
- Debug logs for troubleshooting
- Can trace preprocessing steps
- Useful when predictions are wrong

### 5.3 Think First: Preprocessing Edge Cases

**Question:** What happens if a new occupation type appears in production that wasn't in training?

<details>
<parameter name="summary">Click to review


**Answer:**

The LabelEncoder will raise a ValueError because it only knows categories from training. You have three options:

1. **Fail Fast** (current): Reject the request with clear error
2. **Map to "Unknown"**: Add "Unknown" category during training, map unseen values to it
3. **Retrain**: Add new category and retrain model

Best practice: Fail fast initially, monitor for new categories, retrain periodically.

</details>

### 5.4 Checkpoint

**Self-Assessment:**
- [ ] You understand training-serving skew
- [ ] You know why we reuse preprocessing artifacts
- [ ] You can handle unknown categories
- [ ] You understand feature order importance

## Chapter 6: Redis Caching

### 6.1 Why Cache Predictions?

Caching improves performance for repeated requests.

**Scenario:**
- Same applicant applies multiple times
- Same features → Same prediction
- Why recompute? Cache it!

**Benefits:**
- Faster response (Redis: <1ms vs Model: 10-50ms)
- Reduced CPU usage
- Better user experience

### 6.2 Redis Service Implementation

```python
# app/services/cache_service.py
"""Redis caching service for predictions."""

import redis.asyncio as redis
import json
import hashlib
from typing import Optional, Dict, Any
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class CacheService:
    """Redis caching for predictions."""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
    
    async def connect(self):
        """Connect to Redis."""
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("✓ Redis connected")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self.redis_client = None
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("✓ Redis disconnected")
    
    def _generate_cache_key(self, input_data: Dict[str, Any]) -> str:
        """Generate cache key from input features."""
        # Sort keys for consistent hashing
        sorted_data = json.dumps(input_data, sort_keys=True)
        # Hash to create short key
        return f"pred:{hashlib.md5(sorted_data.encode()).hexdigest()}"
    
    async def get_prediction(self, input_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get cached prediction."""
        if not self.redis_client:
            return None
        
        try:
            key = self._generate_cache_key(input_data)
            cached = await self.redis_client.get(key)
            
            if cached:
                logger.debug(f"Cache hit: {key}")
                return json.loads(cached)
            
            logger.debug(f"Cache miss: {key}")
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set_prediction(self, input_data: Dict[str, Any], prediction: Dict[str, Any]):
        """Cache prediction."""
        if not self.redis_client:
            return
        
        try:
            key = self._generate_cache_key(input_data)
            await self.redis_client.setex(
                key,
                settings.CACHE_TTL,
                json.dumps(prediction)
            )
            logger.debug(f"Cached: {key}")
        except Exception as e:
            logger.error(f"Cache set error: {e}")

cache_service = CacheService()
```

**Key Points:**
- Hash input features to create cache key
- TTL (time-to-live) expires old predictions
- Graceful degradation (if Redis fails, still works)

### 6.3 Checkpoint

**Self-Assessment:**
- [ ] You understand why caching improves performance
- [ ] You know how cache keys are generated
- [ ] You understand TTL concept

## Chapter 7: API Routers

### 7.1 Health Endpoints

```python
# app/routers/health.py
"""Health check endpoints."""

from fastapi import APIRouter, status
from datetime import datetime
from app.schemas.health import HealthResponse, ReadinessResponse
from app.services.model_service import model_service
from app.services.cache_service import cache_service
from app.core.database import engine

router = APIRouter(tags=["health"])

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Liveness probe - is the service running?"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow()
    )

@router.get("/health/ready", response_model=ReadinessResponse)
async def readiness_check():
    """Readiness probe - can the service handle requests?"""
    
    # Check model loaded
    model_loaded = model_service.is_ready()
    
    # Check database
    db_connected = True
    try:
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
    except:
        db_connected = False
    
    # Check Redis
    redis_connected = cache_service.redis_client is not None
    
    # Overall status
    is_ready = model_loaded and db_connected
    status_str = "ready" if is_ready else "not_ready"
    
    return ReadinessResponse(
        status=status_str,
        model_loaded=model_loaded,
        database_connected=db_connected,
        redis_connected=redis_connected,
        timestamp=datetime.utcnow()
    )
```

### 7.2 Prediction Endpoint

```python
# app/routers/predict.py
"""Prediction endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import time
import logging
from app.schemas.prediction import PredictionInput, PredictionOutput, ModelInfo
from app.services.model_service import model_service
from app.services.preprocessing_service import preprocessing_service
from app.services.cache_service import cache_service
from app.core.database import get_db, Prediction

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["predictions"])

@router.post("/predict", response_model=PredictionOutput)
async def predict(
    input_data: PredictionInput,
    db: AsyncSession = Depends(get_db)
):
    """Make credit card approval prediction."""
    
    start_time = time.time()
    
    # Check if model is ready
    if not model_service.is_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded"
        )
    
    try:
        # Check cache
        input_dict = input_data.model_dump(exclude={'request_id'})
        cached_result = await cache_service.get_prediction(input_dict)
        
        if cached_result:
            # Return cached result
            cached_result['from_cache'] = True
            cached_result['request_id'] = input_data.request_id
            return PredictionOutput(**cached_result)
        
        # Preprocess features
        features = preprocessing_service.preprocess(input_data)
        
        # Make prediction
        prediction_result = await model_service.predict(features)
        
        # Build response
        response = PredictionOutput(
            prediction=prediction_result['prediction'],
            probability=prediction_result['probability'],
            decision=prediction_result['decision'],
            confidence=prediction_result['confidence'],
            model_name=model_service.model_info.get('model_name', 'unknown'),
            model_version=model_service.model_info.get('model_version', 'unknown'),
            timestamp=datetime.utcnow(),
            request_id=input_data.request_id,
            from_cache=False
        )
        
        # Cache result
        await cache_service.set_prediction(input_dict, response.model_dump())
        
        # Log to database
        response_time = (time.time() - start_time) * 1000
        
        prediction_log = Prediction(
            model_name=response.model_name,
            model_version=response.model_version,
            prediction=response.prediction,
            probability=response.probability,
            decision=response.decision,
            income=input_data.AMT_INCOME_TOTAL,
            age_years=input_data.AGE_YEARS,
            employment_years=input_data.EMPLOYMENT_YEARS,
            request_id=input_data.request_id,
            response_time_ms=response_time,
            from_cache=False
        )
        
        db.add(prediction_log)
        await db.commit()
        
        logger.info(
            f"Prediction: {response.decision} "
            f"(prob={response.probability:.3f}, time={response_time:.1f}ms)"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/model-info", response_model=ModelInfo)
async def get_model_info():
    """Get current model information."""
    
    if not model_service.is_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded"
        )
    
    info = model_service.get_model_info()
    
    return ModelInfo(
        model_name=info['model_name'],
        model_version=info['model_version'],
        model_stage=info['model_stage'],
        model_uri=info['model_uri'],
        metrics=info.get('metrics', {}),
        loaded_at=datetime.fromisoformat(info['loaded_at'])
    )
```

**Prediction Flow:**
1. Check cache → return if hit
2. Preprocess features
3. Make prediction
4. Cache result
5. Log to database
6. Return response

### 7.3 Main Application

```python
# app/main.py
"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.database import init_db, close_db
from app.services.model_service import model_service
from app.services.cache_service import cache_service
from app.routers import health, predict

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("=" * 70)
    logger.info("STARTING APPLICATION")
    logger.info("=" * 70)
    
    # Initialize database
    await init_db()
    
    # Connect to Redis
    await cache_service.connect()
    
    # Load model
    await model_service.load_model()
    
    logger.info("=" * 70)
    logger.info("APPLICATION READY")
    logger.info("=" * 70)
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    await cache_service.disconnect()
    await close_db()

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(predict.router)

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }
```

**Lifespan Events:**
- Startup: Initialize DB, connect Redis, load model
- Shutdown: Cleanup connections

### 7.4 Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

# Copy application
COPY app/ ./app/

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 7.5 Requirements

```txt
# requirements-api.txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0
sqlalchemy==2.0.25
asyncpg==0.29.0
redis==5.0.1
mlflow==2.9.2
scikit-learn==1.3.2
xgboost==2.0.3
pandas==2.1.4
numpy==1.26.2
joblib==1.3.2
```

## Chapter 8: Docker Compose for Lab 02

```yaml
# docker-compose.local.lab02.yml
version: '3.8'

services:
  # Lab 01 services (Airflow + MLflow)
  postgres-airflow:
    # ... (same as lab01)
  
  postgres-mlflow:
    # ... (same as lab01)
  
  mlflow:
    # ... (same as lab01)
  
  airflow-init:
    # ... (same as lab01)
  
  airflow-webserver:
    # ... (same as lab01)
  
  airflow-scheduler:
    # ... (same as lab01)
  
  # NEW: Lab 02 services
  postgres-api:
    image: postgres:15-alpine
    container_name: lab02-postgres-api
    environment:
      POSTGRES_DB: card_approval_api
      POSTGRES_USER: api_user
      POSTGRES_PASSWORD: ${POSTGRES_API_PASSWORD:-api_password}
    ports:
      - "5432:5432"
    volumes:
      - postgres-api-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U api_user"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - lab02-network
  
  redis:
    image: redis:7-alpine
    container_name: lab02-redis
    command: redis-server --requirepass ${REDIS_PASSWORD:-redis_password}
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - lab02-network
  
  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: lab02-api
    environment:
      POSTGRES_HOST: postgres-api
      POSTGRES_PASSWORD: ${POSTGRES_API_PASSWORD:-api_password}
      REDIS_HOST: redis
      REDIS_PASSWORD: ${REDIS_PASSWORD:-redis_password}
      MLFLOW_TRACKING_URI: http://mlflow:5000
      MODEL_NAME: card_approval_production
      MODEL_STAGE: Production
    ports:
      - "8000:8000"
    volumes:
      - ./training/models:/app/models
    depends_on:
      postgres-api:
        condition: service_healthy
      redis:
        condition: service_healthy
      mlflow:
        condition: service_started
    networks:
      - lab02-network

networks:
  lab02-network:
    driver: bridge

volumes:
  postgres-api-data:
  redis-data:
  # ... (other volumes from lab01)
```

## Epilogue: The Complete System

You now have a production-ready ML API that:

✅ Loads models from MLflow Registry
✅ Validates input with Pydantic
✅ Caches predictions with Redis
✅ Logs predictions to PostgreSQL
✅ Provides health/readiness endpoints
✅ Handles errors gracefully
✅ Responds in <50ms (cached) or <100ms (uncached)

**Test the API:**

```bash
# Start services
docker-compose -f docker-compose.local.lab02.yml up -d

# Test health
curl http://localhost:8000/health

# Test prediction
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "CODE_GENDER": "M",
    "CNT_CHILDREN": 2,
    "AMT_INCOME_TOTAL": 180000,
    "AGE_YEARS": 35,
    "EMPLOYMENT_YEARS": 10,
    ...
  }'

# View docs
open http://localhost:8000/docs
```

## The Principles

1. **Training-Serving Consistency** — Reuse preprocessing artifacts
2. **Fail Fast** — Validate early, reject bad input
3. **Cache Aggressively** — Same input = same output
4. **Log Everything** — Audit trail for compliance
5. **Graceful Degradation** — Work even if Redis fails
6. **Health Checks** — Enable orchestration
7. **Observability** — Log, metrics, traces

## Troubleshooting

**Model Not Loading:**
```bash
# Check MLflow connection
docker exec lab02-api curl http://mlflow:5000/health

# Check model exists
docker exec lab02-api python -c "
import mlflow
mlflow.set_tracking_uri('http://mlflow:5000')
print(mlflow.search_registered_models())
"
```

**Redis Connection Failed:**
```bash
# Check Redis
docker exec lab02-redis redis-cli ping
```

**Preprocessing Errors:**
```bash
# Check artifacts exist
docker exec lab02-api ls -la /app/models/
```

## Next Steps

Lab 03 will add:
- Prometheus metrics
- Grafana dashboards
- Loki logging
- Tempo tracing
- Nginx reverse proxy

---

**🎉 Lab 02 Complete! Ready for Lab 03: Monitoring**
