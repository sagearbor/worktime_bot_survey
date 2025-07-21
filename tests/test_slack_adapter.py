import asyncio
from unittest.mock import patch

from time_profiler.chatbot.adapters import SlackAdapter
from time_profiler.chatbot.base import ChatResponse


def test_slack_send_message_success():
    adapter = SlackAdapter(bot_token="xoxb-test", default_channel="")
    response = ChatResponse("hi")
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"ok": True}
        result = asyncio.run(adapter.send_message("U123", response))
        assert result is True
        args, kwargs = mock_post.call_args
        assert args[0] == "https://slack.com/api/chat.postMessage"
        headers = kwargs["headers"]
        assert headers["Authorization"] == "Bearer xoxb-test"
        payload = kwargs["json"]
        assert payload["channel"] == "U123"
        assert payload["text"] == "hi"


def test_slack_send_message_failure():
    adapter = SlackAdapter(bot_token="xoxb-test", default_channel="")
    response = ChatResponse("hi")
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"ok": False}
        result = asyncio.run(adapter.send_message("U123", response))
        assert result is False

