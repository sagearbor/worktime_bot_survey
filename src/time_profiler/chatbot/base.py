"""Base chatbot framework with platform abstraction layer."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import json
import logging

from ..models import (
    ChatbotFeedback,
    TimeAllocation,
    ProblemIdentification,
)
from ..app import SessionLocal
from .nlp_processor import NLPProcessor


@dataclass
class ChatMessage:
    """Represents a chat message with platform-agnostic structure."""
    user_id: str
    text: str
    timestamp: datetime
    platform: str
    message_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass 
class ChatResponse:
    """Represents a chatbot response."""
    text: str
    message_type: Optional[str] = None
    suggested_actions: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class ChatbotPlatformAdapter(ABC):
    """Abstract base class for platform-specific chatbot adapters."""
    
    @abstractmethod
    async def send_message(self, user_id: str, response: ChatResponse) -> bool:
        """Send a message to the user on the platform."""
        pass
    
    @abstractmethod
    async def parse_message(self, raw_message: Dict[str, Any]) -> ChatMessage:
        """Parse platform-specific message format into ChatMessage."""
        pass
    
    @abstractmethod
    async def authenticate_user(self, raw_message: Dict[str, Any]) -> Optional[str]:
        """Extract and validate user identity from platform message."""
        pass


class ConversationState:
    """Manages conversation state for individual users."""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.current_flow: Optional[str] = None
        self.context: Dict[str, Any] = {}
        self.last_activity: datetime = datetime.utcnow()
    
    def update_context(self, key: str, value: Any):
        """Update conversation context."""
        self.context[key] = value
        self.last_activity = datetime.utcnow()
    
    def get_context(self, key: str, default=None):
        """Get value from conversation context."""
        return self.context.get(key, default)
    
    def reset(self):
        """Reset conversation state."""
        self.current_flow = None
        self.context = {}
        self.last_activity = datetime.utcnow()


class BaseChatbotService:
    """Core chatbot service with platform abstraction."""

    def __init__(self):
        self.adapters: Dict[str, ChatbotPlatformAdapter] = {}
        self.conversation_states: Dict[str, ConversationState] = {}
        self.nlp = NLPProcessor()
        self.logger = logging.getLogger("chatbot")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        self.message_handlers: Dict[str, callable] = {
            "time_allocation": self._handle_time_allocation,
            "problem_report": self._handle_problem_report,
            "success_story": self._handle_success_story,
            "general": self._handle_general_query
        }
    
    def register_adapter(self, platform: str, adapter: ChatbotPlatformAdapter):
        """Register a platform adapter."""
        self.adapters[platform] = adapter
    
    def get_conversation_state(self, user_id: str) -> ConversationState:
        """Get or create conversation state for user."""
        if user_id not in self.conversation_states:
            self.conversation_states[user_id] = ConversationState(user_id)
        return self.conversation_states[user_id]
    
    async def process_message(self, platform: str, raw_message: Dict[str, Any]) -> Optional[ChatResponse]:
        """Process incoming message from any platform."""
        if platform not in self.adapters:
            raise ValueError(f"Unknown platform: {platform}")

        adapter = self.adapters[platform]
        
        # Authenticate and parse message
        user_id = await adapter.authenticate_user(raw_message)
        if not user_id:
            return ChatResponse("Sorry, I couldn't authenticate your identity.")

        message = await adapter.parse_message(raw_message)
        self.logger.info("Received message from %s on %s", user_id, platform)
        
        # Store the feedback in database
        await self._store_chatbot_feedback(message)
        
        # Determine message type and route to appropriate handler
        message_type = self._classify_message(message.text)
        handler = self.message_handlers.get(message_type, self.message_handlers["general"])
        
        try:
            response = await handler(message)
        except Exception as e:
            self.logger.exception("Handler error")
            response = ChatResponse("Sorry, something went wrong processing your message.")

        try:
            await adapter.send_message(user_id, response)
        except Exception as e:
            self.logger.exception("Send message error")

        return response
    
    def _classify_message(self, text: str) -> str:
        """Classify message type based on content analysis."""
        text_lower = text.lower()
        
        # Simple keyword-based classification (can be enhanced with ML)
        time_keywords = ["spent", "hours", "time", "allocation", "working on", "% on"]
        problem_keywords = ["problem", "issue", "frustrating", "difficult", "broken", "bug"]
        success_keywords = ["success", "achievement", "completed", "good", "well", "productive"]
        
        if any(keyword in text_lower for keyword in time_keywords):
            return "time_allocation"
        elif any(keyword in text_lower for keyword in problem_keywords):
            return "problem_report"
        elif any(keyword in text_lower for keyword in success_keywords):
            return "success_story"
        else:
            return "general"
    
    async def _store_chatbot_feedback(self, message: ChatMessage):
        """Store chatbot feedback in database."""
        session = SessionLocal()
        try:
            feedback = ChatbotFeedback(
                user_id=message.user_id,
                message_text=message.text,
                message_type=message.message_type or "general",
                timestamp=message.timestamp
            )
            session.add(feedback)
            session.commit()
            self.logger.info("Stored feedback from %s", message.user_id)
        except Exception as e:
            session.rollback()
            self.logger.exception("Error storing chatbot feedback")
        finally:
            session.close()
    
    async def _handle_time_allocation(self, message: ChatMessage) -> ChatResponse:
        """Handle time allocation related messages."""
        state = self.get_conversation_state(message.user_id)
        
        # Conversation flow
        if state.current_flow != "time_allocation":
            state.current_flow = "time_allocation"
            return ChatResponse(
                "I'll help you log your time allocation. Please provide the approximate percentage of time you spent on each activity.",
                message_type="time_allocation",
                suggested_actions=["60% meetings, 30% research, 10% admin"]
            )

        allocations = self.nlp.parse_time_allocation(message.text)
        if not allocations:
            return ChatResponse(
                "Sorry, I couldn't understand your allocation. Please use a format like '60% meetings, 30% research'.",
                message_type="time_allocation"
            )

        session = SessionLocal()
        try:
            entry = TimeAllocation(
                group_id=message.user_id,
                activities=allocations
            )
            session.add(entry)
            session.commit()
            response = ChatResponse(
                "Thank you for sharing your time allocation. I've recorded this information.",
                message_type="time_allocation"
            )
        except Exception as e:
            session.rollback()
            self.logger.exception("Error storing time allocation")
            response = ChatResponse("There was an error recording your allocation.")
        finally:
            session.close()
            state.reset()

        return response
    
    async def _handle_problem_report(self, message: ChatMessage) -> ChatResponse:
        """Handle problem reporting messages."""
        state = self.get_conversation_state(message.user_id)

        if state.current_flow != "problem_report":
            state.current_flow = "problem_report"
            return ChatResponse(
                "I'm sorry to hear you're facing issues. Could you briefly describe the problem?",
                message_type="problem_report",
            )

        # Use ProblemAggregator to cluster similar issues and track frequency
        from ..ai_insights import ProblemAggregator

        aggregator = ProblemAggregator()

        try:
            problem = aggregator.record_problem(message.text)
            response = ChatResponse(
                "Thanks, I've logged this problem for review.",
                message_type="problem_report",
            )
        except Exception as e:
            self.logger.exception("Error storing problem report")
            response = ChatResponse("There was an error recording the problem.")
        finally:
            state.reset()

        return response
    
    async def _handle_success_story(self, message: ChatMessage) -> ChatResponse:
        """Handle success story messages."""
        state = self.get_conversation_state(message.user_id)

        if state.current_flow != "success_story":
            state.current_flow = "success_story"
            return ChatResponse(
                "I'd love to hear about your success! Please tell me what went well.",
                message_type="success_story",
            )

        state.reset()
        return ChatResponse(
            "Thanks for sharing your success story!",
            message_type="success_story",
        )
    
    async def _handle_general_query(self, message: ChatMessage) -> ChatResponse:
        """Handle general queries."""
        return ChatResponse(
            "I'm here to help you track your time allocation and identify areas for improvement. You can tell me about:\n"
            "• How you spend your time each week\n"
            "• Problems or frustrations you're facing\n" 
            "• Success stories and what's working well\n\n"
            "What would you like to share today?",
            message_type="general"
        )