"""
Model evaluation utilities for classification performance and diagnostic curves.
"""
from typing import Dict, Any
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
    roc_curve,
)

def evaluate_classifier(model, X_test, y_test, model_name: str = "Classifier") -> Dict[str, Any]:
    """
    Evaluates a trained classifier on test data, computing comprehensive metrics.
    """
    y_pred = model.predict(X_test)

    # Determine probability for positive class (1)
    if hasattr(model, "predict_proba"):
        classes = list(model.classes_)
        pos_idx = classes.index(1) if 1 in classes else 1
        y_prob = model.predict_proba(X_test)[:, pos_idx]
    elif hasattr(model, "decision_function"):
        raw_scores = model.decision_function(X_test)
        # Sigmoid transform
        y_prob = 1 / (1 + np.exp(-raw_scores))
    else:
        y_prob = y_pred.astype(float)

    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred, zero_division=0))
    rec = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))

    try:
        auc = float(roc_auc_score(y_test, y_prob))
    except Exception:
        auc = 0.5

    cm = confusion_matrix(y_test, y_pred).tolist()
    # cm format: [[TN, FP], [FN, TP]]

    report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

    # ROC curve points (subsample for compact storage if large)
    fpr, tpr, thresholds = roc_curve(y_test, y_prob)
    subsample_step = max(1, len(fpr) // 50)
    roc_points = {
        "fpr": [round(float(x), 4) for x in fpr[::subsample_step]],
        "tpr": [round(float(x), 4) for x in tpr[::subsample_step]],
    }
    # Ensure (1.0, 1.0) is present
    if roc_points["fpr"][-1] != 1.0:
        roc_points["fpr"].append(1.0)
        roc_points["tpr"].append(1.0)

    return {
        "model_name": model_name,
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "roc_auc": round(auc, 4),
        "confusion_matrix": cm,
        "classification_report": report,
        "roc_curve": roc_points,
    }
