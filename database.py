import sqlite3
from datetime import datetime

DB_NAME = "audit_logs.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        branch TEXT,
        files_changed INTEGER,
        decision TEXT,
        matched_rules TEXT,
        explanation TEXT
    )
    """)

    conn.commit()
    conn.close()

def save_log(branch, files_changed, decision, matched_rules, explanation):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO audit_logs
    (timestamp, branch, files_changed, decision, matched_rules, explanation)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        branch,
        files_changed,
        decision,
        matched_rules,
        explanation
    ))

    conn.commit()
    conn.close()