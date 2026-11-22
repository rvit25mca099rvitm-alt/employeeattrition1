"""
Central configuration for Employee Attrition Analysis and Prediction project.
"""
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent

# Dataset paths (primary and fallback)
PRIMARY_DATASET = BASE_DIR / "dataset" / "WA_Fn-UseC_-HR-Employee-Attrition.csv"
FALLBACK_DATASET = BASE_DIR / "data" / "employee_attrition.csv"
DATASET_PATH = PRIMARY_DATASET if PRIMARY_DATASET.exists() else FALLBACK_DATASET

# Database
DATABASE_DIR = BASE_DIR / "database"
DATABASE_DIR.mkdir(exist_ok=True)
DATABASE_PATH = DATABASE_DIR / "attrition.db"

# Model paths
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)
MODEL_PATH = MODELS_DIR / "attrition_model.pkl"
PIPELINE_PATH = MODELS_DIR / "preprocessing_pipeline.pkl"
METRICS_PATH = MODELS_DIR / "model_metrics.json"
GLOBAL_SHAP_PATH = MODELS_DIR / "global_shap.json"

# Web App Configuration
SECRET_KEY = os.environ.get("SECRET_KEY", "mca_attrition_xai_secret_key_2026")
PORT = int(os.environ.get("PORT", 5001))

# Feature definitions
TARGET_COLUMN = "Attrition"

UNNECESSARY_COLUMNS = [
    "EmployeeNumber",
    "EmployeeCount",
    "Over18",
    "StandardHours",
    # User-requested excluded features:
    "DistanceFromHome",
    "YearsSinceLastPromotion",
    "YearsWithCurrManager",
    "TrainingTimesLastYear",
    "PercentSalaryHike",
    "StockOptionLevel",
    "DailyRate",
    "EnvironmentSatisfaction",
    "RelationshipSatisfaction",
    "WorkLifeBalance",
    "HourlyRate",
    "MonthlyRate",
]

CATEGORICAL_FEATURES = [
    "BusinessTravel",
    "Department",
    "EducationField",
    "Gender",
    "JobRole",
    "MaritalStatus",
    "OverTime",
]

NUMERICAL_FEATURES = [
    "Age",
    "Education",
    "JobInvolvement",
    "JobLevel",
    "JobSatisfaction",
    "MonthlyIncome",
    "NumCompaniesWorked",
    "PerformanceRating",
    "TotalWorkingYears",
    "YearsAtCompany",
    "YearsInCurrentRole",
]

CATEGORICAL_CHOICES = {
    "BusinessTravel": ["Travel_Rarely", "Travel_Frequently", "Non-Travel"],
    "Department": ["Sales", "Research & Development", "Human Resources"],
    "EducationField": ["Life Sciences", "Medical", "Marketing", "Technical Degree", "Human Resources", "Other"],
    "Gender": ["Male", "Female"],
    "JobRole": [
        "Sales Executive",
        "Research Scientist",
        "Laboratory Technician",
        "Manufacturing Director",
        "Healthcare Representative",
        "Manager",
        "Sales Representative",
        "Research Director",
        "Human Resources",
    ],
    "MaritalStatus": ["Single", "Married", "Divorced"],
    "OverTime": ["Yes", "No"],
}

NUMERICAL_SPECS = {
    "Age": {"min": 18, "max": 65, "default": 35, "label": "Age (Years)", "step": 1},
    "Education": {"min": 1, "max": 5, "default": 3, "label": "Education Level (1-5)", "step": 1},
    "JobInvolvement": {"min": 1, "max": 4, "default": 3, "label": "Job Involvement (1-4)", "step": 1},
    "JobLevel": {"min": 1, "max": 5, "default": 2, "label": "Job Level (1-5)", "step": 1},
    "JobSatisfaction": {"min": 1, "max": 4, "default": 3, "label": "Job Satisfaction (1-4)", "step": 1},
    "MonthlyIncome": {"min": 10000, "max": 1000000, "default": 50000, "label": "Monthly Income (₹)", "step": 1000},
    "NumCompaniesWorked": {"min": 0, "max": 10, "default": 2, "label": "Companies Worked", "step": 1},
    "PerformanceRating": {"min": 1, "max": 4, "default": 3, "label": "Performance Rating (1-4)", "step": 1},
    "TotalWorkingYears": {"min": 0, "max": 45, "default": 8, "label": "Total Working Years", "step": 1},
    "YearsAtCompany": {"min": 0, "max": 40, "default": 3, "label": "Years at Company", "step": 1},
    "YearsInCurrentRole": {"min": 0, "max": 20, "default": 2, "label": "Years in Current Role", "step": 1},
}

# Configurable Risk Thresholds
LOW_RISK_THRESHOLD = 0.30       # < 30% = Low Risk
HIGH_RISK_THRESHOLD = 0.60      # >= 60% = High Risk, between 30% and 60% = Medium Risk

def get_risk_category(prob: float) -> dict:
    """Classifies probability into Low, Medium, or High Risk with visual metadata."""
    if prob >= HIGH_RISK_THRESHOLD:
        return {
            "level": "High Risk",
            "badge_class": "badge-high-risk",
            "color": "#dc3545",
            "description": "High probability of voluntary turnover. Immediate proactive retention intervention recommended."
        }
    elif prob >= LOW_RISK_THRESHOLD:
        return {
            "level": "Medium Risk",
            "badge_class": "badge-medium-risk",
            "color": "#ffc107",
            "description": "Moderate turnover probability. Monitoring and supportive engagement recommended."
        }
    else:
        return {
            "level": "Low Risk",
            "badge_class": "badge-low-risk",
            "color": "#198754",
            "description": "Low turnover probability. Employee exhibits healthy organizational retention stability."
        }
