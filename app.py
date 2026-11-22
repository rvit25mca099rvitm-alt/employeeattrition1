"""
Main Flask Application for Employee Attrition Analysis and Prediction Using Explainable AI.
MCA Major Project.
"""
import functools
import json
import logging
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify
)
from config import (
    SECRET_KEY, PORT, NUMERICAL_SPECS, CATEGORICAL_CHOICES
)
NUMERICAL_INPUT_RANGES = NUMERICAL_SPECS
CATEGORICAL_OPTIONS = CATEGORICAL_CHOICES
import database
from model_service import model_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = SECRET_KEY

# Initialize database tables on startup
database.init_db()

def login_required(view):
    """Decorator to require login for protected routes."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login"))
        return view(**kwargs)
    return wrapped_view

# ==========================================
# Authentication Routes
# ==========================================

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Please enter both username and password.", "danger")
            return render_template("login.html")

        valid, user = database.verify_user(username, password)
        if valid and user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash(f"Welcome back, {user['username']}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password. Please try again.", "danger")

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not username or not password:
            flash("Username and password are required.", "danger")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return render_template("register.html")

        success, msg = database.register_user(username, password, email)
        if success:
            flash("Registration successful! You may now log in.", "success")
            return redirect(url_for("login"))
        else:
            flash(msg, "danger")

    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out securely.", "info")
    return redirect(url_for("login"))

# ==========================================
# Application Modules
# ==========================================

@app.route("/")
@app.route("/dashboard")
@login_required
def dashboard():
    """Module 2: HR Dashboard with key indicators and Chart.js visuals."""
    summary = model_service.get_dashboard_summary()
    return render_template("dashboard.html", summary=summary)

@app.route("/analysis")
@login_required
def analysis():
    """Detailed EDA: Attrition Breakdown across Age, Income, and Satisfaction."""
    analysis_data = model_service.get_analysis_data()
    return render_template("analysis.html", data=analysis_data)

@app.route("/predict", methods=["GET", "POST"])
@login_required
def predict():
    """Module 3: Employee Attrition Prediction input form & submission."""
    if request.method == "POST":
        try:
            form = request.form
            emp_ref = form.get("EmployeeRef", f"EMP-{hash(str(form)) % 10000:04d}")

            # Collect active form fields (only 18 active features)
            input_dict = {
                "Age": int(form.get("Age", 30)),
                "BusinessTravel": form.get("BusinessTravel", "Travel_Rarely"),
                "Department": form.get("Department", "Research & Development"),
                "Education": int(form.get("Education", 3)),
                "EducationField": form.get("EducationField", "Life Sciences"),
                "Gender": form.get("Gender", "Male"),
                "JobInvolvement": int(form.get("JobInvolvement", 3)),
                "JobLevel": int(form.get("JobLevel", 2)),
                "JobRole": form.get("JobRole", "Research Scientist"),
                "JobSatisfaction": int(form.get("JobSatisfaction", 3)),
                "MaritalStatus": form.get("MaritalStatus", "Married"),
                "MonthlyIncome": float(form.get("MonthlyIncome", 5000)),
                "NumCompaniesWorked": int(form.get("NumCompaniesWorked", 2)),
                "OverTime": form.get("OverTime", "No"),
                "PerformanceRating": int(form.get("PerformanceRating", 3)),
                "TotalWorkingYears": int(form.get("TotalWorkingYears", 8)),
                "YearsAtCompany": int(form.get("YearsAtCompany", 4)),
                "YearsInCurrentRole": int(form.get("YearsInCurrentRole", 2)),
            }

            # Predict and compute SHAP explanation
            result = model_service.predict_employee(input_dict)

            # Save prediction to SQLite database
            top_pos_str = ", ".join([f"{f['feature']} (+{f['value']})" for f in result["positive_factors"][:3]])
            top_neg_str = ", ".join([f"{f['feature']} ({f['value']})" for f in result["negative_factors"][:3]])

            pred_id = database.save_prediction(
                employee_ref=emp_ref,
                age=input_dict["Age"],
                department=input_dict["Department"],
                job_role=input_dict["JobRole"],
                monthly_income=input_dict["MonthlyIncome"],
                overtime=input_dict["OverTime"],
                prediction=result["prediction"],
                probability=result["probability"],
                risk_category=result["risk_category"],
                top_positive=top_pos_str,
                top_negative=top_neg_str
            )

            return render_template(
                "result.html",
                emp_ref=emp_ref,
                emp_data=input_dict,
                result=result,
                pred_id=pred_id
            )

        except Exception as e:
            logger.error(f"Error during prediction: {e}", exc_info=True)
            flash(f"Error processing prediction: {str(e)}", "danger")
            return redirect(url_for("predict"))

    return render_template(
        "predict.html",
        categorical_options=CATEGORICAL_OPTIONS,
        numerical_ranges=NUMERICAL_INPUT_RANGES
    )

@app.route("/explainability")
@login_required
def explainability():
    """Module 4: Explainable AI Using SHAP - Global Feature Importance."""
    global_shap = model_service.global_shap
    top5_factors = global_shap[:5] if global_shap else []
    top15_factors = global_shap[:15] if global_shap else []

    return render_template(
        "explainability.html",
        top5_factors=top5_factors,
        top15_factors=top15_factors,
        all_factors=global_shap
    )

import re

def clean_feature_name(raw):
    """Converts internal feature names and SHAP notations into friendly readable phrases."""
    name = re.sub(r"\s*\([+-]?[\d.]+\)", "", raw).strip()
    mapping = {
        "OverTime: Yes": "Working Overtime hours",
        "OverTime: No": "Standard working hours (no overtime)",
        "JobSatisfaction": "Lower Job Satisfaction rating",
        "MonthlyIncome": "Monthly compensation level",
        "JobInvolvement": "Job involvement level",
        "NumCompaniesWorked": "Frequent company changes",
        "Age": "Early career age bracket",
        "TotalWorkingYears": "Total working experience",
        "YearsAtCompany": "Years of service at the company",
        "YearsInCurrentRole": "Years in the current role",
        "JobLevel": "Current job hierarchy level",
        "PerformanceRating": "Performance evaluation score",
        "BusinessTravel: Travel_Frequently": "Frequent business travel",
        "BusinessTravel: Travel_Rarely": "Occasional business travel",
        "BusinessTravel: Non-Travel": "Non-travel work arrangement",
        "MaritalStatus: Single": "Single marital status",
        "MaritalStatus: Married": "Married marital status",
        "MaritalStatus: Divorced": "Divorced marital status",
        "Department: Sales": "Sales department demands",
        "Department: Research & Development": "R&D project alignment",
        "Department: Human Resources": "HR departmental environment",
    }
    for k, v in mapping.items():
        if k.lower() in name.lower():
            return v
    if "jobrole:" in name.lower():
        role = name.split(":")[-1].strip()
        return f"{role} role dynamics"
    if "educationfield:" in name.lower():
        field = name.split(":")[-1].strip()
        return f"{field} educational background"
    return name

def format_personalized_xai_summary(rec):
    """Builds an individual, plain-English explanation tailored to that employee's prediction."""
    pos_raw = rec.get("top_positive_factors") or ""
    neg_raw = rec.get("top_negative_factors") or ""
    prob = float(rec.get("probability", 0))
    emp_ref = rec.get("employee_ref", "This employee")
    role = rec.get("job_role", "Employee")
    dept = rec.get("department", "Department")

    pos_items = [clean_feature_name(x) for x in pos_raw.split(",") if x.strip()]
    neg_items = [clean_feature_name(x) for x in neg_raw.split(",") if x.strip()]

    if prob >= 60:
        if pos_items:
            reasons_str = " and ".join(pos_items[:2])
            text = f"For {emp_ref} ({role} in {dept}), the high turnover risk ({prob}%) is primarily driven by {reasons_str}."
            if neg_items:
                text += f" While {neg_items[0]} provides some retention stability, it is currently outweighed by these risk factors."
        else:
            text = f"For {emp_ref}, multiple working factors combine to indicate high turnover risk ({prob}%)."
        action = f"HR Action: Schedule a supportive one-on-one stay conversation with this {role} to review their workload and resolve key concerns early."
    elif prob >= 30:
        if pos_items and neg_items:
            text = f"For {emp_ref} ({role}), the moderate turnover risk ({prob}%) is influenced by {pos_items[0]}, but balanced by stabilizing factors such as {neg_items[0]}."
        elif pos_items:
            text = f"For {emp_ref}, the turnover likelihood ({prob}%) is slightly elevated due to {pos_items[0]}."
        else:
            text = f"For {emp_ref}, this employee exhibits a moderate turnover probability of {prob}% with balanced workplace indicators."
        action = f"HR Action: Check in during the next review to ensure {pos_items[0] if pos_items else 'job satisfaction'} is actively supported."
    else:
        if neg_items:
            anchors_str = " and ".join(neg_items[:2])
            text = f"For {emp_ref} ({role}), the low turnover chance ({prob}%) reflects strong retention stability, supported primarily by {anchors_str}."
        else:
            text = f"For {emp_ref}, this employee exhibits healthy job stability with a very low turnover probability of {prob}%."
        action = f"HR Action: Continue regular engagement and acknowledge their contributions to maintain this positive retention state."

    return {
        "pos_items": pos_items,
        "neg_items": neg_items,
        "individual_reason": text,
        "individual_action": action,
    }

@app.route("/history")
@login_required
def history():
    """Module 6: Prediction History stored in SQLite with individualized XAI analysis."""
    records = database.get_prediction_history(limit=100)
    for rec in records:
        rec["xai_details"] = format_personalized_xai_summary(rec)
    return render_template("history.html", records=records)

@app.route("/performance")
@login_required
def performance():
    """Module 7: Model Performance comparison and confusion matrices."""
    metrics = model_service.metrics
    return render_template("performance.html", metrics=metrics)

# ==========================================
# API Helper Endpoint
# ==========================================

@app.route("/api/sample_profile/<profile_type>")
@login_required
def sample_profile(profile_type):
    """Returns sample pre-filled profiles for testing the prediction form."""
    if profile_type == "high_risk":
        data = {
            "EmployeeRef": "EMP-HIGH-01",
            "Age": 28,
            "BusinessTravel": "Travel_Frequently",
            "Department": "Sales",
            "Education": 2,
            "EducationField": "Marketing",
            "Gender": "Male",
            "JobInvolvement": 1,
            "JobLevel": 1,
            "JobRole": "Sales Representative",
            "JobSatisfaction": 1,
            "MaritalStatus": "Single",
            "MonthlyIncome": 2300,
            "NumCompaniesWorked": 5,
            "OverTime": "Yes",
            "PerformanceRating": 3,
            "TotalWorkingYears": 3,
            "YearsAtCompany": 1,
            "YearsInCurrentRole": 0,
        }
    else:  # low_risk
        data = {
            "EmployeeRef": "EMP-LOW-02",
            "Age": 44,
            "BusinessTravel": "Non-Travel",
            "Department": "Research & Development",
            "Education": 4,
            "EducationField": "Life Sciences",
            "Gender": "Female",
            "JobInvolvement": 4,
            "JobLevel": 3,
            "JobRole": "Manufacturing Director",
            "JobSatisfaction": 4,
            "MaritalStatus": "Married",
            "MonthlyIncome": 9800,
            "NumCompaniesWorked": 1,
            "OverTime": "No",
            "PerformanceRating": 4,
            "TotalWorkingYears": 18,
            "YearsAtCompany": 12,
            "YearsInCurrentRole": 8,
        }
    return jsonify(data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)
