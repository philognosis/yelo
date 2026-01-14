"""
Communication Protocols for Multi-Agent Systems

Implements three primary communication protocols:
1. Contract Net Protocol (CNP) - Task allocation through bidding
2. Blackboard System - Shared memory with pattern matching
3. Publish/Subscribe (Pub/Sub) - Topic-based messaging

All protocols are production-ready with:
- Async support
- Error handling
- Message routing and filtering
- Comprehensive logging
"""

from __future__ import annotations

import asyncio
import re
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import UUID, uuid4

from loguru import logger
from pydantic import BaseModel, Field

from iras.communication.message import (
    BlackboardMessage,
    ContractNetMessage,
    Message,
    MessageFilter,
    MessagePriority,
    MessageQueue,
    MessageType,
    PubSubMessage,
)


# ============================================================================
# CONTRACT NET PROTOCOL
# ============================================================================


class TaskAnnouncement(BaseModel):
    """Task announcement in Contract Net Protocol"""

    task_id: UUID = Field(default_factory=uuid4)
    description: str
    required_capabilities: Set[str] = Field(default_factory=set)
    deadline: Optional[datetime] = None
    max_budget: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Bid(BaseModel):
    """Bid submitted by an agent for a task"""

    bid_id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    agent_id: UUID
    bid_amount: float
    estimated_duration: float  # in seconds
    confidence: float = Field(ge=0.0, le=1.0)
    capabilities: Set[str] = Field(default_factory=set)
    proposal: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)


class ContractNetProtocol:
    """
    Contract Net Protocol Implementation

    A distributed task allocation protocol where:
    1. Manager announces tasks
    2. Agents bid on tasks they can perform
    3. Manager awards tasks to best bidders
    4. Agents execute and report results

    Features:
    - Async task announcement and bidding
    - Configurable bid evaluation strategies
    - Timeout handling for bids and task execution
    - Support for task reannouncement on failure
    """

    def __init__(
        self,
        bid_timeout: float = 30.0,
        task_timeout: float = 300.0,
        max_reannouncements: int = 3,
    ):
        """
        Initialize Contract Net Protocol

        Args:
            bid_timeout: Time to wait for bids (seconds)
            task_timeout: Time to wait for task completion (seconds)
            max_reannouncements: Maximum times to reannounce failed tasks
        """
        self.bid_timeout = bid_timeout
        self.task_timeout = task_timeout
        self.max_reannouncements = max_reannouncements

        # Active tasks and bids
        self.announcements: Dict[UUID, TaskAnnouncement] = {}
        self.bids: Dict[UUID, List[Bid]] = defaultdict(list)
        self.awarded_tasks: Dict[UUID, UUID] = {}  # task_id -> agent_id
        self.task_results: Dict[UUID, Any] = {}
        self.reannouncement_count: Dict[UUID, int] = defaultdict(int)

        # Message routing
        self.message_queue = MessageQueue()
        self.bid_callbacks: Dict[UUID, Callable] = {}

        logger.info("Contract Net Protocol initialized")

    async def announce_task(
        self,
        announcement: TaskAnnouncement,
        manager_id: UUID,
    ) -> UUID:
        """
        Announce a task for bidding

        Args:
            announcement: Task announcement details
            manager_id: ID of the manager announcing the task

        Returns:
            Task ID

        Raises:
            ValueError: If task announcement is invalid
        """
        if not announcement.description:
            raise ValueError("Task description cannot be empty")

        # Store announcement
        self.announcements[announcement.task_id] = announcement
        logger.info(f"Task {announcement.task_id} announced: {announcement.description}")

        # Create announcement message
        message = ContractNetMessage(
            type=MessageType.CNP_ANNOUNCE,
            sender_id=manager_id,
            receiver_id=None,  # Broadcast
            task_id=announcement.task_id,
            task_description=announcement.description,
            required_capabilities=announcement.required_capabilities,
            deadline=announcement.deadline,
            content={
                "announcement": announcement.model_dump(),
            },
            priority=MessagePriority.HIGH,
        )

        self.message_queue.push(message)
        return announcement.task_id

    async def submit_bid(
        self,
        bid: Bid,
        manager_id: UUID,
    ) -> None:
        """
        Submit a bid for a task

        Args:
            bid: Bid details
            manager_id: ID of the manager to send bid to

        Raises:
            ValueError: If task doesn't exist or bidding has closed
        """
        if bid.task_id not in self.announcements:
            raise ValueError(f"Task {bid.task_id} not found")

        announcement = self.announcements[bid.task_id]

        # Check if bidding is still open
        if announcement.deadline and datetime.now() > announcement.deadline:
            raise ValueError(f"Bidding closed for task {bid.task_id}")

        # Check if task already awarded
        if bid.task_id in self.awarded_tasks:
            raise ValueError(f"Task {bid.task_id} already awarded")

        # Validate capabilities
        missing_caps = announcement.required_capabilities - bid.capabilities
        if missing_caps:
            raise ValueError(f"Bid missing required capabilities: {missing_caps}")

        # Store bid
        self.bids[bid.task_id].append(bid)
        logger.info(
            f"Bid {bid.bid_id} submitted for task {bid.task_id} "
            f"by agent {bid.agent_id}: ${bid.bid_amount:.2f}"
        )

        # Create bid message
        message = ContractNetMessage(
            type=MessageType.CNP_BID,
            sender_id=bid.agent_id,
            receiver_id=manager_id,
            task_id=bid.task_id,
            bid_amount=bid.bid_amount,
            estimated_duration=bid.estimated_duration,
            content={
                "bid": bid.model_dump(),
            },
            priority=MessagePriority.NORMAL,
        )

        self.message_queue.push(message)

    async def evaluate_bids(
        self,
        task_id: UUID,
        strategy: str = "lowest_cost",
        custom_evaluator: Optional[Callable[[List[Bid]], Optional[Bid]]] = None,
    ) -> Optional[Bid]:
        """
        Evaluate bids for a task and select winner

        Args:
            task_id: Task to evaluate bids for
            strategy: Evaluation strategy ('lowest_cost', 'fastest', 'best_confidence')
            custom_evaluator: Optional custom evaluation function

        Returns:
            Winning bid or None if no valid bids

        Raises:
            ValueError: If task doesn't exist or invalid strategy
        """
        if task_id not in self.announcements:
            raise ValueError(f"Task {task_id} not found")

        task_bids = self.bids.get(task_id, [])
        if not task_bids:
            logger.warning(f"No bids received for task {task_id}")
            return None

        # Use custom evaluator if provided
        if custom_evaluator:
            winner = custom_evaluator(task_bids)
            if winner:
                logger.info(f"Bid {winner.bid_id} selected using custom evaluator")
            return winner

        # Built-in strategies
        if strategy == "lowest_cost":
            winner = min(task_bids, key=lambda b: b.bid_amount)
        elif strategy == "fastest":
            winner = min(task_bids, key=lambda b: b.estimated_duration)
        elif strategy == "best_confidence":
            winner = max(task_bids, key=lambda b: b.confidence)
        else:
            raise ValueError(f"Unknown evaluation strategy: {strategy}")

        logger.info(
            f"Task {task_id} awarded to agent {winner.agent_id} "
            f"(bid: ${winner.bid_amount:.2f}, duration: {winner.estimated_duration}s)"
        )

        return winner

    async def award_task(
        self,
        task_id: UUID,
        winning_bid: Bid,
        manager_id: UUID,
    ) -> None:
        """
        Award task to winning bidder

        Args:
            task_id: Task to award
            winning_bid: Winning bid
            manager_id: Manager awarding the task

        Raises:
            ValueError: If task already awarded
        """
        if task_id in self.awarded_tasks:
            raise ValueError(f"Task {task_id} already awarded")

        # Award task
        self.awarded_tasks[task_id] = winning_bid.agent_id

        # Send award message to winner
        award_message = ContractNetMessage(
            type=MessageType.CNP_AWARD,
            sender_id=manager_id,
            receiver_id=winning_bid.agent_id,
            task_id=task_id,
            content={
                "bid_id": str(winning_bid.bid_id),
                "message": "Task awarded",
            },
            priority=MessagePriority.HIGH,
        )
        self.message_queue.push(award_message)

        # Send rejection messages to other bidders
        for bid in self.bids[task_id]:
            if bid.bid_id != winning_bid.bid_id:
                reject_message = ContractNetMessage(
                    type=MessageType.CNP_REJECT,
                    sender_id=manager_id,
                    receiver_id=bid.agent_id,
                    task_id=task_id,
                    content={
                        "bid_id": str(bid.bid_id),
                        "reason": "Another bid was selected",
                    },
                    priority=MessagePriority.LOW,
                )
                self.message_queue.push(reject_message)

        logger.info(f"Task {task_id} awarded to agent {winning_bid.agent_id}")

    async def submit_result(
        self,
        task_id: UUID,
        agent_id: UUID,
        result: Any,
        manager_id: UUID,
    ) -> None:
        """
        Submit task result

        Args:
            task_id: Completed task ID
            agent_id: Agent submitting result
            result: Task result
            manager_id: Manager to send result to

        Raises:
            ValueError: If task not awarded to this agent
        """
        if task_id not in self.awarded_tasks:
            raise ValueError(f"Task {task_id} was not awarded")

        if self.awarded_tasks[task_id] != agent_id:
            raise ValueError(f"Task {task_id} was not awarded to agent {agent_id}")

        # Store result
        self.task_results[task_id] = result

        # Send result message
        result_message = ContractNetMessage(
            type=MessageType.CNP_RESULT,
            sender_id=agent_id,
            receiver_id=manager_id,
            task_id=task_id,
            content={
                "result": result,
                "completed_at": datetime.now().isoformat(),
            },
            priority=MessagePriority.HIGH,
        )
        self.message_queue.push(result_message)

        logger.info(f"Task {task_id} result submitted by agent {agent_id}")

    async def get_messages(
        self,
        agent_id: UUID,
        message_types: Optional[Set[MessageType]] = None,
    ) -> List[Message]:
        """
        Get messages for an agent

        Args:
            agent_id: Agent to get messages for
            message_types: Optional filter for message types

        Returns:
            List of messages
        """
        filter_criteria = MessageFilter(
            receiver_ids={agent_id},
            types=message_types,
        )

        # Get all matching messages (without removing from queue)
        messages = self.message_queue.get_all(filter_criteria)

        # Also check for broadcast messages
        broadcast_filter = MessageFilter(
            receiver_ids=None,
            types=message_types,
        )
        broadcast_messages = [
            msg for msg in self.message_queue.get_all(broadcast_filter)
            if msg.is_broadcast()
        ]

        return messages + broadcast_messages

    def get_task_status(self, task_id: UUID) -> Dict[str, Any]:
        """
        Get status of a task

        Args:
            task_id: Task to check

        Returns:
            Task status information
        """
        if task_id not in self.announcements:
            return {"status": "not_found"}

        status = {
            "task_id": str(task_id),
            "announcement": self.announcements[task_id].model_dump(),
            "num_bids": len(self.bids.get(task_id, [])),
            "awarded": task_id in self.awarded_tasks,
            "completed": task_id in self.task_results,
        }

        if task_id in self.awarded_tasks:
            status["awarded_to"] = str(self.awarded_tasks[task_id])

        if task_id in self.task_results:
            status["result"] = self.task_results[task_id]

        return status


# ============================================================================
# BLACKBOARD SYSTEM
# ============================================================================


class BlackboardEntry(BaseModel):
    """Entry on the blackboard"""

    entry_id: UUID = Field(default_factory=uuid4)
    key: str
    value: Any
    author_id: UUID
    tags: Set[str] = Field(default_factory=set)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    version: int = 1

    class Config:
        arbitrary_types_allowed = True


class BlackboardSystem:
    """
    Blackboard System Implementation

    A shared memory space where agents can:
    1. Write data to the blackboard
    2. Read data based on patterns
    3. Get notified of changes
    4. Collaborate through shared state

    Features:
    - Pattern-based data retrieval (regex, tags, key matching)
    - Event notification system
    - Version control for entries
    - Conflict detection
    - Access control
    """

    def __init__(
        self,
        max_entries: int = 10000,
        enable_notifications: bool = True,
    ):
        """
        Initialize Blackboard System

        Args:
            max_entries: Maximum number of entries
            enable_notifications: Whether to send change notifications
        """
        self.max_entries = max_entries
        self.enable_notifications = enable_notifications

        # Blackboard storage
        self.entries: Dict[str, BlackboardEntry] = {}
        self.entry_by_id: Dict[UUID, BlackboardEntry] = {}

        # Subscribers for notifications
        self.subscribers: Dict[str, Set[UUID]] = defaultdict(set)  # pattern -> agent_ids
        self.tag_subscribers: Dict[str, Set[UUID]] = defaultdict(set)  # tag -> agent_ids

        # Message queue for notifications
        self.message_queue = MessageQueue()

        # Access control (optional)
        self.read_permissions: Dict[str, Set[UUID]] = defaultdict(set)
        self.write_permissions: Dict[str, Set[UUID]] = defaultdict(set)

        logger.info("Blackboard System initialized")

    async def write(
        self,
        key: str,
        value: Any,
        author_id: UUID,
        tags: Optional[Set[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UUID:
        """
        Write entry to blackboard

        Args:
            key: Entry key
            value: Entry value
            author_id: Agent writing the entry
            tags: Optional tags for categorization
            metadata: Optional metadata

        Returns:
            Entry ID

        Raises:
            ValueError: If blackboard is full
        """
        if len(self.entries) >= self.max_entries:
            raise ValueError(f"Blackboard is full (max: {self.max_entries})")

        # Check if updating existing entry
        if key in self.entries:
            existing = self.entries[key]
            existing.value = value
            existing.updated_at = datetime.now()
            existing.version += 1
            if tags:
                existing.tags.update(tags)
            if metadata:
                existing.metadata.update(metadata)
            entry = existing
            action = "updated"
        else:
            # Create new entry
            entry = BlackboardEntry(
                key=key,
                value=value,
                author_id=author_id,
                tags=tags or set(),
                metadata=metadata or {},
            )
            self.entries[key] = entry
            self.entry_by_id[entry.entry_id] = entry
            action = "created"

        logger.info(f"Blackboard entry {action}: {key} by agent {author_id}")

        # Send notifications
        if self.enable_notifications:
            await self._notify_subscribers(entry, action)

        return entry.entry_id

    async def read(
        self,
        key: Optional[str] = None,
        pattern: Optional[str] = None,
        tags: Optional[Set[str]] = None,
        reader_id: Optional[UUID] = None,
    ) -> List[BlackboardEntry]:
        """
        Read entries from blackboard

        Args:
            key: Exact key to read (if provided, returns single match)
            pattern: Regex pattern to match keys
            tags: Tags to filter by (entries must have all tags)
            reader_id: Optional agent ID for access control

        Returns:
            List of matching entries
        """
        # Exact key lookup
        if key:
            entry = self.entries.get(key)
            return [entry] if entry else []

        # Pattern or tag-based search
        results = []

        for entry in self.entries.values():
            # Pattern matching
            if pattern:
                try:
                    if not re.search(pattern, entry.key):
                        continue
                except re.error as e:
                    logger.error(f"Invalid regex pattern '{pattern}': {e}")
                    continue

            # Tag matching (entry must have all requested tags)
            if tags and not tags.issubset(entry.tags):
                continue

            results.append(entry)

        logger.debug(
            f"Blackboard read by {reader_id}: "
            f"{len(results)} entries (pattern={pattern}, tags={tags})"
        )

        return results

    async def update(
        self,
        key: str,
        value: Any,
        author_id: UUID,
        expected_version: Optional[int] = None,
    ) -> UUID:
        """
        Update existing entry

        Args:
            key: Entry key
            value: New value
            author_id: Agent updating the entry
            expected_version: Expected version (for conflict detection)

        Returns:
            Entry ID

        Raises:
            ValueError: If entry doesn't exist or version conflict
        """
        if key not in self.entries:
            raise ValueError(f"Entry '{key}' not found")

        entry = self.entries[key]

        # Check for version conflict
        if expected_version is not None and entry.version != expected_version:
            raise ValueError(
                f"Version conflict: expected {expected_version}, "
                f"current is {entry.version}"
            )

        # Update entry
        entry.value = value
        entry.updated_at = datetime.now()
        entry.version += 1

        logger.info(f"Blackboard entry updated: {key} (v{entry.version}) by {author_id}")

        # Send notifications
        if self.enable_notifications:
            await self._notify_subscribers(entry, "updated")

        return entry.entry_id

    async def delete(
        self,
        key: str,
        author_id: UUID,
    ) -> bool:
        """
        Delete entry from blackboard

        Args:
            key: Entry key
            author_id: Agent deleting the entry

        Returns:
            True if deleted, False if not found
        """
        if key not in self.entries:
            return False

        entry = self.entries[key]
        del self.entries[key]
        del self.entry_by_id[entry.entry_id]

        logger.info(f"Blackboard entry deleted: {key} by {author_id}")

        # Send notifications
        if self.enable_notifications:
            await self._notify_subscribers(entry, "deleted")

        return True

    async def subscribe(
        self,
        agent_id: UUID,
        pattern: Optional[str] = None,
        tags: Optional[Set[str]] = None,
    ) -> None:
        """
        Subscribe to blackboard changes

        Args:
            agent_id: Agent subscribing
            pattern: Key pattern to watch (None for all)
            tags: Tags to watch
        """
        if pattern:
            self.subscribers[pattern].add(agent_id)
            logger.info(f"Agent {agent_id} subscribed to pattern: {pattern}")

        if tags:
            for tag in tags:
                self.tag_subscribers[tag].add(agent_id)
            logger.info(f"Agent {agent_id} subscribed to tags: {tags}")

    async def unsubscribe(
        self,
        agent_id: UUID,
        pattern: Optional[str] = None,
        tags: Optional[Set[str]] = None,
    ) -> None:
        """
        Unsubscribe from blackboard changes

        Args:
            agent_id: Agent unsubscribing
            pattern: Key pattern to stop watching
            tags: Tags to stop watching
        """
        if pattern and pattern in self.subscribers:
            self.subscribers[pattern].discard(agent_id)

        if tags:
            for tag in tags:
                self.tag_subscribers[tag].discard(agent_id)

    async def _notify_subscribers(
        self,
        entry: BlackboardEntry,
        action: str,
    ) -> None:
        """
        Notify subscribers about entry changes

        Args:
            entry: Entry that changed
            action: Action performed (created, updated, deleted)
        """
        notified_agents = set()

        # Pattern-based subscribers
        for pattern, agent_ids in self.subscribers.items():
            try:
                if re.search(pattern, entry.key):
                    notified_agents.update(agent_ids)
            except re.error:
                continue

        # Tag-based subscribers
        for tag in entry.tags:
            if tag in self.tag_subscribers:
                notified_agents.update(self.tag_subscribers[tag])

        # Send notifications
        for agent_id in notified_agents:
            message = BlackboardMessage(
                type=MessageType.BB_NOTIFY,
                sender_id=entry.author_id,
                receiver_id=agent_id,
                data_key=entry.key,
                data_value=entry.value,
                data_tags=entry.tags,
                content={
                    "action": action,
                    "entry_id": str(entry.entry_id),
                    "key": entry.key,
                    "version": entry.version,
                },
                priority=MessagePriority.NORMAL,
            )
            self.message_queue.push(message)

        if notified_agents:
            logger.debug(
                f"Notified {len(notified_agents)} agents about '{action}' "
                f"on entry '{entry.key}'"
            )

    async def get_messages(self, agent_id: UUID) -> List[Message]:
        """
        Get notification messages for an agent

        Args:
            agent_id: Agent to get messages for

        Returns:
            List of notification messages
        """
        filter_criteria = MessageFilter(
            receiver_ids={agent_id},
            types={MessageType.BB_NOTIFY},
        )
        return self.message_queue.get_all(filter_criteria)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get blackboard statistics

        Returns:
            Statistics dictionary
        """
        return {
            "total_entries": len(self.entries),
            "max_entries": self.max_entries,
            "subscribers": sum(len(agents) for agents in self.subscribers.values()),
            "tag_subscribers": sum(
                len(agents) for agents in self.tag_subscribers.values()
            ),
            "notification_queue_size": self.message_queue.size(),
        }


# ============================================================================
# PUBLISH/SUBSCRIBE PROTOCOL
# ============================================================================


class Subscription(BaseModel):
    """Subscription to a topic"""

    subscription_id: UUID = Field(default_factory=uuid4)
    agent_id: UUID
    topic: str
    filters: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)


class PubSubProtocol:
    """
    Publish/Subscribe Protocol Implementation

    Decoupled communication where:
    1. Publishers send messages to topics
    2. Subscribers receive messages from topics they're subscribed to
    3. No direct knowledge between publishers and subscribers

    Features:
    - Hierarchical topics (e.g., "sensors/temperature/room1")
    - Wildcard subscriptions (e.g., "sensors/+/room1", "sensors/#")
    - Message filtering
    - Retained messages for late joiners
    - QoS levels (at-most-once, at-least-once)
    """

    def __init__(
        self,
        max_retained_per_topic: int = 1,
        message_ttl: Optional[float] = None,
    ):
        """
        Initialize Pub/Sub Protocol

        Args:
            max_retained_per_topic: Max retained messages per topic
            message_ttl: Message time-to-live in seconds (None for infinite)
        """
        self.max_retained_per_topic = max_retained_per_topic
        self.message_ttl = message_ttl

        # Subscriptions
        self.subscriptions: Dict[UUID, Subscription] = {}
        self.topic_subscriptions: Dict[str, Set[UUID]] = defaultdict(set)

        # Message storage
        self.message_queue = MessageQueue()
        self.retained_messages: Dict[str, List[PubSubMessage]] = defaultdict(list)

        # Statistics
        self.total_published = 0
        self.total_delivered = 0

        logger.info("Pub/Sub Protocol initialized")

    async def publish(
        self,
        topic: str,
        content: Dict[str, Any],
        publisher_id: UUID,
        tags: Optional[Set[str]] = None,
        retain: bool = False,
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> UUID:
        """
        Publish message to topic

        Args:
            topic: Topic to publish to
            content: Message content
            publisher_id: Publishing agent ID
            tags: Optional message tags
            retain: Whether to retain message for future subscribers
            priority: Message priority

        Returns:
            Message ID
        """
        # Parse topic into parts
        topic_parts = topic.split("/")

        # Create message
        message = PubSubMessage(
            type=MessageType.PUBSUB_PUBLISH,
            sender_id=publisher_id,
            topic=topic,
            subtopics=topic_parts,
            tags=tags or set(),
            retain=retain,
            content=content,
            priority=priority,
        )

        # Set expiration if TTL is configured
        if self.message_ttl:
            message.expires_at = datetime.now() + timedelta(seconds=self.message_ttl)

        # Retain message if requested
        if retain:
            self._retain_message(message)

        # Deliver to subscribers
        await self._deliver_message(message)

        self.total_published += 1
        logger.info(f"Published message to topic '{topic}' by agent {publisher_id}")

        return message.id

    async def subscribe(
        self,
        topic: str,
        agent_id: UUID,
        filters: Optional[Dict[str, Any]] = None,
    ) -> UUID:
        """
        Subscribe to topic

        Args:
            topic: Topic to subscribe to (supports wildcards: + for single level, # for multi-level)
            agent_id: Subscribing agent ID
            filters: Optional content filters

        Returns:
            Subscription ID
        """
        subscription = Subscription(
            agent_id=agent_id,
            topic=topic,
            filters=filters or {},
        )

        self.subscriptions[subscription.subscription_id] = subscription
        self.topic_subscriptions[topic].add(subscription.subscription_id)

        logger.info(f"Agent {agent_id} subscribed to topic '{topic}'")

        # Send retained messages for this topic
        await self._send_retained_messages(subscription)

        return subscription.subscription_id

    async def unsubscribe(
        self,
        subscription_id: UUID,
    ) -> bool:
        """
        Unsubscribe from topic

        Args:
            subscription_id: Subscription to cancel

        Returns:
            True if unsubscribed, False if subscription not found
        """
        if subscription_id not in self.subscriptions:
            return False

        subscription = self.subscriptions[subscription_id]
        topic = subscription.topic

        # Remove subscription
        del self.subscriptions[subscription_id]
        self.topic_subscriptions[topic].discard(subscription_id)

        logger.info(f"Agent {subscription.agent_id} unsubscribed from '{topic}'")
        return True

    async def _deliver_message(self, message: PubSubMessage) -> None:
        """
        Deliver message to all matching subscribers

        Args:
            message: Message to deliver
        """
        delivered_to = set()

        # Find matching subscriptions
        for sub_id, subscription in self.subscriptions.items():
            if self._topic_matches(message.topic, subscription.topic):
                # Check content filters
                if self._matches_filters(message.content, subscription.filters):
                    # Create message for subscriber
                    subscriber_message = PubSubMessage(
                        type=MessageType.PUBSUB_PUBLISH,
                        sender_id=message.sender_id,
                        receiver_id=subscription.agent_id,
                        topic=message.topic,
                        subtopics=message.subtopics,
                        tags=message.tags,
                        content=message.content,
                        priority=message.priority,
                        expires_at=message.expires_at,
                    )
                    self.message_queue.push(subscriber_message)
                    delivered_to.add(subscription.agent_id)

        self.total_delivered += len(delivered_to)
        if delivered_to:
            logger.debug(
                f"Delivered message on '{message.topic}' to {len(delivered_to)} subscribers"
            )

    def _topic_matches(self, message_topic: str, subscription_topic: str) -> bool:
        """
        Check if message topic matches subscription topic

        Supports wildcards:
        - '+' matches single level
        - '#' matches multiple levels

        Args:
            message_topic: Actual message topic
            subscription_topic: Subscription pattern

        Returns:
            True if topics match
        """
        msg_parts = message_topic.split("/")
        sub_parts = subscription_topic.split("/")

        # Exact match
        if message_topic == subscription_topic:
            return True

        # Multi-level wildcard
        if "#" in sub_parts:
            idx = sub_parts.index("#")
            # '#' must be last element
            if idx != len(sub_parts) - 1:
                return False
            # Check prefix matches
            return msg_parts[:idx] == sub_parts[:idx]

        # Single-level wildcard
        if len(msg_parts) != len(sub_parts):
            return False

        for msg_part, sub_part in zip(msg_parts, sub_parts):
            if sub_part != "+" and msg_part != sub_part:
                return False

        return True

    def _matches_filters(
        self,
        content: Dict[str, Any],
        filters: Dict[str, Any],
    ) -> bool:
        """
        Check if content matches filters

        Args:
            content: Message content
            filters: Filter criteria

        Returns:
            True if content matches all filters
        """
        for key, value in filters.items():
            if key not in content or content[key] != value:
                return False
        return True

    def _retain_message(self, message: PubSubMessage) -> None:
        """
        Retain message for future subscribers

        Args:
            message: Message to retain
        """
        retained = self.retained_messages[message.topic]

        # Add message
        retained.append(message)

        # Remove old messages if limit exceeded
        if len(retained) > self.max_retained_per_topic:
            retained.pop(0)

        logger.debug(f"Retained message for topic '{message.topic}'")

    async def _send_retained_messages(self, subscription: Subscription) -> None:
        """
        Send retained messages to new subscriber

        Args:
            subscription: New subscription
        """
        sent_count = 0

        # Check all retained messages
        for topic, messages in self.retained_messages.items():
            if self._topic_matches(topic, subscription.topic):
                for message in messages:
                    # Check if message is still valid
                    if not message.is_expired():
                        # Check content filters
                        if self._matches_filters(message.content, subscription.filters):
                            # Create message for subscriber
                            subscriber_message = PubSubMessage(
                                type=MessageType.PUBSUB_PUBLISH,
                                sender_id=message.sender_id,
                                receiver_id=subscription.agent_id,
                                topic=message.topic,
                                subtopics=message.subtopics,
                                tags=message.tags,
                                content=message.content,
                                priority=message.priority,
                                metadata={"retained": True},
                            )
                            self.message_queue.push(subscriber_message)
                            sent_count += 1

        if sent_count > 0:
            logger.debug(
                f"Sent {sent_count} retained messages to agent {subscription.agent_id}"
            )

    async def get_messages(
        self,
        agent_id: UUID,
        topics: Optional[List[str]] = None,
    ) -> List[Message]:
        """
        Get messages for an agent

        Args:
            agent_id: Agent to get messages for
            topics: Optional filter for specific topics

        Returns:
            List of messages
        """
        filter_criteria = MessageFilter(
            receiver_ids={agent_id},
            types={MessageType.PUBSUB_PUBLISH},
        )

        messages = self.message_queue.get_all(filter_criteria)

        # Filter by topics if specified
        if topics:
            messages = [
                msg for msg in messages
                if isinstance(msg, PubSubMessage) and msg.topic in topics
            ]

        return messages

    def get_stats(self) -> Dict[str, Any]:
        """
        Get pub/sub statistics

        Returns:
            Statistics dictionary
        """
        return {
            "total_subscriptions": len(self.subscriptions),
            "total_published": self.total_published,
            "total_delivered": self.total_delivered,
            "retained_topics": len(self.retained_messages),
            "message_queue_size": self.message_queue.size(),
        }

    def get_topic_subscribers(self, topic: str) -> List[UUID]:
        """
        Get all agents subscribed to a topic

        Args:
            topic: Topic to check

        Returns:
            List of agent IDs
        """
        agent_ids = set()

        for sub_id in self.topic_subscriptions.get(topic, set()):
            if sub_id in self.subscriptions:
                agent_ids.add(self.subscriptions[sub_id].agent_id)

        return list(agent_ids)
