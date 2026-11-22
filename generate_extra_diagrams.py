"""
Generates high-resolution Context Diagram, Dataflow Diagram, and Workflow Diagram
for the MCA Major Project Report.
"""
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path

out_dir = Path("report_assets")
out_dir.mkdir(exist_ok=True)

# -------------------------------------------------------------
# 1. CONTEXT DIAGRAM (Figure 4.3.1)
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
ax.set_xlim(0, 10)
ax.set_ylim(0, 6)
ax.axis('off')

# Central System Circle
sys_circle = patches.Circle((5, 3), 1.3, facecolor='#EBF5FB', edgecolor='#2980B9', linewidth=2.5, zorder=3)
ax.add_patch(sys_circle)
ax.text(5, 3.2, "Employee Attrition\nPrediction & Analysis\nSystem", ha='center', va='center', fontsize=11, fontweight='bold', color='#1B4F72', zorder=4)
ax.text(5, 2.3, "(Flask + ML + XAI)", ha='center', va='center', fontsize=8.5, fontstyle='italic', color='#5D6D7E', zorder=4)

# External Entity: HR Manager (Left)
hr_box = patches.FancyBboxPatch((0.5, 2.2), 2.2, 1.6, boxstyle="round,pad=0.1", facecolor='#F4F6F7', edgecolor='#34495E', linewidth=2, zorder=3)
ax.add_patch(hr_box)
ax.text(1.6, 3.2, "HR Manager /\nAdministrator", ha='center', va='center', fontsize=10.5, fontweight='bold', color='#2C3E50', zorder=4)
ax.text(1.6, 2.5, "(End User)", ha='center', va='center', fontsize=8.5, color='#7F8C8D', zorder=4)

# External Entity: Database & Models (Bottom)
db_box = patches.FancyBboxPatch((3.8, 0.3), 2.4, 1.1, boxstyle="round,pad=0.1", facecolor='#FEF9E7', edgecolor='#F39C12', linewidth=2, zorder=3)
ax.add_patch(db_box)
ax.text(5, 0.95, "SQLite Database &\nTrained Model Artifacts", ha='center', va='center', fontsize=9.5, fontweight='bold', color='#B9770E', zorder=4)
ax.text(5, 0.55, "(attrition.db & .pkl files)", ha='center', va='center', fontsize=8, color='#7D6608', zorder=4)

# Arrows between HR Manager and System
# HR -> System: Login, 18 Employee Parameters
ax.annotate("", xy=(3.7, 3.4), xytext=(2.7, 3.4),
            arrowprops=dict(arrowstyle="->", color="#2980B9", lw=1.8, mutation_scale=15))
ax.text(3.2, 3.6, "1. Credentials\n2. 18 Profile Inputs", ha='center', va='bottom', fontsize=8, color='#1B4F72', fontweight='semibold')

# System -> HR: Predictions, SHAP Explanations, Retention Advice
ax.annotate("", xy=(2.7, 2.6), xytext=(3.7, 2.6),
            arrowprops=dict(arrowstyle="->", color="#27AE60", lw=1.8, mutation_scale=15))
ax.text(3.2, 2.2, "1. Turnover Probability\n2. SHAP Explanations\n3. Retention Advice", ha='center', va='top', fontsize=8, color='#196F3D', fontweight='semibold')

# Arrows between System and Database/Artifacts
ax.annotate("", xy=(4.6, 1.4), xytext=(4.6, 1.7),
            arrowprops=dict(arrowstyle="->", color="#D35400", lw=1.8, mutation_scale=15))
ax.text(4.2, 1.55, "Save Audit\nLog", ha='right', va='center', fontsize=7.5, color='#935116', fontweight='semibold')

ax.annotate("", xy=(5.4, 1.7), xytext=(5.4, 1.4),
            arrowprops=dict(arrowstyle="->", color="#D35400", lw=1.8, mutation_scale=15))
ax.text(5.8, 1.55, "Load Models &\nHistory Records", ha='left', va='center', fontsize=7.5, color='#935116', fontweight='semibold')

# External Entity: IBM HR Baseline Dataset (Right)
ds_box = patches.FancyBboxPatch((7.5, 2.2), 2.1, 1.6, boxstyle="round,pad=0.1", facecolor='#E8F8F5', edgecolor='#16A085', linewidth=2, zorder=3)
ax.add_patch(ds_box)
ax.text(8.55, 3.2, "IBM HR Analytics\nBaseline Dataset", ha='center', va='center', fontsize=10, fontweight='bold', color='#117A65', zorder=4)
ax.text(8.55, 2.5, "(1,470 Records)", ha='center', va='center', fontsize=8.5, color='#76D7C4', zorder=4)

ax.annotate("", xy=(6.3, 3.0), xytext=(7.5, 3.0),
            arrowprops=dict(arrowstyle="->", color="#16A085", lw=1.8, mutation_scale=15))
ax.text(6.9, 3.2, "Training Data &\nBaseline Metrics", ha='center', va='bottom', fontsize=8, color='#0E6251', fontweight='semibold')

plt.title("Figure 4.3.1: Context Diagram of Employee Attrition Prediction & Analysis System", fontsize=11, fontweight='bold', pad=15, color='#2C3E50')
plt.tight_layout()
plt.savefig(out_dir / "context_diagram.png", bbox_inches='tight')
plt.close()
print("Generated context_diagram.png")

# -------------------------------------------------------------
# 2. DATAFLOW DIAGRAM (Figure 5.1.1)
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10.5, 6.2), dpi=300)
ax.set_xlim(0, 11)
ax.set_ylim(0, 6.5)
ax.axis('off')

# Entity: HR Manager
e1 = patches.FancyBboxPatch((0.4, 2.6), 1.8, 1.4, boxstyle="square,pad=0", facecolor='#F2F4F4', edgecolor='#34495E', linewidth=1.8)
ax.add_patch(e1)
ax.text(1.3, 3.3, "HR Manager\n(User)", ha='center', va='center', fontsize=9.5, fontweight='bold', color='#2C3E50')

# Process 1: Input Validation & Preprocessing
p1 = patches.FancyBboxPatch((2.8, 2.5), 2.2, 1.6, boxstyle="round,pad=0.2", facecolor='#EBF5FB', edgecolor='#2980B9', linewidth=1.8)
ax.add_patch(p1)
ax.text(3.9, 3.6, "1.0 Validate &", ha='center', va='center', fontsize=9.5, fontweight='bold', color='#1B4F72')
ax.text(3.9, 3.3, "Preprocess Inputs", ha='center', va='center', fontsize=9.5, fontweight='bold', color='#1B4F72')
ax.text(3.9, 2.9, "(Scale + One-Hot)", ha='center', va='center', fontsize=8, color='#5499C7')

# Process 2: Model Inference & SHAP Calculation
p2 = patches.FancyBboxPatch((5.6, 2.5), 2.3, 1.6, boxstyle="round,pad=0.2", facecolor='#FEF9E7', edgecolor='#F39C12', linewidth=1.8)
ax.add_patch(p2)
ax.text(6.75, 3.6, "2.0 Predict &", ha='center', va='center', fontsize=9.5, fontweight='bold', color='#B9770E')
ax.text(6.75, 3.3, "Explain Attrition", ha='center', va='center', fontsize=9.5, fontweight='bold', color='#B9770E')
ax.text(6.75, 2.9, "(Logistic + SHAP)", ha='center', va='center', fontsize=8, color='#D4AC0D')

# Process 3: Retention Recommendation & Logging
p3 = patches.FancyBboxPatch((8.5, 2.5), 2.1, 1.6, boxstyle="round,pad=0.2", facecolor='#E8F8F5', edgecolor='#16A085', linewidth=1.8)
ax.add_patch(p3)
ax.text(9.55, 3.6, "3.0 Recommend &", ha='center', va='center', fontsize=9.5, fontweight='bold', color='#117A65')
ax.text(9.55, 3.3, "Log Record", ha='center', va='center', fontsize=9.5, fontweight='bold', color='#117A65')
ax.text(9.55, 2.9, "(Rules + SQLite)", ha='center', va='center', fontsize=8, color='#48C9B0')

# Data Store D1: SQLite Database
ds1_top = patches.Rectangle((5.0, 0.4), 3.0, 0.9, facecolor='#FDEDEC', edgecolor='#C0392B', linewidth=1.5)
ax.add_patch(ds1_top)
ax.text(6.5, 0.85, "D1: SQLite Database (attrition.db)", ha='center', va='center', fontsize=9, fontweight='bold', color='#922B21')

# Arrows
# HR -> P1.0
ax.annotate("", xy=(2.8, 3.5), xytext=(2.2, 3.5), arrowprops=dict(arrowstyle="->", color="#2980B9", lw=1.5))
ax.text(2.5, 3.7, "Profile\nInputs", ha='center', va='bottom', fontsize=7.5, color='#1B4F72')

# P1.0 -> P2.0
ax.annotate("", xy=(5.6, 3.3), xytext=(5.0, 3.3), arrowprops=dict(arrowstyle="->", color="#2980B9", lw=1.5))
ax.text(5.3, 3.5, "Standardized\nVector X", ha='center', va='bottom', fontsize=7.5, color='#1B4F72')

# P2.0 -> P3.0
ax.annotate("", xy=(8.5, 3.3), xytext=(7.9, 3.3), arrowprops=dict(arrowstyle="->", color="#F39C12", lw=1.5))
ax.text(8.2, 3.5, "Prob & SHAP\nValues", ha='center', va='bottom', fontsize=7.5, color='#B9770E')

# P3.0 -> Data Store D1
ax.annotate("", xy=(7.2, 1.3), xytext=(8.8, 2.5), arrowprops=dict(arrowstyle="->", color="#C0392B", lw=1.5))
ax.text(8.2, 1.8, "Save Audit\nRecord", ha='left', va='center', fontsize=7.5, color='#922B21')

# P3.0 feedback to HR Manager (Return results)
ax.plot([9.5, 9.5, 1.3, 1.3], [2.5, 5.5, 5.5, 4.0], color='#27AE60', lw=1.5, linestyle='--')
ax.annotate("", xy=(1.3, 4.0), xytext=(1.3, 4.2), arrowprops=dict(arrowstyle="->", color="#27AE60", lw=1.5))
ax.text(5.4, 5.7, "Formatted Results, Visual Risk Bar, SHAP Waterfall & Retention Suggestions", ha='center', va='bottom', fontsize=8, color='#196F3D', fontweight='bold')

plt.title("Figure 5.1.1: Data Flow Diagram (DFD Level-1) for Employee Attrition Prediction & Analysis", fontsize=11, fontweight='bold', pad=15, color='#2C3E50')
plt.tight_layout()
plt.savefig(out_dir / "dataflow_diagram.png", bbox_inches='tight')
plt.close()
print("Generated dataflow_diagram.png")

# -------------------------------------------------------------
# 3. WORKFLOW DIAGRAM (Figure 5.2.1)
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10.5, 6.2), dpi=300)
ax.set_xlim(0, 11)
ax.set_ylim(0, 6.5)
ax.axis('off')

# 5 Sequential Workflow Stages
stages = [
    ("1. Data Ingestion\n& Security", "HR Manager authenticates;\nSubmits 18 profile fields\n(Salary in INR)", "#EBF5FB", "#2980B9"),
    ("2. Preprocessing\nPipeline", "StandardScaler on 11 num;\nOneHotEncoder on 7 cat;\n16 noise columns dropped", "#FEF9E7", "#F39C12"),
    ("3. Machine Learning\nInference", "Balanced Logistic Regression\ncomputes turnover prob;\nRisk level assigned", "#E8F8F5", "#16A085"),
    ("4. Explainable AI\n(SHAP Engine)", "LinearExplainer computes\nexact additive contributions;\nFlags positive & negative drivers", "#F4ECF7", "#8E44AD"),
    ("5. Insights &\nAudit Storage", "Actionable advice generated;\nRecord stored in SQLite;\nDashboard renders visual bar", "#FDEDEC", "#C0392B")
]

x_start = 0.5
box_w = 1.8
spacing = 0.35

for i, (title, desc, bg, border) in enumerate(stages):
    bx = x_start + i * (box_w + spacing)
    b = patches.FancyBboxPatch((bx, 2.0), box_w, 2.8, boxstyle="round,pad=0.15", facecolor=bg, edgecolor=border, linewidth=2)
    ax.add_patch(b)
    ax.text(bx + box_w/2, 4.4, title, ha='center', va='center', fontsize=9.5, fontweight='bold', color=border)
    ax.text(bx + box_w/2, 3.1, desc, ha='center', va='center', fontsize=8, color='#34495E', linespacing=1.3)
    
    # Arrow to next stage
    if i < 4:
        ax.annotate("", xy=(bx + box_w + spacing - 0.05, 3.4), xytext=(bx + box_w + 0.05, 3.4),
                    arrowprops=dict(arrowstyle="->", color="#7F8C8D", lw=2, mutation_scale=15))

# Top & Bottom summary labels
ax.text(5.5, 5.8, "End-to-End Operational Workflow of the Employee Attrition Analyser", ha='center', va='center', fontsize=11, fontweight='bold', color='#2C3E50')
ax.text(5.5, 1.0, "Every single employee evaluation traverses this 5-stage automated pipeline in under 50 ms.", ha='center', va='center', fontsize=9, fontstyle='italic', color='#7F8C8D')

plt.title("Figure 5.2.1: Step-by-Step System Workflow Diagram", fontsize=11, fontweight='bold', pad=15, color='#2C3E50')
plt.tight_layout()
plt.savefig(out_dir / "workflow_diagram.png", bbox_inches='tight')
plt.close()
print("Generated workflow_diagram.png")
