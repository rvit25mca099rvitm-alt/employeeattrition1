"""
Integration tests for Flask application routes, authentication, web UI, and JSON API endpoints.
"""
import pytest
from app import app
from src.db import init_db, register_user, authenticate_user

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client

@pytest.fixture
def auth_client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "testuser"
            sess["full_name"] = "Test User"
            sess["role"] = "HR Analyst"
        yield client

def test_unauthenticated_redirect_to_login(client):
    response = client.get("/", follow_redirects=True)
    assert response.status_code == 200
    assert b"HR User Login" in response.data

def test_home_route_authenticated(auth_client):
    response = auth_client.get("/")
    assert response.status_code == 200
    assert b"Employee Attrition Analysis and Prediction" in response.data

def test_login_get_route(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"HR User Login" in response.data

def test_register_get_route(client):
    response = client.get("/register")
    assert response.status_code == 200
    assert b"Create HR Account" in response.data

def test_auth_workflow(client):
    # Test valid registration
    res_reg = client.post("/register", data={
        "full_name": "Test Analyst",
        "username": "testanalyst",
        "email": "analyst@company.com",
        "password": "password123",
        "confirm_password": "password123"
    }, follow_redirects=True)
    assert res_reg.status_code == 200

    # Test login with created credentials
    res_login = client.post("/login", data={
        "username": "testanalyst",
        "password": "password123"
    }, follow_redirects=True)
    assert res_login.status_code == 200
    assert b"Welcome back, Test Analyst!" in res_login.data

    # Test logout
    res_logout = client.get("/logout", follow_redirects=True)
    assert res_logout.status_code == 200
    assert b"signed out successfully" in res_logout.data

def test_dashboard_route(auth_client):
    response = auth_client.get("/dashboard")
    # Dashboard was removed per user requirements, redirects to home
    assert response.status_code == 302

def test_predict_get_route(auth_client):
    response = auth_client.get("/predict")
    assert response.status_code == 200
    assert b"Enter Employee Details" in response.data

def test_predict_post_valid(auth_client):
    valid_payload = {
        "Age": 35,
        "DailyRate": 800,
        "DistanceFromHome": 5,
        "Education": 3,
        "EnvironmentSatisfaction": 3,
        "HourlyRate": 65,
        "JobInvolvement": 3,
        "JobLevel": 2,
        "JobSatisfaction": 3,
        "MonthlyIncome": 50000, # Large income in Rupees without limits
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
    response = auth_client.post("/predict", data=valid_payload)
    assert response.status_code == 200
    assert b"Analysed Employee Data Successfully Saved!" in response.data

def test_predict_post_simplified(auth_client):
    simplified_payload = {
        "employee_name": "Sarah Connor",
        "employee_id": "EMP-9999",
        "Age": 28,
        "Gender": "Female",
        "Department": "Sales",
        "JobRole": "Sales Representative",
        "TotalWorkingYears": 4,
        "YearsAtCompany": 2,
        "MonthlyIncome": 85000, # Large salary in Rupees
        "OverTime": "Yes",
        "JobSatisfaction": 2,
        "JobInvolvement": 2,
    }
    response = auth_client.post("/predict", data=simplified_payload)
    assert response.status_code == 200
    assert b"Analysed Employee Data Successfully Saved!" in response.data
    assert b"Sarah Connor" in response.data
    assert b"EMP-9999" in response.data

def test_predict_post_invalid(auth_client):
    invalid_payload = {"Age": 5}
    response = auth_client.post("/predict", data=invalid_payload)
    assert response.status_code == 200
    assert b"Field" in response.data

def test_explain_route(auth_client):
    response = auth_client.get("/explain")
    assert response.status_code == 200

def test_bulk_predict_route(auth_client):
    response = auth_client.get("/bulk-predict")
    assert response.status_code == 200

def test_download_template_route(auth_client):
    response = auth_client.get("/bulk-predict/download-template")
    assert response.status_code == 200
    assert response.content_type == "text/csv; charset=utf-8"

def test_model_evaluation_route(auth_client):
    response = auth_client.get("/model-evaluation")
    assert response.status_code == 200
    assert b"Multi-Classifier Performance Benchmark" in response.data

def test_history_route(auth_client):
    response = auth_client.get("/history")
    assert response.status_code == 200
    assert b"Stored Analysed Employee Records" in response.data

def test_about_route_redirect(auth_client):
    response = auth_client.get("/about", follow_redirects=False)
    assert response.status_code == 302
    assert response.location in ["/home", "/", "http://localhost/home", "http://localhost/"]

def test_api_predict(client):
    valid_payload = {
        "Age": 30,
        "DailyRate": 800,
        "DistanceFromHome": 10,
        "Education": 3,
        "EnvironmentSatisfaction": 3,
        "HourlyRate": 65,
        "JobInvolvement": 3,
        "JobLevel": 2,
        "JobSatisfaction": 3,
        "MonthlyIncome": 50000,
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
    response = client.post("/api/predict", json=valid_payload)
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["status"] == "success"
    assert "probability" in json_data["result"]
