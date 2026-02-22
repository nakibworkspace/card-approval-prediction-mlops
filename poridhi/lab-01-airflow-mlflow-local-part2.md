# Lab 01: Part 2 - Implementation and Airflow Integration

## Chapter 3: Data Preprocessing Implementation

### 3.1 Building the Preprocessing Pipeline

Now implement the preprocessing strategy developed in Chapter 1. Each step is explained in detail.

```python
# training/scripts/preprocess_data.py
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from imblearn.over_sampling import SMOTE
import joblib
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def preprocess_data(
    input_path='training/data/raw/application_record.csv',
    output_dir='training/data/processed',
    model_dir='training/models'
):
    """
    Complete preprocessing pipeline for credit card approval data.
    
    Pipeline Steps:
    1. Load raw data
    2. Handle missing values
    3. Feature engineering (temporal conversions)
    4. Encode categorical variables
    5. Train-test split (stratified)
    6. Feature scaling
    7. Handle class imbalance (SMOTE)
    8. Save processed data and artifacts
    
    Args:
        input_path: Path to raw CSV file
        output_dir: Directory to save processed data
        model_dir: Directory to save preprocessing artifacts
        
    Returns:
        tuple: (X_train_balanced, y_train_balanced, X_test, y_test)
    """
    
    # Create output directories
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(model_dir, exist_ok=True)
    
    logger.info("=" * 70)
    logger.info("CREDIT CARD APPROVAL - DATA PREPROCESSING PIPELINE")
    logger.info("=" * 70)
    logger.info("")
    
    # ========================================
    # STEP 1: LOAD DATA
    # ========================================
    logger.info("STEP 1: Loading Data")
    logger.info("-" * 70)
    
    df = pd.read_csv(input_path)
    logger.info(f"✓ Loaded {len(df):,} samples with {df.shape[1]} features")
    logger.info(f"  Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
    logger.info("")
    
    # ========================================
    # STEP 2: HANDLE MISSING VALUES
    # ========================================
    logger.info("STEP 2: Handling Missing Values")
    logger.info("-" * 70)
    
    # Check missing values before
    missing_before = df.isnull().sum().sum()
    logger.info(f"Missing values before: {missing_before}")
    
    # Strategy 1: Categorical - Fill with 'Unknown'
    # Rationale: Creates a new category for missing occupation
    # This allows the model to learn patterns for people without reported occupation
    if 'OCCUPATION_TYPE' in df.columns:
        missing_occupation = df['OCCUPATION_TYPE'].isnull().sum()
        df['OCCUPATION_TYPE'].fillna('Unknown', inplace=True)
        logger.info(f"✓ OCCUPATION_TYPE: Filled {missing_occupation} missing values with 'Unknown'")
    
    # Strategy 2: Numeric - Fill with median
    # Rationale: Median is robust to outliers (unlike mean)
    # Preserves the central tendency of the distribution
    if 'CNT_FAM_MEMBERS' in df.columns:
        missing_fam = df['CNT_FAM_MEMBERS'].isnull().sum()
        median_fam = df['CNT_FAM_MEMBERS'].median()
        df['CNT_FAM_MEMBERS'].fillna(median_fam, inplace=True)
        logger.info(f"✓ CNT_FAM_MEMBERS: Filled {missing_fam} missing values with median ({median_fam})")
    
    missing_after = df.isnull().sum().sum()
    logger.info(f"Missing values after: {missing_after}")
    logger.info("")
    
    # ========================================
    # STEP 3: FEATURE ENGINEERING
    # ========================================
    logger.info("STEP 3: Feature Engineering")
    logger.info("-" * 70)
    
    # Convert DAYS_BIRTH to AGE_YEARS
    # Original: Negative days before application (e.g., -14000)
    # Converted: Positive years (e.g., 38.4 years)
    # Rationale: Human-interpretable, easier to validate
    if 'DAYS_BIRTH' in df.columns:
        df['AGE_YEARS'] = -df['DAYS_BIRTH'] / 365.25  # 365.25 accounts for leap years
        age_range = (df['AGE_YEARS'].min(), df['AGE_YEARS'].max())
        logger.info(f"✓ Created AGE_YEARS from DAYS_BIRTH")
        logger.info(f"  Range: {age_range[0]:.1f} to {age_range[1]:.1f} years")
        df.drop('DAYS_BIRTH', axis=1, inplace=True)
    
    # Convert DAYS_EMPLOYED to EMPLOYMENT_YEARS
    # Original: Negative days (e.g., -2500)
    # Converted: Positive years (e.g., 6.8 years)
    # Special case: Very large positive values indicate unemployment
    if 'DAYS_EMPLOYED' in df.columns:
        # Handle anomaly: positive values mean unemployed
        df['EMPLOYMENT_YEARS'] = df['DAYS_EMPLOYED'].apply(
            lambda x: -x / 365.25 if x < 0 else 0
        )
        emp_range = (df['EMPLOYMENT_YEARS'].min(), df['EMPLOYMENT_YEARS'].max())
        logger.info(f"✓ Created EMPLOYMENT_YEARS from DAYS_EMPLOYED")
        logger.info(f"  Range: {emp_range[0]:.1f} to {emp_range[1]:.1f} years")
        df.drop('DAYS_EMPLOYED', axis=1, inplace=True)
    
    logger.info("")
    
    # ========================================
    # STEP 4: ENCODE CATEGORICAL VARIABLES
    # ========================================
    logger.info("STEP 4: Encoding Categorical Variables")
    logger.info("-" * 70)
    
    # Identify categorical columns
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    
    # Remove target if present
    if 'TARGET' in categorical_cols:
        categorical_cols.remove('TARGET')
    
    logger.info(f"Found {len(categorical_cols)} categorical columns")
    
    # Create and apply label encoders
    # LabelEncoder converts categories to integers (0, 1, 2, ...)
    # We save encoders to use the same mapping during inference
    label_encoders = {}
    
    for col in categorical_cols:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
        label_encoders[col] = le
        
        n_categories = len(le.classes_)
        logger.info(f"✓ {col:<25} → {n_categories} categories encoded")
    
    # Save label encoders for inference
    encoder_path = os.path.join(model_dir, 'label_encoders.pkl')
    joblib.dump(label_encoders, encoder_path)
    logger.info(f"\n✓ Saved label encoders to {encoder_path}")
    logger.info("")
    
    # ========================================
    # STEP 5: SPLIT FEATURES AND TARGET
    # ========================================
    logger.info("STEP 5: Splitting Features and Target")
    logger.info("-" * 70)
    
    # Separate features (X) and target (y)
    X = df.drop('TARGET', axis=1)
    y = df['TARGET']
    
    logger.info(f"Features (X): {X.shape}")
    logger.info(f"Target (y):   {y.shape}")
    
    # Show target distribution
    target_dist = y.value_counts().sort_index()
    target_pct = (target_dist / len(y)) * 100
    logger.info(f"\nTarget distribution:")
    logger.info(f"  Class 0 (Rejected): {target_dist[0]:>6,} ({target_pct[0]:>5.1f}%)")
    logger.info(f"  Class 1 (Approved): {target_dist[1]:>6,} ({target_pct[1]:>5.1f}%)")
    logger.info("")
    
    # ========================================
    # STEP 6: TRAIN-TEST SPLIT (STRATIFIED)
    # ========================================
    logger.info("STEP 6: Train-Test Split (Stratified)")
    logger.info("-" * 70)
    
    # Stratified split preserves class distribution in both sets
    # This is crucial for imbalanced datasets
    # test_size=0.2 means 80% train, 20% test
    # random_state=42 ensures reproducibility
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42,
        stratify=y  # KEY: Preserve class ratio
    )
    
    logger.info(f"Training set:   {X_train.shape[0]:>6,} samples ({X_train.shape[0]/len(X)*100:.1f}%)")
    logger.info(f"Test set:       {X_test.shape[0]:>6,} samples ({X_test.shape[0]/len(X)*100:.1f}%)")
    
    # Verify stratification worked
    train_dist = y_train.value_counts().sort_index()
    test_dist = y_test.value_counts().sort_index()
    train_pct = (train_dist / len(y_train)) * 100
    test_pct = (test_dist / len(y_test)) * 100
    
    logger.info(f"\nClass distribution verification:")
    logger.info(f"  Train - Class 0: {train_pct[0]:.1f}%, Class 1: {train_pct[1]:.1f}%")
    logger.info(f"  Test  - Class 0: {test_pct[0]:.1f}%, Class 1: {test_pct[1]:.1f}%")
    logger.info("")
    
    # ========================================
    # STEP 7: FEATURE SCALING
    # ========================================
    logger.info("STEP 7: Feature Scaling (StandardScaler)")
    logger.info("-" * 70)
    
    # StandardScaler: (x - mean) / std
    # Result: mean=0, std=1 for each feature
    # Rationale: Prevents features with large scales from dominating
    
    scaler = StandardScaler()
    
    # CRITICAL: Fit on training data only
    # This prevents data leakage (test data influencing training)
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)  # Use training statistics
    
    logger.info(f"✓ Scaled {X_train.shape[1]} features")
    logger.info(f"  Training set: mean={X_train_scaled.mean():.6f}, std={X_train_scaled.std():.6f}")
    logger.info(f"  Test set:     mean={X_test_scaled.mean():.6f}, std={X_test_scaled.std():.6f}")
    
    # Save scaler for inference
    scaler_path = os.path.join(model_dir, 'scaler.pkl')
    joblib.dump(scaler, scaler_path)
    logger.info(f"✓ Saved scaler to {scaler_path}")
    logger.info("")
    
    # ========================================
    # STEP 8: HANDLE CLASS IMBALANCE (SMOTE)
    # ========================================
    logger.info("STEP 8: Handling Class Imbalance (SMOTE)")
    logger.info("-" * 70)
    
    # SMOTE: Synthetic Minority Over-sampling Technique
    # Creates synthetic samples of minority class
    # Works by interpolating between existing minority samples
    
    logger.info("Before SMOTE:")
    before_dist = dict(zip(*np.unique(y_train, return_counts=True)))
    for class_label, count in sorted(before_dist.items()):
        pct = (count / len(y_train)) * 100
        logger.info(f"  Class {class_label}: {count:>6,} ({pct:>5.1f}%)")
    
    # Apply SMOTE
    # random_state=42 for reproducibility
    smote = SMOTE(random_state=42)
    X_train_balanced, y_train_balanced = smote.fit_resample(X_train_scaled, y_train)
    
    logger.info("\nAfter SMOTE:")
    after_dist = dict(zip(*np.unique(y_train_balanced, return_counts=True)))
    for class_label, count in sorted(after_dist.items()):
        pct = (count / len(y_train_balanced)) * 100
        logger.info(f"  Class {class_label}: {count:>6,} ({pct:>5.1f}%)")
    
    # Calculate synthetic samples created
    synthetic_samples = len(y_train_balanced) - len(y_train)
    logger.info(f"\n✓ Created {synthetic_samples:,} synthetic samples")
    logger.info(f"  Training set size: {len(y_train):,} → {len(y_train_balanced):,}")
    
    # IMPORTANT: Test set is NOT balanced
    # Test set must represent real-world distribution
    logger.info(f"\n⚠ Test set remains imbalanced (realistic distribution)")
    logger.info("")
    
    # ========================================
    # STEP 9: SAVE PROCESSED DATA
    # ========================================
    logger.info("STEP 9: Saving Processed Data")
    logger.info("-" * 70)
    
    # Save as numpy arrays for efficient loading
    np.save(os.path.join(output_dir, 'X_train_balanced.npy'), X_train_balanced)
    np.save(os.path.join(output_dir, 'y_train_balanced.npy'), y_train_balanced)
    np.save(os.path.join(output_dir, 'X_test.npy'), X_test_scaled)
    np.save(os.path.join(output_dir, 'y_test.npy'), y_test)
    
    # Save feature names for reference
    feature_names = X.columns.tolist()
    joblib.dump(feature_names, os.path.join(model_dir, 'feature_names.pkl'))
    
    logger.info(f"✓ Saved training data: X_train_balanced.npy, y_train_balanced.npy")
    logger.info(f"✓ Saved test data: X_test.npy, y_test.npy")
    logger.info(f"✓ Saved feature names: feature_names.pkl")
    logger.info("")
    
    logger.info("=" * 70)
    logger.info("PREPROCESSING COMPLETE")
    logger.info("=" * 70)
    logger.info(f"Balanced training set: {X_train_balanced.shape}")
    logger.info(f"Test set:              {X_test_scaled.shape}")
    logger.info("")
    
    return X_train_balanced, y_train_balanced, X_test_scaled, y_test

if __name__ == "__main__":
    # Run preprocessing
    X_train, y_train, X_test, y_test = preprocess_data()
    
    print(f"\nPreprocessing successful!")
    print(f"Training samples: {len(y_train):,}")
    print(f"Test samples: {len(y_test):,}")
```

**Key Concepts Explained:**

1. **Why save preprocessing artifacts?**
   - During inference, new data must use the SAME encoders and scaler
   - If training encoded "Manager"=5, inference must use the same mapping
   - If training scaled with mean=50000, inference must use the same mean

2. **Why fit scaler only on training data?**
   - Fitting on all data causes data leakage
   - Test set statistics would influence training
   - Model would have unfair advantage (seen test data indirectly)

3. **Why SMOTE only on training data?**
   - Test set must represent real-world distribution
   - If we balance test set, we can't evaluate real-world performance
   - SMOTE is a training trick, not a real-world phenomenon

### 3.2 Testing the Preprocessing Pipeline

Before integrating with Airflow, test the preprocessing script locally.

```bash
# Run preprocessing
python training/scripts/preprocess_data.py

# Verify output files
ls -lh training/data/processed/
# Should see: X_train_balanced.npy, y_train_balanced.npy, X_test.npy, y_test.npy

ls -lh training/models/
# Should see: label_encoders.pkl, scaler.pkl, feature_names.pkl
```

**Expected Output:**
```
==================================================================
CREDIT CARD APPROVAL - DATA PREPROCESSING PIPELINE
==================================================================

STEP 1: Loading Data
----------------------------------------------------------------------
✓ Loaded 50,000 samples with 18 features
  Memory usage: 6.87 MB

STEP 2: Handling Missing Values
----------------------------------------------------------------------
Missing values before: 15000
✓ OCCUPATION_TYPE: Filled 15000 missing values with 'Unknown'
✓ CNT_FAM_MEMBERS: Filled 0 missing values with median (2.0)
Missing values after: 0

...

STEP 8: Handling Class Imbalance (SMOTE)
----------------------------------------------------------------------
Before SMOTE:
  Class 0: 28,000 (70.0%)
  Class 1: 12,000 (30.0%)

After SMOTE:
  Class 0: 28,000 (50.0%)
  Class 1: 28,000 (50.0%)

✓ Created 16,000 synthetic samples
  Training set size: 40,000 → 56,000
```

### 3.3 Checkpoint

Verify your understanding of the preprocessing implementation.

**Self-Assessment:**
- [ ] You understand why we save preprocessing artifacts (encoders, scaler)
- [ ] You can explain the data leakage risk with scaling
- [ ] You know why SMOTE is applied only to training data
- [ ] You understand the order of operations (split → scale → SMOTE)
- [ ] You can interpret the preprocessing output logs
- [ ] You know how to verify preprocessing worked correctly

**Practical Exercise:**

Load the processed data and verify the shapes:

```python
import numpy as np

# Load processed data
X_train = np.load('training/data/processed/X_train_balanced.npy')
y_train = np.load('training/data/processed/y_train_balanced.npy')
X_test = np.load('training/data/processed/X_test.npy')
y_test = np.load('training/data/processed/y_test.npy')

print(f"Training: {X_train.shape}, {y_train.shape}")
print(f"Test: {X_test.shape}, {y_test.shape}")

# Verify balance
unique, counts = np.unique(y_train, return_counts=True)
print(f"Training class distribution: {dict(zip(unique, counts))}")
```

---

**Continue to Part 3 for Model Training and Airflow Integration...**
