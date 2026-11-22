# Employee Attrition Analysis and Prediction Using Explainable AI (XAI)

An enterprise-grade MCA Major Project built with **Python Flask**, **Scikit-learn**, **SHAP (Explainable AI)**, **Chart.js**, and **SQLite**.

---

## 🌟 Key Features

1. **HR Management & Authentication**
   - Secure login and registration with salted PBKDF2 password hashing.
   - Protected routes and session management.
   - Seeded default administrator account: `Namratha K S` / `adminpass0213`.

2. **Interactive HR Dashboard**
   - Live KPI summary cards: Total Employees, Departed Staff, Retained Staff, and Attrition Rate.
   - Department-wise attrition breakdown with Chart.js.
   - Overtime correlation and Job Role distribution analysis.

3. **Predictive Machine Learning Engine**
   - Preprocessing pipeline with `ColumnTransformer` (StandardScaler & OneHotEncoder) fitted on the IBM HR dataset.
   - Multi-metric benchmark between **Logistic Regression** and **Random Forest Classifier**.
   - Champion model selection prioritizes **Recall**, **F1-Score**, and **ROC-AUC** to minimize critical false negatives.
   - Models saved using **Joblib** (`models/attrition_model.pkl`, `models/preprocessing_pipeline.pkl`). No re-training on app requests.

4. **Explainable AI (SHAP Interpretability)**
   - **Global Feature Importance**: Top 5 and Top 15 factors ranked by Mean Absolute SHAP values across 1,470 employee records.
   - **Individual Employee Explanation**: Positive (risk-increasing) and Negative (retention-supporting) SHAP values calculated for every single assessment.
   - Horizontal bar charts visually displaying factor directions and magnitudes.

5. **Actionable HR Retention Recommendations**
   - Rule-based suggestions tailored to specific employee pain points (Overtime fatigue, Job Satisfaction, Environment, Promotion stagnation, Commute distance, Stock Options).

6. **SQLite Prediction Audit Trail**
   - Complete historical logging of employee assessments in `database/attrition.db`.
   - Real-time client-side search and filtering.

7. **Model Performance Module**
   - Side-by-side algorithm comparison table.
   - Detailed Confusion Matrices (True Positives, False Positives, True Negatives, False Negatives).
   - Pedagogical explanations on the business significance of Recall in HR analytics.

---

## 🛠️ Technology Stack

- **Backend:** Python 3.10+, Flask
- **Frontend:** HTML5, CSS3, Bootstrap 5, Bootstrap Icons, JavaScript, Chart.js
- **Machine Learning & XAI:** Pandas, NumPy, Scikit-learn, SHAP, Joblib
- **Database:** SQLite3

---

## 📁 Project Directory Structure

```
employeeattrition/
│
├── app.py                      # Flask web application controller and routes
├── train_model.py              # ML model training, evaluation, and SHAP serialization
├── model_service.py            # Inference engine, individual SHAP, and analytics
├── database.py                 # SQLite database helper and user authentication
├── config.py                   # Central configurations, feature names, and thresholds
├── requirements.txt            # Python dependencies
│
├── dataset/
│   └── WA_Fn-UseC_-HR-Employee-Attrition.csv  # IBM HR Analytics Dataset
│
├── models/
│   ├── attrition_model.pkl         # Serialized champion model
│   ├── preprocessing_pipeline.pkl  # Serialized ColumnTransformer pipeline
│   ├── model_metrics.json          # Benchmark evaluation metrics & confusion matrices
│   └── global_shap.json            # Mean absolute SHAP values for global ranking
│
├── database/
│   └── attrition.db            # SQLite database with users and predictions tables
│
├── templates/
│   ├── base.html               # Base layout with Dark Navy sidebar and 7 nav links
│   ├── login.html              # HR login portal
│   ├── register.html           # Admin registration
│   ├── dashboard.html          # Executive HR analytics dashboard
│   ├── analysis.html           # Deep demographic and satisfaction analysis
│   ├── predict.html            # 30-feature assessment form with 1-click test profiles
│   ├── result.html             # Individual verdict, probability meter, and SHAP chart
│   ├── explainability.html     # Global XAI insights and Top 5 attrition drivers
│   ├── history.html            # SQLite prediction audit log
│   └── performance.html        # Model benchmark and confusion matrices
│
├── static/
│   ├── css/
│   │   └── style.css           # Clean, professional HR styling
│   └── js/
│       └── charts.js           # Chart.js color palette and utility functions
│
└── README.md
```

---

## 🚀 Getting Started

### 1. Install Dependencies
Make sure Python is installed, then run:
```bash
pip install -r requirements.txt
```

### 2. Train the Machine Learning Model
To generate the model artifacts (`attrition_model.pkl`, `preprocessing_pipeline.pkl`, `model_metrics.json`, `global_shap.json`):
```bash
python train_model.py
```

### 3. Run the Flask Web Application
```bash
python app.py
```
Open your browser and navigate to:
**http://127.0.0.1:5001**

### 4. Default Login Credentials
- **Username:** `Namratha K S`
- **Password:** `adminpass0213`
*(You can also create a new administrator account via the registration page).*

---

## 📊 Configurable Risk Thresholds

- **Low Risk:** Turnover Probability < 30% (Stable retention)
- **Medium Risk:** 30% ≤ Turnover Probability < 60% (Monitoring suggested)
- **High Risk:** Turnover Probability ≥ 60% (Immediate HR intervention recommended)
