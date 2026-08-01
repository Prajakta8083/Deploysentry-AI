"""
DeploySentry AI — API layer

Wraps the PolicyEngine in a FastAPI service so external tools (like Jenkins,
or a frontend, or curl/Postman for testing) can request a decision over HTTP
instead of running Python scripts directly.
"""

import sqlite3
from typing import List, Optional
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from policy_engine import PolicyEngine, ChangeRequest
from database import init_db, save_log
import sqlite3
from fastapi.staticfiles import StaticFiles


app = FastAPI(title="DeploySentry AI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the policy engine once when the server starts (not on every request)
engine = PolicyEngine("rules.yaml")
engine = PolicyEngine("rules.yaml")

init_db()


class ChangeRequestInput(BaseModel):
    files_changed: List[str]
    lines_changed: int
    branch: str
    is_pull_request: bool
    deploy_hour: Optional[int] = None  # if omitted, uses current server time



@app.post("/evaluate")
def evaluate_change(payload: ChangeRequestInput):
    if payload.lines_changed < 0:
        raise HTTPException(status_code=400, detail="lines_changed cannot be negative")

    change = ChangeRequest(
        files_changed=payload.files_changed,
        lines_changed=payload.lines_changed,
        branch=payload.branch,
        is_pull_request=payload.is_pull_request,
        deploy_hour=payload.deploy_hour,
    )

    result = engine.evaluate(change)

    save_log(
        branch=payload.branch,
        files_changed=len(payload.files_changed),
        decision=result["action"],
        matched_rules=result["matched_rule"],
        explanation=result["reason"]
    )

    return result

# ── 2. YOUR HEALTH CHECK ROUTE SHOULD NOW LOOK LIKE THIS ──
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "deploysentry-ai"}


# ── 3. ADD THIS NEW ROUTE ANYWHERE AMONG YOUR OTHER @app.get/@app.post ROUTES ──
@app.get("/analytics/summary")
def analytics_summary():
    conn = sqlite3.connect("audit_logs.db")
    cursor = conn.cursor()

    # 🔧 change "decision" below to your actual column name if different
    cursor.execute("""
        SELECT decision, COUNT(*) as count
        FROM audit_logs
        GROUP BY decision
    """)
    rows = cursor.fetchall()
    conn.close()

    summary = {"APPROVE": 0, "REVIEW": 0, "BLOCK": 0}
    for decision, count in rows:
        if decision in summary:
            summary[decision] = count

    total = sum(summary.values())
    return {"summary": summary, "total": total}


# ── 4. THIS MUST BE THE ABSOLUTE LAST LINE IN main.py ──
# Serves index.html (sitting in your project root) at http://localhost:8090/
# It must come AFTER every other @app.get / @app.post route, otherwise it
# will intercept requests meant for /evaluate, /audit-logs, /health, etc.


@app.get("/audit-logs")
def get_audit_logs():
    conn = sqlite3.connect("audit_logs.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        timestamp,
        branch,
        files_changed,
        decision,
        matched_rules,
        explanation
    FROM audit_logs
    ORDER BY id DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    logs = []

    for row in rows:
        logs.append({
            "time": row[0],
            "branch": row[1],
            "files_changed": row[2],
            "status": row[3],
            "rule": row[4],
            "reason": row[5]
        })

    return logs

app.mount("/", StaticFiles(directory=".", html=True), name="frontend")