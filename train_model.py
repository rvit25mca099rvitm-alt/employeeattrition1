"""
Machine Learning Training Pipeline for Employee Attrition Prediction.
Trains Logistic Regression and Random Forest models with stratified splitting,
balanced class weights, full metric comparisons, and SHAP explainability.
"""
import json
import logging
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
import shap

import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def load_and_clean_data(dataset_path: Path = config.DATASET_PATH) -> pd.DataFrame:
    """Loads CSV and removes uninformative/constant columns."""
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found at {dataset_path}. Please place the IBM HR dataset there.")

    df = pd.read_csv(dataset_path)
    logger.info(f"Loaded raw dataset with shape: {df.shape}")

    # Drop non-predictive / constant columns
    drop_cols = [c for c in config.UNNECESSARY_COLUMNS if c in df.columns]
    if drop_cols:
        df = df.drop(columns=drop_cols)
        logger.info(f"Dropped columns: {drop_cols}")

    return df

def build_preprocessing_pipeline() -> ColumnTransformer:
    """Builds scikit-learn ColumnTransformer for numerical scaling and categorical one-hot encoding."""
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), config.NUMERICAL_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), config.CATEGORICAL_FEATURES),
        ],
        remainder="drop"
    )
    return preprocessor

def get_feature_names(preprocessor: ColumnTransformer) -> list:
    """Extracts human-readable transformed feature names from the fitted preprocessor."""
    feature_names = []
    # Numerical names
    feature_names.extend(config.NUMERICAL_FEATURES)
    # One-hot categorical names
    cat_encoder = preprocessor.named_transformers_["cat"]
    if hasattr(cat_encoder, "get_feature_names_out"):
        cat_names = list(cat_encoder.get_feature_names_out(config.CATEGORICAL_FEATURES))
    else:
        cat_names = [f"cat_{i}" for i in range(cat_encoder.transform([[c[0] for c in config.CATEGORICAL_CHOICES.values()]]).shape[1])]

    # Clean names like "Department_Sales" -> "Department: Sales"
    cleaned_cat = []
    for name in cat_names:
        if "_" in name:
            parts = name.split("_", 1)
            cleaned_cat.append(f"{parts[0]}: {parts[1]}")
        else:
            cleaned_cat.append(name)
    feature_names.extend(cleaned_cat)
    return feature_names

def evaluate_model(name: str, model, X_test, y_test) -> dict:
    """Calculates accuracy, precision, recall, f1, roc-auc, and confusion matrix."""
    y_pred = model.predict(X_test)
    if hasattr(model, "predict_proba"):
        y_prob = model.predict_proba(X_test)[:, 1]
    else:
        y_prob = y_pred

    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()

    metrics = {
        "algorithm": name,
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
        "f1_score": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, y_prob)), 4),
        "confusion_matrix": {
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp),
        },
        "selection_score": round(float(0.4 * recall_score(y_test, y_pred, zero_division=0) +
                                       0.3 * f1_score(y_test, y_pred, zero_division=0) +
                                       0.3 * roc_auc_score(y_test, y_prob)), 4)
    }
    logger.info(f"{name} Evaluation: Accuracy={metrics['accuracy']}, Recall={metrics['recall']}, F1={metrics['f1_score']}, ROC-AUC={metrics['roc_auc']}")
    return metrics

def train_and_evaluate_all():
    """Executes full training pipeline, model selection, SHAP computation, and serialization."""
    df = load_and_clean_data()

    # Encode Target
    if df[config.TARGET_COLUMN].dtype == object:
        df[config.TARGET_COLUMN] = df[config.TARGET_COLUMN].map({"Yes": 1, "No": 0})

    X = df.drop(columns=[config.TARGET_COLUMN])
    y = df[config.TARGET_COLUMN].values

    # Stratified Train-Test Split (80% train, 20% test)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    logger.info(f"Split completed. Training set: {X_train.shape[0]} samples, Test set: {X_test.shape[0]} samples.")

    # Fit Preprocessing Pipeline ONLY on training data (prevents data leakage)
    preprocessor = build_preprocessing_pipeline()
    X_train_trans = preprocessor.fit_transform(X_train)
    X_test_trans = preprocessor.transform(X_test)
    feature_names = get_feature_names(preprocessor)

    # Candidate Algorithms
    models = {
        "Logistic Regression": LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            random_state=42,
            solver="liblinear"
        ),
        "Random Forest Classifier": RandomForestClassifier(
            n_estimators=150,
            max_depth=10,
            min_samples_split=5,
            class_weight="balanced",
            random_state=42
        ),
    }

    results = {}
    fitted_models = {}

    for name, model in models.items():
        logger.info(f"Training {name}...")
        model.fit(X_train_trans, y_train)
        fitted_models[name] = model
        results[name] = evaluate_model(name, model, X_test_trans, y_test)

    # Select champion model based on composite selection score (recall, f1, roc-auc)
    best_name = max(results.keys(), key=lambda k: results[k]["selection_score"])
    best_model = fitted_models[best_name]
    logger.info(f"Champion Model selected: '{best_name}' (Selection Score: {results[best_name]['selection_score']})")

    # Compute Global SHAP feature importances using TreeExplainer (RF) or LinearExplainer
    rf_model = fitted_models["Random Forest Classifier"]
    explainer = shap.TreeExplainer(rf_model)
    shap_values = explainer.shap_values(X_test_trans)

    # In binary classification, take SHAP values for positive class (Attrition = 1)
    if isinstance(shap_values, list) and len(shap_values) == 2:
        class1_shap = shap_values[1]
    elif isinstance(shap_values, np.ndarray) and len(shap_values.shape) == 3:
        class1_shap = shap_values[:, :, 1]
    else:
        class1_shap = shap_values

    mean_abs_shap = np.mean(np.abs(class1_shap), axis=0)
    top_indices = np.argsort(mean_abs_shap)[::-1]

    global_importance = []
    for idx in top_indices:
        global_importance.append({
            "feature": feature_names[idx],
            "importance": round(float(mean_abs_shap[idx]), 4)
        })

    # Save artifacts
    config.MODELS_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(best_model, config.MODEL_PATH)
    joblib.dump(preprocessor, config.PIPELINE_PATH)

    metrics_payload = {
        "best_model_name": best_name,
        "results": results,
        "feature_names": feature_names,
        "test_size": len(y_test),
        "train_size": len(y_train),
        "attrition_rate_train": round(float(np.mean(y_train) * 100), 2),
        "attrition_rate_test": round(float(np.mean(y_test) * 100), 2),
    }

    with open(config.METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics_payload, f, indent=2)

    with open(config.GLOBAL_SHAP_PATH, "w", encoding="utf-8") as f:
        json.dump(global_importance, f, indent=2)

    logger.info(f"Model saved to: {config.MODEL_PATH}")
    logger.info(f"Pipeline saved to: {config.PIPELINE_PATH}")
    logger.info(f"Metrics saved to: {config.METRICS_PATH}")
    logger.info(f"Global SHAP saved to: {config.GLOBAL_SHAP_PATH}")
    logger.info("Training and evaluation completed successfully!")
    return metrics_payload

if __name__ == "__main__":
    train_and_evaluate_all()
