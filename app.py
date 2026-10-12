"""
HostelCare - Hostel Maintenance Request Tracking System
A simple Flask + SQLite application for a college DevOps lab.

Student flow : Report Issue -> Flask -> SQLite -> Request ID -> Track Status
Admin flow   : Dashboard -> View Requests -> Update Status -> SQLite
"""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime

from flask import Flask, flash, redirect, render_template, request, url_for

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# The database ALWAYS lives inside the data/ folder.
# Inside Docker this becomes /app/data/hostel_maintenance.db (mounted volume).
DATABASE = os.path.join(BASE_DIR, "data", "hostel_maintenance.db")

CATEGORIES = [
    "Electrical",
    "Plumbing",
    "Furniture / Carpentry",
    "Wi-Fi / Internet",
    "Cleaning / Housekeeping",
    "Other",
]
PRIORITIES = ["Low", "Medium", "High"]
STATUSES = ["Pending", "Assigned", "In Progress", "Resolved"]

app = Flask(__name__)
app.config["DATABASE"] = DATABASE
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "hostelcare-devops-lab")


# ---------------------------------------------------------------- database
@contextmanager
def get_db():
    """Open a SQLite connection, commit on success and always close it."""
    conn = sqlite3.connect(app.config["DATABASE"])
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Create the data folder, database file and table if they don't exist."""
    os.makedirs(os.path.dirname(app.config["DATABASE"]), exist_ok=True)
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS maintenance_requests (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT NOT NULL,
                room_number  TEXT NOT NULL,
                category     TEXT NOT NULL,
                description  TEXT NOT NULL,
                priority     TEXT NOT NULL,
                status       TEXT NOT NULL DEFAULT 'Pending',
                created_at   TEXT NOT NULL,
                updated_at   TEXT NOT NULL
            )
            """
        )


def format_request_id(request_id):
    """1 -> 'HM-0001' (friendly ID shown to students)."""
    return f"HM-{request_id:04d}"


def parse_request_id(text):
    """Accept 'HM-0001', 'hm-1' or just '1'. Returns int or None."""
    text = (text or "").strip().upper()
    if text.startswith("HM-"):
        text = text[3:]
    return int(text) if text.isdigit() else None


@app.context_processor
def inject_helpers():
    return {"format_request_id": format_request_id, "current_year": datetime.now().year}


@app.before_request
def ensure_db():
    init_db()


# ------------------------------------------------------------------ routes
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/report")
def report():
    return render_template(
        "report.html", categories=CATEGORIES, priorities=PRIORITIES, form={}
    )


@app.route("/submit_request", methods=["POST"])
def submit_request():
    form = {
        "student_name": request.form.get("student_name", "").strip(),
        "room_number": request.form.get("room_number", "").strip(),
        "category": request.form.get("category", "").strip(),
        "description": request.form.get("description", "").strip(),
        "priority": request.form.get("priority", "Medium").strip(),
    }

    # ---- validation
    errors = []
    if not form["student_name"] or len(form["student_name"]) > 60:
        errors.append("Please enter your name (max 60 characters).")
    if not form["room_number"] or len(form["room_number"]) > 30:
        errors.append("Please enter your block / room number (max 30 characters).")
    if form["category"] not in CATEGORIES:
        errors.append("Please select a valid issue category.")
    if len(form["description"]) < 10 or len(form["description"]) > 500:
        errors.append("Description must be between 10 and 500 characters.")
    if form["priority"] not in PRIORITIES:
        errors.append("Please select a valid priority.")

    if errors:
        for error in errors:
            flash(error, "error")
        return (
            render_template(
                "report.html", categories=CATEGORIES, priorities=PRIORITIES, form=form
            ),
            400,
        )

    # ---- store in SQLite (parameterized query = safe from SQL injection)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO maintenance_requests
                (student_name, room_number, category, description, priority,
                 status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'Pending', ?, ?)
            """,
            (
                form["student_name"],
                form["room_number"],
                form["category"],
                form["description"],
                form["priority"],
                now,
                now,
            ),
        )
        new_id = cursor.lastrowid

    flash(
        f"Request submitted successfully! Your Request ID is {format_request_id(new_id)}. "
        "Save it to track your request.",
        "success",
    )
    return redirect(url_for("track", request_id=format_request_id(new_id)))


@app.route("/track", methods=["GET", "POST"])
def track():
    raw_id = request.values.get("request_id", "").strip()
    found = None
    searched = bool(raw_id)

    if searched:
        request_id = parse_request_id(raw_id)
        if request_id is None:
            flash("Invalid Request ID. Use the format HM-0001.", "error")
        else:
            with get_db() as conn:
                found = conn.execute(
                    "SELECT * FROM maintenance_requests WHERE id = ?", (request_id,)
                ).fetchone()
            if found is None:
                flash(f"No request found with ID {raw_id.upper()}.", "error")

    return render_template(
        "track.html", req=found, request_id=raw_id, statuses=STATUSES, searched=searched
    )


@app.route("/admin")
def admin():
    status_filter = request.args.get("status", "All")
    with get_db() as conn:
        if status_filter in STATUSES:
            rows = conn.execute(
                "SELECT * FROM maintenance_requests WHERE status = ? ORDER BY id DESC",
                (status_filter,),
            ).fetchall()
        else:
            status_filter = "All"
            rows = conn.execute(
                "SELECT * FROM maintenance_requests ORDER BY id DESC"
            ).fetchall()

        counts = {status: 0 for status in STATUSES}
        for row in conn.execute(
            "SELECT status, COUNT(*) AS total FROM maintenance_requests GROUP BY status"
        ):
            counts[row["status"]] = row["total"]

    summary = {"Total": sum(counts.values()), **counts}
    return render_template(
        "admin.html",
        requests=rows,
        summary=summary,
        statuses=STATUSES,
        status_filter=status_filter,
    )


@app.route("/update_status", methods=["POST"])
def update_status():
    request_id = parse_request_id(request.form.get("request_id", ""))
    new_status = request.form.get("status", "").strip()

    if request_id is None or new_status not in STATUSES:
        flash("Invalid request ID or status.", "error")
        return redirect(url_for("admin"))

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.execute(
            "UPDATE maintenance_requests SET status = ?, updated_at = ? WHERE id = ?",
            (new_status, now, request_id),
        )

    if cursor.rowcount == 0:
        flash(f"Request {format_request_id(request_id)} not found.", "error")
    else:
        flash(
            f"Request {format_request_id(request_id)} updated to '{new_status}'.",
            "success",
        )
    return redirect(url_for("admin"))


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
