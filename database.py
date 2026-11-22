"""
Database management module for Employee Attrition Application using SQLite.
Handles user authentication and prediction history logging.
"""
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from config import DATABASE_PATH

def get_db_connection():
    """Create and return a database connection with dict-like row access."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database tables and create default admin account if not present."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Prediction history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_ref TEXT NOT NULL,
            age INTEGER,
            department TEXT,
            job_role TEXT,
            monthly_income REAL,
            overtime TEXT,
            prediction TEXT NOT NULL,
            probability REAL NOT NULL,
            risk_category TEXT NOT NULL,
            top_positive_factors TEXT,
            top_negative_factors TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    # Seed default administrator if users table is empty
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    if count == 0:
        default_user = "Namratha K S"
        default_pass = "adminpass0213"
        hashed = generate_password_hash(default_pass, method="pbkdf2:sha256")
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (default_user, "admin@attrition-ai.org", hashed)
        )
        conn.commit()

    conn.close()

def register_user(username, password, email=None):
    """Register a new user with hashed password."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        hashed = generate_password_hash(password, method="pbkdf2:sha256")
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username.strip(), email.strip() if email else None, hashed)
        )
        conn.commit()
        return True, "User registered successfully."
    except sqlite3.IntegrityError:
        return False, "Username already exists. Please choose a different username."
    except Exception as e:
        return False, f"Registration error: {str(e)}"
    finally:
        conn.close()

def verify_user(username, password):
    """Verify user credentials."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username.strip(),))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user["password_hash"], password):
        return True, dict(user)
    return False, None

def save_prediction(employee_ref, age, department, job_role, monthly_income, overtime,
                    prediction, probability, risk_category, top_positive, top_negative):
    """Save a prediction record into the SQLite database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO predictions (
            employee_ref, age, department, job_role, monthly_income, overtime,
            prediction, probability, risk_category, top_positive_factors, top_negative_factors
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        employee_ref, age, department, job_role, monthly_income, overtime,
        prediction, probability, risk_category, top_positive, top_negative
    ))
    conn.commit()
    pred_id = cursor.lastrowid
    conn.close()
    return pred_id

def get_prediction_history(limit=100):
    """Retrieve recent prediction history records."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM predictions
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_prediction_by_id(pred_id):
    """Fetch single prediction details by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM predictions WHERE id = ?", (pred_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None
