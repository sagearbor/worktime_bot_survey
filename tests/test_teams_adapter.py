import asyncio
from unittest.mock import patch
from time_profiler.chatbot.adapters import TeamsAdapter, ChatResponse


def test_send_message_calls_api(monkeypatch):
    adapter = TeamsAdapter(app_id="id", app_password="pw")
    adapter._conversations["u1"] = {
        "conversation_id": "conv",
        "service_url": "https://service"
    }

    token_payload = {"access_token": "tok", "expires_in": 3600}

    calls = {}

    def fake_post(url, *args, **kwargs):
        if url.startswith("https://login.microsoftonline.com"):
            calls["token"] = True
            class Resp:
                status_code = 200
                def json(self):
                    return token_payload
                def raise_for_status(self):
                    pass
            return Resp()
        else:
            calls["message"] = {
                "url": url,
                "headers": kwargs.get("headers"),
                "json": kwargs.get("json")
            }
            class Resp:
                status_code = 200
            return Resp()

    monkeypatch.setattr("time_profiler.chatbot.adapters.requests.post", fake_post)

    result = asyncio.run(adapter.send_message("u1", ChatResponse("hi")))

    assert result is True
    assert "token" in calls
    assert "message" in calls
    assert calls["message"]["json"]["text"] == "hi"

