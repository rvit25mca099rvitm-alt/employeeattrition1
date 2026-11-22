"""
Model Service module:
Handles model loading, single prediction, SHAP explanation calculation,
HR retention suggestions, and dataset analytics for Chart.js dashboards.
"""
import json
import logging
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import shap

from config import (
    MODEL_PATH,
    PIPELINE_PATH,
    METRICS_PATH,
    GLOBAL_SHAP_PATH,
    DATASET_PATH,
    UNNECESSARY_COLUMNS,
    TARGET_COLUMN,
    CATEGORICAL_FEATURES,
    NUMERICAL_FEATURES,
    get_risk_category,
)

logger = logging.getLogger(__name__)

class ModelService:
    def __init__(self):
        self.model = None
        self.pipeline = None
        self.feature_names = []
        self.explainer = None
        self.dataset_df = None
        self.metrics = {}
        self.global_shap = []
        self.load_artifacts()

    def load_artifacts(self):
        """Load trained model, pipeline, metrics, dataset, and initialize SHAP explainer."""
        try:
            if MODEL_PATH.exists() and PIPELINE_PATH.exists():
                self.model = joblib.load(MODEL_PATH)
                self.pipeline = joblib.load(PIPELINE_PATH)
                logger.info("Loaded model and preprocessing pipeline.")
            else:
                logger.warning("Model or pipeline not found on disk. Run train_model.py first.")

            if METRICS_PATH.exists():
                with open(METRICS_PATH, "r") as f:
                    self.metrics = json.load(f)
                    self.feature_names = self.metrics.get("feature_names", [])

            if GLOBAL_SHAP_PATH.exists():
                with open(GLOBAL_SHAP_PATH, "r") as f:
                    self.global_shap = json.load(f)

            if DATASET_PATH.exists():
                self.dataset_df = pd.read_csv(DATASET_PATH)
                # Initialize SHAP explainer with a sample of preprocessed data
                if self.model is not None and self.pipeline is not None:
                    raw_sample = self.dataset_df.drop(columns=UNNECESSARY_COLUMNS)
                    X_sample = raw_sample.drop(columns=[TARGET_COLUMN]).head(100)
                    X_sample_proc = self.pipeline.transform(X_sample)
                    self.explainer = shap.LinearExplainer(self.model, X_sample_proc)
                    logger.info("SHAP LinearExplainer initialized with background sample.")
            else:
                logger.warning(f"Dataset not found at {DATASET_PATH}")
        except Exception as e:
            logger.error(f"Error loading artifacts: {e}", exc_info=True)

    def predict_employee(self, input_dict):
        """
        Takes raw dictionary of input features for 1 employee, runs pipeline,
        predicts probability, class, risk category, and computes individual SHAP values.
        """
        if self.model is None or self.pipeline is None:
            raise RuntimeError("Model or pipeline is not loaded. Please train the model first.")

        # Construct single-row DataFrame
        df_input = pd.DataFrame([input_dict])

        # Cast types correctly
        for num_col in NUMERICAL_FEATURES:
            if num_col in df_input.columns:
                df_input[num_col] = pd.to_numeric(df_input[num_col], errors="coerce").fillna(0)

        # Seamlessly map Indian Rupee salaries (e.g. ₹50,000) to model scaling range (~1,000 to ~20,000)
        if "MonthlyIncome" in df_input.columns and (df_input["MonthlyIncome"] > 20000).any():
            df_input["MonthlyIncome"] = df_input["MonthlyIncome"] / 10.0

        for cat_col in CATEGORICAL_FEATURES:
            if cat_col in df_input.columns:
                df_input[cat_col] = df_input[cat_col].astype(str)

        # Preprocess features
        X_proc = self.pipeline.transform(df_input)

        # Predict probability for class 1 (Attrition: Yes)
        prob_attrition = float(self.model.predict_proba(X_proc)[0, 1])
        prediction = "Yes" if prob_attrition >= 0.50 else "No"
        risk_info = get_risk_category(prob_attrition)
        risk_category = risk_info["level"]
        risk_badge_class = risk_info["badge_class"]
        risk_color = risk_info["color"]
        risk_desc = risk_info["description"]

        # Compute SHAP explanation for this individual
        positive_factors, negative_factors, all_contributions = self._compute_individual_shap(X_proc)

        # Generate rule-based HR retention suggestions
        suggestions = self._generate_retention_suggestions(input_dict, prob_attrition)

        return {
            "prediction": prediction,
            "probability": round(prob_attrition * 100, 2),
            "risk_category": risk_category,
            "risk_badge": risk_badge_class,
            "risk_color": risk_color,
            "risk_description": risk_desc,
            "positive_factors": positive_factors,
            "negative_factors": negative_factors,
            "all_contributions": all_contributions,
            "suggestions": suggestions,
        }

    def _compute_individual_shap(self, X_proc):
        """Compute positive and negative SHAP contributions for the input sample."""
        try:
            shap_vals = self.explainer(X_proc)
            values = shap_vals.values[0]

            contributions = []
            for name, val in zip(self.feature_names, values):
                contributions.append({
                    "feature": name,
                    "value": round(float(val), 4),
                    "abs_value": abs(round(float(val), 4)),
                    "direction": "Increases Risk" if val > 0 else "Decreases Risk"
                })

            # Sort factors
            # Positive factors (val > 0): push prediction toward Attrition = Yes
            positive = sorted([c for c in contributions if c["value"] > 0], key=lambda x: x["value"], reverse=True)[:5]
            # Negative factors (val < 0): push prediction toward Retention / Attrition = No
            negative = sorted([c for c in contributions if c["value"] < 0], key=lambda x: x["value"])[:5]

            # Top 10 overall for chart
            top_all = sorted(contributions, key=lambda x: x["abs_value"], reverse=True)[:10]

            return positive, negative, top_all
        except Exception as e:
            logger.error(f"Error computing individual SHAP: {e}")
            return [], [], []

    def _generate_retention_suggestions(self, input_dict, probability):
        """
        Generate transparent, rule-based retention suggestions based on active HR indicators.
        """
        suggestions = []

        # Overtime
        if str(input_dict.get("OverTime", "")).lower() == "yes":
            suggestions.append({
                "category": "Workload & Working Hours",
                "concern": "Employee is engaged in frequent Overtime.",
                "action": "Audit current project deadlines, rebalance workloads across team members, and implement compensatory time-off to prevent burnout."
            })

        # Job Satisfaction
        job_sat = int(input_dict.get("JobSatisfaction", 3))
        if job_sat <= 2:
            suggestions.append({
                "category": "Job Satisfaction",
                "concern": f"Reported Job Satisfaction is low ({job_sat}/4).",
                "action": "Schedule an open one-on-one stay interview to discuss day-to-day responsibilities, pain points, and role alignment."
            })

        # Job Involvement
        job_inv = int(input_dict.get("JobInvolvement", 3))
        if job_inv <= 2:
            suggestions.append({
                "category": "Employee Engagement & Involvement",
                "concern": f"Job Involvement is rated low ({job_inv}/4).",
                "action": "Involve employee in key departmental initiatives, decision-making, and give greater project ownership."
            })

        # Career Stagnation in Current Role
        years_role = int(input_dict.get("YearsInCurrentRole", 0))
        if years_role >= 4:
            suggestions.append({
                "category": "Career Growth & Mobility",
                "concern": f"Employee has spent {years_role} years in the current role without transition.",
                "action": "Discuss career progression paths, provide cross-functional leadership opportunities, or sponsor specialized professional development."
            })

        # Compensation benchmark (INR)
        income = float(input_dict.get("MonthlyIncome", 50000))
        if income < 35000 or (income < 3500 and income > 0):
            suggestions.append({
                "category": "Compensation Review",
                "concern": f"Monthly income (₹{income:,.0f}) is below median organizational tier.",
                "action": "Conduct a compensation benchmark against current market rates for this role and consider a salary adjustment."
            })

        # Business Travel
        travel = str(input_dict.get("BusinessTravel", ""))
        if travel == "Travel_Frequently":
            suggestions.append({
                "category": "Travel & Work Fatigue",
                "concern": "Frequent business travel schedule required.",
                "action": "Explore options for virtual meetings, reduced travel frequency, or compensatory downtime following travel stints."
            })

        # Frequent Company Changes
        companies = int(input_dict.get("NumCompaniesWorked", 0))
        if companies >= 5:
            suggestions.append({
                "category": "Tenure & Loyalty Building",
                "concern": f"High historical mobility ({companies} previous companies worked).",
                "action": "Focus on building long-term organizational attachment, mentorship programs, and strong team connections."
            })

        # Fallback if no specific trigger fired but risk is moderate/high
        if not suggestions:
            if probability >= 0.30:
                suggestions.append({
                    "category": "General Retention Review",
                    "concern": "Moderate attrition risk identified by predictive factors.",
                    "action": "Hold an informal check-in meeting with HR business partner to review career aspirations and general sentiment."
                })
            else:
                suggestions.append({
                    "category": "Positive Retention State",
                    "concern": "Employee exhibits high retention indicators.",
                    "action": "Maintain ongoing appreciation, acknowledge contributions, and continue regular performance feedback."
                })

        return suggestions

    def get_dashboard_summary(self):
        """Compute key metrics and chart distributions from the dataset for Dashboard."""
        if self.dataset_df is None:
            return {}

        df = self.dataset_df
        total_employees = len(df)
        left_count = int((df["Attrition"] == "Yes").sum())
        retained_count = total_employees - left_count
        attrition_rate = round((left_count / total_employees) * 100, 1)

        # Department-wise Attrition
        dept_grouped = df.groupby(["Department", "Attrition"]).size().unstack(fill_value=0)
        dept_labels = list(dept_grouped.index)
        dept_attrition = [int(dept_grouped.loc[d, "Yes"]) if "Yes" in dept_grouped.columns else 0 for d in dept_labels]
        dept_retained = [int(dept_grouped.loc[d, "No"]) if "No" in dept_grouped.columns else 0 for d in dept_labels]

        # Job Role Attrition
        role_grouped = df.groupby(["JobRole", "Attrition"]).size().unstack(fill_value=0)
        role_labels = list(role_grouped.index)
        role_attrition = [int(role_grouped.loc[r, "Yes"]) if "Yes" in role_grouped.columns else 0 for r in role_labels]
        role_retained = [int(role_grouped.loc[r, "No"]) if "No" in role_grouped.columns else 0 for r in role_labels]

        # Overtime Attrition
        ot_grouped = df.groupby(["OverTime", "Attrition"]).size().unstack(fill_value=0)
        ot_labels = ["No Overtime", "Overtime"]
        ot_attrition = [
            int(ot_grouped.loc["No", "Yes"]) if "No" in ot_grouped.index and "Yes" in ot_grouped.columns else 0,
            int(ot_grouped.loc["Yes", "Yes"]) if "Yes" in ot_grouped.index and "Yes" in ot_grouped.columns else 0
        ]
        ot_retained = [
            int(ot_grouped.loc["No", "No"]) if "No" in ot_grouped.index and "No" in ot_grouped.columns else 0,
            int(ot_grouped.loc["Yes", "No"]) if "Yes" in ot_grouped.index and "No" in ot_grouped.columns else 0
        ]

        return {
            "total_employees": total_employees,
            "left_count": left_count,
            "retained_count": retained_count,
            "attrition_rate": attrition_rate,
            "department_chart": {
                "labels": dept_labels,
                "attrition": dept_attrition,
                "retained": dept_retained
            },
            "role_chart": {
                "labels": role_labels,
                "attrition": role_attrition,
                "retained": role_retained
            },
            "overtime_chart": {
                "labels": ot_labels,
                "attrition": ot_attrition,
                "retained": ot_retained
            }
        }

    def get_analysis_data(self):
        """Detailed HR analytics data for the Attrition Analysis page."""
        if self.dataset_df is None:
            return {}

        df = self.dataset_df

        # Age Groups
        bins = [18, 25, 35, 45, 55, 65]
        labels = ["18-25", "26-35", "36-45", "46-55", "56-65"]
        df_copy = df.copy()
        df_copy["AgeGroup"] = pd.cut(df_copy["Age"], bins=bins, labels=labels, right=True)
        age_grp = df_copy.groupby(["AgeGroup", "Attrition"], observed=False).size().unstack(fill_value=0)
        age_labels = list(age_grp.index)
        age_attrition = [int(age_grp.loc[a, "Yes"]) if "Yes" in age_grp.columns else 0 for a in age_labels]
        age_retained = [int(age_grp.loc[a, "No"]) if "No" in age_grp.columns else 0 for a in age_labels]

        # Monthly Income Bins
        income_bins = [0, 3000, 6000, 10000, 15000, 25000]
        income_labels = ["< $3k", "$3k-$6k", "$6k-$10k", "$10k-$15k", "> $15k"]
        df_copy["IncomeBracket"] = pd.cut(df_copy["MonthlyIncome"], bins=income_bins, labels=income_labels, right=True)
        inc_grp = df_copy.groupby(["IncomeBracket", "Attrition"], observed=False).size().unstack(fill_value=0)
        inc_labels = list(inc_grp.index)
        inc_attrition = [int(inc_grp.loc[i, "Yes"]) if "Yes" in inc_grp.columns else 0 for i in inc_labels]
        inc_retained = [int(inc_grp.loc[i, "No"]) if "No" in inc_grp.columns else 0 for i in inc_labels]

        # Job Satisfaction breakdown
        sat_grp = df.groupby(["JobSatisfaction", "Attrition"]).size().unstack(fill_value=0)
        sat_labels = ["1 - Low", "2 - Medium", "3 - High", "4 - Very High"]
        sat_attrition = [int(sat_grp.loc[idx, "Yes"]) if idx in sat_grp.index and "Yes" in sat_grp.columns else 0 for idx in [1, 2, 3, 4]]
        sat_retained = [int(sat_grp.loc[idx, "No"]) if idx in sat_grp.index and "No" in sat_grp.columns else 0 for idx in [1, 2, 3, 4]]

        # Work-Life Balance breakdown
        wlb_grp = df.groupby(["WorkLifeBalance", "Attrition"]).size().unstack(fill_value=0)
        wlb_labels = ["1 - Bad", "2 - Good", "3 - Better", "4 - Best"]
        wlb_attrition = [int(wlb_grp.loc[idx, "Yes"]) if idx in wlb_grp.index and "Yes" in wlb_grp.columns else 0 for idx in [1, 2, 3, 4]]
        wlb_retained = [int(wlb_grp.loc[idx, "No"]) if idx in wlb_grp.index and "No" in wlb_grp.columns else 0 for idx in [1, 2, 3, 4]]

        return {
            "age_chart": {"labels": age_labels, "attrition": age_attrition, "retained": age_retained},
            "income_chart": {"labels": inc_labels, "attrition": inc_attrition, "retained": inc_retained},
            "satisfaction_chart": {"labels": sat_labels, "attrition": sat_attrition, "retained": sat_retained},
            "worklife_chart": {"labels": wlb_labels, "attrition": wlb_attrition, "retained": wlb_retained},
        }

# Singleton instance
model_service = ModelService()
