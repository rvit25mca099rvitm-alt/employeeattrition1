"""
Data preprocessing, validation, and pipeline preparation.
"""
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional
import pandas as pd
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

import config

def load_raw_dataset(filepath: Optional[Path] = None) -> pd.DataFrame:
    """
    Loads raw CSV dataset from disk and checks existence.
    """
    path = Path(filepath or config.DATASET_PATH)
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found at '{path}'. Please ensure 'WA_Fn-UseC_-HR-Employee-Attrition.csv' "
            f"or 'employee_attrition.csv' is placed inside '{config.DATA_DIR}'."
        )
    df = pd.read_csv(path)
    return df

def validate_dataset(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Performs data integrity and quality checks on the dataset.
    """
    issues = []
    if config.TARGET_COLUMN not in df.columns:
        issues.append(f"Target column '{config.TARGET_COLUMN}' is missing from the dataset.")

    missing_cats = [col for col in config.CATEGORICAL_FEATURES if col not in df.columns]
    if missing_cats:
        issues.append(f"Missing categorical columns: {missing_cats}")

    missing_nums = [col for col in config.NUMERICAL_FEATURES if col not in df.columns]
    if missing_nums:
        issues.append(f"Missing numerical columns: {missing_nums}")

    null_count = int(df.isnull().sum().sum())
    dup_count = int(df.duplicated().sum())

    target_dist = {}
    if config.TARGET_COLUMN in df.columns:
        target_dist = df[config.TARGET_COLUMN].value_counts().to_dict()

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "rows": len(df),
        "columns": len(df.columns),
        "null_count": null_count,
        "duplicate_count": dup_count,
        "target_distribution": target_dist,
    }

def clean_and_split_features_target(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Cleans dataset, drops constant/identifier columns, maps target to binary integers.
    Returns: (X, y)
    """
    df_clean = df.copy()

    # Drop zero-variance or identifier columns if present
    cols_to_drop = [c for c in config.DROP_COLUMNS if c in df_clean.columns]
    if cols_to_drop:
        df_clean = df_clean.drop(columns=cols_to_drop)

    # Validate target presence
    if config.TARGET_COLUMN not in df_clean.columns:
        raise ValueError(f"Target column '{config.TARGET_COLUMN}' not found in data.")

    # Target variable mapping: 'Yes' -> 1, 'No' -> 0
    y_raw = df_clean[config.TARGET_COLUMN]
    if y_raw.dtype == object or str(y_raw.dtype) == "category":
        y = y_raw.map(config.TARGET_MAPPING)
        if y.isnull().any():
            raise ValueError(f"Target contains unrecognized values: {y_raw.unique()}")
    else:
        y = y_raw.astype(int)

    X = df_clean.drop(columns=[config.TARGET_COLUMN])

    # Ensure all required features are present
    expected_features = config.NUMERICAL_FEATURES + config.CATEGORICAL_FEATURES
    missing_in_X = [f for f in expected_features if f not in X.columns]
    if missing_in_X:
        raise ValueError(f"Expected features missing from X: {missing_in_X}")

    # Reorder X columns consistently
    X = X[expected_features]

    return X, y

def build_preprocessor() -> ColumnTransformer:
    """
    Constructs the Scikit-learn ColumnTransformer for categorical and numerical features.
    - Numerical: StandardScaler
    - Categorical: OneHotEncoder(handle_unknown='ignore', sparse_output=False)
    """
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "num",
                StandardScaler(),
                config.NUMERICAL_FEATURES,
            ),
            (
                "cat",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=False,
                ),
                config.CATEGORICAL_FEATURES,
            ),
        ],
        remainder="drop",
        verbose_feature_names_out=True,
    )
    return preprocessor

def get_transformed_feature_names(fitted_preprocessor: ColumnTransformer) -> List[str]:
    """
    Extracts readable feature names from the fitted preprocessor.
    Cleans prefixes for clearer display in SHAP and charts.
    """
    raw_names = list(fitted_preprocessor.get_feature_names_out())
    cleaned_names = []
    for name in raw_names:
        # e.g., 'num__MonthlyIncome' -> 'MonthlyIncome'
        # e.g., 'cat__Department_Sales' -> 'Department: Sales'
        if name.startswith("num__"):
            cleaned_names.append(name.replace("num__", ""))
        elif name.startswith("cat__"):
            cat_part = name.replace("cat__", "")
            # Split by first underscore to get feature and category
            parts = cat_part.split("_", 1)
            if len(parts) == 2:
                cleaned_names.append(f"{parts[0]}: {parts[1]}")
            else:
                cleaned_names.append(cat_part)
        else:
            cleaned_names.append(name)
    return cleaned_names

# Default background values for features omitted from the simplified input form
DEFAULT_BACKGROUND_VALUES = {
    "BusinessTravel": "Travel_Rarely",
    "MaritalStatus": "Married",
    "EducationField": "Life Sciences",
    "Education": 3,
    "DistanceFromHome": 9,
    "JobLevel": 2,
    "NumCompaniesWorked": 2,
    "EnvironmentSatisfaction": 3,
    "WorkLifeBalance": 3,
    "StockOptionLevel": 1,
    "PercentSalaryHike": 15,
    "DailyRate": 800,
    "HourlyRate": 65,
    "MonthlyRate": 14000,
    "PerformanceRating": 3,
    "RelationshipSatisfaction": 3,
    "TrainingTimesLastYear": 3,
}

def fill_simplified_defaults(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fills benchmark defaults for fields removed from the simplified user form.
    """
    for k, v in DEFAULT_BACKGROUND_VALUES.items():
        if k not in input_data or input_data[k] is None or str(input_data[k]).strip() == "":
            input_data[k] = v

    # Dynamic clamping to respect tenure
    try:
        yrs_comp = float(input_data.get("YearsAtCompany", 5))
        if "YearsInCurrentRole" not in input_data or str(input_data.get("YearsInCurrentRole", "")).strip() == "":
            input_data["YearsInCurrentRole"] = min(yrs_comp, 3)
        if "YearsWithCurrManager" not in input_data or str(input_data.get("YearsWithCurrManager", "")).strip() == "":
            input_data["YearsWithCurrManager"] = min(yrs_comp, 3)
        if "YearsSinceLastPromotion" not in input_data or str(input_data.get("YearsSinceLastPromotion", "")).strip() == "":
            input_data["YearsSinceLastPromotion"] = min(yrs_comp, 1)
    except (ValueError, TypeError):
        pass

    return input_data

def validate_input_dict(input_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates user-submitted employee record against defined boundaries and choices.
    """
    errors = []

    # Fill defaults for omitted simplified fields first
    fill_simplified_defaults(input_data)

    # Check Employee Name and ID if present
    if "employee_name" in input_data and not str(input_data.get("employee_name", "")).strip():
        errors.append("Employee Name is required.")
    if "employee_id" in input_data and not str(input_data.get("employee_id", "")).strip():
        errors.append("Employee ID is required.")

    # Check Categorical values
    for cat_col, valid_choices in config.CATEGORICAL_CHOICES.items():
        val = input_data.get(cat_col)
        if val is None or str(val).strip() == "":
            errors.append(f"Field '{cat_col}' is required.")
        elif str(val) not in valid_choices:
            errors.append(f"Invalid choice for '{cat_col}': '{val}'. Must be one of {valid_choices}.")

    # Check Numerical values
    for num_col, specs in config.NUMERICAL_SPECS.items():
        val = input_data.get(num_col)
        if val is None or str(val).strip() == "":
            errors.append(f"Field '{num_col}' is required.")
        else:
            try:
                num_val = float(val)
                has_min = specs.get("min") is not None
                has_max = specs.get("max") is not None
                if (has_min and num_val < specs["min"]) or (has_max and num_val > specs["max"]):
                    if has_min and has_max:
                        errors.append(
                            f"Field '{num_col}' must be between {specs['min']} and {specs['max']} (received {num_val})."
                        )
                    elif has_min:
                        errors.append(
                            f"Field '{num_col}' must be at least {specs['min']} (received {num_val})."
                        )
            except (ValueError, TypeError):
                errors.append(f"Field '{num_col}' must be a valid number.")

    # Cross-field logical validity checks
    try:
        tot_work = float(input_data.get("TotalWorkingYears", 0))
        yrs_comp = float(input_data.get("YearsAtCompany", 0))
        yrs_role = float(input_data.get("YearsInCurrentRole", 0))
        yrs_mgr = float(input_data.get("YearsWithCurrManager", 0))
        age = float(input_data.get("Age", 0))

        if yrs_comp > tot_work:
            errors.append(f"Years at Company ({yrs_comp}) cannot be greater than Total Working Years ({tot_work}).")

        if yrs_role > yrs_comp:
            errors.append(f"Years in Current Role ({yrs_role}) cannot exceed Years at Company ({yrs_comp}).")

        if yrs_mgr > yrs_comp:
            errors.append(f"Years with Current Manager ({yrs_mgr}) cannot exceed Years at Company ({yrs_comp}).")

        if (age - tot_work) < 14:
            errors.append(f"Age ({age}) is incompatible with Total Working Years ({tot_work}). Career start age would be under 14.")

        if (age + tot_work) > 65:
            errors.append(f"Total of Age ({age}) and Total Working Years ({tot_work}) must not exceed 65 years.")
    except (ValueError, TypeError):
        pass

    return len(errors) == 0, errors

def format_input_dataframe(input_data: Dict[str, Any]) -> pd.DataFrame:
    """
    Converts a single validated input dictionary into a correctly typed pandas DataFrame
    matching the training schema.
    """
    record = {}
    for num_col in config.NUMERICAL_FEATURES:
        record[num_col] = float(input_data[num_col])
    for cat_col in config.CATEGORICAL_FEATURES:
        record[cat_col] = str(input_data[cat_col])

    df = pd.DataFrame([record])
    # Order columns
    df = df[config.NUMERICAL_FEATURES + config.CATEGORICAL_FEATURES]
    return df
