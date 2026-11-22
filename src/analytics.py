"""
HR Analytics and interactive data visualization engine using Plotly.
Computes workforce KPIs, historical distributions, attrition breakdowns,
and dynamic filtered analytics for HR dashboards.
"""
from typing import Dict, Any, Optional
import json
import numpy as np
import pandas as pd
import joblib
import plotly.express as px
import plotly.graph_objects as go
import plotly.utils

import config
from src.data_preprocessing import load_raw_dataset

# Colors
COLOR_LEAVE = "#dc3545"    # Crimson Red
COLOR_STAY = "#0d6efd"     # Royal Blue
COLOR_ACCENT = "#20c997"   # Teal

def get_dashboard_data(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Computes summary metrics and interactive Plotly chart JSON objects
    supporting dynamic HR dashboard filters.
    """
    df_all = load_raw_dataset()

    active_filters = dict(filters) if filters else {}
    selected_dept = active_filters.get("department", "All")
    selected_role = active_filters.get("job_role", "All")

    # Dynamic JobRole choices matching selected department
    if selected_dept and selected_dept != "All":
        dept_roles = sorted(list(df_all[df_all["Department"] == selected_dept]["JobRole"].unique()))
        available_roles = ["All"] + dept_roles
        if selected_role not in available_roles:
            selected_role = "All"
            active_filters["job_role"] = "All"
    else:
        available_roles = ["All"] + config.CATEGORICAL_CHOICES["JobRole"]

    # Filter dataset
    df = df_all.copy()
    if selected_dept and selected_dept != "All":
        df = df[df["Department"] == selected_dept]
    if selected_role and selected_role != "All":
        df = df[df["JobRole"] == selected_role]
    if active_filters.get("overtime") and active_filters["overtime"] != "All":
        df = df[df["OverTime"] == active_filters["overtime"]]
    if active_filters.get("min_age"):
        try:
            df = df[df["Age"] >= int(active_filters["min_age"])]
        except ValueError:
            pass
    if active_filters.get("max_age"):
        try:
            df = df[df["Age"] <= int(active_filters["max_age"])]
        except ValueError:
            pass

    total_records = len(df)
    
    # Filter dictionary returned to template
    filter_dict = {
        "departments": ["All"] + config.CATEGORICAL_CHOICES["Department"],
        "roles": available_roles,
        "overtime_options": ["All", "Yes", "No"],
        "selected_dept": selected_dept,
        "selected_role": selected_role,
        "selected_overtime": active_filters.get("overtime", "All"),
        "selected_min_age": active_filters.get("min_age", ""),
        "selected_max_age": active_filters.get("max_age", ""),
    }

    if total_records == 0:
        return {
            "empty": True,
            "total_records": 0,
            "filters": filter_dict,
            "charts": {
                "dept": "{}", "role": "{}", "overtime": "{}",
                "satisfaction": "{}", "income": "{}", "age": "{}", "global_shap": None
            },
            "kpis": {
                "total_records": "0", "left_count": "0", "stay_count": "0",
                "attrition_rate": "0%", "avg_income": "₹0", "avg_tenure": "0 yrs", "avg_age": "0 yrs"
            }
        }

    left_count = int((df["Attrition"] == "Yes").sum())
    stay_count = int((df["Attrition"] == "No").sum())
    attrition_rate = round((left_count / total_records) * 100, 1) if total_records > 0 else 0.0
    avg_income = round(float(df["MonthlyIncome"].mean()), 2) if total_records > 0 else 0.0
    avg_tenure = round(float(df["YearsAtCompany"].mean()), 1) if total_records > 0 else 0.0
    avg_age = round(float(df["Age"].mean()), 1) if total_records > 0 else 0.0

    # 1. Department Breakdown Chart
    dept_df = (
        df.groupby(["Department", "Attrition"])
        .size()
        .reset_index(name="Count")
    )
    if not dept_df.empty:
        dept_fig = px.bar(
            dept_df,
            x="Department",
            y="Count",
            color="Attrition",
            barmode="group",
            color_discrete_map={"Yes": COLOR_LEAVE, "No": COLOR_STAY},
            title="Employee Count & Attrition by Department",
        )
    else:
        dept_fig = go.Figure()

    dept_fig.update_layout(
        height=320,
        margin=dict(l=20, r=20, t=40, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
    )

    # 2. Job Role Breakdown Chart (Horizontal Bar)
    role_df = (
        df.groupby(["JobRole", "Attrition"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    if "Yes" not in role_df.columns:
        role_df["Yes"] = 0
    if "No" not in role_df.columns:
        role_df["No"] = 0
    role_df["Total"] = role_df["Yes"] + role_df["No"]
    role_df["Rate"] = (role_df["Yes"] / role_df["Total"].replace(0, 1)) * 100
    role_df = role_df.sort_values(by="Rate", ascending=True)

    role_fig = go.Figure()
    role_fig.add_trace(
        go.Bar(
            y=role_df["JobRole"],
            x=role_df["Rate"],
            orientation="h",
            marker_color=COLOR_LEAVE,
            text=[f"{r:.1f}% ({y})" for r, y in zip(role_df["Rate"], role_df["Yes"])],
            textposition="auto",
        )
    )
    role_fig.update_layout(
        title="Attrition Rate by Job Role (%)",
        xaxis_title="Attrition Rate (%)",
        height=360,
        margin=dict(l=20, r=20, t=40, b=30),
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
    )

    # 3. Overtime Attrition Impact
    ot_df = (
        df.groupby(["OverTime", "Attrition"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    if "Yes" not in ot_df.columns:
        ot_df["Yes"] = 0
    if "No" not in ot_df.columns:
        ot_df["No"] = 0
    ot_df["Total"] = ot_df["Yes"] + ot_df["No"]
    ot_df["Attrition_Rate"] = (ot_df["Yes"] / ot_df["Total"].replace(0, 1)) * 100

    ot_fig = go.Figure()
    ot_fig.add_trace(go.Bar(
        name="Stayed",
        x=ot_df["OverTime"],
        y=ot_df["No"],
        marker_color=COLOR_STAY
    ))
    ot_fig.add_trace(go.Bar(
        name="Left",
        x=ot_df["OverTime"],
        y=ot_df["Yes"],
        marker_color=COLOR_LEAVE
    ))
    ot_fig.update_layout(
        barmode="stack",
        title="Attrition by Overtime Status",
        xaxis_title="OverTime",
        yaxis_title="Headcount",
        height=320,
        margin=dict(l=20, r=20, t=40, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
    )

    # 4. Job Satisfaction Impact
    sat_df = (
        df.groupby(["JobSatisfaction", "Attrition"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    if "Yes" not in sat_df.columns:
        sat_df["Yes"] = 0
    if "No" not in sat_df.columns:
        sat_df["No"] = 0
    sat_df["Total"] = sat_df["Yes"] + sat_df["No"]
    sat_df["Rate"] = (sat_df["Yes"] / sat_df["Total"].replace(0, 1)) * 100
    
    sat_map = {1: "1 (Low)", 2: "2 (Medium)", 3: "3 (High)", 4: "4 (Very High)"}
    sat_labels = [sat_map.get(int(i), f"Level {i}") for i in sat_df["JobSatisfaction"]]

    sat_fig = go.Figure(
        go.Bar(
            x=sat_labels,
            y=sat_df["Rate"],
            marker_color="#fd7e14",
            text=[f"{r:.1f}%" for r in sat_df["Rate"]],
            textposition="auto",
        )
    )
    sat_fig.update_layout(
        title="Attrition Rate by Job Satisfaction Level",
        xaxis_title="Satisfaction Level",
        yaxis_title="Attrition Rate (%)",
        height=320,
        margin=dict(l=20, r=20, t=40, b=30),
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
    )

    # 5. Monthly Income Distribution Boxplot
    if len(df) > 0 and len(df["Attrition"].unique()) > 0:
        inc_fig = px.box(
            df,
            x="Attrition",
            y="MonthlyIncome",
            color="Attrition",
            color_discrete_map={"Yes": COLOR_LEAVE, "No": COLOR_STAY},
            title="Monthly Income Distribution (₹)",
        )
    else:
        inc_fig = go.Figure()

    inc_fig.update_layout(
        height=320,
        margin=dict(l=20, r=20, t=40, b=30),
        showlegend=False,
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
    )

    # 6. Age Group Breakdown
    df_copy = df.copy()
    age_bins = [17, 25, 35, 45, 55, 70]
    age_labels = ["<25", "25-34", "35-44", "45-54", "55+"]
    df_copy["AgeGroup"] = pd.cut(df_copy["Age"], bins=age_bins, labels=age_labels, right=True)
    age_df = (
        df_copy.groupby(["AgeGroup", "Attrition"], observed=False)
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    if "Yes" not in age_df.columns:
        age_df["Yes"] = 0
    if "No" not in age_df.columns:
        age_df["No"] = 0
    age_df["Rate"] = (age_df["Yes"] / (age_df["Yes"] + age_df["No"]).replace(0, 1)) * 100

    age_fig = go.Figure(
        go.Bar(
            x=[str(x) for x in age_df["AgeGroup"]],
            y=age_df["Rate"],
            marker_color="#6f42c1",
            text=[f"{r:.1f}%" for r in age_df["Rate"]],
            textposition="auto",
        )
    )
    age_fig.update_layout(
        title="Attrition Rate by Age Bracket",
        xaxis_title="Age Bracket",
        yaxis_title="Attrition Rate (%)",
        height=320,
        margin=dict(l=20, r=20, t=40, b=30),
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
    )

    # 7. Global SHAP Feature Importance Chart
    shap_fig_json = None
    if config.SHAP_SUMMARY_PATH.exists():
        shap_data = joblib.load(config.SHAP_SUMMARY_PATH)
        top_importances = shap_data.get("global_importance", [])[:12]
        if top_importances:
            feat_names = [item["feature"] for item in reversed(top_importances)]
            feat_vals = [item["importance"] for item in reversed(top_importances)]

            shap_fig = go.Figure(
                go.Bar(
                    x=feat_vals,
                    y=feat_names,
                    orientation="h",
                    marker_color="#0dcaf0",
                    text=[f"{v:.3f}" for v in feat_vals],
                    textposition="auto",
                )
            )
            shap_fig.update_layout(
                title="Global Feature Importance (Mean |SHAP Value| Across Dataset)",
                xaxis_title="Mean |SHAP Attribution| (Log-odds / Impact)",
                height=380,
                margin=dict(l=20, r=20, t=40, b=30),
                plot_bgcolor="#ffffff",
                paper_bgcolor="#ffffff",
            )
            shap_fig_json = json.dumps(shap_fig, cls=plotly.utils.PlotlyJSONEncoder)

    return {
        "empty": False,
        "kpis": {
            "total_records": f"{total_records:,}",
            "left_count": f"{left_count:,}",
            "stay_count": f"{stay_count:,}",
            "attrition_rate": f"{attrition_rate}%",
            "avg_income": f"₹{avg_income:,.0f}",
            "avg_tenure": f"{avg_tenure} yrs",
            "avg_age": f"{avg_age} yrs",
        },
        "charts": {
            "dept": json.dumps(dept_fig, cls=plotly.utils.PlotlyJSONEncoder),
            "role": json.dumps(role_fig, cls=plotly.utils.PlotlyJSONEncoder),
            "overtime": json.dumps(ot_fig, cls=plotly.utils.PlotlyJSONEncoder),
            "satisfaction": json.dumps(sat_fig, cls=plotly.utils.PlotlyJSONEncoder),
            "income": json.dumps(inc_fig, cls=plotly.utils.PlotlyJSONEncoder),
            "age": json.dumps(age_fig, cls=plotly.utils.PlotlyJSONEncoder),
            "global_shap": shap_fig_json,
        },
        "filters": filter_dict,
    }
