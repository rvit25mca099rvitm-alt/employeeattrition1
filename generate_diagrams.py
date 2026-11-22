"""
Generates academic diagram images for the MCA Major Project Report.
Outputs PNG diagrams to report_assets/
"""
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import json
from pathlib import Path

out_dir = Path("report_assets")
out_dir.mkdir(exist_ok=True)

plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]

# -------------------------------------------------------------
# 1. System Architecture Diagram
# -------------------------------------------------------------
def make_architecture_diagram():
    fig, ax = plt.subplots(figsize=(10, 7), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Title
    ax.text(50, 96, "Figure 4.1: Three-Tier System Architecture", ha='center', va='center', fontsize=14, fontweight='bold', color='#0f172a')

    # Tier 1: Presentation Layer
    p1 = patches.FancyBboxPatch((5, 70), 90, 20, boxstyle="round,pad=1,rounding_size=2", ec="#2563eb", fc="#eff6ff", lw=2)
    ax.add_patch(p1)
    ax.text(50, 85, "1. Presentation Layer (User Interface Tier)", ha='center', va='center', fontsize=12, fontweight='bold', color='#1e3a8a')
    ax.text(50, 77, "Bootstrap 5 Responsive UI  |  Chart.js Visualizations  |  Jinja2 Templates  |  Custom Corporate Styling", ha='center', va='center', fontsize=10, color='#334155')

    # Arrow 1 <-> 2
    ax.annotate('', xy=(50, 64), xytext=(50, 70), arrowprops=dict(arrowstyle="<->", color="#2563eb", lw=2))
    ax.text(52, 67, "HTTP / JSON REST Requests", fontsize=9, color="#64748b")

    # Tier 2: Application / Business Logic Layer
    p2 = patches.FancyBboxPatch((5, 38), 90, 26, boxstyle="round,pad=1,rounding_size=2", ec="#0d9488", fc="#f0fdfa", lw=2)
    ax.add_patch(p2)
    ax.text(50, 59, "2. Application & Intelligence Layer (Python Flask Tier)", ha='center', va='center', fontsize=12, fontweight='bold', color='#115e59')
    
    # Submodules
    sub_modules = [
        ("Authentication\n(PBKDF2 Hashing)", (12, 42), 22, 12),
        ("Pre-processing Pipeline\n(StandardScaler + OHE)", (39, 42), 24, 12),
        ("Predictive Engine\n(Logistic Regression)", (68, 42), 23, 12),
        ("Explainable AI (SHAP)\n& Rule-Based Guidance", (39, 26), 24, 9)
    ]
    for title, pos, w, h in sub_modules:
        sp = patches.FancyBboxPatch(pos, w, h, boxstyle="round,pad=0.5", ec="#0f766e", fc="#ffffff", lw=1.2)
        ax.add_patch(sp)
        ax.text(pos[0]+w/2, pos[1]+h/2, title, ha='center', va='center', fontsize=8.5, fontweight='bold', color='#0f172a')

    # Arrow 2 <-> 3
    ax.annotate('', xy=(50, 21), xytext=(50, 26), arrowprops=dict(arrowstyle="<->", color="#0d9488", lw=2))
    ax.text(52, 23, "SQL Queries & Artifact Loading", fontsize=9, color="#64748b")

    # Tier 3: Persistence Layer
    p3 = patches.FancyBboxPatch((5, 3), 90, 17, boxstyle="round,pad=1,rounding_size=2", ec="#7c3aed", fc="#f5f3ff", lw=2)
    ax.add_patch(p3)
    ax.text(50, 15, "3. Data & Storage Layer (Persistence Tier)", ha='center', va='center', fontsize=12, fontweight='bold', color='#5b21b6')
    ax.text(50, 8, "SQLite Database (database/attrition.db)  |  Serialized Model Artifacts (Joblib .pkl)  |  IBM HR CSV Dataset", ha='center', va='center', fontsize=9.5, color='#334155')

    plt.tight_layout()
    plt.savefig(out_dir / "architecture_diagram.png", bbox_inches='tight')
    plt.close()
    print("Architecture diagram generated.")

# -------------------------------------------------------------
# 2. Activity Diagram
# -------------------------------------------------------------
def make_activity_diagram():
    fig, ax = plt.subplots(figsize=(8, 10), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    ax.text(50, 97, "Figure 5.1: System Activity Diagram", ha='center', va='center', fontsize=13, fontweight='bold', color='#0f172a')

    nodes = [
        ("Start", (50, 92), "circle", "#22c55e"),
        ("Admin Login & Verification", (50, 82), "box", "#3b82f6"),
        ("Access Dashboard / Workforce Analytics", (50, 71), "box", "#3b82f6"),
        ("Enter Employee Assessment Form (18 Features)", (50, 60), "box", "#3b82f6"),
        ("Preprocess Inputs via ColumnTransformer", (50, 49), "box", "#0d9488"),
        ("Compute Turnover Probability & Risk Category", (50, 38), "box", "#0d9488"),
        ("Calculate Local SHAP Values (Positive & Negative)", (50, 27), "box", "#8b5cf6"),
        ("Generate Rule-Based Retention Advice & Audit Record", (50, 16), "box", "#8b5cf6"),
        ("End / Decision Handed to HR", (50, 5), "circle", "#ef4444"),
    ]

    for title, pos, shape, col in nodes:
        if shape == "circle":
            c = plt.Circle(pos, 3, color=col, ec='#0f172a', lw=1.5, zorder=3)
            ax.add_patch(c)
            ax.text(pos[0], pos[1]-4.5, title, ha='center', va='center', fontsize=9, fontweight='bold', color='#0f172a')
        else:
            w, h = 60, 6.5
            box = patches.FancyBboxPatch((pos[0]-w/2, pos[1]-h/2), w, h, boxstyle="round,pad=0.5", ec='#0f172a', fc='#f8fafc', lw=1.5, zorder=3)
            ax.add_patch(box)
            ax.text(pos[0], pos[1], title, ha='center', va='center', fontsize=9, fontweight='semibold', color='#0f172a')

    # Draw Arrows between steps
    y_starts = [89, 78.5, 67.5, 56.5, 45.5, 34.5, 23.5, 12.5]
    y_ends = [85.5, 74.5, 63.5, 52.5, 41.5, 30.5, 19.5, 8.5]
    for ys, ye in zip(y_starts, y_ends):
        ax.annotate('', xy=(50, ye), xytext=(50, ys), arrowprops=dict(arrowstyle="->", color="#0f172a", lw=1.8))

    plt.tight_layout()
    plt.savefig(out_dir / "activity_diagram.png", bbox_inches='tight')
    plt.close()
    print("Activity diagram generated.")

# -------------------------------------------------------------
# 3. Use Case Diagram
# -------------------------------------------------------------
def make_usecase_diagram():
    fig, ax = plt.subplots(figsize=(10, 8), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    ax.text(50, 96, "Figure 5.2: Use Case Diagram", ha='center', va='center', fontsize=13, fontweight='bold', color='#0f172a')

    # System boundary box
    sys_box = patches.Rectangle((30, 8), 65, 83, fill=True, fc='#f8fafc', ec='#0f172a', lw=2, linestyle='--')
    ax.add_patch(sys_box)
    ax.text(62.5, 88, "Employee Attrition Analysis & Explainable AI System", ha='center', va='center', fontsize=11, fontweight='bold', color='#1e3a8a')

    # Actor (Stick Figure on Left)
    # Head
    head = plt.Circle((15, 55), 3, color='#0f172a', fill=False, lw=2)
    ax.add_patch(head)
    # Body
    ax.plot([15, 15], [52, 40], color='#0f172a', lw=2)
    # Arms
    ax.plot([8, 22], [47, 47], color='#0f172a', lw=2)
    # Legs
    ax.plot([15, 10], [40, 28], color='#0f172a', lw=2)
    ax.plot([15, 20], [40, 28], color='#0f172a', lw=2)
    ax.text(15, 24, "HR Manager /\nAdministrator", ha='center', va='center', fontsize=10, fontweight='bold', color='#0f172a')

    use_cases = [
        "1. Authenticate / Login to System",
        "2. View HR Workforce Dashboard",
        "3. Explore Department & Demographic Analytics",
        "4. Input Employee Parameters for Assessment",
        "5. Receive Turnover Probability & Risk Category",
        "6. Examine Individual Explainable AI (SHAP) Insights",
        "7. Review Tailored Retention Recommendations",
        "8. Search & Filter Prediction Audit History",
        "9. Review Model Performance & Metrics"
    ]

    y_pos = np.linspace(80, 15, len(use_cases))
    for i, (uc, y) in enumerate(zip(use_cases, y_pos)):
        # Draw ellipse for use case
        ellipse = patches.Ellipse((62.5, y), 50, 6, fill=True, fc='#eff6ff', ec='#2563eb', lw=1.5)
        ax.add_patch(ellipse)
        ax.text(62.5, y, uc, ha='center', va='center', fontsize=8.5, fontweight='semibold', color='#0f172a')
        # Connector line from actor to use case
        ax.plot([22, 37.5], [47, y], color='#64748b', lw=1.2, linestyle=':')

    plt.tight_layout()
    plt.savefig(out_dir / "usecase_diagram.png", bbox_inches='tight')
    plt.close()
    print("Use Case diagram generated.")

# -------------------------------------------------------------
# 4. Class Diagram
# -------------------------------------------------------------
def make_class_diagram():
    fig, ax = plt.subplots(figsize=(10, 7.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    ax.text(50, 97, "Figure 5.3: System Class Diagram", ha='center', va='center', fontsize=13, fontweight='bold', color='#0f172a')

    def draw_class(x, y, w, h, title, attrs, methods):
        # Outer box
        rect = patches.Rectangle((x, y), w, h, fc='#ffffff', ec='#0f172a', lw=1.5)
        ax.add_patch(rect)
        # Title bar
        t_h = 4
        title_box = patches.Rectangle((x, y+h-t_h), w, t_h, fc='#2563eb', ec='#0f172a', lw=1.5)
        ax.add_patch(title_box)
        ax.text(x+w/2, y+h-t_h/2, title, ha='center', va='center', fontsize=9.5, fontweight='bold', color='#ffffff')
        # Attributes
        attr_y = y + h - t_h - 2
        for att in attrs:
            ax.text(x+1, attr_y, att, fontsize=7.5, color='#334155')
            attr_y -= 2.2
        # Divider line
        div_y = y + len(methods)*2.3 + 2.5
        ax.plot([x, x+w], [div_y, div_y], color='#0f172a', lw=1)
        # Methods
        meth_y = div_y - 2.2
        for m in methods:
            ax.text(x+1, meth_y, m, fontsize=7.5, color='#0f766e', fontweight='semibold')
            meth_y -= 2.2

    # Class 1: User
    draw_class(4, 60, 28, 30, "User", 
               ["- id: Integer", "- username: String", "- password_hash: String", "- email: String", "- created_at: Timestamp"],
               ["+ verify_password()", "+ register_user()"])

    # Class 2: ModelService
    draw_class(36, 50, 32, 42, "ModelService",
               ["- model: LogisticRegression", "- pipeline: ColumnTransformer", "- feature_names: List[str]", "- explainer: LinearExplainer", "- dataset_df: DataFrame"],
               ["+ load_artifacts()", "+ predict_employee()", "+ compute_shap()", "+ get_suggestions()", "+ get_dashboard_summary()"])

    # Class 3: PredictionRecord
    draw_class(72, 55, 25, 35, "PredictionRecord",
               ["- id: Integer", "- employee_ref: String", "- department: String", "- probability: Float", "- risk_category: String", "- top_factors: String"],
               ["+ save_prediction()", "+ get_history()"])

    # Class 4: DatabaseManager
    draw_class(36, 8, 32, 28, "DatabaseManager",
               ["- db_path: Path", "- connection: SQLite3"],
               ["+ get_db_connection()", "+ init_db()", "+ execute_query()", "+ fetch_all()"])

    # Associations
    ax.annotate('', xy=(36, 75), xytext=(32, 75), arrowprops=dict(arrowstyle="->", lw=1.5, color='#0f172a'))
    ax.annotate('', xy=(68, 75), xytext=(72, 75), arrowprops=dict(arrowstyle="->", lw=1.5, color='#0f172a'))
    ax.annotate('', xy=(52, 36), xytext=(52, 50), arrowprops=dict(arrowstyle="->", lw=1.5, color='#0f172a'))

    plt.tight_layout()
    plt.savefig(out_dir / "class_diagram.png", bbox_inches='tight')
    plt.close()
    print("Class diagram generated.")

# -------------------------------------------------------------
# 5. Sequence Diagram
# -------------------------------------------------------------
def make_sequence_diagram():
    fig, ax = plt.subplots(figsize=(10, 7.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    ax.text(50, 97, "Figure 5.4: Prediction & Explanation Sequence Diagram", ha='center', va='center', fontsize=13, fontweight='bold', color='#0f172a')

    lifelines = [
        ("HR Manager", 12),
        ("UI (predict.html)", 32),
        ("Controller (app.py)", 52),
        ("ModelService", 72),
        ("SQLite Database", 90)
    ]

    for name, x in lifelines:
        box = patches.FancyBboxPatch((x-9, 87), 18, 5, boxstyle="round,pad=0.3", ec='#0f172a', fc='#e2e8f0', lw=1.5)
        ax.add_patch(box)
        ax.text(x, 89.5, name, ha='center', va='center', fontsize=8.5, fontweight='bold', color='#0f172a')
        ax.plot([x, x], [87, 8], color='#94a3b8', lw=1.2, linestyle='--')

    messages = [
        (80, 12, 32, "1. Submits 18 Profile Features", True),
        (72, 32, 52, "2. POST /predict request", True),
        (64, 52, 72, "3. predict_employee(input_dict)", True),
        (56, 72, 72, "4. Pipeline transform & model infer", False),
        (48, 72, 72, "5. Compute SHAP additive values", False),
        (40, 72, 52, "6. Return prediction, probability, SHAP", False),
        (32, 52, 90, "7. save_prediction(record)", True),
        (24, 90, 52, "8. Confirm record inserted (ID)", False),
        (16, 52, 32, "9. Render result.html with metrics", False),
        (10, 32, 12, "10. View Prediction Verdict & XAI Bar", False),
    ]

    for y, x1, x2, msg, is_call in messages:
        if x1 == x2: # Self invocation
            ax.plot([x1, x1+6, x1+6, x1], [y+2, y+2, y-2, y-2], color='#0d9488', lw=1.5)
            ax.annotate('', xy=(x1, y-2), xytext=(x1+6, y-2), arrowprops=dict(arrowstyle="->", color='#0d9488', lw=1.5))
            ax.text(x1+7, y, msg, va='center', fontsize=8, color='#0f766e', fontweight='semibold')
        else:
            style = "->" if is_call else "--"
            col = "#2563eb" if is_call else "#475569"
            ax.annotate('', xy=(x2, y), xytext=(x1, y), arrowprops=dict(arrowstyle="->" if is_call else "->", linestyle='solid' if is_call else 'dashed', color=col, lw=1.5))
            ax.text((x1+x2)/2, y+1.5, msg, ha='center', va='bottom', fontsize=7.8, color=col, fontweight='semibold')

    plt.tight_layout()
    plt.savefig(out_dir / "sequence_diagram.png", bbox_inches='tight')
    plt.close()
    print("Sequence diagram generated.")

# -------------------------------------------------------------
# 6. Confusion Matrix Heatmap
# -------------------------------------------------------------
def make_confusion_matrix_chart():
    fig, ax = plt.subplots(figsize=(6, 5), dpi=300)
    cm = np.array([[188, 59], [14, 33]])
    
    cax = ax.matshow(cm, cmap='Blues')
    fig.colorbar(cax)

    for (i, j), z in np.ndenumerate(cm):
        label = f"{z}\n"
        if i == 0 and j == 0: label += "(True Neg: Retained)"
        elif i == 0 and j == 1: label += "(False Pos: Flagged)"
        elif i == 1 and j == 0: label += "(False Neg: Missed)"
        elif i == 1 and j == 1: label += "(True Pos: Detected)"
        ax.text(j, i, label, ha='center', va='center', fontsize=9, color='white' if z > 100 else 'black', fontweight='bold')

    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(['Predicted Retain (0)', 'Predicted Attrition (1)'])
    ax.set_yticklabels(['Actual Retain (0)', 'Actual Attrition (1)'])
    ax.set_title("Figure 7.1: Confusion Matrix (Logistic Regression Champion)", fontsize=11, fontweight='bold', pad=15)
    ax.set_xlabel("Predicted Class", fontweight='semibold')
    ax.set_ylabel("True Class", fontweight='semibold')

    plt.tight_layout()
    plt.savefig(out_dir / "confusion_matrix_chart.png", bbox_inches='tight')
    plt.close()
    print("Confusion matrix chart generated.")

# -------------------------------------------------------------
# 7. SHAP Feature Importance Chart
# -------------------------------------------------------------
def make_shap_chart():
    fig, ax = plt.subplots(figsize=(7.5, 4.5), dpi=300)
    
    with open("models/global_shap.json", "r") as f:
        data = json.load(f)[:8]

    features = [d["feature"] for d in reversed(data)]
    values = [d["importance"] for d in reversed(data)]

    bars = ax.barh(features, values, color='#2563eb', height=0.6, edgecolor='#1e3a8a')
    for bar in bars:
        w = bar.get_width()
        ax.text(w + 0.001, bar.get_y() + bar.get_height()/2, f"{w:.4f}", va='center', fontsize=8.5, fontweight='bold', color='#1e293b')

    ax.set_title("Figure 6.1: Top Global Feature Importance (Mean |SHAP Value|)", fontsize=11, fontweight='bold', pad=12)
    ax.set_xlabel("Mean Absolute SHAP Value (Impact on Turnover Prediction)", fontsize=9.5, fontweight='semibold')
    ax.grid(axis='x', linestyle='--', alpha=0.5)

    plt.tight_layout()
    plt.savefig(out_dir / "shap_feature_importance.png", bbox_inches='tight')
    plt.close()
    print("SHAP chart generated.")

if __name__ == "__main__":
    make_architecture_diagram()
    make_activity_diagram()
    make_usecase_diagram()
    make_class_diagram()
    make_sequence_diagram()
    make_confusion_matrix_chart()
    make_shap_chart()
    print("All report diagrams generated successfully!")
