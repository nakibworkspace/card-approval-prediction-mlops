# Lab 02: Part 2 - Pydantic Schemas and Services

## Chapter 3: Pydantic Schemas

### 3.1 Understanding Pydantic Validation

Pydantic provides automatic validation, serialization, and documentation.

**Validation Flow:**
```
1. Client sends JSON
   ↓
2. FastAPI receives request
   ↓
3. Pydantic parses JSON
   ↓
4. Pydantic validates types
   ↓
5. Pydantic validates constraints (Field)
   ↓
6. Pydantic runs custom validators
   ↓
7. If valid: Create Python object
   If invalid: Return 422 error
```

### 3.2 Health Check Schemas

Create schemas for health endpoints.

```python
# app/schemas/health.py
"""
Health check schemas.

Used by load balancers and orchestration systems
to determine service health and readiness.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class HealthResponse(BaseModel):
    """
    Basic health check response.
    
    Indicates if the service process is running.
    Used for liveness probes.
    """
    status: str  # "healthy" or "unhealthy"
    timestamp: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2024-01-15T10:30:00"
            }
        }

class ReadinessResponse(BaseModel):
    """
    Readiness check response.
    
    Indicates if the service can handle requests.
    Used for readiness probes.
    """
    status: str  # "ready" or "not_ready"
    model_loaded: bool
    database_connected: bool
    redis_connected: bool
    timestamp: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "ready",
                "model_loaded": True,
                "database_connected": True,
                "redis_connected": True,
                "timestamp": "2024-01-15T10:30:00"
            }
        }
```

**Schema Explanation:**

**1. Config.json_schema_extra:**
- Provides example in OpenAPI docs
- Helps API consumers understand response format
- Shows up in Swagger UI

**2. Liveness vs. Readiness:**
- **Liveness**: Is process alive? (if not, restart container)
- **Readiness**: Can serve requests? (if not, don't route traffic)

### 3.3 Prediction Schemas

Create comprehensive schemas for predictions.

```python
# app/schemas/prediction.py
"""
Prediction request and response schemas.

Defines input validation and output format for predictions.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class PredictionInput(BaseModel):
    """
    Credit card approval prediction input.
    
    All features required for prediction.
    Validation ensures data quality before inference.
    """
    
    # ========================================
    # DEMOGRAPHIC FEATURES
    # ========================================
    CODE_GENDER: str = Field(
        ...,
        pattern="^[MF]$",
        description="Gender: M (Male) or F (Female)"
    )
    
    CNT_CHILDREN: int = Field(
        ...,
        ge=0,
        le=20,
        description="Number of children (0-20)"
    )
    
    NAME_FAMILY_STATUS: str = Field(
        ...,
        description="Marital status (e.g., Married, Single)"
    )
    
    NAME_EDUCATION_TYPE: str = Field(
        ...,
        description="Education level (e.g., Higher education, Secondary)"
    )
    
    # ========================================
    # FINANCIAL FEATURES
    # ========================================
    AMT_INCOME_TOTAL: float = Field(
        ...,
        gt=0,
        le=10000000,
        description="Annual income in dollars (must be positive)"
    )
    
    NAME_INCOME_TYPE: str = Field(
        ...,
        description="Income source (e.g., Working, Commercial)"
    )
    
    FLAG_OWN_CAR: str = Field(
        ...,
        pattern="^[YN]$",
        description="Car ownership: Y (Yes) or N (No)"
    )
    
    FLAG_OWN_REALTY: str = Field(
        ...,
        pattern="^[YN]$",
        description="Property ownership: Y (Yes) or N (No)"
    )
    
    # ========================================
    # EMPLOYMENT FEATURES
    # ========================================
    OCCUPATION_TYPE: str = Field(
        ...,
        description="Job category (e.g., Managers, Laborers, Unknown)"
    )
    
    # ========================================
    # TEMPORAL FEATURES (in years, not days)
    # ========================================
    AGE_YEARS: float = Field(
        ...,
        ge=18,
        le=100,
        description="Age in years (18-100)"
    )
    
    EMPLOYMENT_YEARS: float = Field(
        ...,
        ge=0,
        le=80,
        description="Years of employment (0-80)"
    )
    
    # ========================================
    # CONTACT FEATURES
    # ========================================
    FLAG_MOBIL: int = Field(
        ...,
        ge=0,
        le=1,
        description="Mobile phone: 1 (Yes) or 0 (No)"
    )
    
    FLAG_WORK_PHONE: int = Field(
        ...,
        ge=0,
        le=1,
        description="Work phone: 1 (Yes) or 0 (No)"
    )
    
    FLAG_PHONE: int = Field(
        ...,
        ge=0,
        le=1,
        description="Home phone: 1 (Yes) or 0 (No)"
    )
    
    FLAG_EMAIL: int = Field(
        ...,
        ge=0,
        le=1,
        description="Email: 1 (Yes) or 0 (No)"
    )
    
    # ========================================
    # HOUSEHOLD FEATURES
    # ========================================
    NAME_HOUSING_TYPE: str = Field(
        ...,
        description="Housing situation (e.g., House / apartment, Rented)"
    )
    
    CNT_FAM_MEMBERS: float = Field(
        ...,
        ge=1,
        le=20,
        description="Family size (1-20)"
    )
    
    # ========================================
    # OPTIONAL METADATA
    # ========================================
    request_id: Optional[str] = Field(
        None,
        description="Optional request ID for tracing"
    )
    
    # ========================================
    # CUSTOM VALIDATORS
    # ========================================
    @validator('EMPLOYMENT_YEARS')
    def validate_employment_years(cls, v, values):
        """
        Validate employment years against age.
        
        Employment years cannot exceed (age - 18).
        Minimum working age is 18.
        """
        if 'AGE_YEARS' in values:
            max_employment = values['AGE_YEARS'] - 18
            if v > max_employment:
                raise ValueError(
                    f"Employment years ({v}) cannot exceed age - 18 ({max_employment})"
                )
        return v
    
    @validator('CNT_FAM_MEMBERS')
    def validate_family_members(cls, v, values):
        """
        Validate family members against children.
        
        Family members must be at least children + 1 (applicant).
        """
        if 'CNT_CHILDREN' in values:
            min_family = values['CNT_CHILDREN'] + 1
            if v < min_family:
                raise ValueError(
                    f"Family members ({v}) must be at least children + 1 ({min_family})"
                )
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "CODE_GENDER": "M",
                "CNT_CHILDREN": 2,
                "NAME_FAMILY_STATUS": "Married",
                "NAME_EDUCATION_TYPE": "Higher education",
                "AMT_INCOME_TOTAL": 180000.0,
                "NAME_INCOME_TYPE": "Working",
                "FLAG_OWN_CAR": "Y",
                "FLAG_OWN_REALTY": "Y",
                "OCCUPATION_TYPE": "Managers",
                "AGE_YEARS": 35.0,
                "EMPLOYMENT_YEARS": 10.0,
                "FLAG_MOBIL": 1,
                "FLAG_WORK_PHONE": 1,
                "FLAG_PHONE": 1,
                "FLAG_EMAIL": 1,
                "NAME_HOUSING_TYPE": "House / apartment",
                "CNT_FAM_MEMBERS": 4.0,
                "request_id": "req_123456"
            }
        }

class PredictionOutput(BaseModel):
    """
    Credit card approval prediction output.
    
    Provides prediction, probability, and decision.
    """
    prediction: int = Field(
        ...,
        description="Prediction: 0 (Rejected) or 1 (Approved)"
    )
    
    probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Approval probability (0.0 to 1.0)"
    )
    
    decision: str = Field(
        ...,
        description="Human-readable decision: APPROVED or REJECTED"
    )
    
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (distance from 0.5 threshold)"
    )
    
    model_name: str = Field(
        ...,
        description="Model name used for prediction"
    )
    
    model_version: str = Field(
        ...,
        description="Model version used for prediction"
    )
    
    timestamp: datetime = Field(
        ...,
        description="Prediction timestamp"
    )
    
    request_id: Optional[str] = Field(
        None,
        description="Request ID (if provided in input)"
    )
    
    from_cache: bool = Field(
        default=False,
        description="Whether result was served from cache"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "prediction": 1,
                "probability": 0.8542,
                "decision": "APPROVED",
                "confidence": 0.7084,
                "model_name": "card_approval_production",
                "model_version": "3",
                "timestamp": "2024-01-15T10:30:00",
                "request_id": "req_123456",
                "from_cache": False
            }
        }

class ModelInfo(BaseModel):
    """
    Model information response.
    
    Provides transparency about which model is serving predictions.
    """
    model_name: str
    model_version: str
    model_stage: str
    model_uri: str
    metrics: dict
    loaded_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "model_name": "card_approval_production",
                "model_version": "3",
                "model_stage": "Production",
                "model_uri": "models:/card_approval_production/Production",
                "metrics": {
                    "roc_auc": 0.9123,
                    "f1_score": 0.8234,
                    "precision": 0.8456,
                    "recall": 0.8023
                },
                "loaded_at": "2024-01-15T10:00:00"
            }
        }
```

**Schema Design Explanation:**

**1. Field Descriptions:**
```python
Field(..., description="Age in years (18-100)")
```
- Shows in OpenAPI docs
- Helps API consumers understand fields
- Self-documenting API

**2. Validation Constraints:**
```python
Field(..., ge=18, le=100)
```
- `ge`: Greater than or equal
- `le`: Less than or equal
- `gt`: Greater than
- `lt`: Less than
- `pattern`: Regex pattern

**3. Custom Validators:**
```python
@validator('EMPLOYMENT_YEARS')
def validate_employment_years(cls, v, values):
```
- Cross-field validation
- Business logic validation
- Access to other field values via `values` dict

**4. Optional Fields:**
```python
request_id: Optional[str] = Field(None, ...)
```
- Not required for prediction
- Useful for tracing/debugging
- Defaults to None if not provided

**5. Config Examples:**
- Shows up in Swagger UI
- Helps developers test API
- Documents expected format

### 3.4 Understanding Validation Errors

When validation fails, Pydantic returns detailed error messages.

**Example Invalid Request:**
```json
{
  "CODE_GENDER": "X",
  "AGE_YEARS": 15,
  "EMPLOYMENT_YEARS": 20,
  "AMT_INCOME_TOTAL": -5000
}
```

**Pydantic Response (422):**
```json
{
  "detail": [
    {
      "loc": ["body", "CODE_GENDER"],
      "msg": "string does not match regex \"^[MF]$\"",
      "type": "value_error.str.regex"
    },
    {
      "loc": ["body", "AGE_YEARS"],
      "msg": "ensure this value is greater than or equal to 18",
      "type": "value_error.number.not_ge"
    },
    {
      "loc": ["body", "EMPLOYMENT_YEARS"],
      "msg": "Employment years (20) cannot exceed age - 18 (-3)",
      "type": "value_error"
    },
    {
      "loc": ["body", "AMT_INCOME_TOTAL"],
      "msg": "ensure this value is greater than 0",
      "type": "value_error.number.not_gt"
    }
  ]
}
```

**Error Structure:**
- `loc`: Where error occurred (path to field)
- `msg`: Human-readable error message
- `type`: Error type (for programmatic handling)

**Why This Matters:**
- Clear error messages improve developer experience
- Clients can display specific field errors
- Prevents bad data from reaching model

### 3.5 Checkpoint

Verify your understanding of Pydantic schemas.

**Self-Assessment:**
- [ ] You understand Field constraints (ge, le, pattern)
- [ ] You know how to write custom validators
- [ ] You understand cross-field validation
- [ ] You can interpret validation error responses
- [ ] You know the difference between required and optional fields
- [ ] You understand the purpose of Config.json_schema_extra

**Practical Exercise:**

Test the validation logic:

```python
from app.schemas.prediction import PredictionInput

# Valid input
valid_data = {
    "CODE_GENDER": "M",
    "AGE_YEARS": 35,
    "EMPLOYMENT_YEARS": 10,
    # ... other fields
}

try:
    input_obj = PredictionInput(**valid_data)
    print("✓ Valid")
except Exception as e:
    print(f"✗ Invalid: {e}")

# Invalid input (employment > age - 18)
invalid_data = {
    "CODE_GENDER": "M",
    "AGE_YEARS": 25,
    "EMPLOYMENT_YEARS": 20,  # 20 > (25 - 18)
    # ... other fields
}

try:
    input_obj = PredictionInput(**invalid_data)
    print("✓ Valid")
except Exception as e:
    print(f"✗ Invalid: {e}")
```

## Chapter 4: Model Service

### 4.1 Model Loading Strategy

Create a service to load and manage the ML model.

```python
# app/services/model_service.py
"""
Model service for loading and managing ML models.

Loads model from MLflow Registry and preprocessing artifacts.
Provides prediction interface with consistent preprocessing.
"""

import mlflow
import mlflow.sklearn
import joblib
import numpy as np
from typing import Optional, Dict, Any
from datetime import datetime
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class ModelService:
    """
    Service for ML model management.
    
    Responsibilities:
    - Load model from MLflow Registry
    - Load preprocessing artifacts (scaler, encoders)
    - Provide prediction interface
    - Track model metadata
    """
    
    def __init__(self):
        """Initialize model service."""
        self.model = None
        self.scaler = None
        self.label_encoders = None
        self.feature_names = None
        self.model_info = {}
        self.loaded_at = None
    
    async def load_model(self):
        """
        Load model and preprocessing artifacts.
        
        Steps:
        1. Configure MLflow tracking URI
        2. Load model from registry
        3. Load preprocessing artifacts
        4. Extract model metadata
        5. Validate everything loaded correctly
        
        Raises:
            Exception: If model or artifacts cannot be loaded
        """
        try:
            logger.info("=" * 70)
            logger.info("LOADING MODEL FROM MLFLOW")
            logger.info("=" * 70)
            
            # ========================================
            # STEP 1: CONFIGURE MLFLOW
            # ========================================
            mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
            logger.info(f"MLflow URI: {settings.MLFLOW_TRACKING_URI}")
            
            # ========================================
            # STEP 2: LOAD MODEL FROM REGISTRY
            # ========================================
            model_uri = f"models:/{settings.MODEL_NAME}/{settings.MODEL_STAGE}"
            logger.info(f"Loading model: {model_uri}")
            
            self.model = mlflow.sklearn.load_model(model_uri)
            logger.info(f"✓ Model loaded: {type(self.model).__name__}")
            
            # ========================================
            # STEP 3: LOAD PREPROCESSING ARTIFACTS
            # ========================================
            logger.info("Loading preprocessing artifacts...")
            
            # Load scaler
            self.scaler = joblib.load(settings.SCALER_PATH)
            logger.info(f"✓ Scaler loaded: {type(self.scaler).__name__}")
            
            # Load label encoders
            self.label_encoders = joblib.load(settings.ENCODERS_PATH)
            logger.info(f"✓ Label encoders loaded: {len(self.label_encoders)} encoders")
            
            # Load feature names
            self.feature_names = joblib.load(settings.FEATURES_PATH)
            logger.info(f"✓ Feature names loaded: {len(self.feature_names)} features")
            
            # ========================================
            # STEP 4: EXTRACT MODEL METADATA
            # ========================================
            from mlflow.tracking import MlflowClient
            client = MlflowClient()
            
            # Get model version details
            model_versions = client.search_model_versions(
                f"name='{settings.MODEL_NAME}'"
            )
            
            # Find the version in specified stage
            current_version = None
            for mv in model_versions:
                if mv.current_stage == settings.MODEL_STAGE:
                    current_version = mv
                    break
            
            if current_version:
                # Get run details for metrics
                run = client.get_run(current_version.run_id)
                
                self.model_info = {
                    "model_name": settings.MODEL_NAME,
                    "model_version": current_version.version,
                    "model_stage": current_version.current_stage,
                    "model_uri": model_uri,
                    "run_id": current_version.run_id,
                    "metrics": run.data.metrics,
                    "description": current_version.description or "No description"
                }
                
                logger.info(f"✓ Model metadata extracted")
                logger.info(f"  Version: {current_version.version}")
                logger.info(f"  Stage: {current_version.current_stage}")
                logger.info(f"  Metrics: {run.data.metrics}")
            else:
                logger.warning(f"No model found in {settings.MODEL_STAGE} stage")
                self.model_info = {
                    "model_name": settings.MODEL_NAME,
                    "model_version": "unknown",
                    "model_stage": settings.MODEL_STAGE,
                    "model_uri": model_uri,
                    "metrics": {}
                }
            
            # ========================================
            # STEP 5: VALIDATE
            # ========================================
            self._validate_loaded_components()
            
            self.loaded_at = datetime.utcnow()
            
            logger.info("=" * 70)
            logger.info("MODEL LOADED SUCCESSFULLY")
            logger.info("=" * 70)
            logger.info("")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def _validate_loaded_components(self):
        """
        Validate all components loaded correctly.
        
        Checks:
        - Model is not None
        - Scaler is not None
        - Label encoders is not None
        - Feature names is not None
        - Model has predict method
        - Model has predict_proba method
        
        Raises:
            ValueError: If validation fails
        """
        if self.model is None:
            raise ValueError("Model is None")
        
        if self.scaler is None:
            raise ValueError("Scaler is None")
        
        if self.label_encoders is None:
            raise ValueError("Label encoders is None")
        
        if self.feature_names is None:
            raise ValueError("Feature names is None")
        
        if not hasattr(self.model, 'predict'):
            raise ValueError("Model does not have predict method")
        
        if not hasattr(self.model, 'predict_proba'):
            raise ValueError("Model does not have predict_proba method")
        
        logger.info("✓ All components validated")
    
    def is_ready(self) -> bool:
        """
        Check if model is ready to serve predictions.
        
        Returns:
            bool: True if model is loaded and ready
        """
        return (
            self.model is not None and
            self.scaler is not None and
            self.label_encoders is not None and
            self.feature_names is not None
        )
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get model information.
        
        Returns:
            dict: Model metadata including version, metrics, etc.
        """
        return {
            **self.model_info,
            "loaded_at": self.loaded_at.isoformat() if self.loaded_at else None,
            "is_ready": self.is_ready()
        }
    
    async def predict(self, features: np.ndarray) -> Dict[str, Any]:
        """
        Make prediction using loaded model.
        
        Args:
            features: Preprocessed feature array (scaled, encoded)
        
        Returns:
            dict: Prediction results
                - prediction: 0 or 1
                - probability: float (0.0 to 1.0)
                - decision: "APPROVED" or "REJECTED"
                - confidence: float (distance from 0.5)
        
        Raises:
            ValueError: If model is not loaded
        """
        if not self.is_ready():
            raise ValueError("Model is not loaded")
        
        # Get prediction
        prediction = self.model.predict(features)[0]
        
        # Get probability
        probability = self.model.predict_proba(features)[0][1]
        
        # Determine decision
        decision = "APPROVED" if prediction == 1 else "REJECTED"
        
        # Calculate confidence (distance from 0.5 threshold)
        confidence = abs(probability - 0.5) * 2
        
        return {
            "prediction": int(prediction),
            "probability": float(probability),
            "decision": decision,
            "confidence": float(confidence)
        }

# Global model service instance
model_service = ModelService()
```

**Model Service Explanation:**

**1. Singleton Pattern:**
```python
model_service = ModelService()
```
- One instance shared across application
- Model loaded once, used by all requests
- Memory efficient

**2. Lazy Loading:**
- Model not loaded in `__init__`
- Loaded explicitly via `load_model()`
- Allows application to start even if MLflow is temporarily unavailable

**3. Validation:**
```python
def _validate_loaded_components(self):
```
- Ensures all components loaded correctly
- Fails fast if something is wrong
- Prevents silent failures

**4. Readiness Check:**
```python
def is_ready(self) -> bool:
```
- Used by readiness endpoint
- Load balancer checks this before routing traffic
- Prevents requests to unready service

**5. Metadata Tracking:**
```python
self.model_info = {...}
```
- Tracks which model version is serving
- Useful for debugging
- Required for compliance

---

**Continue to Part 3 for Preprocessing Service and Routers...**
