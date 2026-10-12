"""
Automated tests for HostelCare.
Run with:  python -m pytest test_app.py

Every test uses a brand-new temporary SQLite database, so the tests never
depend on (or modify) the real data/hostel_maintenance.db file.
"""

import sqlite3

import pytest

from app import app, init_db


@pytest.fixture
def client(tmp_path):
    app.config["TESTING"] = True
    app.config["DATABASE"] = str(tmp_path / "test_hostel_maintenance.db")
    init_db()
    with app.test_client() as client:
        yield client


def submit_sample(client, **overrides):
    data = {
        "student_name": "Vijay Kumar",
        "room_number": "Block A - 214",
        "category": "Electrical",
        "description": "Ceiling fan is not working since yesterday.",
        "priority": "High",
    }
    data.update(overrides)
    return client.post("/submit_request", data=data)


def fetch_all():
    conn = sqlite3.connect(app.config["DATABASE"])
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM maintenance_requests").fetchall()
    conn.close()
    return rows


def test_app_starts():
    assert app is not None
    assert app.name == "app"


def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"HostelCare" in response.data


def test_report_page(client):
    response = client.get("/report")
    assert response.status_code == 200
    assert b"Report a Maintenance Issue" in response.data


def test_track_page(client):
    assert client.get("/track").status_code == 200


def test_admin_page(client):
    response = client.get("/admin")
    assert response.status_code == 200
    assert b"Admin Dashboard" in response.data


def test_submit_request_and_store_in_sqlite(client):
    response = submit_sample(client)
    assert response.status_code == 302          # redirected to the track page
    assert "HM-0001" in response.headers["Location"]

    rows = fetch_all()
    assert len(rows) == 1
    assert rows[0]["student_name"] == "Vijay Kumar"
    assert rows[0]["category"] == "Electrical"
    assert rows[0]["priority"] == "High"
    assert rows[0]["status"] == "Pending"


def test_success_message_shows_request_id(client):
    response = client.post(
        "/submit_request",
        data={
            "student_name": "Asha",
            "room_number": "B-101",
            "category": "Plumbing",
            "description": "Water is leaking from the bathroom tap.",
            "priority": "Medium",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Request submitted successfully" in response.data
    assert b"HM-0001" in response.data


def test_invalid_request_is_rejected(client):
    response = submit_sample(client, category="Spaceship", description="short")
    assert response.status_code == 400
    assert len(fetch_all()) == 0


def test_track_existing_request(client):
    submit_sample(client)
    response = client.post("/track", data={"request_id": "HM-0001"})
    assert response.status_code == 200
    assert b"Block A - 214" in response.data
    assert b"Pending" in response.data


def test_track_unknown_request(client):
    response = client.post("/track", data={"request_id": "HM-9999"})
    assert b"No request found" in response.data


def test_admin_shows_database_records(client):
    submit_sample(client)
    response = client.get("/admin")
    assert b"HM-0001" in response.data
    assert b"Ceiling fan is not working" in response.data


def test_update_status_modifies_database(client):
    submit_sample(client)
    response = client.post("/update_status", data={"request_id": "1", "status": "Assigned"})
    assert response.status_code == 302
    assert fetch_all()[0]["status"] == "Assigned"

    client.post("/update_status", data={"request_id": "1", "status": "Resolved"})
    assert fetch_all()[0]["status"] == "Resolved"


def test_update_status_rejects_invalid_status(client):
    submit_sample(client)
    client.post("/update_status", data={"request_id": "1", "status": "Deleted"})
    assert fetch_all()[0]["status"] == "Pending"
