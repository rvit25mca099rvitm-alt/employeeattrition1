"""
Generates a comprehensive, professional PDF document of the project's
About Section, System Architecture, Tech Stack, and Academic Viva Guide.
"""
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)

def build_pdf(filename="Project_Documentation_About_Section.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0f172a"),
        alignment=1, # Center
        spaceAfter=6,
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#475569"),
        alignment=1,
        spaceAfter=15,
    )

    h1_style = ParagraphStyle(
        "SectionH1",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#0d6efd"),
        spaceBefore=14,
        spaceAfter=6,
    )

    h2_style = ParagraphStyle(
        "SectionH2",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=8,
        spaceAfter=4,
    )

    body_style = ParagraphStyle(
        "DocBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155"),
        spaceAfter=6,
    )

    bullet_style = ParagraphStyle(
        "DocBullet",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#334155"),
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=3,
    )

    qa_q_style = ParagraphStyle(
        "QAQuestion",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=6,
        spaceAfter=3,
    )

    qa_a_style = ParagraphStyle(
        "QAAnswer",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12.5,
        textColor=colors.HexColor("#334155"),
        leftIndent=10,
        spaceAfter=6,
    )

    story = []

    # Title & Subtitle
    story.append(Paragraph("Employee Attrition Analysis and Prediction System", title_style))
    story.append(Paragraph("System Architecture, Methodology, Machine Learning Benchmark & Technical Defense Documentation", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0d6efd"), spaceBefore=0, spaceAfter=12))

    # Section 1: Executive Overview
    story.append(Paragraph("1. Executive Project Overview", h1_style))
    story.append(Paragraph(
        "Employee attrition represents one of the most substantial financial and operational challenges in modern workforce management. "
        "The cost of backfilling a specialized position often ranges from 50% to 200% of an employee's annual salary, compounded by lost institutional memory, team disruption, and reduced project velocity. "
        "This system provides human resource leadership with an end-to-end, interpretable machine learning decision support platform. "
        "Rather than relying on subjective intuition or post-hoc exit surveys, the application objectively forecasts voluntary departure risks early, "
        "unpacks underlying friction drivers via mathematical Explainable AI (SHAP), and enables proactive retention interventions.",
        body_style,
    ))

    # Section 2: Existing vs Proposed
    story.append(Paragraph("2. Limitations of Existing Systems vs. Proposed Solution", h1_style))
    compare_data = [
        [
            Paragraph("<b>Traditional / Existing HR Practices</b>", h2_style),
            Paragraph("<b>Proposed Machine Learning & XAI Platform</b>", h2_style),
        ],
        [
            Paragraph("&bull; <b>Reactive Exit Interviews:</b> Interventions only occur after resignation letters are tendered, making retention virtually impossible.", bullet_style),
            Paragraph("&bull; <b>Proactive Risk Identification:</b> Flags elevated resignation probability weeks/months in advance while retention is still viable.", bullet_style),
        ],
        [
            Paragraph("&bull; <b>Subjective Gut Feeling:</b> Managers rely on anecdotal heuristics rather than empirical multidimensional indicators.", bullet_style),
            Paragraph("&bull; <b>Empirical Data-Driven Model:</b> Evaluates 30+ validated factors across career tenure, compensation, and work-life balance.", bullet_style),
        ],
        [
            Paragraph("&bull; <b>Black-Box Predictions:</b> Legacy AI tools generate opaque binary labels without explaining factor contributions.", bullet_style),
            Paragraph("&bull; <b>Instance-Level SHAP Interpretability:</b> Quantifies exact mathematical positive risk drivers and protective retention buffers.", bullet_style),
        ],
        [
            Paragraph("&bull; <b>Uniform Blanket Retention:</b> Organizations apply generalized raises or perks without identifying specific root causes.", bullet_style),
            Paragraph("&bull; <b>Targeted Interventions:</b> Diagnostic factor attribution allows HR to address specific individual concerns (e.g. overtime burnout).", bullet_style),
        ],
    ]
    t_compare = Table(compare_data, colWidths=[260, 260])
    t_compare.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#fff5f5")),
        ("BACKGROUND", (1, 0), (1, -1), colors.HexColor("#f0fdf4")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t_compare)
    story.append(Spacer(1, 10))

    # Section 3: System Architecture
    story.append(Paragraph("3. End-to-End System Architecture", h1_style))
    story.append(Paragraph(
        "The application is structured into five distinct, decoupled architectural layers designed for stability, reproducibility, and enterprise readiness:",
        body_style,
    ))
    story.append(Paragraph("<b>1. Data Ingestion & Integrity Layer:</b> Ingests 1,470 employee records across 35 attributes. Executes rigorous type checking, null validation, duplicate removal, and drops identifier/zero-variance features (<i>EmployeeNumber, EmployeeCount, StandardHours, Over18</i>).", bullet_style))
    story.append(Paragraph("<b>2. Feature Engineering & Preprocessing Pipeline:</b> Enforces strict data leakage prevention via a stratified 80/20 train/test split. Constructs a Scikit-learn <code>ColumnTransformer</code> applying <code>StandardScaler</code> to numerical features and <code>OneHotEncoder</code> with unknown-category handling to categorical features, producing 51 model-ready inputs.", bullet_style))
    story.append(Paragraph("<b>3. Machine Learning Modeling & Benchmarking:</b> Trains, cross-validates, and evaluates four candidate algorithms (Logistic Regression, Decision Tree, Random Forest, and XGBoost). Persists the champion model and preprocessor artifacts using Joblib.", bullet_style))
    story.append(Paragraph("<b>4. Explainable AI (XAI) Attribution Engine:</b> Integrates SHAP (SHapley Additive exPlanations) based on cooperative game theory. Computes exact marginal contributions for every individual prediction, categorizing features into Risk Drivers (+SHAP) and Protective Buffers (-SHAP).", bullet_style))
    story.append(Paragraph("<b>5. Secure Application & Presentation Layer:</b> Built on Python Flask with SQLite database persistence, password hashing, dynamic Plotly analytics charts, responsive Bootstrap 5 interface, and REST API endpoints.", bullet_style))
    story.append(Spacer(1, 10))

    # Section 4: Technology Stack
    story.append(Paragraph("4. Comprehensive Technology Stack", h1_style))
    tech_data = [
        [Paragraph("<b>Component / Layer</b>", h2_style), Paragraph("<b>Technologies & Libraries</b>", h2_style), Paragraph("<b>Functional Responsibility</b>", h2_style)],
        [Paragraph("Backend Framework", body_style), Paragraph("Python 3.12, Flask 3.1, Werkzeug", body_style), Paragraph("HTTP routing, session auth, validation, database integration", body_style)],
        [Paragraph("Machine Learning", body_style), Paragraph("Scikit-learn 1.6, XGBoost 3.4, NumPy, Pandas", body_style), Paragraph("Feature transformations, model training, probabilistic prediction", body_style)],
        [Paragraph("Explainable AI (XAI)", body_style), Paragraph("SHAP 0.46, TreeExplainer, LinearExplainer", body_style), Paragraph("Instance-level Shapley value computation and feature attributions", body_style)],
        [Paragraph("Data Storage & Audit", body_style), Paragraph("SQLite3, Python sqlite3 module", body_style), Paragraph("User authentication, prediction history, employee records storage", body_style)],
        [Paragraph("Frontend UI & UX", body_style), Paragraph("HTML5, Bootstrap 5.3, Bootstrap Icons", body_style), Paragraph("Responsive interface, clean top menu navigation, validation alerts", body_style)],
        [Paragraph("Interactive Analytics", body_style), Paragraph("Plotly.js 2.30, Plotly Express", body_style), Paragraph("Dynamic departmental distributions, overtime and salary charts", body_style)],
        [Paragraph("Testing & Quality", body_style), Paragraph("Pytest 9.2, pytest-cov", body_style), Paragraph("Automated unit and integration test suite covering 26 test specs", body_style)],
    ]
    t_tech = Table(tech_data, colWidths=[120, 160, 240])
    t_tech.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t_tech)
    story.append(Spacer(1, 10))

    # Section 5: Model Evaluation Benchmark
    story.append(Paragraph("5. Model Evaluation & Benchmark Comparison", h1_style))
    story.append(Paragraph(
        "Four machine learning algorithms were trained on the training split (1,176 samples) and comprehensively evaluated against the held-out test split (294 samples):",
        body_style,
    ))
    bench_data = [
        [
            Paragraph("<b>Algorithm</b>", h2_style),
            Paragraph("<b>ROC-AUC</b>", h2_style),
            Paragraph("<b>Recall (Exits)</b>", h2_style),
            Paragraph("<b>Precision</b>", h2_style),
            Paragraph("<b>Accuracy</b>", h2_style),
            Paragraph("<b>F1-Score</b>", h2_style),
            Paragraph("<b>Benchmark Status</b>", h2_style),
        ],
        [Paragraph("<b>Logistic Regression</b>", body_style), Paragraph("<b>0.8070</b>", body_style), Paragraph("<b>63.8%</b>", body_style), Paragraph("35.3%", body_style), Paragraph("75.5%", body_style), Paragraph("<b>0.4545</b>", body_style), Paragraph("<b>Champion (Selected)</b>", body_style)],
        [Paragraph("Random Forest", body_style), Paragraph("0.7925", body_style), Paragraph("38.3%", body_style), Paragraph("52.9%", body_style), Paragraph("84.7%", body_style), Paragraph("0.4444", body_style), Paragraph("Baseline Candidate", body_style)],
        [Paragraph("XGBoost Classifier", body_style), Paragraph("0.7779", body_style), Paragraph("46.8%", body_style), Paragraph("46.8%", body_style), Paragraph("83.0%", body_style), Paragraph("0.4681", body_style), Paragraph("Baseline Candidate", body_style)],
        [Paragraph("Decision Tree", body_style), Paragraph("0.7017", body_style), Paragraph("55.3%", body_style), Paragraph("35.6%", body_style), Paragraph("76.9%", body_style), Paragraph("0.4333", body_style), Paragraph("Baseline Candidate", body_style)],
    ]
    t_bench = Table(bench_data, colWidths=[110, 60, 75, 60, 60, 60, 95])
    t_bench.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#e0f2fe")), # Champion highlight
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_bench)
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "<b>Champion Selection Rationale:</b> In voluntary employee attrition forecasting, the target class is naturally imbalanced (~16.1% attrition rate). "
        "A trivial model predicting 'Nobody ever leaves' achieves an 83.9% accuracy while missing 100% of departing personnel. "
        "Therefore, <b>Recall</b> (the ability to catch exiting employees) and <b>ROC-AUC</b> (discriminative capability across thresholds) are the deciding metrics. "
        "Logistic Regression demonstrated the highest overall ROC-AUC (0.8070) and captured 63.8% of all true resignations, outperforming deep tree ensembles.",
        body_style,
    ))
    story.append(Spacer(1, 10))

    # Section 6: Mathematical Foundation of SHAP
    story.append(Paragraph("6. Mathematical Foundation of Explainable AI (SHAP)", h1_style))
    story.append(Paragraph(
        "SHAP connects cooperative game theory with machine learning interpretability by calculating Shapley values across feature coalitions. "
        "For a model prediction f(x) on instance x, the attribution of feature i is computed as:",
        body_style,
    ))
    story.append(Paragraph(
        "<b>&phi;<sub>i</sub>(x) = &sum;<sub>S &sube; F \ {i}</sub> [ |S|! (|F| - |S| - 1)! / |F|! ] &times; [ f<sub>S &cup; {i}</sub>(x<sub>S &cup; {i}</sub>) - f<sub>S</sub>(x<sub>S</sub>) ]</b>",
        ParagraphStyle("Formula", parent=body_style, fontName="Helvetica-Bold", fontSize=9, alignment=1, spaceBefore=4, spaceAfter=4),
    ))
    story.append(Paragraph(
        "This formulation guarantees three foundational mathematical properties: (1) <b>Efficiency / Local Accuracy</b> (the sum of feature attributions equals the difference between model output and expected baseline value); "
        "(2) <b>Missingness</b> (features missing from the instance receive zero attribution); and (3) <b>Consistency</b> (if a model changes so a feature has larger marginal impact, its Shapley value never decreases).",
        body_style,
    ))
    story.append(Spacer(1, 10))

    # Section 7: Viva Voce Technical Defense Q&A
    story.append(Paragraph("7. Academic Viva Voce Technical Defense & Examiner Q&A Guide", h1_style))
    
    qas = [
        (
            "Q1: Why is raw classification accuracy an insufficient and potentially misleading metric for employee attrition?",
            "The benchmark dataset exhibits class imbalance (1,233 stay vs. 237 leave, an 83.9% to 16.1% ratio). "
            "A naive baseline classifier that blindly predicts 'Stay' for every record yields an 83.9% accuracy score but has a Recall of 0.0%, "
            "failing to detect a single resignation. In corporate talent retention, False Negatives (unanticipated resignations) carry substantial organizational costs, "
            "whereas False Positives (over-flagging loyal staff for retention check-ins) incur minimal risk. "
            "Hence, models must be evaluated primarily on Recall, ROC-AUC, and F1-score rather than raw accuracy."
        ),
        (
            "Q2: How does SHAP feature attribution differ from traditional Gini importance in tree-based algorithms?",
            "Traditional Gini impurity reduction or feature weight scores suffer from two major limitations: (1) they only deliver global, aggregate importance scores without explaining why a specific employee was flagged; and (2) they exhibit empirical bias toward continuous and high-cardinality features. "
            "In contrast, SHAP computes local, instance-level Shapley values grounded in cooperative game theory. It establishes both magnitude and directionality, explicitly showing whether an attribute pushed risk upward (+SHAP) or functioned as a protective stabilizer (-SHAP)."
        ),
        (
            "Q3: How was data leakage prevented during the preprocessing and feature engineering stages?",
            "Data leakage was eliminated by performing a stratified 80/20 train/test split prior to fitting any data transformations. "
            "The ColumnTransformer (comprising StandardScaler for continuous variables and OneHotEncoder for categorical features) was fitted strictly on X_train. "
            "The test partition (X_test) and any incoming live user inputs are transformed strictly using parameters learned from training data, without refitting. "
            "Furthermore, uninformative identifier features (EmployeeNumber) and constants (StandardHours, EmployeeCount, Over18) were excised prior to modeling."
        ),
        (
            "Q4: What ethical guidelines and Responsible AI (RAI) safeguards are incorporated in this project?",
            "Under Responsible AI principles: (1) Predictions are explicitly communicated as statistical risk assessments rather than deterministic certainties; "
            "(2) The system emphasizes that feature attributions reflect statistical correlation rather than causal mechanics; "
            "(3) Ethical guidelines strictly prohibit using model outputs to justify punitive measures, dismissal, or denial of advancement; "
            "and (4) All workflows are structured as supportive decision aids designed to facilitate empathetic manager-employee dialogue."
        ),
    ]

    for q, a in qas:
        story.append(Paragraph(q, qa_q_style))
        story.append(Paragraph(a, qa_a_style))

    # Build PDF Document
    doc.build(story)
    print(f"Successfully generated PDF: {filename}")

if __name__ == "__main__":
    build_pdf()
