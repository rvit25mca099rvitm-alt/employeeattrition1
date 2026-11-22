"""
SQLite database persistence for users, authentication, prediction history, and audit tracking.
"""
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from werkzeug.security import generate_password_hash, check_password_hash

import config

def get_db_connection() -> sqlite3.Connection:
    """Creates a connection to the SQLite database."""
    config.DATABASE_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(config.DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes database tables if they do not exist."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Users Table for Authentication
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                role TEXT DEFAULT 'HR Analyst',
                created_at TIMESTAMP NOT NULL
            );
        """)
        
        # Predictions Table for Storing Analysed Data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_name TEXT,
                employee_id TEXT,
                user_id INTEGER,
                username TEXT,
                created_at TIMESTAMP NOT NULL,
                age INTEGER,
                gender TEXT,
                department TEXT,
                job_role TEXT,
                monthly_income REAL,
                overtime TEXT,
                total_working_years INTEGER,
                years_at_company INTEGER,
                attrition_prob REAL NOT NULL,
                risk_level TEXT NOT NULL,
                prediction_label TEXT NOT NULL,
                top_risk_factors TEXT,
                top_protective_factors TEXT,
                full_input_data TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            );
        """)

        # Migration helpers for columns
        cursor.execute("PRAGMA table_info(predictions)")
        cols = [c[1] for c in cursor.fetchall()]
        for col_name in ["employee_name", "employee_id", "gender", "user_id", "username"]:
            if col_name not in cols:
                try:
                    cursor.execute(f"ALTER TABLE predictions ADD COLUMN {col_name} TEXT")
                except Exception:
                    pass

        # Ensure schema commit
        conn.commit()

# --- User Authentication Functions ---

def register_user(username: str, email: str, password: str, full_name: str = "") -> Tuple[bool, str]:
    """Registers a new user with hashed password."""
    init_db()
    username = username.strip().lower()
    email = email.strip().lower()

    if not username or not email or not password:
        return False, "All fields (Username, Email, Password) are required."

    if len(password) < 6:
        return False, "Password must be at least 6 characters long."

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            return False, "Username is already taken. Please choose another."

        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            return False, "Email is already registered. Please login."

        pw_hash = generate_password_hash(password)
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, full_name, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (username, email, pw_hash, full_name.strip() or username.title(), now))
        conn.commit()
        return True, "Registration successful! You can now log in."

def authenticate_user(username_or_email: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticates user credentials against stored password hash."""
    init_db()
    key = username_or_email.strip().lower()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE LOWER(username) = ? OR LOWER(email) = ?", (key, key))
        user_row = cursor.fetchone()
        if not user_row:
            return None
        user = dict(user_row)
        if check_password_hash(user["password_hash"], password):
            return user
        return None

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves user by primary key ID."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email, full_name, role, created_at FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

# --- Analysed Data Storage & Query Functions ---

def log_prediction(
    input_data: Dict[str, Any],
    prob: float,
    risk_level: str,
    prediction_label: str,
    top_risk_factors: Optional[List[Dict[str, Any]]] = None,
    top_protective_factors: Optional[List[Dict[str, Any]]] = None,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    employee_name: Optional[str] = None,
    employee_id: Optional[str] = None,
) -> int:
    """Saves an individual analysed prediction event to the database."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO predictions (
                employee_name, employee_id, user_id, username, created_at, age, gender,
                department, job_role, monthly_income, overtime, total_working_years,
                years_at_company, attrition_prob, risk_level, prediction_label,
                top_risk_factors, top_protective_factors, full_input_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            employee_name or input_data.get("employee_name") or "Employee",
            employee_id or input_data.get("employee_id") or "-",
            user_id,
            username or "HR User",
            now,
            int(input_data.get("Age", 0)),
            str(input_data.get("Gender", "Male")),
            str(input_data.get("Department", "")),
            str(input_data.get("JobRole", "")),
            float(input_data.get("MonthlyIncome", 0)),
            str(input_data.get("OverTime", "")),
            int(input_data.get("TotalWorkingYears", 0)),
            int(input_data.get("YearsAtCompany", 0)),
            float(prob),
            str(risk_level),
            str(prediction_label),
            json.dumps(top_risk_factors or []),
            json.dumps(top_protective_factors or []),
            json.dumps(input_data)
        ))
        conn.commit()
        return cursor.lastrowid

def get_recent_predictions(limit: int = 200, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Fetches stored analysed prediction records."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, employee_name, employee_id, user_id, username, created_at,
                   age, gender, department, job_role, monthly_income, overtime,
                   total_working_years, years_at_company, attrition_prob, risk_level,
                   prediction_label
            FROM predictions
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_prediction_by_id(pred_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves a single prediction by ID with full inputs and factors."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM predictions WHERE id = ?", (pred_id,))
        row = cursor.fetchone()
        if not row:
            return None
        res = dict(row)
        if res.get("top_risk_factors"):
            res["top_risk_factors"] = json.loads(res["top_risk_factors"])
        if res.get("top_protective_factors"):
            res["top_protective_factors"] = json.loads(res["top_protective_factors"])
        if res.get("full_input_data"):
            res["full_input_data"] = json.loads(res["full_input_data"])
        return res

def delete_prediction_by_id(pred_id: int) -> bool:
    """Deletes a specific prediction record."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM predictions WHERE id = ?", (pred_id,))
        conn.commit()
        return cursor.rowcount > 0

def clear_prediction_history(user_id: Optional[int] = None):
    """Clears prediction records."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM predictions")
        conn.commit()

def get_prediction_stats() -> Dict[str, Any]:
    """Computes summary statistics on all stored analysed predictions."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM predictions")
        total = cursor.fetchone()["total"]
        if total == 0:
            return {"total": 0, "high_risk": 0, "medium_risk": 0, "low_risk": 0, "avg_prob": 0.0}

        cursor.execute("SELECT COUNT(*) as high FROM predictions WHERE risk_level = 'High Risk'")
        high = cursor.fetchone()["high"]
        cursor.execute("SELECT COUNT(*) as med FROM predictions WHERE risk_level = 'Medium Risk'")
        med = cursor.fetchone()["med"]
        cursor.execute("SELECT COUNT(*) as low FROM predictions WHERE risk_level = 'Low Risk'")
        low = cursor.fetchone()["low"]
        cursor.execute("SELECT AVG(attrition_prob) as avg_p FROM predictions")
        avg_p = cursor.fetchone()["avg_p"] or 0.0

        return {
            "total": total,
            "high_risk": high,
            "medium_risk": med,
            "low_risk": low,
            "avg_prob": round(float(avg_p) * 100, 1)
        }
