"""
Prediction engine for individual employee evaluations and bulk CSV processing.
"""
from typing import Dict, Any, Tuple, Optional
import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
import io

import config
from src.data_preprocessing import (
    validate_input_dict,
    format_input_dataframe,
    get_transformed_feature_names,
)
from src.explainability import explain_employee
from src.db import log_prediction

# Module-level cache for model artifacts
_MODEL_CACHE = {
    "model": None,
    "preprocessor": None,
    "metadata": None,
    "feature_names": None,
}

def load_model_artifacts():
    """
    Loads saved model, preprocessor, and metadata from disk into memory.
    Raises FileNotFoundError with friendly message if models have not been trained yet.
    """
    if _MODEL_CACHE["model"] is not None:
        return (
            _MODEL_CACHE["model"],
            _MODEL_CACHE["preprocessor"],
            _MODEL_CACHE["metadata"],
            _MODEL_CACHE["feature_names"],
        )

    if not config.MODEL_PATH.exists() or not config.PREPROCESSOR_PATH.exists():
        raise FileNotFoundError(
            "Trained model artifacts not found. Please run 'python -m src.train_model' first "
            "to train the classifiers and save the pipeline."
        )

    model = joblib.load(config.MODEL_PATH)
    preprocessor = joblib.load(config.PREPROCESSOR_PATH)

    metadata = {}
    if config.METADATA_PATH.exists():
        with open(config.METADATA_PATH, "r", encoding="utf-8") as f:
            metadata = json.load(f)

    feature_names = metadata.get("feature_names") or get_transformed_feature_names(preprocessor)

    _MODEL_CACHE["model"] = model
    _MODEL_CACHE["preprocessor"] = preprocessor
    _MODEL_CACHE["metadata"] = metadata
    _MODEL_CACHE["feature_names"] = feature_names

    return model, preprocessor, metadata, feature_names

def predict_single_employee(
    employee_data: Dict[str, Any],
    user_id: Optional[int] = None,
    username: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Validates user input, executes ML pipeline, computes probability, risk level,
    and returns full SHAP explainability package, storing the analysed record in database.
    """
    # 1. Validate Input
    is_valid, errors = validate_input_dict(employee_data)
    if not is_valid:
        raise ValueError("; ".join(errors))

    # 2. Load Pipeline
    model, preprocessor, metadata, feature_names = load_model_artifacts()

    # 3. Format DataFrame and Transform
    input_df = format_input_dataframe(employee_data)
    X_transformed = preprocessor.transform(input_df)

    # 4. Predict Probability (Ensuring positive class '1' index)
    if hasattr(model, "predict_proba"):
        classes = list(model.classes_)
        pos_idx = classes.index(1) if 1 in classes else 1
        prob = float(model.predict_proba(X_transformed)[0, pos_idx])
    elif hasattr(model, "decision_function"):
        raw_margin = float(model.decision_function(X_transformed)[0])
        prob = float(1 / (1 + np.exp(-raw_margin)))
    else:
        prob = float(model.predict(X_transformed)[0])

    # 5. Risk Categorization
    risk_info = config.get_risk_category(prob)
    prediction_label = "Likely to Leave" if prob >= config.LOW_RISK_THRESHOLD else "Likely to Stay"

    # 6. SHAP Explanations
    explanation = explain_employee(model, preprocessor, employee_data, feature_names)

    # 7. Persist to SQLite History (Storing Analysed Data)
    emp_name = str(employee_data.get("employee_name") or "Employee").strip()
    emp_id = str(employee_data.get("employee_id") or "-").strip()

    record_id = log_prediction(
        input_data=employee_data,
        prob=prob,
        risk_level=risk_info["level"],
        prediction_label=prediction_label,
        top_risk_factors=explanation["top_risk_factors"],
        top_protective_factors=explanation["top_protective_factors"],
        user_id=user_id,
        username=username,
        employee_name=emp_name,
        employee_id=emp_id,
    )

    return {
        "prediction_id": record_id,
        "employee_name": emp_name,
        "employee_id": emp_id,
        "probability": round(prob, 4),
        "probability_percent": round(prob * 100, 1),
        "prediction_label": prediction_label,
        "risk_category": risk_info["level"],
        "badge_class": risk_info["badge_class"],
        "risk_color": risk_info["color"],
        "risk_description": risk_info["description"],
        "explanation": explanation,
        "model_name": metadata.get("best_model_name", type(model).__name__),
        "input_summary": employee_data,
    }

def process_bulk_predictions(csv_file_or_content) -> Tuple[Dict[str, Any], pd.DataFrame]:
    """
    Parses an uploaded CSV file, validates columns, runs batch predictions,
    and returns aggregate analytics and output DataFrame.
    """
    model, preprocessor, metadata, _ = load_model_artifacts()

    # Read CSV
    if isinstance(csv_file_or_content, (str, Path)):
        df = pd.read_csv(csv_file_or_content)
    elif hasattr(csv_file_or_content, "read"):
        df = pd.read_csv(csv_file_or_content)
    else:
        raise ValueError("Invalid file object provided for bulk prediction.")

    if df.empty:
        raise ValueError("Uploaded CSV file contains no data.")

    # Drop target column if user mistakenly included it
    if config.TARGET_COLUMN in df.columns:
        df = df.drop(columns=[config.TARGET_COLUMN])

    # Check for required columns
    required_cols = config.NUMERICAL_FEATURES + config.CATEGORICAL_FEATURES
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(
            f"The uploaded file is missing {len(missing_cols)} required column(s): {', '.join(missing_cols[:5])}..."
        )

    # Clean and fill any accidental blank numericals with defaults
    df_clean = df[required_cols].copy()
    for col in config.NUMERICAL_FEATURES:
        df_clean[col] = pd.to_numeric(df_clean[col], errors="coerce").fillna(config.NUMERICAL_SPECS[col]["default"])

    for col in config.CATEGORICAL_FEATURES:
        valid_choices = config.CATEGORICAL_CHOICES[col]
        df_clean[col] = df_clean[col].astype(str)
        # Fallback to first valid choice if invalid
        df_clean[col] = df_clean[col].apply(lambda x: x if x in valid_choices else valid_choices[0])

    # Transform and Predict
    X_transformed = preprocessor.transform(df_clean)

    if hasattr(model, "predict_proba"):
        classes = list(model.classes_)
        pos_idx = classes.index(1) if 1 in classes else 1
        probs = model.predict_proba(X_transformed)[:, pos_idx]
    else:
        probs = model.predict(X_transformed).astype(float)

    # Compile result columns
    results_df = df.copy()
    results_df["Attrition_Probability"] = [round(float(p), 4) for p in probs]
    results_df["Attrition_Probability_%"] = [round(float(p) * 100, 1) for p in probs]

    risk_levels = []
    pred_labels = []
    for p in probs:
        cat = config.get_risk_category(p)
        risk_levels.append(cat["level"])
        pred_labels.append("Likely to Leave" if p >= config.LOW_RISK_THRESHOLD else "Likely to Stay")

    results_df["Risk_Category"] = risk_levels
    results_df["Predicted_Attrition"] = pred_labels

    # Aggregates
    total_records = len(results_df)
    high_risk_count = int(sum(results_df["Risk_Category"] == "High Risk"))
    medium_risk_count = int(sum(results_df["Risk_Category"] == "Medium Risk"))
    low_risk_count = int(sum(results_df["Risk_Category"] == "Low Risk"))
    predicted_leave_count = int(sum(results_df["Predicted_Attrition"] == "Likely to Leave"))

    summary = {
        "total_records": total_records,
        "predicted_leave_count": predicted_leave_count,
        "predicted_stay_count": total_records - predicted_leave_count,
        "predicted_leave_rate": round((predicted_leave_count / max(1, total_records)) * 100, 1),
        "high_risk_count": high_risk_count,
        "medium_risk_count": medium_risk_count,
        "low_risk_count": low_risk_count,
        "model_name": metadata.get("best_model_name", type(model).__name__),
    }

    return summary, results_df
