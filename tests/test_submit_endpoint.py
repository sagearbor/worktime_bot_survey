import json
from pathlib import Path

from time_profiler import create_app, SessionLocal, ActivityLog
from time_profiler.app import load_config


def setup_app(tmp_path):
    db_url = f"sqlite:///{tmp_path}/test.db"
    app = create_app({"TESTING": True, "DATABASE_URL": db_url})
    return app


def test_submit_endpoint_valid(tmp_path):
    app = setup_app(tmp_path)
    client = app.test_client()

    config = load_config(Path(app.config["DCRI_CONFIG_PATH"]))
    group_id = config["groups"][0]["id"]
    activity = config["activities"][0]["category"]
    sub_activity = config["activities"][0]["sub_activities"][0]

    payload = {
        "group_id": group_id,
        "activity": activity,
        "sub_activity": sub_activity,
    }
    response = client.post("/api/submit", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"

    session = SessionLocal()
    logs = session.query(ActivityLog).all()
    session.close()
    assert len(logs) == 1
    assert logs[0].group_id == group_id


def test_submit_endpoint_invalid_group(tmp_path):
    app = setup_app(tmp_path)
    client = app.test_client()

    config = load_config(Path(app.config["DCRI_CONFIG_PATH"]))
    activity = config["activities"][0]["category"]
    sub_activity = config["activities"][0]["sub_activities"][0]

    payload = {
        "group_id": "invalid",
        "activity": activity,
        "sub_activity": sub_activity,
    }
    response = client.post("/api/submit", json=payload)
    assert response.status_code == 400




