from pathlib import Path

from datetime import datetime

from time_profiler import create_app, SessionLocal, ActivityLog
from time_profiler.app import load_config


def setup_app(tmp_path):
    db_url = f"sqlite:///{tmp_path}/test.db"
    app = create_app({"TESTING": True, "DATABASE_URL": db_url})
    return app


def test_results_endpoint_empty(tmp_path):
    app = setup_app(tmp_path)
    client = app.test_client()

    response = client.get("/api/results")
    assert response.status_code == 200
    assert response.get_json() == []


def test_results_endpoint_with_data(tmp_path):
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
    # Submit two logs
    client.post("/api/submit", json=payload)
    client.post("/api/submit", json=payload)

    response = client.get("/api/results")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert data[0]["group_id"] == group_id
    assert data[0]["activity"] == activity
    assert data[0]["count"] == 2


def test_results_endpoint_filters(tmp_path):
    app = setup_app(tmp_path)
    client = app.test_client()

    config = load_config(Path(app.config["DCRI_CONFIG_PATH"]))
    group1 = config["groups"][0]["id"]
    group2 = config["groups"][1]["id"]
    activity = config["activities"][0]["category"]
    sub_activity = config["activities"][0]["sub_activities"][0]

    session = SessionLocal()
    session.add(
        ActivityLog(
            group_id=group1,
            activity=activity,
            sub_activity=sub_activity,
            timestamp=datetime(2022, 1, 1),
        )
    )
    session.add(
        ActivityLog(
            group_id=group2,
            activity=activity,
            sub_activity=sub_activity,
            timestamp=datetime(2022, 1, 5),
        )
    )
    session.commit()
    session.close()

    resp = client.get(f"/api/results?group_id={group1}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 1
    assert data[0]["group_id"] == group1

    resp = client.get("/api/results?start_date=2022-01-03&end_date=2022-01-06")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 1
    assert data[0]["group_id"] == group2
