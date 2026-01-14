"""
Communication Protocols Module

Multi-agent communication infrastructure providing:
- Message types and routing
- Contract Net Protocol for task allocation
- Blackboard System for shared memory
- Pub/Sub for decoupled messaging

Example usage:

    # Contract Net Protocol
    cnp = ContractNetProtocol()
    announcement = TaskAnnouncement(
        description="Process sensor data",
        required_capabilities={"data_processing"}
    )
    task_id = await cnp.announce_task(announcement, manager_id)

    # Blackboard System
    blackboard = BlackboardSystem()
    entry_id = await blackboard.write(
        key="sensor_reading",
        value={"temperature": 22.5},
        author_id=agent_id,
        tags={"sensors", "temperature"}
    )

    # Pub/Sub Protocol
    pubsub = PubSubProtocol()
    await pubsub.subscribe("sensors/#", agent_id)
    await pubsub.publish(
        topic="sensors/temperature",
        content={"value": 22.5},
        publisher_id=agent_id
    )
"""

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
from iras.communication.protocols import (
    Bid,
    BlackboardEntry,
    BlackboardSystem,
    ContractNetProtocol,
    PubSubProtocol,
    Subscription,
    TaskAnnouncement,
)

__all__ = [
    # Message classes
    "Message",
    "MessageType",
    "MessagePriority",
    "MessageFilter",
    "MessageQueue",
    "ContractNetMessage",
    "BlackboardMessage",
    "PubSubMessage",
    # Contract Net Protocol
    "ContractNetProtocol",
    "TaskAnnouncement",
    "Bid",
    # Blackboard System
    "BlackboardSystem",
    "BlackboardEntry",
    # Pub/Sub Protocol
    "PubSubProtocol",
    "Subscription",
]

__version__ = "1.0.0"
