"""
Message Classes for Agent Communication

Provides comprehensive message types and utilities for multi-agent communication:
- Base message structure
- Typed messages for different protocols
- Message routing and filtering
- Serialization support
"""

from __future__ import annotations

import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class MessageType(str, Enum):
    """Types of messages in the system"""

    # General messages
    DIRECT = "direct"
    BROADCAST = "broadcast"

    # Contract Net Protocol messages
    CNP_ANNOUNCE = "cnp_announce"
    CNP_BID = "cnp_bid"
    CNP_AWARD = "cnp_award"
    CNP_REJECT = "cnp_reject"
    CNP_RESULT = "cnp_result"

    # Blackboard messages
    BB_WRITE = "bb_write"
    BB_READ = "bb_read"
    BB_UPDATE = "bb_update"
    BB_DELETE = "bb_delete"
    BB_NOTIFY = "bb_notify"

    # Pub/Sub messages
    PUBSUB_PUBLISH = "pubsub_publish"
    PUBSUB_SUBSCRIBE = "pubsub_subscribe"
    PUBSUB_UNSUBSCRIBE = "pubsub_unsubscribe"

    # System messages
    HEARTBEAT = "heartbeat"
    ERROR = "error"
    ACK = "ack"


class MessagePriority(int, Enum):
    """Message priority levels"""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class Message(BaseModel):
    """
    Base message class for all agent communication

    Attributes:
        id: Unique message identifier
        type: Type of message
        sender_id: ID of sending agent
        receiver_id: ID of receiving agent (None for broadcast)
        content: Message payload
        metadata: Additional message metadata
        priority: Message priority level
        timestamp: Message creation time
        expires_at: Optional expiration timestamp
        reply_to: ID of message this is replying to
        requires_ack: Whether acknowledgment is required
    """

    id: UUID = Field(default_factory=uuid4)
    type: MessageType
    sender_id: UUID
    receiver_id: Optional[UUID] = None
    content: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    reply_to: Optional[UUID] = None
    requires_ack: bool = False

    def is_expired(self) -> bool:
        """Check if message has expired"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    def is_broadcast(self) -> bool:
        """Check if this is a broadcast message"""
        return self.receiver_id is None or self.type == MessageType.BROADCAST

    def create_reply(
        self,
        content: Dict[str, Any],
        message_type: Optional[MessageType] = None,
    ) -> Message:
        """
        Create a reply to this message

        Args:
            content: Reply content
            message_type: Type of reply (defaults to same type)

        Returns:
            New message as reply
        """
        return Message(
            type=message_type or self.type,
            sender_id=self.receiver_id or self.sender_id,
            receiver_id=self.sender_id,
            content=content,
            reply_to=self.id,
            priority=self.priority,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        data = self.model_dump()
        # Convert UUIDs to strings for serialization
        data["id"] = str(data["id"])
        data["sender_id"] = str(data["sender_id"])
        if data["receiver_id"]:
            data["receiver_id"] = str(data["receiver_id"])
        if data["reply_to"]:
            data["reply_to"] = str(data["reply_to"])
        if data["timestamp"]:
            data["timestamp"] = data["timestamp"].isoformat()
        if data["expires_at"]:
            data["expires_at"] = data["expires_at"].isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Message:
        """Create message from dictionary"""
        # Convert string UUIDs back to UUID objects
        if isinstance(data.get("id"), str):
            data["id"] = UUID(data["id"])
        if isinstance(data.get("sender_id"), str):
            data["sender_id"] = UUID(data["sender_id"])
        if data.get("receiver_id") and isinstance(data["receiver_id"], str):
            data["receiver_id"] = UUID(data["receiver_id"])
        if data.get("reply_to") and isinstance(data["reply_to"], str):
            data["reply_to"] = UUID(data["reply_to"])
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        if data.get("expires_at") and isinstance(data["expires_at"], str):
            data["expires_at"] = datetime.fromisoformat(data["expires_at"])
        return cls(**data)

    def to_json(self) -> str:
        """Convert message to JSON string"""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> Message:
        """Create message from JSON string"""
        return cls.from_dict(json.loads(json_str))


class ContractNetMessage(Message):
    """
    Specialized message for Contract Net Protocol

    Additional fields for CNP-specific data
    """

    task_id: Optional[UUID] = None
    task_description: Optional[str] = None
    bid_amount: Optional[float] = None
    estimated_duration: Optional[float] = None
    required_capabilities: Set[str] = Field(default_factory=set)
    deadline: Optional[datetime] = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: MessageType) -> MessageType:
        """Ensure message type is CNP-related"""
        cnp_types = {
            MessageType.CNP_ANNOUNCE,
            MessageType.CNP_BID,
            MessageType.CNP_AWARD,
            MessageType.CNP_REJECT,
            MessageType.CNP_RESULT,
        }
        if v not in cnp_types:
            raise ValueError(f"Invalid CNP message type: {v}")
        return v


class BlackboardMessage(Message):
    """
    Specialized message for Blackboard System

    Additional fields for blackboard operations
    """

    pattern: Optional[str] = None
    pattern_type: Optional[str] = None
    match_criteria: Dict[str, Any] = Field(default_factory=dict)
    data_key: Optional[str] = None
    data_value: Optional[Any] = None
    data_tags: Set[str] = Field(default_factory=set)

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: MessageType) -> MessageType:
        """Ensure message type is blackboard-related"""
        bb_types = {
            MessageType.BB_WRITE,
            MessageType.BB_READ,
            MessageType.BB_UPDATE,
            MessageType.BB_DELETE,
            MessageType.BB_NOTIFY,
        }
        if v not in bb_types:
            raise ValueError(f"Invalid blackboard message type: {v}")
        return v


class PubSubMessage(Message):
    """
    Specialized message for Pub/Sub Protocol

    Additional fields for topic-based messaging
    """

    topic: str
    subtopics: List[str] = Field(default_factory=list)
    tags: Set[str] = Field(default_factory=set)
    retain: bool = False  # Whether to retain message for future subscribers

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: MessageType) -> MessageType:
        """Ensure message type is pubsub-related"""
        pubsub_types = {
            MessageType.PUBSUB_PUBLISH,
            MessageType.PUBSUB_SUBSCRIBE,
            MessageType.PUBSUB_UNSUBSCRIBE,
        }
        if v not in pubsub_types:
            raise ValueError(f"Invalid pub/sub message type: {v}")
        return v


class MessageFilter(BaseModel):
    """
    Filter for selecting messages

    Supports filtering by:
    - Message type
    - Sender/receiver
    - Priority
    - Time range
    - Content matching
    - Custom predicates
    """

    types: Optional[Set[MessageType]] = None
    sender_ids: Optional[Set[UUID]] = None
    receiver_ids: Optional[Set[UUID]] = None
    min_priority: Optional[MessagePriority] = None
    after: Optional[datetime] = None
    before: Optional[datetime] = None
    content_match: Optional[Dict[str, Any]] = None
    exclude_expired: bool = True

    def matches(self, message: Message) -> bool:
        """
        Check if message matches filter criteria

        Args:
            message: Message to check

        Returns:
            True if message matches all criteria
        """
        # Check expiration
        if self.exclude_expired and message.is_expired():
            return False

        # Check type
        if self.types is not None and message.type not in self.types:
            return False

        # Check sender
        if self.sender_ids is not None and message.sender_id not in self.sender_ids:
            return False

        # Check receiver
        if self.receiver_ids is not None:
            if message.receiver_id is None or message.receiver_id not in self.receiver_ids:
                return False

        # Check priority
        if self.min_priority is not None and message.priority < self.min_priority:
            return False

        # Check time range
        if self.after is not None and message.timestamp < self.after:
            return False

        if self.before is not None and message.timestamp > self.before:
            return False

        # Check content matching
        if self.content_match is not None:
            for key, value in self.content_match.items():
                if key not in message.content or message.content[key] != value:
                    return False

        return True


class MessageQueue(BaseModel):
    """
    Priority queue for messages

    Supports:
    - Priority-based ordering
    - FIFO within same priority
    - Filtering
    - Size limits
    """

    messages: List[Message] = Field(default_factory=list)
    max_size: int = 1000
    auto_remove_expired: bool = True

    class Config:
        arbitrary_types_allowed = True

    def push(self, message: Message) -> None:
        """
        Add message to queue

        Args:
            message: Message to add

        Raises:
            ValueError: If queue is full
        """
        if len(self.messages) >= self.max_size:
            raise ValueError(f"Queue is full (max size: {self.max_size})")

        # Insert in priority order (higher priority first)
        # Within same priority, maintain FIFO (append at end)
        insert_idx = len(self.messages)
        for i, msg in enumerate(self.messages):
            if message.priority > msg.priority:
                insert_idx = i
                break

        self.messages.insert(insert_idx, message)

    def pop(self, filter_criteria: Optional[MessageFilter] = None) -> Optional[Message]:
        """
        Remove and return highest priority message matching filter

        Args:
            filter_criteria: Optional filter to apply

        Returns:
            Message or None if queue is empty or no match
        """
        if self.auto_remove_expired:
            self._remove_expired()

        if not self.messages:
            return None

        if filter_criteria is None:
            return self.messages.pop(0)

        # Find first matching message
        for i, msg in enumerate(self.messages):
            if filter_criteria.matches(msg):
                return self.messages.pop(i)

        return None

    def peek(self, filter_criteria: Optional[MessageFilter] = None) -> Optional[Message]:
        """
        Return highest priority message without removing

        Args:
            filter_criteria: Optional filter to apply

        Returns:
            Message or None if queue is empty or no match
        """
        if self.auto_remove_expired:
            self._remove_expired()

        if not self.messages:
            return None

        if filter_criteria is None:
            return self.messages[0]

        # Find first matching message
        for msg in self.messages:
            if filter_criteria.matches(msg):
                return msg

        return None

    def get_all(self, filter_criteria: Optional[MessageFilter] = None) -> List[Message]:
        """
        Get all messages matching filter (without removing)

        Args:
            filter_criteria: Optional filter to apply

        Returns:
            List of matching messages
        """
        if self.auto_remove_expired:
            self._remove_expired()

        if filter_criteria is None:
            return self.messages.copy()

        return [msg for msg in self.messages if filter_criteria.matches(msg)]

    def _remove_expired(self) -> None:
        """Remove all expired messages"""
        self.messages = [msg for msg in self.messages if not msg.is_expired()]

    def size(self) -> int:
        """Get current queue size"""
        if self.auto_remove_expired:
            self._remove_expired()
        return len(self.messages)

    def clear(self) -> None:
        """Clear all messages from queue"""
        self.messages.clear()
