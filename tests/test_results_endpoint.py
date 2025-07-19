from pathlib import Path

from time_profiler import create_app
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
