"""Test Suite for Communication Protocols"""

import pytest
import asyncio
from datetime import datetime
from uuid import uuid4

from iras.communication.protocols import (
    MessageBus,
    MessageProtocol,
    RequestReplyProtocol,
    PublishSubscribeProtocol,
)
from iras.communication.message import Message, MessageType, MessagePriority


class TestMessageBus:
    """Test message bus functionality"""

    @pytest.mark.asyncio
    async def test_message_bus_initialization(self):
        bus = MessageBus()
        assert len(bus.queues) == 0

    @pytest.mark.asyncio
    async def test_send_message(self):
        bus = MessageBus()
        receiver_id = uuid4()

        message = Message(
            sender=uuid4(),
            receiver=receiver_id,
            content={"data": "test"},
            message_type=MessageType.REQUEST,
        )

        await bus.send(message)
        assert receiver_id in bus.queues

    @pytest.mark.asyncio
    async def test_receive_message(self):
        bus = MessageBus()
        receiver_id = uuid4()

        message = Message(
            sender=uuid4(),
            receiver=receiver_id,
            content={"test": "data"},
            message_type=MessageType.REQUEST,
        )

        await bus.send(message)
        received = await bus.receive(receiver_id, timeout=1.0)

        assert received is not None
        assert received.content["test"] == "data"

    @pytest.mark.asyncio
    async def test_receive_timeout(self):
        bus = MessageBus()
        receiver_id = uuid4()

        received = await bus.receive(receiver_id, timeout=0.1)
        assert received is None

    @pytest.mark.asyncio
    async def test_message_priority_ordering(self):
        bus = MessageBus()
        receiver_id = uuid4()

        # Send low priority first
        await bus.send(Message(
            sender=uuid4(),
            receiver=receiver_id,
            content={"priority": "low"},
            message_type=MessageType.REQUEST,
            priority=MessagePriority.LOW,
        ))

        # Send high priority
        await bus.send(Message(
            sender=uuid4(),
            receiver=receiver_id,
            content={"priority": "high"},
            message_type=MessageType.REQUEST,
            priority=MessagePriority.HIGH,
        ))

        # High priority should be received first
        first = await bus.receive(receiver_id, timeout=1.0)
        assert first.content["priority"] == "high"


class TestRequestReplyProtocol:
    """Test request-reply communication pattern"""

    @pytest.mark.asyncio
    async def test_request_reply(self):
        protocol = RequestReplyProtocol()
        requester_id = uuid4()
        responder_id = uuid4()

        # Simulate responder
        async def responder():
            request = await protocol.receive_request(responder_id, timeout=2.0)
            if request:
                await protocol.send_reply(
                    request,
                    {"result": "success"},
                )

        # Run responder in background
        responder_task = asyncio.create_task(responder())

        # Send request
        response = await protocol.send_request(
            sender=requester_id,
            receiver=responder_id,
            content={"query": "test"},
            timeout=2.0,
        )

        await responder_task

        assert response is not None
        assert response.content["result"] == "success"

    @pytest.mark.asyncio
    async def test_request_timeout(self):
        protocol = RequestReplyProtocol()

        response = await protocol.send_request(
            sender=uuid4(),
            receiver=uuid4(),
            content={"test": "data"},
            timeout=0.1,
        )

        assert response is None


class TestPublishSubscribeProtocol:
    """Test pub-sub communication pattern"""

    @pytest.mark.asyncio
    async def test_subscribe_and_publish(self):
        protocol = PublishSubscribeProtocol()
        subscriber_id = uuid4()

        # Subscribe to topic
        await protocol.subscribe(subscriber_id, "test_topic")

        # Publish message
        await protocol.publish(
            "test_topic",
            {"data": "test_message"},
            sender=uuid4(),
        )

        # Receive published message
        message = await protocol.receive(subscriber_id, timeout=1.0)

        assert message is not None
        assert message.content["data"] == "test_message"

    @pytest.mark.asyncio
    async def test_multiple_subscribers(self):
        protocol = PublishSubscribeProtocol()
        sub1 = uuid4()
        sub2 = uuid4()

        await protocol.subscribe(sub1, "topic")
        await protocol.subscribe(sub2, "topic")

        await protocol.publish("topic", {"msg": "broadcast"}, uuid4())

        msg1 = await protocol.receive(sub1, timeout=1.0)
        msg2 = await protocol.receive(sub2, timeout=1.0)

        assert msg1 is not None
        assert msg2 is not None

    @pytest.mark.asyncio
    async def test_unsubscribe(self):
        protocol = PublishSubscribeProtocol()
        subscriber_id = uuid4()

        await protocol.subscribe(subscriber_id, "topic")
        await protocol.unsubscribe(subscriber_id, "topic")

        await protocol.publish("topic", {"msg": "test"}, uuid4())

        message = await protocol.receive(subscriber_id, timeout=0.1)
        assert message is None  # Should not receive after unsubscribe


class TestEdgeCases:
    """Test edge cases in communication"""

    @pytest.mark.asyncio
    async def test_empty_message_content(self):
        bus = MessageBus()
        receiver_id = uuid4()

        message = Message(
            sender=uuid4(),
            receiver=receiver_id,
            content={},
            message_type=MessageType.REQUEST,
        )

        await bus.send(message)
        received = await bus.receive(receiver_id, timeout=1.0)
        assert received is not None

    @pytest.mark.asyncio
    async def test_concurrent_sends(self):
        bus = MessageBus()
        receiver_id = uuid4()

        async def send_message(i):
            await bus.send(Message(
                sender=uuid4(),
                receiver=receiver_id,
                content={"index": i},
                message_type=MessageType.REQUEST,
            ))

        await asyncio.gather(*[send_message(i) for i in range(10)])

        count = 0
        while True:
            msg = await bus.receive(receiver_id, timeout=0.1)
            if msg is None:
                break
            count += 1

        assert count == 10
