"""
Unit and integration tests for prediction engine, SHAP calculations, and bulk processing.
"""
import pytest
import io
import pandas as pd
import config
from src.predict import (
    load_model_artifacts,
    predict_single_employee,
    process_bulk_predictions,
)

@pytest.fixture
def sample_valid_employee():
    return {
        "Age": 32,
        "DailyRate": 850,
        "DistanceFromHome": 5,
        "Education": 3,
        "EnvironmentSatisfaction": 3,
        "HourlyRate": 70,
        "JobInvolvement": 3,
        "JobLevel": 2,
        "JobSatisfaction": 3,
        "MonthlyIncome": 6000,
        "MonthlyRate": 15000,
        "NumCompaniesWorked": 1,
        "PercentSalaryHike": 14,
        "PerformanceRating": 3,
        "RelationshipSatisfaction": 3,
        "StockOptionLevel": 1,
        "TotalWorkingYears": 9,
        "TrainingTimesLastYear": 2,
        "WorkLifeBalance": 3,
        "YearsAtCompany": 6,
        "YearsInCurrentRole": 4,
        "YearsSinceLastPromotion": 1,
        "YearsWithCurrManager": 4,
        "BusinessTravel": "Travel_Rarely",
        "Department": "Sales",
        "EducationField": "Marketing",
        "Gender": "Female",
        "JobRole": "Sales Executive",
        "MaritalStatus": "Married",
        "OverTime": "No",
    }

def test_load_model_artifacts():
    model, preprocessor, metadata, feature_names = load_model_artifacts()
    assert model is not None
    assert preprocessor is not None
    assert isinstance(metadata, dict)
    assert len(feature_names) > 0

def test_predict_single_employee(sample_valid_employee):
    res = predict_single_employee(sample_valid_employee)
    assert "probability" in res
    assert 0.0 <= res["probability"] <= 1.0
    assert res["prediction_label"] in ["Likely to Leave", "Likely to Stay"]
    assert res["risk_category"] in ["Low Risk", "Medium Risk", "High Risk"]
    assert "explanation" in res
    assert "top_risk_factors" in res["explanation"]
    assert "top_protective_factors" in res["explanation"]
    assert "recommendations" in res["explanation"]
    assert len(res["explanation"]["recommendations"]) > 0

def test_risk_threshold_mapping():
    low = config.get_risk_category(0.15)
    assert low["level"] == "Low Risk"

    med = config.get_risk_category(0.45)
    assert med["level"] == "Medium Risk"

    high = config.get_risk_category(0.85)
    assert high["level"] == "High Risk"

def test_bulk_csv_processing(sample_valid_employee):
    # Create sample DataFrame
    df = pd.DataFrame([sample_valid_employee, sample_valid_employee])
    csv_bytes = io.BytesIO()
    df.to_csv(csv_bytes, index=False)
    csv_bytes.seek(0)

    summary, results_df = process_bulk_predictions(csv_bytes)
    assert summary["total_records"] == 2
    assert "Attrition_Probability" in results_df.columns
    assert "Risk_Category" in results_df.columns
    assert "Predicted_Attrition" in results_df.columns
