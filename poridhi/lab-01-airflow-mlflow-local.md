# Lab 01: Automated ML Pipeline with Airflow & MLflow (Local Development)

## Introduction

This lab builds a production-grade automated ML pipeline for credit card approval prediction. You will set up Apache Airflow to orchestrate the complete ML workflow and MLflow to track all experiments. Everything runs locally using Docker Compose, providing a foundation for understanding ML pipeline automation before moving to cloud deployment.

The lab focuses on understanding the dataset, selecting appropriate models with clear justification, and automating the entire training process. By the end, you will have a fully automated system that requires zero manual intervention.

## Learning Objectives

By the end of this lab, you will be able to:

1. Analyze credit card approval dataset characteristics and identify key challenges
2. Justify model selection based on dataset properties and business requirements
3. Implement data preprocessing strategies (handling imbalance, missing values, encoding)
4. Set up Apache Airflow with Docker Compose for ML orchestration
5. Create Airflow DAGs to automate the complete ML workflow
6. Integrate MLflow tracking within Airflow tasks
7. Compare multiple models systematically using MLflow experiments
8. Register best models to MLflow Model Registry with proper versioning
9. Monitor and debug automated pipeline execution

**Prerequisites:** Basic Python, pandas, scikit-learn knowledge, Docker basics

**Estimated Time:** 6-8 hours

## Prologue: The Challenge

You join a fintech startup building an automated credit card approval system. The data science team currently runs training scripts manually on their laptops. Models are saved with names like `model_v2_final_FINAL.pkl`. Nobody remembers which hyperparameters produced which results. When someone asks "which model is in production?", the answer is "I think it's the one from last Tuesday?"

The problems are mounting:
- Models are retrained inconsistently (whenever someone remembers)
- No experiment tracking (lost knowledge of what works)
- Manual script execution (error-prone, time-consuming)
- No failure recovery (if a script fails at 3 AM, nobody knows until morning)
- Deployment chaos (which model file should we deploy?)

Your task: Build an automated ML pipeline that:
- Runs on a schedule without human intervention
- Tracks every experiment automatically
- Handles failures gracefully with retries
- Provides visibility into pipeline health
- Maintains a clear model registry

Apache Airflow will orchestrate the workflow. MLflow will track experiments. Docker Compose will manage all services locally.

## Environment Setup

Create the project structure and set up the local development environment.

```bash
# Create project directory
mkdir -p card-approval-mlops
cd card-approval-mlops

# Create directory structure
mkdir -p dags training/{data/{raw,processed},scripts,src/{config,utils},models} \
  logs plugins airflow/config monitoring/{prometheus,grafana,loki,tempo}

# Create virtual environment (for local development)
python3 -m venv venv
source venv/bin/activate

# Install core dependencies
pip install apache-airflow==2.8.0 mlflow pandas numpy scikit-learn \
  xgboost imbalanced-learn matplotlib seaborn
```

**Directory Structure Explained:**
- `dags/`: Airflow DAG definitions (workflow orchestration)
- `training/`: All ML training code and data
  - `data/raw/`: Original datasets
  - `data/processed/`: Preprocessed data ready for training
  - `scripts/`: Executable training scripts
  - `src/`: Reusable source code modules
  - `models/`: Saved model artifacts
- `logs/`: Airflow execution logs
- `plugins/`: Custom Airflow plugins (if needed)
- `airflow/config/`: Airflow configuration files
- `monitoring/`: Monitoring stack configurations (for later labs)

## Chapter 1: Understanding the Dataset and Challenges

### 1.1 The Credit Card Approval Dataset

Before building any ML pipeline, you must understand your data deeply. The credit card approval dataset contains information about credit card applicants and their approval decisions.

**Dataset Characteristics:**
- **Source:** Credit card application records from financial institutions
- **Target Variable:** `TARGET` (0 = Rejected, 1 = Approved)
- **Sample Size:** Typically 10,000-50,000 applications
- **Feature Types:** Mix of demographic, financial, and behavioral data

**Key Features:**
```python
# Demographic Features
CODE_GENDER          # Gender (M/F)
CNT_CHILDREN         # Number of children
NAME_FAMILY_STATUS   # Marital status
NAME_EDUCATION_TYPE  # Education level

# Financial Features
AMT_INCOME_TOTAL     # Annual income
NAME_INCOME_TYPE     # Income source (Working, Commercial, etc.)
FLAG_OWN_CAR         # Car ownership (Y/N)
FLAG_OWN_REALTY      # Property ownership (Y/N)

# Employment Features
OCCUPATION_TYPE      # Job category
DAYS_EMPLOYED        # Employment duration (negative days)

# Temporal Features
DAYS_BIRTH           # Age in days (negative value)

# Contact Features
FLAG_MOBIL           # Mobile phone (1/0)
FLAG_WORK_PHONE      # Work phone (1/0)
FLAG_PHONE           # Home phone (1/0)
FLAG_EMAIL           # Email (1/0)

# Household Features
NAME_HOUSING_TYPE    # Housing situation
CNT_FAM_MEMBERS      # Family size
```

### 1.2 Think First: Dataset Challenges

Before jumping into code, identify the challenges this dataset presents. Understanding these challenges will guide every decision you make.

**Question 1:** What problems do you expect when working with credit card approval data?

<details>
<summary>Click to review</summary>

**Challenge 1: Class Imbalance**
- Credit decisions are rarely 50-50 split
- Typically 70-30 or 80-20 ratio (more rejections or approvals)
- Models trained on imbalanced data bias toward majority class
- **Impact:** Model might predict "reject all" and still achieve 80% accuracy
- **Solution:** SMOTE (Synthetic Minority Over-sampling Technique)

**Challenge 2: Missing Values**
- Real-world data has gaps (people skip questions)
- `OCCUPATION_TYPE` often missing (~30% typical)
- Cannot simply drop rows (lose valuable information)
- **Impact:** Most ML algorithms cannot handle missing values
- **Solution:** Strategic imputation (median for numeric, mode for categorical)

**Challenge 3: Categorical Features**
- Many features are text-based (gender, education, occupation)
- ML models require numeric inputs
- Simple conversion loses information (is "Manager" > "Driver"?)
- **Impact:** Models cannot process text directly
- **Solution:** Label encoding or one-hot encoding

**Challenge 4: Feature Scaling**
- Income ranges from $10,000 to $1,000,000
- Age in days (negative values: -7,000 to -25,000)
- Binary flags (0 or 1)
- **Impact:** Features with larger scales dominate model training
- **Solution:** StandardScaler normalization

**Challenge 5: Temporal Features**
- `DAYS_BIRTH` and `DAYS_EMPLOYED` are negative (days before application)
- Hard to interpret (-14,000 days vs. 38 years)
- **Impact:** Difficult for humans to understand and validate
- **Solution:** Convert to years for interpretability

</details>

**Question 2:** Why is class imbalance particularly problematic for credit approval?

<details>
<summary>Click to review</summary>

In credit approval, class imbalance creates business risk:

**Scenario:** 80% of applications are rejected, 20% approved.

**Naive Model Behavior:**
- Model learns to predict "reject" for everyone
- Achieves 80% accuracy (looks good!)
- But approves 0% of applications (business fails)

**Business Impact:**
- False Negatives: Reject good customers (lost revenue)
- False Positives: Approve bad customers (credit risk)
- Both have different costs (rejecting good customer costs less than approving bad one)

**Why Standard Metrics Fail:**
- Accuracy is misleading (80% by predicting one class)
- Need metrics that account for both classes: F1-score, ROC-AUC
- Need balanced training data: SMOTE creates synthetic minority samples

</details>

### 1.3 Exploratory Data Analysis (EDA)

Create a script to explore the dataset and validate your assumptions about the challenges.

```python
# training/scripts/eda_analysis.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_and_explore_data(data_path='training/data/raw/application_record.csv'):
    """
    Perform comprehensive exploratory data analysis.
    
    This function loads the dataset and analyzes:
    - Basic statistics (shape, types, missing values)
    - Target distribution (class imbalance)
    - Feature distributions
    - Correlations
    
    Args:
        data_path: Path to the raw CSV file
        
    Returns:
        DataFrame: Loaded dataset for further analysis
    """
    
    logger.info("=" * 60)
    logger.info("LOADING DATASET")
    logger.info("=" * 60)
    
    # Load dataset
    df = pd.read_csv(data_path)
    
    logger.info(f"✓ Dataset loaded from {data_path}")
    logger.info(f"Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
    logger.info("")
    
    # ========================================
    # 1. DATA TYPES ANALYSIS
    # ========================================
    logger.info("=" * 60)
    logger.info("DATA TYPES")
    logger.info("=" * 60)
    
    type_counts = df.dtypes.value_counts()
    logger.info(f"Numeric columns: {type_counts.get('int64', 0) + type_counts.get('float64', 0)}")
    logger.info(f"Categorical columns: {type_counts.get('object', 0)}")
    logger.info("")
    logger.info("Column types:")
    for col, dtype in df.dtypes.items():
        logger.info(f"  {col:<25} {dtype}")
    logger.info("")
    
    # ========================================
    # 2. MISSING VALUES ANALYSIS
    # ========================================
    logger.info("=" * 60)
    logger.info("MISSING VALUES ANALYSIS")
    logger.info("=" * 60)
    
    missing = df.isnull().sum()
    missing_pct = (missing / len(df)) * 100
    
    missing_df = pd.DataFrame({
        'Column': missing.index,
        'Missing Count': missing.values,
        'Percentage': missing_pct.values
    })
    
    # Show only columns with missing values
    missing_data = missing_df[missing_df['Missing Count'] > 0].sort_values(
        'Percentage', ascending=False
    )
    
    if len(missing_data) > 0:
        logger.info("Columns with missing values:")
        for _, row in missing_data.iterrows():
            logger.info(f"  {row['Column']:<25} {row['Missing Count']:>6} ({row['Percentage']:>5.1f}%)")
    else:
        logger.info("✓ No missing values found")
    logger.info("")
    
    # ========================================
    # 3. TARGET DISTRIBUTION (CLASS IMBALANCE)
    # ========================================
    logger.info("=" * 60)
    logger.info("TARGET DISTRIBUTION (CLASS IMBALANCE CHECK)")
    logger.info("=" * 60)
    
    target_counts = df['TARGET'].value_counts().sort_index()
    target_pct = (target_counts / len(df)) * 100
    
    logger.info(f"Class 0 (Rejected):  {target_counts[0]:>6,} ({target_pct[0]:>5.1f}%)")
    logger.info(f"Class 1 (Approved):  {target_counts[1]:>6,} ({target_pct[1]:>5.1f}%)")
    logger.info("")
    
    # Calculate imbalance ratio
    majority_class = target_counts.max()
    minority_class = target_counts.min()
    imbalance_ratio = majority_class / minority_class
    
    logger.info(f"Imbalance Ratio: {imbalance_ratio:.2f}:1")
    
    if imbalance_ratio > 1.5:
        logger.warning(f"⚠ Significant class imbalance detected!")
        logger.warning(f"  Recommendation: Use SMOTE or class weights")
    else:
        logger.info("✓ Classes are relatively balanced")
    logger.info("")
    
    # ========================================
    # 4. NUMERIC FEATURES SUMMARY
    # ========================================
    logger.info("=" * 60)
    logger.info("NUMERIC FEATURES SUMMARY")
    logger.info("=" * 60)
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    logger.info(df[numeric_cols].describe())
    logger.info("")
    
    # ========================================
    # 5. CATEGORICAL FEATURES ANALYSIS
    # ========================================
    logger.info("=" * 60)
    logger.info("CATEGORICAL FEATURES")
    logger.info("=" * 60)
    
    categorical_cols = df.select_dtypes(include=['object']).columns
    
    for col in categorical_cols:
        unique_count = df[col].nunique()
        logger.info(f"\n{col} ({unique_count} unique values):")
        
        # Show top 5 most frequent values
        value_counts = df[col].value_counts().head(5)
        for value, count in value_counts.items():
            pct = (count / len(df)) * 100
            logger.info(f"  {str(value):<30} {count:>6,} ({pct:>5.1f}%)")
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("EDA COMPLETE")
    logger.info("=" * 60)
    
    return df

if __name__ == "__main__":
    df = load_and_explore_data()
```

**Code Explanation:**

1. **Function Structure**: The `load_and_explore_data()` function is organized into clear sections, each analyzing a specific aspect of the data.

2. **Data Types Analysis**: Identifies numeric vs. categorical columns. This determines which preprocessing techniques to apply (scaling for numeric, encoding for categorical).

3. **Missing Values Analysis**: Calculates both count and percentage of missing values. Percentage is crucial—30% missing is very different from 0.1% missing.

4. **Target Distribution**: Checks for class imbalance by calculating the ratio between majority and minority classes. A ratio > 1.5:1 indicates significant imbalance requiring intervention.

5. **Numeric Summary**: Uses `describe()` to show min, max, mean, std, and quartiles. This reveals outliers and scale differences.

6. **Categorical Analysis**: Shows the distribution of categorical values. This helps identify if encoding will create too many features (high cardinality problem).

**Expected Output:**
```
==============================================================
TARGET DISTRIBUTION (CLASS IMBALANCE CHECK)
==============================================================
Class 0 (Rejected):  35,000 (70.0%)
Class 1 (Approved):  15,000 (30.0%)

Imbalance Ratio: 2.33:1
⚠ Significant class imbalance detected!
  Recommendation: Use SMOTE or class weights
```

### 1.4 Understanding the Preprocessing Strategy

Based on the EDA findings, develop a preprocessing strategy. Every decision must be justified by data characteristics.

**Preprocessing Pipeline:**

```
1. HANDLE MISSING VALUES
   ├── OCCUPATION_TYPE: Fill with 'Unknown' (new category)
   ├── CNT_FAM_MEMBERS: Fill with median (numeric)
   └── Rationale: Preserve all samples, don't lose information

2. FEATURE ENGINEERING
   ├── DAYS_BIRTH → AGE_YEARS (divide by -365)
   ├── DAYS_EMPLOYED → EMPLOYMENT_YEARS (divide by -365)
   └── Rationale: Human-interpretable features, easier validation

3. ENCODE CATEGORICAL VARIABLES
   ├── Use LabelEncoder for ordinal-like features
   ├── Save encoders for inference (must use same mapping)
   └── Rationale: Convert text to numbers for ML algorithms

4. TRAIN-TEST SPLIT
   ├── 80-20 split with stratification
   ├── Stratify by TARGET (preserve class ratio in both sets)
   └── Rationale: Test set must represent real-world distribution

5. FEATURE SCALING
   ├── StandardScaler (mean=0, std=1)
   ├── Fit on train, transform both train and test
   └── Rationale: Prevent large-scale features from dominating

6. HANDLE CLASS IMBALANCE
   ├── Apply SMOTE to training set only
   ├── Never apply to test set (must remain realistic)
   └── Rationale: Balance classes for better model learning
```

**Why This Order Matters:**

1. **Missing values first**: Can't split or scale data with NaN values
2. **Feature engineering before encoding**: Create meaningful features first
3. **Split before scaling**: Prevent data leakage (test data influences scaler)
4. **SMOTE last**: Only balance training data, keep test data realistic

### 1.5 Checkpoint

Before moving to implementation, verify your understanding.

**Self-Assessment:**
- [ ] You can explain why class imbalance is problematic for credit approval
- [ ] You understand the difference between missing value strategies (drop vs. impute)
- [ ] You know why we convert DAYS_BIRTH to AGE_YEARS (interpretability)
- [ ] You can explain why we stratify the train-test split
- [ ] You understand why SMOTE is applied only to training data
- [ ] You can identify which features need encoding vs. scaling

**Conceptual Questions:**

**Q1:** Why not just drop rows with missing OCCUPATION_TYPE?

<details>
<summary>Click to review</summary>

Dropping rows with missing OCCUPATION_TYPE would:
- Lose ~30% of data (significant information loss)
- Potentially introduce bias (maybe unemployed people don't report occupation)
- Reduce model training data (worse performance)

Better approach: Create "Unknown" category. The model can learn patterns for people who don't report occupation.

</details>

**Q2:** Why apply SMOTE after train-test split, not before?

<details>
<summary>Click to review</summary>

If you apply SMOTE before splitting:
- Synthetic samples in training set might be very similar to real samples in test set
- This is data leakage (test data influences training)
- Model performance will be artificially inflated
- Real-world performance will be worse

Correct approach: Split first, then SMOTE only the training set. Test set must remain realistic.

</details>

## Chapter 2: Model Selection and Training Strategy

### 2.1 Why Multiple Models?

Many beginners ask: "Why not just use the best model?" The answer reveals a fundamental principle of machine learning.

**The No Free Lunch Theorem:**
- No single algorithm works best for all datasets
- Dataset characteristics determine which model performs best
- Must compare multiple approaches empirically

**Question:** What factors should influence model selection for credit approval?

<details>
<summary>Click to review</summary>

**Factor 1: Interpretability vs. Performance Trade-off**
- Logistic Regression: Highly interpretable (coefficients show feature impact)
- XGBoost: Higher performance but less interpretable
- Business requirement: Regulatory compliance may require explainability

**Factor 2: Training Time**
- Logistic Regression: Seconds
- Random Forest: Minutes
- XGBoost: Minutes to hours
- Consideration: How often do we retrain?

**Factor 3: Inference Speed**
- Logistic Regression: Microseconds per prediction
- XGBoost: Milliseconds per prediction
- Random Forest: Slower (must aggregate multiple trees)
- Consideration: Real-time API requirements

**Factor 4: Handling Imbalance**
- All three models support class weights
- XGBoost has built-in `scale_pos_weight` parameter
- Random Forest and Logistic Regression use `class_weight='balanced'`

**Factor 5: Feature Interactions**
- Logistic Regression: Only linear relationships
- Random Forest: Captures non-linear patterns
- XGBoost: Captures complex interactions with boosting

</details>

### 2.2 Our Three-Model Strategy

We will train three models, each serving a specific purpose.

**Model 1: Logistic Regression (Baseline)**
```python
LogisticRegression(
    max_iter=1000,           # Sufficient iterations for convergence
    random_state=42,         # Reproducibility
    class_weight='balanced'  # Handle remaining imbalance
)
```

**Purpose:**
- Establish baseline performance
- Provide interpretable coefficients for stakeholders
- Fast training and inference
- Regulatory compliance (explainable AI)

**Strengths:**
- Simple, well-understood algorithm
- Coefficients show feature importance
- Probability outputs are well-calibrated
- Works well with linearly separable data

**Weaknesses:**
- Cannot capture non-linear relationships
- Assumes feature independence
- May underperform on complex patterns

**Model 2: Random Forest (Ensemble)**
```python
RandomForestClassifier(
    n_estimators=100,        # Number of trees
    max_depth=10,            # Prevent overfitting
    random_state=42,         # Reproducibility
    class_weight='balanced', # Handle imbalance
    n_jobs=-1                # Use all CPU cores
)
```

**Purpose:**
- Capture non-linear relationships
- Provide feature importance rankings
- Robust to outliers
- Ensemble approach reduces overfitting

**Strengths:**
- Handles non-linear patterns naturally
- Feature importance scores
- Robust to outliers and noise
- No feature scaling required (but we scale anyway for consistency)

**Weaknesses:**
- Slower inference (must aggregate trees)
- Less interpretable than logistic regression
- Can overfit with too many trees

**Model 3: XGBoost (Gradient Boosting)**
```python
XGBClassifier(
    n_estimators=100,        # Number of boosting rounds
    max_depth=6,             # Tree depth
    learning_rate=0.1,       # Step size shrinkage
    random_state=42,         # Reproducibility
    eval_metric='logloss',   # Optimization metric
    use_label_encoder=False  # Avoid deprecation warning
)
```

**Purpose:**
- Achieve maximum performance
- Industry standard for tabular data
- Built-in regularization
- Handles missing values natively

**Strengths:**
- Often achieves best performance
- Built-in regularization (prevents overfitting)
- Handles missing values
- Fast training with GPU support

**Weaknesses:**
- Requires careful hyperparameter tuning
- Less interpretable (but SHAP values help)
- Can overfit if not regularized properly

### 2.3 Evaluation Metrics Strategy

Choosing the right metrics is as important as choosing the right models.

**Why Not Just Accuracy?**

Consider this scenario:
```
Dataset: 80% rejected, 20% approved
Model: Predicts "reject" for everyone
Accuracy: 80% (looks great!)
Business value: Zero (approves nobody)
```

**Our Metrics:**

**1. F1-Score (Primary Metric)**
```python
F1 = 2 * (Precision * Recall) / (Precision + Recall)
```
- Harmonic mean of precision and recall
- Balances false positives and false negatives
- Good for imbalanced datasets
- Range: 0 to 1 (higher is better)

**2. ROC-AUC (Model Selection)**
```python
ROC-AUC = Area Under Receiver Operating Characteristic Curve
```
- Measures model's ability to distinguish classes
- Threshold-independent (evaluates all possible thresholds)
- Range: 0.5 (random) to 1.0 (perfect)
- Best metric for comparing models

**3. Precision (Business Context)**
```python
Precision = True Positives / (True Positives + False Positives)
```
- Of all approved applications, how many should be approved?
- High precision = low false positive rate
- Important when false positives are costly (credit risk)

**4. Recall (Business Context)**
```python
Recall = True Positives / (True Positives + False Negatives)
```
- Of all good applicants, how many did we approve?
- High recall = low false negative rate
- Important when false negatives are costly (lost customers)

**Metric Selection Strategy:**
- Use ROC-AUC to select best model (overall performance)
- Use F1-Score to evaluate balanced performance
- Use Precision/Recall to understand business trade-offs

### 2.4 Think First: Model Behavior

Before training, predict how each model will behave.

**Scenario:** A 35-year-old manager with $80,000 income, owns a car, has 2 children.

**Question:** Which model is most likely to approve this application? Why?

<details>
<summary>Click to review</summary>

**Logistic Regression:**
- Will compute: w1*age + w2*income + w3*car_ownership + ...
- Linear combination of features
- If similar profiles were approved in training, likely approves
- Behavior: Consistent, predictable

**Random Forest:**
- Will check multiple decision trees
- Tree 1: "Income > $70k? Yes → Check children..."
- Tree 2: "Manager? Yes → Check age..."
- Aggregates votes from all trees
- Behavior: Can capture "manager with high income" pattern

**XGBoost:**
- Sequential boosting: each tree corrects previous errors
- Can learn: "High income + manager + car = strong approval signal"
- Most likely to capture complex interactions
- Behavior: Most flexible, highest performance potential

**Expected Result:** XGBoost likely performs best, but Logistic Regression provides clearest explanation.

</details>

### 2.5 Checkpoint

Verify your understanding of model selection before implementation.

**Self-Assessment:**
- [ ] You can explain why we train three models instead of one
- [ ] You understand the strengths and weaknesses of each model
- [ ] You know why accuracy is misleading for imbalanced data
- [ ] You can explain the difference between F1-score and ROC-AUC
- [ ] You understand the precision-recall trade-off
- [ ] You can justify hyperparameter choices (e.g., max_depth=10)

**Conceptual Question:**

**Q:** A stakeholder asks: "Why not just use XGBoost since it's the best?" How do you respond?

<details>
<summary>Click to review</summary>

"XGBoost often achieves the best performance, but we train multiple models for several reasons:

1. **Validation**: We need to verify XGBoost actually performs best on *this* dataset. Sometimes simpler models surprise us.

2. **Interpretability**: Logistic Regression provides clear coefficients for regulatory compliance and stakeholder communication.

3. **Baseline**: Logistic Regression establishes a baseline. If XGBoost only improves by 1%, the added complexity may not be worth it.

4. **Robustness**: If XGBoost fails or has issues, we have fallback options.

5. **Learning**: Comparing models teaches us about the data. If all models perform similarly, the problem is likely linear. If XGBoost significantly outperforms, there are complex interactions.

The cost of training three models is small compared to the value of this knowledge."

</details>

---

**Continue to Part 2 of Lab 01 for implementation...**
