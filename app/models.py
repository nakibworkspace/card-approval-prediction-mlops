"""
SQLAlchemy models for database tables
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Decimal, DateTime, Boolean, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.database import Base


class Prediction(Base):
    """Prediction records table"""
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    prediction_id = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    
    # Input features
    customer_id = Column(Integer)
    code_gender = Column(String(10))
    flag_own_car = Column(String(10))
    flag_own_realty = Column(String(10))
    cnt_children = Column(Integer)
    amt_income_total = Column(Decimal(12, 2))
    name_income_type = Column(String(50))
    name_education_type = Column(String(50))
    name_family_status = Column(String(50))
    name_housing_type = Column(String(50))
    days_birth = Column(Integer)
    days_employed = Column(Integer)
    flag_mobil = Column(Integer)
    flag_work_phone = Column(Integer)
    flag_phone = Column(Integer)
    flag_email = Column(Integer)
    occupation_type = Column(String(50))
    cnt_fam_members = Column(Decimal(3, 1))
    
    # Prediction results
    prediction = Column(Integer, nullable=False)
    probability = Column(Decimal(5, 4), nullable=False)
    decision = Column(String(20), nullable=False)
    confidence = Column(Decimal(5, 4), nullable=False)
    model_version = Column(String(50))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    response_time_ms = Column(Integer)

    __table_args__ = (
        Index('idx_created_at', 'created_at'),
        Index('idx_prediction', 'prediction'),
        Index('idx_customer_id', 'customer_id'),
    )


class PredictionCache(Base):
    """Prediction cache table"""
    __tablename__ = "prediction_cache"

    id = Column(Integer, primary_key=True, index=True)
    cache_key = Column(String(255), unique=True, nullable=False, index=True)
    prediction_result = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False, index=True)
    hit_count = Column(Integer, default=0)


class ModelPerformance(Base):
    """Model performance metrics table"""
    __tablename__ = "model_performance"

    id = Column(Integer, primary_key=True, index=True)
    model_version = Column(String(50), nullable=False, index=True)
    metric_name = Column(String(50), nullable=False)
    metric_value = Column(Decimal(10, 6), nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)


class DriftDetection(Base):
    """Drift detection results table"""
    __tablename__ = "drift_detection"

    id = Column(Integer, primary_key=True, index=True)
    drift_detected = Column(Boolean, nullable=False, index=True)
    drift_share = Column(Decimal(5, 4))
    drifted_features = Column(JSON)
    num_drifted_features = Column(Integer)
    report_path = Column(String(255))
    detected_at = Column(DateTime, default=datetime.utcnow, index=True)
