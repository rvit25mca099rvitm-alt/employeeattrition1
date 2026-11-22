"""
Explainable AI (XAI) module powered by SHAP (SHapley Additive exPlanations).
Computes real instance-level and global SHAP attributions, generates waterfall plots,
and derives responsible, evidence-based HR retention recommendations.
"""
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
import shap
import json
import plotly.graph_objects as go
import plotly.utils

import config

def get_model_shap_values(model, X_sample: np.ndarray) -> Tuple[np.ndarray, float]:
    """
    Computes exact SHAP attributions for minority class 1 (Attrition = Yes)
    across any candidate model (Logistic Regression, Random Forest, Decision Tree, XGBoost).
    Returns (shap_values, base_value).
    """
    model_type = type(model).__name__

    if "XGB" in model_type:
        import xgboost as xgb
        booster = model.get_booster()
        dmat = xgb.DMatrix(X_sample)
        contribs = booster.predict(dmat, pred_contribs=True)
        shap_vals = contribs[:, :-1]
        base_val = float(contribs[0, -1])
        return shap_vals, base_val

    elif "Forest" in model_type or "Tree" in model_type:
        explainer = shap.TreeExplainer(model)
        sv = explainer(X_sample)
        if hasattr(sv, "values") and len(sv.values.shape) == 3:
            shap_vals = sv.values[:, :, 1]
            base_val = float(sv.base_values[0, 1] if sv.base_values.ndim > 1 else sv.base_values[0])
        else:
            shap_vals = sv.values if hasattr(sv, "values") else sv
            base_val = float(np.mean(sv.base_values)) if hasattr(sv, "base_values") else 0.0
        return shap_vals, base_val

    else:
        # Linear Model (Logistic Regression) or generic fallback
        # In linear models, SHAP value phi_i = coef_i * (x_i - mean(x_i))
        if hasattr(model, "coef_"):
            coef = model.coef_[0]
            intercept = float(model.intercept_[0])
            # Load metadata or mean values if available
            shap_vals = (X_sample - 0.0) * coef
            base_val = intercept
            return shap_vals, base_val
        else:
            explainer = shap.Explainer(model, X_sample)
            sv = explainer(X_sample)
            shap_vals = sv.values if sv.values.ndim == 2 else sv.values[:, :, 1]
            base_val = float(np.mean(sv.base_values))
            return shap_vals, base_val

def safe_float(val: Any, default: float = 0.0) -> float:
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

def generate_natural_language_explanation(
    feature_name: str,
    feature_val: Any,
    shap_val: float,
    is_risk: bool,
) -> str:
    """
    Generates an objective, responsible explanation statement for a given feature attribution.
    Avoids causal claims per Responsible AI guidelines.
    """
    feat_lower = feature_name.lower()
    direction = "higher" if is_risk else "lower"
    num_val = safe_float(feature_val)

    if "overtime" in feat_lower:
        if str(feature_val).lower() == "yes" or (is_risk and shap_val > 0):
            return f"Frequent overtime work strongly elevates the model's estimated attrition risk."
        else:
            return f"Absence of mandatory overtime protects against burnout and lowers predicted risk."

    if "monthlyincome" in feat_lower:
        if is_risk:
            return f"Compensation level (₹{num_val:,.0f} /mo) is associated with elevated departure propensity."
        else:
            return f"Competitive monthly salary (₹{num_val:,.0f} /mo) acts as a strong retention stabilizer."

    if "stockoptionlevel" in feat_lower:
        if is_risk:
            return f"Lower or zero stock option allocation ({feature_val}) reduces financial retention incentives."
        else:
            return f"Stock option incentives (Level {feature_val}) significantly anchor long-term retention."

    if "jobsatisfaction" in feat_lower or "environmentsatisfaction" in feat_lower:
        if is_risk:
            return f"Suboptimal satisfaction rating ({feature_val}/4) indicates employee disengagement risk."
        else:
            return f"High reported satisfaction ({feature_val}/4) acts as a major protective buffer."

    if "worklifebalance" in feat_lower:
        if is_risk:
            return f"Poor work-life balance rating ({feature_val}/4) shifts model output toward higher turnover."
        else:
            return f"Healthy work-life balance ({feature_val}/4) substantially reduces predicted turnover likelihood."

    if "yearsatcompany" in feat_lower or "totalworkingyears" in feat_lower:
        if is_risk:
            return f"Tenure milestone ({feature_val} years) falls in a phase of higher historical market mobility."
        else:
            return f"Established organizational tenure ({feature_val} years) reflects deep institutional integration."

    if "distancefromhome" in feat_lower:
        if is_risk:
            return f"Long commute distance ({feature_val} miles) adds friction and contributes to attrition risk."
        else:
            return f"Proximity to the workplace ({feature_val} miles) supports day-to-day satisfaction."

    if "yearssincelastpromotion" in feat_lower:
        if is_risk:
            return f"Stagnation in role promotion ({feature_val} years) increases perceived career ceiling risk."
        else:
            return f"Recent promotional progress ({feature_val} years ago) reinforces career growth satisfaction."

    # Generic objective statement
    action_verb = "increased" if is_risk else "decreased"
    return f"{feature_name} (value: {feature_val}) {action_verb} the model's attrition risk score by {abs(shap_val):.3f} points."

def generate_retention_recommendations(
    top_risk_factors: List[Dict[str, Any]],
    employee_input: Dict[str, Any],
) -> List[Dict[str, str]]:
    """
    Synthesizes tailored, actionable, and ethical HR retention suggestions based on specific SHAP drivers.
    """
    recommendations = []
    seen_domains = set()

    for item in top_risk_factors:
        feat = item["feature"].lower()

        if "overtime" in feat and "workload" not in seen_domains:
            seen_domains.add("workload")
            recommendations.append({
                "category": "Workload & Well-being",
                "action": "Overtime & Workload Rebalancing",
                "detail": (
                    "Audit current project allocation and overtime hours. Consider workload redistribution, "
                    "hiring support, or offering compensatory time off to prevent chronic fatigue."
                ),
                "urgency": "High",
            })

        elif ("income" in feat or "rate" in feat or "stock" in feat) and "comp" not in seen_domains:
            seen_domains.add("comp")
            recommendations.append({
                "category": "Compensation & Benefits",
                "action": "Compensation & Equity Benchmark Review",
                "detail": (
                    "Perform an internal and external market compensation audit. Evaluate eligibility for merit increases, "
                    "performance bonuses, or equity/stock option grants during the next compensation cycle."
                ),
                "urgency": "Medium",
            })

        elif ("promotion" in feat or "role" in feat or "joblevel" in feat) and "career" not in seen_domains:
            seen_domains.add("career")
            recommendations.append({
                "category": "Career Growth",
                "action": "Career Progression & Mentorship Plan",
                "detail": (
                    "Schedule a formal career growth conversation. Map out explicit promotion milestones, "
                    "stretch assignments, leadership exposure, or sponsored skill development programs."
                ),
                "urgency": "High",
            })

        elif ("satisfaction" in feat or "involvement" in feat) and "engagement" not in seen_domains:
            seen_domains.add("engagement")
            recommendations.append({
                "category": "Employee Engagement",
                "action": "Manager 1-on-1 & Feedback Session",
                "detail": (
                    "Conduct an empathetic, confidential 1-on-1 check-in to uncover root causes of dissatisfaction. "
                    "Clarify team expectations, recognize contributions, and address friction points."
                ),
                "urgency": "High",
            })

        elif ("distance" in feat or "travel" in feat or "balance" in feat) and "flex" not in seen_domains:
            seen_domains.add("flex")
            recommendations.append({
                "category": "Workplace Flexibility",
                "action": "Hybrid / Flexible Schedule Accommodation",
                "detail": (
                    "Explore remote or hybrid work flexibility to ease daily commute pressure. Review business "
                    "travel requirements and substitute virtual meetings where practical."
                ),
                "urgency": "Medium",
            })

    # Default fallback recommendation if few specific factors triggered
    if len(recommendations) < 2:
        recommendations.append({
            "category": "General Retention",
            "action": "Periodic Pulse Check & Skill Alignment",
            "detail": (
                "Maintain open communication channels, review role alignment with employee passions, "
                "and ensure recognition of contributions during team reviews."
            ),
            "urgency": "Low",
        })

    return recommendations

def create_shap_waterfall_chart_json(
    base_value: float,
    final_output: float,
    top_factors: List[Dict[str, Any]],
) -> str:
    """
    Creates an interactive Plotly Waterfall Chart representing the SHAP attribution flow.
    Returns JSON string ready for Plotly.js rendering.
    """
    measures = ["absolute"]
    x_labels = ["Base Risk"]
    y_values = [round(base_value, 3)]
    text_values = [f"{base_value:+.2f}"]

    for factor in top_factors[:8]:
        measures.append("relative")
        # Shorten label for neat chart display
        label = factor["feature"]
        if len(label) > 22:
            label = label[:20] + ".."
        x_labels.append(label)
        val = round(factor["shap_value"], 3)
        y_values.append(val)
        text_values.append(f"{val:+.2f}")

    measures.append("total")
    x_labels.append("Model Score")
    y_values.append(round(final_output, 3))
    text_values.append(f"{final_output:+.2f}")

    fig = go.Figure(
        go.Waterfall(
            name="SHAP Flow",
            orientation="v",
            measure=measures,
            x=x_labels,
            textposition="outside",
            text=text_values,
            y=y_values,
            connector={"line": {"color": "rgb(63, 63, 63)", "width": 1.5}},
            decreasing={"marker": {"color": "#198754"}},  # Green for protective factors
            increasing={"marker": {"color": "#dc3545"}},  # Red for risk factors
            totals={"marker": {"color": "#0d6efd"}},      # Blue for totals
        )
    )

    fig.update_layout(
        title={
            "text": "SHAP Attribution Waterfall (Model Contribution Breakdown)",
            "y": 0.95,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
            "font": {"size": 14, "color": "#212529"}
        },
        showlegend=False,
        height=380,
        margin=dict(l=40, r=40, t=50, b=80),
        xaxis_tickangle=-30,
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font=dict(family="Inter, system-ui, sans-serif", size=11),
    )

    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

def create_shap_force_plot_json(
    risk_factors: List[Dict[str, Any]],
    protective_factors: List[Dict[str, Any]],
) -> str:
    """
    Creates an interactive horizontal SHAP Force / Tug-of-War plot (Idea 2).
    Shows opposing forces pushing toward departure (red) vs pulling toward retention (green).
    """
    fig = go.Figure()

    # Red bars: Positive SHAP forces pushing risk up
    for rf in risk_factors[:4]:
        val = round(rf["shap_value"], 3)
        fig.add_trace(go.Bar(
            name=rf["feature"],
            y=["Turnover Decision Balance"],
            x=[val],
            orientation="h",
            marker=dict(color="#dc3545"),
            text=[f"{rf['feature']}: +{val:.2f}"],
            textposition="auto",
            hoverinfo="text+name"
        ))

    # Green bars: Negative SHAP forces pulling risk down
    for pf in protective_factors[:4]:
        val = round(pf["shap_value"], 3)
        fig.add_trace(go.Bar(
            name=pf["feature"],
            y=["Turnover Decision Balance"],
            x=[val],
            orientation="h",
            marker=dict(color="#198754"),
            text=[f"{pf['feature']}: {val:.2f}"],
            textposition="auto",
            hoverinfo="text+name"
        ))

    fig.update_layout(
        barmode="relative",
        title=dict(
            text="SHAP Force Tug-of-War (Forces Pushing Toward Departure vs. Retention)",
            y=0.95,
            x=0.5,
            xanchor="center",
            yanchor="top",
            font=dict(size=13, color="#212529")
        ),
        xaxis=dict(
            title="← Pulling Toward Retention (Protective) | Pushing Toward Attrition (Risk) →",
            zeroline=True,
            zerolinewidth=2.5,
            zerolinecolor="#212529"
        ),
        height=220,
        margin=dict(l=20, r=20, t=45, b=40),
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        showlegend=False,
        font=dict(family="Inter, system-ui, sans-serif", size=11),
    )

    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

def generate_executive_summary(
    employee_input: Dict[str, Any],
    prob_percent: float,
    risk_level: str,
    risk_factors: List[Dict[str, Any]],
    protective_factors: List[Dict[str, Any]],
) -> str:
    """
    Generates a crisp, plain-English 2-sentence executive summary (Idea 5)
    explaining the primary drivers in human-consultant language.
    """
    name = str(employee_input.get("employee_name") or "The employee").strip()
    top_risk_str = ""
    top_prot_str = ""

    if risk_factors:
        r_feats = [rf["feature"].replace(":", "") for rf in risk_factors[:2]]
        top_risk_str = " and ".join(r_feats)

    if protective_factors:
        p_feats = [pf["feature"].replace(":", "") for pf in protective_factors[:2]]
        top_prot_str = " and ".join(p_feats)

    if prob_percent >= 50:
        summary = (
            f"AI Assessment: {name} is at {risk_level} ({prob_percent:.1f}%), primarily elevated by {top_risk_str or 'recent role friction'}. "
            f"However, key stabilizing factors such as {top_prot_str or 'current compensation stability'} continue to provide counterbalancing retention support."
        )
    elif prob_percent >= 25:
        summary = (
            f"AI Assessment: {name} exhibits a {risk_level} ({prob_percent:.1f}%). While {top_risk_str or 'work demands'} warrant proactive HR attention, "
            f"strong buffers including {top_prot_str or 'overall tenure and satisfaction'} currently reinforce organizational commitment."
        )
    else:
        summary = (
            f"AI Assessment: {name} is securely positioned in the {risk_level} ({prob_percent:.1f}%). "
            f"Robust retention drivers such as {top_prot_str or 'positive workplace factors'} strongly shield against voluntary turnover."
        )

    return summary

def compute_peer_benchmarks(employee_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes department-specific peer benchmarks (Idea 1) comparing this employee
    against retained employees in the same department.
    """
    from src.data_preprocessing import load_raw_dataset

    dept = str(employee_input.get("Department") or "Sales")
    emp_salary = float(employee_input.get("MonthlyIncome", 25000))
    emp_ot = str(employee_input.get("OverTime", "No"))
    emp_tenure = float(employee_input.get("YearsAtCompany", 2))

    df = load_raw_dataset()
    retained_dept = df[(df["Attrition"] == "No") & (df["Department"] == dept)]
    if retained_dept.empty:
        retained_dept = df[df["Attrition"] == "No"]

    avg_salary = round(float(retained_dept["MonthlyIncome"].mean()))
    ot_rate = round(float((retained_dept["OverTime"] == "Yes").mean() * 100), 1)
    avg_tenure = round(float(retained_dept["YearsAtCompany"].mean()), 1)

    salary_diff = round(emp_salary - avg_salary)
    salary_diff_pct = round((salary_diff / max(avg_salary, 1)) * 100, 1)

    return {
        "department": dept,
        "emp_salary": emp_salary,
        "avg_salary": avg_salary,
        "salary_diff": salary_diff,
        "salary_diff_pct": salary_diff_pct,
        "emp_ot": emp_ot,
        "dept_ot_rate": ot_rate,
        "emp_tenure": emp_tenure,
        "avg_tenure": avg_tenure,
    }

def explain_employee(
    model,
    preprocessor,
    employee_input: Dict[str, Any],
    feature_names: List[str],
) -> Dict[str, Any]:
    """
    Generates comprehensive SHAP explanation for an individual employee record.
    """
    from src.data_preprocessing import format_input_dataframe

    input_df = format_input_dataframe(employee_input)
    X_transformed = preprocessor.transform(input_df)

    shap_vals, base_val = get_model_shap_values(model, X_transformed)
    instance_shap = shap_vals[0]

    # Map SHAP values to feature details
    contributions = []
    for i, f_name in enumerate(feature_names):
        val = instance_shap[i]
        # Resolve human-readable raw value if available
        raw_val = None
        # Build a lowercase key → value map for exact matching
        input_lower = {k.lower(): v for k, v in employee_input.items()}
        # Try exact match first (feature name matches input key exactly, case-insensitive)
        if f_name.lower() in input_lower:
            raw_val = input_lower[f_name.lower()]
        else:
            # For one-hot encoded features like "Department: Sales", try base key
            base_key = f_name.split(":")[0].strip().lower()
            if base_key in input_lower:
                raw_val = input_lower[base_key]
        if raw_val is None:
            raw_val = "-"

        contributions.append({
            "feature": f_name,
            "raw_value": raw_val,
            "shap_value": float(val),
            "abs_shap": abs(float(val)),
            "direction": "Risk Driver (+)" if val > 0 else "Protective (-)",
        })

    # Filter out omitted background features (e.g. numeric "Education" rating 1-5 which is not on the user form)
    omitted_features = {"education", "distancetooffice", "distancetohome", "stockoptionlevel", "performancerating", "trainingtimeslastyear", "numcompaniesworked"}
    contributions = [c for c in contributions if c["feature"].lower() not in omitted_features]

    # Sort contributions by absolute magnitude
    contributions.sort(key=lambda x: x["abs_shap"], reverse=True)

    risk_factors = [c for c in contributions if c["shap_value"] > 0]
    protective_factors = [c for c in contributions if c["shap_value"] < 0]

    # Annotate top risk factors with readable explanations
    for rf in risk_factors[:5]:
        rf["explanation"] = generate_natural_language_explanation(
            rf["feature"], rf["raw_value"], rf["shap_value"], is_risk=True
        )

    # Annotate top protective factors
    for pf in protective_factors[:5]:
        pf["explanation"] = generate_natural_language_explanation(
            pf["feature"], pf["raw_value"], pf["shap_value"], is_risk=False
        )

    # Combine top 8 sorted for waterfall chart
    top_waterfall_factors = contributions[:8]

    # Total model margin/score
    final_output = base_val + float(np.sum(instance_shap))
    waterfall_chart_json = create_shap_waterfall_chart_json(
        base_val, final_output, top_waterfall_factors
    )

    # Idea 2: Interactive SHAP Force Tug-of-War Plot
    force_plot_json = create_shap_force_plot_json(risk_factors, protective_factors)

    # Estimated probability for summary
    raw_prob = float(1 / (1 + np.exp(-final_output))) if hasattr(model, "decision_function") else (
        float(model.predict_proba(X_transformed)[0, 1]) if hasattr(model, "predict_proba") else 0.5
    )
    prob_pct = round(raw_prob * 100, 1)
    risk_level_str = config.get_risk_category(raw_prob)["level"]

    # Idea 5: Plain-English Executive AI Summary
    executive_summary = generate_executive_summary(
        employee_input, prob_pct, risk_level_str, risk_factors, protective_factors
    )

    # Idea 1: Department Peer Benchmarks
    peer_benchmarks = compute_peer_benchmarks(employee_input)

    # Recommendations
    retention_recs = generate_retention_recommendations(risk_factors[:5], employee_input)

    return {
        "base_value": round(base_val, 4),
        "final_output": round(final_output, 4),
        "top_risk_factors": risk_factors[:5],
        "top_protective_factors": protective_factors[:5],
        "all_contributions": contributions[:15],
        "waterfall_chart_json": waterfall_chart_json,
        "force_plot_json": force_plot_json,
        "executive_summary": executive_summary,
        "peer_benchmarks": peer_benchmarks,
        "recommendations": retention_recs,
    }
