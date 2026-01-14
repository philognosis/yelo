"""
Communication Protocols Demo

Demonstrates the usage of all three communication protocols:
1. Contract Net Protocol (CNP)
2. Blackboard System
3. Publish/Subscribe (Pub/Sub)
"""

import asyncio
from datetime import datetime, timedelta
from uuid import uuid4

from iras.communication import (
    Bid,
    BlackboardSystem,
    ContractNetProtocol,
    MessageType,
    PubSubProtocol,
    TaskAnnouncement,
)


async def demo_contract_net():
    """Demonstrate Contract Net Protocol"""
    print("\n" + "=" * 60)
    print("CONTRACT NET PROTOCOL DEMO")
    print("=" * 60)

    # Initialize protocol
    cnp = ContractNetProtocol(bid_timeout=30.0)

    # Create agent IDs
    manager_id = uuid4()
    agent1_id = uuid4()
    agent2_id = uuid4()
    agent3_id = uuid4()

    print(f"\nManager: {manager_id}")
    print(f"Agent 1: {agent1_id}")
    print(f"Agent 2: {agent2_id}")
    print(f"Agent 3: {agent3_id}")

    # 1. Manager announces task
    print("\n1. Manager announces task...")
    announcement = TaskAnnouncement(
        description="Process sensor data from 100 devices",
        required_capabilities={"data_processing", "sensor_interface"},
        deadline=datetime.now() + timedelta(hours=1),
        max_budget=100.0,
    )
    task_id = await cnp.announce_task(announcement, manager_id)
    print(f"   Task {task_id} announced")

    # 2. Agents submit bids
    print("\n2. Agents submit bids...")

    bid1 = Bid(
        task_id=task_id,
        agent_id=agent1_id,
        bid_amount=80.0,
        estimated_duration=300.0,
        confidence=0.85,
        capabilities={"data_processing", "sensor_interface"},
        proposal="Will use parallel processing for faster completion",
    )
    await cnp.submit_bid(bid1, manager_id)
    print(f"   Agent 1 bid: ${bid1.bid_amount} (duration: {bid1.estimated_duration}s)")

    bid2 = Bid(
        task_id=task_id,
        agent_id=agent2_id,
        bid_amount=60.0,
        estimated_duration=450.0,
        confidence=0.90,
        capabilities={"data_processing", "sensor_interface", "optimization"},
        proposal="Specialized in sensor data optimization",
    )
    await cnp.submit_bid(bid2, manager_id)
    print(f"   Agent 2 bid: ${bid2.bid_amount} (duration: {bid2.estimated_duration}s)")

    bid3 = Bid(
        task_id=task_id,
        agent_id=agent3_id,
        bid_amount=75.0,
        estimated_duration=350.0,
        confidence=0.75,
        capabilities={"data_processing", "sensor_interface"},
        proposal="Standard processing approach",
    )
    await cnp.submit_bid(bid3, manager_id)
    print(f"   Agent 3 bid: ${bid3.bid_amount} (duration: {bid3.estimated_duration}s)")

    # 3. Manager evaluates bids
    print("\n3. Manager evaluates bids...")

    # Try different strategies
    lowest_cost = await cnp.evaluate_bids(task_id, strategy="lowest_cost")
    print(f"   Lowest cost bid: Agent {lowest_cost.agent_id} - ${lowest_cost.bid_amount}")

    fastest = await cnp.evaluate_bids(task_id, strategy="fastest")
    print(f"   Fastest bid: Agent {fastest.agent_id} - {fastest.estimated_duration}s")

    best_conf = await cnp.evaluate_bids(task_id, strategy="best_confidence")
    print(f"   Best confidence: Agent {best_conf.agent_id} - {best_conf.confidence:.2%}")

    # 4. Award task (using lowest cost strategy)
    print("\n4. Awarding task to lowest cost bidder...")
    await cnp.award_task(task_id, lowest_cost, manager_id)
    print(f"   Task awarded to Agent {lowest_cost.agent_id}")

    # 5. Check task status
    print("\n5. Task status:")
    status = cnp.get_task_status(task_id)
    print(f"   Awarded: {status['awarded']}")
    print(f"   Awarded to: {status['awarded_to']}")
    print(f"   Number of bids: {status['num_bids']}")

    # 6. Agent submits result
    print("\n6. Agent submits result...")
    result = {
        "processed_devices": 100,
        "success_rate": 0.98,
        "processing_time": 280.5,
    }
    await cnp.submit_result(task_id, lowest_cost.agent_id, result, manager_id)
    print(f"   Result submitted: {result}")

    # 7. Final status
    final_status = cnp.get_task_status(task_id)
    print("\n7. Final task status:")
    print(f"   Completed: {final_status['completed']}")
    print(f"   Result: {final_status.get('result')}")


async def demo_blackboard():
    """Demonstrate Blackboard System"""
    print("\n" + "=" * 60)
    print("BLACKBOARD SYSTEM DEMO")
    print("=" * 60)

    # Initialize blackboard
    bb = BlackboardSystem(enable_notifications=True)

    # Create agent IDs
    sensor_agent = uuid4()
    processor_agent = uuid4()
    analyzer_agent = uuid4()

    print(f"\nSensor Agent: {sensor_agent}")
    print(f"Processor Agent: {processor_agent}")
    print(f"Analyzer Agent: {analyzer_agent}")

    # 1. Subscribe to patterns
    print("\n1. Setting up subscriptions...")
    await bb.subscribe(processor_agent, pattern=r"sensor_.*")
    await bb.subscribe(analyzer_agent, tags={"analysis"})
    print("   Processor subscribed to pattern: sensor_.*")
    print("   Analyzer subscribed to tag: analysis")

    # 2. Write sensor data
    print("\n2. Writing sensor data to blackboard...")
    await bb.write(
        key="sensor_temp_room1",
        value={"temperature": 22.5, "humidity": 45.0},
        author_id=sensor_agent,
        tags={"sensor", "temperature"},
    )
    print("   Wrote: sensor_temp_room1")

    await bb.write(
        key="sensor_temp_room2",
        value={"temperature": 23.1, "humidity": 48.0},
        author_id=sensor_agent,
        tags={"sensor", "temperature"},
    )
    print("   Wrote: sensor_temp_room2")

    # 3. Read data with patterns
    print("\n3. Reading data with patterns...")
    sensor_entries = await bb.read(pattern=r"sensor_temp_.*")
    print(f"   Found {len(sensor_entries)} sensor entries:")
    for entry in sensor_entries:
        print(f"      {entry.key}: {entry.value}")

    # 4. Write analysis results
    print("\n4. Writing analysis results...")
    await bb.write(
        key="analysis_temp_avg",
        value={"average_temp": 22.8, "variance": 0.3},
        author_id=processor_agent,
        tags={"analysis", "temperature"},
    )
    print("   Wrote: analysis_temp_avg")

    # 5. Read with tags
    print("\n5. Reading data with tags...")
    analysis_entries = await bb.read(tags={"analysis"})
    print(f"   Found {len(analysis_entries)} analysis entries:")
    for entry in analysis_entries:
        print(f"      {entry.key}: {entry.value}")

    # 6. Update entry with version control
    print("\n6. Updating entry with version control...")
    entries = await bb.read(key="sensor_temp_room1")
    if entries:
        entry = entries[0]
        print(f"   Current version: {entry.version}")
        await bb.update(
            key="sensor_temp_room1",
            value={"temperature": 22.8, "humidity": 46.0},
            author_id=sensor_agent,
            expected_version=entry.version,
        )
        print(f"   Updated to version: {entry.version}")

    # 7. Check notifications
    print("\n7. Checking notifications...")
    processor_msgs = await bb.get_messages(processor_agent)
    analyzer_msgs = await bb.get_messages(analyzer_agent)
    print(f"   Processor received {len(processor_msgs)} notifications")
    print(f"   Analyzer received {len(analyzer_msgs)} notifications")

    # 8. Blackboard statistics
    print("\n8. Blackboard statistics:")
    stats = bb.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")


async def demo_pubsub():
    """Demonstrate Pub/Sub Protocol"""
    print("\n" + "=" * 60)
    print("PUB/SUB PROTOCOL DEMO")
    print("=" * 60)

    # Initialize pub/sub
    pubsub = PubSubProtocol(max_retained_per_topic=5)

    # Create agent IDs
    sensor_publisher = uuid4()
    monitor_subscriber = uuid4()
    analytics_subscriber = uuid4()
    alert_subscriber = uuid4()

    print(f"\nSensor Publisher: {sensor_publisher}")
    print(f"Monitor Subscriber: {monitor_subscriber}")
    print(f"Analytics Subscriber: {analytics_subscriber}")
    print(f"Alert Subscriber: {alert_subscriber}")

    # 1. Set up subscriptions
    print("\n1. Setting up subscriptions...")

    # Monitor subscribes to all sensor topics
    await pubsub.subscribe("sensors/#", monitor_subscriber)
    print("   Monitor subscribed to: sensors/#")

    # Analytics subscribes to specific sensor types
    await pubsub.subscribe("sensors/temperature/+", analytics_subscriber)
    print("   Analytics subscribed to: sensors/temperature/+")

    # Alert subscribes to critical events
    await pubsub.subscribe("alerts/+", alert_subscriber)
    print("   Alert subscribed to: alerts/+")

    # 2. Publish temperature data
    print("\n2. Publishing temperature data...")
    await pubsub.publish(
        topic="sensors/temperature/room1",
        content={"value": 22.5, "unit": "celsius", "timestamp": datetime.now().isoformat()},
        publisher_id=sensor_publisher,
        retain=True,
    )
    print("   Published to: sensors/temperature/room1")

    await pubsub.publish(
        topic="sensors/temperature/room2",
        content={"value": 23.1, "unit": "celsius", "timestamp": datetime.now().isoformat()},
        publisher_id=sensor_publisher,
        retain=True,
    )
    print("   Published to: sensors/temperature/room2")

    # 3. Publish humidity data
    print("\n3. Publishing humidity data...")
    await pubsub.publish(
        topic="sensors/humidity/room1",
        content={"value": 45.0, "unit": "percent", "timestamp": datetime.now().isoformat()},
        publisher_id=sensor_publisher,
    )
    print("   Published to: sensors/humidity/room1")

    # 4. Publish alert
    print("\n4. Publishing critical alert...")
    await pubsub.publish(
        topic="alerts/temperature",
        content={"level": "critical", "message": "Temperature exceeds threshold"},
        publisher_id=sensor_publisher,
        tags={"critical", "temperature"},
        priority=3,  # CRITICAL priority
    )
    print("   Published to: alerts/temperature")

    # 5. Check received messages
    print("\n5. Checking received messages...")

    monitor_msgs = await pubsub.get_messages(monitor_subscriber)
    print(f"   Monitor received {len(monitor_msgs)} messages:")
    for msg in monitor_msgs:
        if hasattr(msg, "topic"):
            print(f"      - {msg.topic}")

    analytics_msgs = await pubsub.get_messages(analytics_subscriber)
    print(f"   Analytics received {len(analytics_msgs)} messages:")
    for msg in analytics_msgs:
        if hasattr(msg, "topic"):
            print(f"      - {msg.topic}")

    alert_msgs = await pubsub.get_messages(alert_subscriber)
    print(f"   Alert received {len(alert_msgs)} messages:")
    for msg in alert_msgs:
        if hasattr(msg, "topic"):
            print(f"      - {msg.topic} (priority: {msg.priority})")

    # 6. Late subscriber gets retained messages
    print("\n6. Late subscriber joining...")
    late_subscriber = uuid4()
    await pubsub.subscribe("sensors/temperature/#", late_subscriber)
    print(f"   Late subscriber: {late_subscriber}")

    late_msgs = await pubsub.get_messages(late_subscriber)
    print(f"   Received {len(late_msgs)} retained messages:")
    for msg in late_msgs:
        if hasattr(msg, "topic"):
            print(f"      - {msg.topic} (retained)")

    # 7. Topic wildcard matching
    print("\n7. Testing topic wildcard matching...")
    test_topics = [
        ("sensors/temperature/room1", "sensors/+/room1"),
        ("sensors/temperature/room2", "sensors/#"),
        ("sensors/humidity/room1", "sensors/humidity/+"),
    ]
    for msg_topic, sub_topic in test_topics:
        matches = pubsub._topic_matches(msg_topic, sub_topic)
        print(f"   '{msg_topic}' matches '{sub_topic}': {matches}")

    # 8. Pub/Sub statistics
    print("\n8. Pub/Sub statistics:")
    stats = pubsub.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")


async def main():
    """Run all demos"""
    print("\n" + "=" * 60)
    print("MULTI-AGENT COMMUNICATION PROTOCOLS DEMONSTRATION")
    print("=" * 60)

    # Run each demo
    await demo_contract_net()
    await demo_blackboard()
    await demo_pubsub()

    print("\n" + "=" * 60)
    print("ALL DEMOS COMPLETED SUCCESSFULLY")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
