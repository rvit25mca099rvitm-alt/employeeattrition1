"""
Model training, evaluation, comparison, and persistence pipeline.
Trains Logistic Regression, Decision Tree, Random Forest, and XGBoost.
Selects the best model based on balanced metrics and saves all artifacts.
"""
import sys
import json
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier

# Check for XGBoost availability
try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

import config
from src.data_preprocessing import (
    load_raw_dataset,
    validate_dataset,
    clean_and_split_features_target,
    build_preprocessor,
    get_transformed_feature_names,
)
from src.evaluate_model import evaluate_classifier

def train_all_models():
    """
    Executes complete ML training and model comparison workflow.
    """
    print("=" * 70)
    print(" MCA MAJOR PROJECT: EMPLOYEE ATTRITION PREDICTION & XAI PIPELINE")
    print("=" * 70)

    # 1. Load Dataset
    print(f"\n[1/6] Loading dataset from: {config.DATASET_PATH}")
    df = load_raw_dataset()
    val_report = validate_dataset(df)
    if not val_report["valid"]:
        raise ValueError(f"Dataset validation failed: {val_report['issues']}")
    print(f"      Rows: {val_report['rows']}, Columns: {val_report['columns']}")
    print(f"      Target Distribution: {val_report['target_distribution']}")

    # 2. Preprocess & Train/Test Split
    print("\n[2/6] Splitting features and target (Stratified 80/20)...")
    X, y = clean_and_split_features_target(df)

    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        X,
        y,
        test_size=config.TEST_SIZE,
        stratify=y,
        random_state=config.RANDOM_STATE,
    )

    print(f"      Train samples: {len(X_train_raw)} (Attrition Yes: {y_train.sum()})")
    print(f"      Test samples:  {len(X_test_raw)} (Attrition Yes: {y_test.sum()})")

    # Fit ColumnTransformer on training data only
    preprocessor = build_preprocessor()
    X_train = preprocessor.fit_transform(X_train_raw)
    X_test = preprocessor.transform(X_test_raw)

    feature_names = get_transformed_feature_names(preprocessor)
    print(f"      Engineered Features count: {len(feature_names)}")

    # Class imbalance weight calculation
    neg_count = int((y_train == 0).sum())
    pos_count = int((y_train == 1).sum())
    scale_pos_weight = float(neg_count / max(1, pos_count))

    # 3. Model Definitions
    print("\n[3/6] Configuring Machine Learning Classifiers...")
    candidate_models = {
        "Logistic Regression": LogisticRegression(
            class_weight="balanced",
            max_iter=1000,
            C=0.5,
            random_state=config.RANDOM_STATE,
        ),
        "Decision Tree": DecisionTreeClassifier(
            class_weight="balanced",
            max_depth=5,
            min_samples_split=10,
            min_samples_leaf=10,
            random_state=config.RANDOM_STATE,
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=150,
            max_depth=8,
            min_samples_leaf=4,
            class_weight="balanced",
            random_state=config.RANDOM_STATE,
            n_jobs=-1,
        ),
    }

    if XGBOOST_AVAILABLE:
        candidate_models["XGBoost"] = XGBClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.08,
            scale_pos_weight=scale_pos_weight,
            eval_metric="logloss",
            random_state=config.RANDOM_STATE,
            n_jobs=-1,
        )
    else:
        print("      [Warning] XGBoost not installed. Continuing with remaining classifiers.")

    # 4. Train & Evaluate Models
    print("\n[4/6] Training & Evaluating Classifiers...")
    trained_models = {}
    evaluation_results = {}

    for name, model in candidate_models.items():
        print(f"      Training {name}...")
        model.fit(X_train, y_train)
        metrics = evaluate_classifier(model, X_test, y_test, model_name=name)
        evaluation_results[name] = metrics
        trained_models[name] = model

        print(
            f"        -> Accuracy: {metrics['accuracy']:.4f} | "
            f"Precision: {metrics['precision']:.4f} | "
            f"Recall: {metrics['recall']:.4f} | "
            f"F1: {metrics['f1_score']:.4f} | "
            f"ROC-AUC: {metrics['roc_auc']:.4f}"
        )

    # 5. Model Comparison & Selection
    print("\n[5/6] Model Comparison & Selection...")
    # In attrition prediction, false negatives (missing an employee who leaves) are costly.
    # We select the model that maximizes a balanced combination: 0.40 * ROC-AUC + 0.35 * F1 + 0.25 * Recall
    selection_scores = {}
    for name, m in evaluation_results.items():
        score = (
            0.40 * m["roc_auc"]
            + 0.35 * m["f1_score"]
            + 0.25 * m["recall"]
        )
        selection_scores[name] = round(score, 4)
        print(f"      {name}: Composite Selection Score = {score:.4f}")

    best_model_name = max(selection_scores, key=selection_scores.get)
    best_model = trained_models[best_model_name]
    best_metrics = evaluation_results[best_model_name]

    print(f"\n      >>> SELECTED BEST MODEL: {best_model_name} <<<")
    print(f"      Selection rationale: Highest composite balance of ROC-AUC ({best_metrics['roc_auc']}), "
          f"F1-Score ({best_metrics['f1_score']}), and Recall ({best_metrics['recall']}).")

    # 6. Precompute Global SHAP Values for fast interpretability
    print("\n[6/6] Computing SHAP values and saving artifacts...")
    shap_summary_data = compute_and_bundle_shap_summary(
        best_model,
        best_model_name,
        X_test,
        feature_names,
    )

    # Save artifacts
    joblib.dump(best_model, config.MODEL_PATH)
    joblib.dump(preprocessor, config.PREPROCESSOR_PATH)
    joblib.dump(shap_summary_data, config.SHAP_SUMMARY_PATH)

    metadata = {
        "best_model_name": best_model_name,
        "selection_rationale": (
            f"Selected {best_model_name} based on comprehensive evaluation maximizing ROC-AUC "
            f"({best_metrics['roc_auc']}) and minority class Recall ({best_metrics['recall']}) "
            f"to reliably detect retention risks while maintaining high precision."
        ),
        "trained_at": datetime.now().isoformat(),
        "total_samples": len(df),
        "train_samples": len(X_train_raw),
        "test_samples": len(X_test_raw),
        "target_distribution": val_report["target_distribution"],
        "feature_names": feature_names,
        "raw_numerical_features": config.NUMERICAL_FEATURES,
        "raw_categorical_features": config.CATEGORICAL_FEATURES,
        "thresholds": {
            "low_risk": config.LOW_RISK_THRESHOLD,
            "high_risk": config.HIGH_RISK_THRESHOLD,
        },
        "evaluation_results": evaluation_results,
        "selection_scores": selection_scores,
    }

    with open(config.METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    # Save diagnostic curves for frontend
    evaluation_plots = {
        name: {
            "roc_curve": metrics["roc_curve"],
            "confusion_matrix": metrics["confusion_matrix"],
            "accuracy": metrics["accuracy"],
            "precision": metrics["precision"],
            "recall": metrics["recall"],
            "f1_score": metrics["f1_score"],
            "roc_auc": metrics["roc_auc"],
        }
        for name, metrics in evaluation_results.items()
    }
    with open(config.EVALUATION_PLOTS_PATH, "w", encoding="utf-8") as f:
        json.dump(evaluation_plots, f, indent=2)

    print(f"\n[OK] Pipeline artifacts saved successfully:")
    print(f"     - Model:        {config.MODEL_PATH}")
    print(f"     - Preprocessor: {config.PREPROCESSOR_PATH}")
    print(f"     - Metadata:     {config.METADATA_PATH}")
    print(f"     - SHAP Summary: {config.SHAP_SUMMARY_PATH}")
    print("=" * 70)
    return metadata

def compute_and_bundle_shap_summary(model, model_name: str, X_test: np.ndarray, feature_names: list) -> dict:
    """
    Computes real SHAP values on the test set for global feature importance and summary plots.
    """
    import shap
    print(f"      Calculating global SHAP values using {model_name}...")

    if model_name == "XGBoost":
        dmat = XGBClassifier.DMatrix if hasattr(XGBClassifier, "DMatrix") else None
        import xgboost as xgb
        booster = model.get_booster()
        dmat = xgb.DMatrix(X_test)
        contribs = booster.predict(dmat, pred_contribs=True)
        shap_values = contribs[:, :-1]
        base_value = float(contribs[0, -1])
    elif model_name in ["Random Forest", "Decision Tree"]:
        explainer = shap.TreeExplainer(model)
        sv = explainer(X_test)
        # Handle 3D array (samples, features, classes)
        if len(sv.values.shape) == 3:
            shap_values = sv.values[:, :, 1]
            base_val = sv.base_values[:, 1] if sv.base_values.ndim > 1 else sv.base_values
            base_value = float(np.mean(base_val))
        else:
            shap_values = sv.values
            base_value = float(np.mean(sv.base_values))
    else:
        # Linear / Fallback explainer
        explainer = shap.Explainer(model, X_test[:50])
        sv = explainer(X_test)
        shap_values = sv.values if sv.values.ndim == 2 else sv.values[:, :, 1]
        base_value = float(np.mean(sv.base_values))

    # Calculate mean absolute SHAP for each feature
    mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
    top_indices = np.argsort(mean_abs_shap)[::-1]

    top_features = []
    for idx in top_indices:
        top_features.append({
            "feature": feature_names[idx],
            "importance": round(float(mean_abs_shap[idx]), 4),
        })

    return {
        "model_name": model_name,
        "feature_names": feature_names,
        "base_value": base_value,
        "global_importance": top_features,
        "shap_values_sample": shap_values[:100].tolist(),
        "X_test_sample": X_test[:100].tolist(),
    }

if __name__ == "__main__":
    train_all_models()
