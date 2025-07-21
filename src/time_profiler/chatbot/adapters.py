"""Platform-specific adapters for different chatbot platforms."""

from __future__ import annotations

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import os
import json
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

    def __init__(self, app_id: Optional[str] = None, app_password: Optional[str] = None):
        config = {}
        try:
            cfg_path = Path(__file__).resolve().parents[2] / "config" / "dcri_config.json"
            with cfg_path.open("r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception:
            pass

        teams_cfg = config.get("teams", {}) if isinstance(config, dict) else {}
        self.app_id = app_id or os.getenv("TEAMS_APP_ID") or teams_cfg.get("app_id")
        self.app_password = (
            app_password or os.getenv("TEAMS_APP_PASSWORD") or teams_cfg.get("app_password")
        )
        self._access_token: Optional[str] = None
        self._token_expiry: datetime = datetime.utcnow()
        self._conversations: Dict[str, Dict[str, str]] = {}

    async def send_message(self, user_id: str, response: ChatResponse) -> bool:
        """Send message to Teams user."""
        convo = self._conversations.get(user_id)
        if not convo:
            return False

        token = self._get_access_token()
        if not token:
            return False

        url = f"{convo['service_url']}/v3/conversations/{convo['conversation_id']}/activities"
        headers = {"Authorization": f"Bearer {token}"}
        payload = {"type": "message", "text": response.text}

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=5)
            return 200 <= resp.status_code < 300
        except Exception:
            return False

    async def parse_message(self, raw_message: Dict[str, Any]) -> ChatMessage:
        """Parse Teams activity format."""
        # Teams Bot Framework activity structure
        activity = raw_message

        user_id = activity.get("from", {}).get("id", "unknown")
        conv_id = activity.get("conversation", {}).get("id")
        service_url = activity.get("serviceUrl")
        if user_id and conv_id and service_url:
            self._conversations[user_id] = {
                "conversation_id": conv_id,
                "service_url": service_url,
            }

        return ChatMessage(
            user_id=user_id,
            text=activity.get("text", ""),
            timestamp=datetime.fromisoformat(activity.get("timestamp", datetime.utcnow().isoformat())),
            platform="teams",
            metadata={
                "channel_id": activity.get("channelId"),
                "conversation_id": activity.get("conversation", {}).get("id"),
                "activity_id": activity.get("id")
            }
        )

    def _get_access_token(self) -> Optional[str]:
        """Retrieve (and cache) a Bot Framework access token."""
        if self._access_token and datetime.utcnow() < self._token_expiry:
            return self._access_token

        if not self.app_id or not self.app_password:
            return None

        url = "https://login.microsoftonline.com/botframework.com/oauth2/v2.0/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.app_id,
            "client_secret": self.app_password,
            "scope": "https://api.botframework.com/.default",
        }

        try:
            resp = requests.post(url, data=data, timeout=5)
            resp.raise_for_status()
            payload = resp.json()
            self._access_token = payload.get("access_token")
            expires = int(payload.get("expires_in", 3600))
            self._token_expiry = datetime.utcnow() + timedelta(seconds=expires - 60)
        except Exception:
            self._access_token = None

        return self._access_token
    
    async def authenticate_user(self, raw_message: Dict[str, Any]) -> Optional[str]:
        """Authenticate Teams user from activity."""
        from_user = raw_message.get("from", {})
        user_id = from_user.get("id")
        # Additional Teams-specific authentication could be added here
        return user_id


class SlackAdapter(ChatbotPlatformAdapter):
    """Adapter for Slack integration."""
    
    async def send_message(self, user_id: str, response: ChatResponse) -> bool:
        """Send message to Slack user."""
        # TODO: Implement Slack Web API integration
        print(f"Slack message to {user_id}: {response.text}")
        return True
    
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
