-- Initialize Card Approval API Database

-- Create predictions table
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    prediction_id UUID UNIQUE NOT NULL,
    
    -- Input features
    customer_id INTEGER,
    code_gender VARCHAR(10),
    flag_own_car VARCHAR(10),
    flag_own_realty VARCHAR(10),
    cnt_children INTEGER,
    amt_income_total DECIMAL(12, 2),
    name_income_type VARCHAR(50),
    name_education_type VARCHAR(50),
    name_family_status VARCHAR(50),
    name_housing_type VARCHAR(50),
    days_birth INTEGER,
    days_employed INTEGER,
    flag_mobil INTEGER,
    flag_work_phone INTEGER,
    flag_phone INTEGER,
    flag_email INTEGER,
    occupation_type VARCHAR(50),
    cnt_fam_members DECIMAL(3, 1),
    
    -- Prediction results
    prediction INTEGER NOT NULL,
    probability DECIMAL(5, 4) NOT NULL,
    decision VARCHAR(20) NOT NULL,
    confidence DECIMAL(5, 4) NOT NULL,
    model_version VARCHAR(50),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    response_time_ms INTEGER,
    
    -- Indexing
    INDEX idx_created_at (created_at),
    INDEX idx_prediction (prediction),
    INDEX idx_customer_id (customer_id)
);

-- Create prediction cache table (for frequently requested predictions)
CREATE TABLE IF NOT EXISTS prediction_cache (
    id SERIAL PRIMARY KEY,
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    prediction_result JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    hit_count INTEGER DEFAULT 0,
    
    INDEX idx_cache_key (cache_key),
    INDEX idx_expires_at (expires_at)
);

-- Create model performance tracking table
CREATE TABLE IF NOT EXISTS model_performance (
    id SERIAL PRIMARY KEY,
    model_version VARCHAR(50) NOT NULL,
    metric_name VARCHAR(50) NOT NULL,
    metric_value DECIMAL(10, 6) NOT NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_model_version (model_version),
    INDEX idx_recorded_at (recorded_at)
);

-- Create drift detection results table
CREATE TABLE IF NOT EXISTS drift_detection (
    id SERIAL PRIMARY KEY,
    drift_detected BOOLEAN NOT NULL,
    drift_share DECIMAL(5, 4),
    drifted_features JSONB,
    num_drifted_features INTEGER,
    report_path VARCHAR(255),
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_detected_at (detected_at),
    INDEX idx_drift_detected (drift_detected)
);

-- Create function to clean expired cache
CREATE OR REPLACE FUNCTION clean_expired_cache()
RETURNS void AS $$
BEGIN
    DELETE FROM prediction_cache WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- Create function to get prediction statistics
CREATE OR REPLACE FUNCTION get_prediction_stats(days INTEGER DEFAULT 7)
RETURNS TABLE (
    total_predictions BIGINT,
    approved_count BIGINT,
    rejected_count BIGINT,
    approval_rate DECIMAL(5, 4),
    avg_confidence DECIMAL(5, 4),
    avg_response_time_ms DECIMAL(10, 2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT as total_predictions,
        SUM(CASE WHEN prediction = 1 THEN 1 ELSE 0 END)::BIGINT as approved_count,
        SUM(CASE WHEN prediction = 0 THEN 1 ELSE 0 END)::BIGINT as rejected_count,
        (SUM(CASE WHEN prediction = 1 THEN 1 ELSE 0 END)::DECIMAL / NULLIF(COUNT(*), 0))::DECIMAL(5, 4) as approval_rate,
        AVG(confidence)::DECIMAL(5, 4) as avg_confidence,
        AVG(response_time_ms)::DECIMAL(10, 2) as avg_response_time_ms
    FROM predictions
    WHERE created_at >= NOW() - INTERVAL '1 day' * days;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO api_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO api_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO api_user;

-- Insert initial data (optional)
INSERT INTO model_performance (model_version, metric_name, metric_value) VALUES
    ('1.0.0', 'f1_score', 0.9234),
    ('1.0.0', 'roc_auc', 0.9567),
    ('1.0.0', 'precision', 0.9123),
    ('1.0.0', 'recall', 0.9345);

COMMENT ON TABLE predictions IS 'Stores all prediction requests and results';
COMMENT ON TABLE prediction_cache IS 'Caches frequently requested predictions';
COMMENT ON TABLE model_performance IS 'Tracks model performance metrics over time';
COMMENT ON TABLE drift_detection IS 'Stores drift detection results';
