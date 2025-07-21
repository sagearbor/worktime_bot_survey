"""Platform-specific adapters for different chatbot platforms."""

from __future__ import annotations

from typing import Dict, Any, Optional
from datetime import datetime
import os
import requests

from .base import ChatbotPlatformAdapter, ChatMessage, ChatResponse


class WebChatAdapter(ChatbotPlatformAdapter):
    """Adapter for web-based chat interface."""
    
    async def send_message(self, user_id: str, response: ChatResponse) -> bool:
        """Send message back to web client (stored for retrieval via API)."""
        # In a real implementation, this would push to a WebSocket or store in a cache
        # For now, we'll just return True to indicate success
        return True
    
    async def parse_message(self, raw_message: Dict[str, Any]) -> ChatMessage:
        """Parse web chat message format."""
        return ChatMessage(
            user_id=raw_message.get("user_id", "anonymous"),
            text=raw_message.get("text", ""),
            timestamp=datetime.fromisoformat(raw_message.get("timestamp", datetime.utcnow().isoformat())),
            platform="web",
            message_type=raw_message.get("message_type"),
            metadata=raw_message.get("metadata", {})
        )
    
    async def authenticate_user(self, raw_message: Dict[str, Any]) -> Optional[str]:
        """Authenticate web user (basic implementation)."""
        user_id = raw_message.get("user_id")
        # In production, this would validate session tokens, etc.
        return user_id if user_id else None


class TeamsAdapter(ChatbotPlatformAdapter):
    """Adapter for Microsoft Teams integration."""
    
    async def send_message(self, user_id: str, response: ChatResponse) -> bool:
        """Send message to Teams user."""
        # TODO: Implement Teams Bot Framework integration
        # This would use the Bot Framework SDK to send messages
        print(f"Teams message to {user_id}: {response.text}")
        return True
    
    async def parse_message(self, raw_message: Dict[str, Any]) -> ChatMessage:
        """Parse Teams activity format."""
        # Teams Bot Framework activity structure
        activity = raw_message
        
        return ChatMessage(
            user_id=activity.get("from", {}).get("id", "unknown"),
            text=activity.get("text", ""),
            timestamp=datetime.fromisoformat(activity.get("timestamp", datetime.utcnow().isoformat())),
            platform="teams",
            metadata={
                "channel_id": activity.get("channelId"),
                "conversation_id": activity.get("conversation", {}).get("id"),
                "activity_id": activity.get("id")
            }
        )
    
    async def authenticate_user(self, raw_message: Dict[str, Any]) -> Optional[str]:
        """Authenticate Teams user from activity."""
        from_user = raw_message.get("from", {})
        user_id = from_user.get("id")
        # Additional Teams-specific authentication could be added here
        return user_id


class SlackAdapter(ChatbotPlatformAdapter):
    """Adapter for Slack integration."""

    def __init__(self, bot_token: str | None = None, default_channel: str | None = None) -> None:
        """Initialize Slack adapter from environment settings."""
        self.bot_token = bot_token or os.getenv("SLACK_BOT_TOKEN")
        if default_channel is not None:
            self.default_channel = default_channel
        else:
            self.default_channel = os.getenv("SLACK_DEFAULT_CHANNEL", "#general")

    async def send_message(self, user_id: str, response: ChatResponse) -> bool:
        """Send message to Slack user."""
        token = self.bot_token
        if not token:
            raise RuntimeError("Slack bot token not configured")

        channel = self.default_channel
        if response.metadata and response.metadata.get("channel"):
            channel = response.metadata["channel"]
        if not channel:
            channel = user_id

        payload = {"channel": channel, "text": response.text}
        url = "https://slack.com/api/chat.postMessage"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        if resp.status_code != 200:
            return False
        data = resp.json()
        return bool(data.get("ok"))
    
    async def parse_message(self, raw_message: Dict[str, Any]) -> ChatMessage:
        """Parse Slack event format."""
        event = raw_message.get("event", {})
        
        return ChatMessage(
            user_id=event.get("user", "unknown"),
            text=event.get("text", ""),
            timestamp=datetime.fromtimestamp(float(event.get("ts", "0"))),
            platform="slack",
            metadata={
                "channel": event.get("channel"),
                "team": raw_message.get("team_id"),
                "event_id": raw_message.get("event_id")
            }
        )
    
    async def authenticate_user(self, raw_message: Dict[str, Any]) -> Optional[str]:
        """Authenticate Slack user from event."""
        event = raw_message.get("event", {})
        user_id = event.get("user")
        # Slack token validation could be added here
        return user_id
