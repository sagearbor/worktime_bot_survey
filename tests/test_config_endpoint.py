import json
from time_profiler import create_app


def test_get_config_endpoint(tmp_path):
    app = create_app({"TESTING": True})
    client = app.test_client()

    response = client.get("/api/config")
    assert response.status_code == 200

    data = response.get_json()
    assert isinstance(data, dict)
    assert "groups" in data
    assert "activities" in data
    assert "enableFreeTextFeedback" in data
