"""
Integration and End-to-End Test Suite for Employee Attrition Application.
Tests authentication, routes, model inference, SHAP generation, and SQLite logging.
"""
import pytest
from app import app
import database

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_unauthenticated_redirect(client):
    """Verify protected routes redirect to /login when unauthenticated."""
    routes = ["/", "/dashboard", "/analysis", "/predict", "/explainability", "/history", "/performance"]
    for r in routes:
        res = client.get(r, follow_redirects=False)
        assert res.status_code == 302, f"Route {r} should redirect to /login"
        assert "/login" in res.headers["Location"]

def test_login_and_access(client):
    """Verify logging in with default credentials grants access to all routes."""
    # Login
    res = client.post("/login", data={
        "username": "Namratha K S",
        "password": "adminpass0213"
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Dashboard" in res.data

    # Test all 7 pages return 200 OK
    routes = ["/dashboard", "/analysis", "/predict", "/explainability", "/history", "/performance"]
    for r in routes:
        resp = client.get(r)
        assert resp.status_code == 200, f"Page {r} failed with status {resp.status_code}"

def test_prediction_pipeline(client):
    """Verify single prediction with SHAP calculation and database persistence."""
    # Login first
    client.post("/login", data={
        "username": "Namratha K S",
        "password": "adminpass0213"
    }, follow_redirects=True)

    # Post prediction data (18 active features)
    form_data = {
        "EmployeeRef": "EMP-TEST-99",
        "Age": 29,
        "BusinessTravel": "Travel_Frequently",
        "Department": "Sales",
        "Education": 3,
        "EducationField": "Marketing",
        "Gender": "Male",
        "JobInvolvement": 2,
        "JobLevel": 1,
        "JobRole": "Sales Representative",
        "JobSatisfaction": 1,
        "MaritalStatus": "Single",
        "MonthlyIncome": 2600,
        "NumCompaniesWorked": 4,
        "OverTime": "Yes",
        "PerformanceRating": 3,
        "TotalWorkingYears": 4,
        "YearsAtCompany": 2,
        "YearsInCurrentRole": 1
    }

    res = client.post("/predict", data=form_data, follow_redirects=True)
    assert res.status_code == 200
    assert b"EMP-TEST-99" in res.data
    assert b"SHAP Individual Feature Contributions" in res.data
    assert b"Tailored HR Retention Recommendations" in res.data

    # Check history contains this record
    history_resp = client.get("/history")
    assert b"EMP-TEST-99" in history_resp.data

def test_sample_profile_api(client):
    """Verify demo profile API endpoints."""
    client.post("/login", data={"username": "Namratha K S", "password": "adminpass0213"})
    res_high = client.get("/api/sample_profile/high_risk")
    assert res_high.status_code == 200
    data_high = res_high.get_json()
    assert data_high["OverTime"] == "Yes"

    res_low = client.get("/api/sample_profile/low_risk")
    assert res_low.status_code == 200
    data_low = res_low.get_json()
    assert data_low["OverTime"] == "No"
