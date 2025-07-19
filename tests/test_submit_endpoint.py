import json
from pathlib import Path

from time_profiler import create_app, SessionLocal, ActivityLog
from time_profiler.app import load_config


def setup_app(tmp_path):
    SessionLocal.remove()
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


def test_submit_endpoint_with_feedback(tmp_path):
    app = setup_app(tmp_path)
    client = app.test_client()

    config = load_config(Path(app.config["DCRI_CONFIG_PATH"]))
    if not config.get("enableFreeTextFeedback"):
        return

    group_id = config["groups"][0]["id"]
    activity = config["activities"][0]["category"]
    sub_activity = config["activities"][0]["sub_activities"][0]

    feedback = "great work"
    payload = {
        "group_id": group_id,
        "activity": activity,
        "sub_activity": sub_activity,
        "feedback": feedback,
    }
    response = client.post("/api/submit", json=payload)
    assert response.status_code == 200

    session = SessionLocal()
    log = session.query(ActivityLog).first()
    session.close()
    assert log.feedback == feedback


def test_feedback_ignored_when_disabled(tmp_path):
    config_path = tmp_path / "config.json"
    orig = load_config(Path(__file__).resolve().parents[1] / "config" / "dcri_config.json.example")
    orig["enableFreeTextFeedback"] = False
    config_path.write_text(json.dumps(orig))

    SessionLocal.remove()
    db_url = f"sqlite:///{tmp_path}/test.db"
    app = create_app({"TESTING": True, "DATABASE_URL": db_url, "DCRI_CONFIG_PATH": config_path})
    client = app.test_client()

    group_id = orig["groups"][0]["id"]
    activity = orig["activities"][0]["category"]
    sub_activity = orig["activities"][0]["sub_activities"][0]

    payload = {
        "group_id": group_id,
        "activity": activity,
        "sub_activity": sub_activity,
        "feedback": "should not store",
    }
    response = client.post("/api/submit", json=payload)
    assert response.status_code == 200

    session = SessionLocal()
    log = session.query(ActivityLog).first()
    session.close()
    assert log.feedback is None




