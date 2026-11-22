"""
Unit tests for data preprocessing, validation, and schema checking.
"""
import pytest
import pandas as pd
import numpy as np

import config
from src.data_preprocessing import (
    load_raw_dataset,
    validate_dataset,
    clean_and_split_features_target,
    build_preprocessor,
    validate_input_dict,
    format_input_dataframe,
)

def test_load_dataset_exists():
    df = load_raw_dataset()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert len(df) == 1470

def test_validate_dataset_integrity():
    df = load_raw_dataset()
    report = validate_dataset(df)
    assert report["valid"] is True
    assert report["null_count"] == 0
    assert report["duplicate_count"] == 0
    assert "Yes" in report["target_distribution"]
    assert "No" in report["target_distribution"]

def test_clean_and_split():
    df = load_raw_dataset()
    X, y = clean_and_split_features_target(df)

    # Identifiers and constant columns dropped
    for col in config.DROP_COLUMNS:
        assert col not in X.columns

    assert config.TARGET_COLUMN not in X.columns
    assert set(y.unique()) == {0, 1}
    assert len(X) == len(y)
    assert len(X.columns) == len(config.NUMERICAL_FEATURES) + len(config.CATEGORICAL_FEATURES)

def test_column_transformer():
    df = load_raw_dataset()
    X, y = clean_and_split_features_target(df)
    preprocessor = build_preprocessor()
    X_trans = preprocessor.fit_transform(X)

    assert isinstance(X_trans, np.ndarray)
    assert X_trans.shape[0] == len(X)
    assert X_trans.shape[1] > len(X.columns)  # One-hot expansion
    assert not np.isnan(X_trans).any()

def test_validate_input_dict_valid():
    valid_employee = {
        "Age": 30,
        "DailyRate": 800,
        "DistanceFromHome": 10,
        "Education": 3,
        "EnvironmentSatisfaction": 3,
        "HourlyRate": 65,
        "JobInvolvement": 3,
        "JobLevel": 2,
        "JobSatisfaction": 3,
        "MonthlyIncome": 5000,
        "MonthlyRate": 14000,
        "NumCompaniesWorked": 2,
        "PercentSalaryHike": 15,
        "PerformanceRating": 3,
        "RelationshipSatisfaction": 3,
        "StockOptionLevel": 1,
        "TotalWorkingYears": 10,
        "TrainingTimesLastYear": 3,
        "WorkLifeBalance": 3,
        "YearsAtCompany": 5,
        "YearsInCurrentRole": 3,
        "YearsSinceLastPromotion": 1,
        "YearsWithCurrManager": 3,
        "BusinessTravel": "Travel_Rarely",
        "Department": "Research & Development",
        "EducationField": "Life Sciences",
        "Gender": "Male",
        "JobRole": "Research Scientist",
        "MaritalStatus": "Married",
        "OverTime": "No",
    }
    is_valid, errors = validate_input_dict(valid_employee)
    assert is_valid is True
    assert len(errors) == 0

def test_validate_input_dict_invalid_bounds():
    invalid_employee = {
        "Age": 10,  # Below min 18
        "MonthlyIncome": -500,  # Negative
        "OverTime": "Sometimes",  # Invalid category
        "Department": "Artificial Intelligence",  # Invalid choice
    }
    is_valid, errors = validate_input_dict(invalid_employee)
    assert is_valid is False
    assert len(errors) > 0
