"""
WebSocket Handlers for Real-time Updates

Provides WebSocket connections for real-time evaluation updates,
notifications, and agent swarm status.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger
from pydantic import ValidationError

from bloom.api.models import WebSocketMessage


class ConnectionManager:
    """
    Manages WebSocket connections and message broadcasting

    Supports:
    - Individual evaluation subscriptions
    - Global notifications
    - Swarm status updates
    """

    def __init__(self):
        """Initialize connection manager"""
        # Active WebSocket connections
        self.active_connections: List[WebSocket] = []

        # Connections subscribed to specific evaluations
        self.evaluation_subscriptions: Dict[UUID, Set[WebSocket]] = {}

        # Connections subscribed to swarm status
        self.swarm_subscriptions: Set[WebSocket] = set()

        # Connection metadata
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}

        logger.info("Connection manager initialized")

    async def connect(
        self,
        websocket: WebSocket,
        user_id: Optional[UUID] = None,
    ) -> None:
        """
        Accept a new WebSocket connection

        Args:
            websocket: WebSocket connection to accept
            user_id: Optional authenticated user ID
        """
        await websocket.accept()
        self.active_connections.append(websocket)

        # Store metadata
        self.connection_metadata[websocket] = {
            "user_id": user_id,
            "connected_at": datetime.now(),
            "message_count": 0,
        }

        logger.info(
            f"WebSocket connected (total: {len(self.active_connections)})"
            + (f" - user: {user_id}" if user_id else "")
        )

        # Send welcome message
        await self.send_personal_message(
            {
                "type": "connection",
                "data": {
                    "status": "connected",
                    "message": "Welcome to Bloom real-time updates",
                },
                "timestamp": datetime.now().isoformat(),
            },
            websocket,
        )

    def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove a WebSocket connection

        Args:
            websocket: WebSocket connection to remove
        """
        # Remove from active connections
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        # Remove from evaluation subscriptions
        for evaluation_id, subscribers in self.evaluation_subscriptions.items():
            if websocket in subscribers:
                subscribers.remove(websocket)

        # Remove from swarm subscriptions
        if websocket in self.swarm_subscriptions:
            self.swarm_subscriptions.remove(websocket)

        # Remove metadata
        if websocket in self.connection_metadata:
            metadata = self.connection_metadata.pop(websocket)
            logger.info(
                f"WebSocket disconnected (total: {len(self.active_connections)}) "
                f"- sent {metadata['message_count']} messages"
            )

    async def subscribe_to_evaluation(
        self,
        websocket: WebSocket,
        evaluation_id: UUID,
    ) -> None:
        """
        Subscribe a WebSocket to evaluation updates

        Args:
            websocket: WebSocket connection
            evaluation_id: Evaluation to subscribe to
        """
        if evaluation_id not in self.evaluation_subscriptions:
            self.evaluation_subscriptions[evaluation_id] = set()

        self.evaluation_subscriptions[evaluation_id].add(websocket)

        logger.info(
            f"WebSocket subscribed to evaluation {evaluation_id} "
            f"(total subscribers: {len(self.evaluation_subscriptions[evaluation_id])})"
        )

        # Send confirmation
        await self.send_personal_message(
            {
                "type": "subscription",
                "data": {
                    "status": "subscribed",
                    "evaluation_id": str(evaluation_id),
                },
                "timestamp": datetime.now().isoformat(),
            },
            websocket,
        )

    async def unsubscribe_from_evaluation(
        self,
        websocket: WebSocket,
        evaluation_id: UUID,
    ) -> None:
        """
        Unsubscribe a WebSocket from evaluation updates

        Args:
            websocket: WebSocket connection
            evaluation_id: Evaluation to unsubscribe from
        """
        if (
            evaluation_id in self.evaluation_subscriptions
            and websocket in self.evaluation_subscriptions[evaluation_id]
        ):
            self.evaluation_subscriptions[evaluation_id].remove(websocket)
            logger.info(f"WebSocket unsubscribed from evaluation {evaluation_id}")

    async def subscribe_to_swarm(self, websocket: WebSocket) -> None:
        """
        Subscribe a WebSocket to swarm status updates

        Args:
            websocket: WebSocket connection
        """
        self.swarm_subscriptions.add(websocket)

        logger.info(
            f"WebSocket subscribed to swarm status "
            f"(total subscribers: {len(self.swarm_subscriptions)})"
        )

        # Send confirmation
        await self.send_personal_message(
            {
                "type": "subscription",
                "data": {
                    "status": "subscribed",
                    "topic": "swarm_status",
                },
                "timestamp": datetime.now().isoformat(),
            },
            websocket,
        )

    async def send_personal_message(
        self,
        message: Dict[str, Any],
        websocket: WebSocket,
    ) -> None:
        """
        Send a message to a specific WebSocket

        Args:
            message: Message dictionary
            websocket: Target WebSocket connection
        """
        try:
            await websocket.send_json(message)

            # Update message count
            if websocket in self.connection_metadata:
                self.connection_metadata[websocket]["message_count"] += 1

        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)

    async def broadcast_to_all(self, message: Dict[str, Any]) -> None:
        """
        Broadcast a message to all connected WebSockets

        Args:
            message: Message dictionary
        """
        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_json(message)

                # Update message count
                if connection in self.connection_metadata:
                    self.connection_metadata[connection]["message_count"] += 1

            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected.append(connection)

        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)

        if disconnected:
            logger.warning(f"Removed {len(disconnected)} disconnected connections")

    async def broadcast_to_evaluation(
        self,
        evaluation_id: UUID,
        message: Dict[str, Any],
    ) -> None:
        """
        Broadcast a message to all subscribers of an evaluation

        Args:
            evaluation_id: Evaluation ID
            message: Message dictionary
        """
        if evaluation_id not in self.evaluation_subscriptions:
            return

        subscribers = self.evaluation_subscriptions[evaluation_id]
        disconnected = []

        logger.debug(
            f"Broadcasting to {len(subscribers)} subscribers of evaluation {evaluation_id}"
        )

        for connection in subscribers:
            try:
                await connection.send_json(message)

                # Update message count
                if connection in self.connection_metadata:
                    self.connection_metadata[connection]["message_count"] += 1

            except Exception as e:
                logger.error(f"Error broadcasting to subscriber: {e}")
                disconnected.append(connection)

        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)

    async def broadcast_to_swarm_subscribers(
        self,
        message: Dict[str, Any],
    ) -> None:
        """
        Broadcast a message to all swarm status subscribers

        Args:
            message: Message dictionary
        """
        disconnected = []

        logger.debug(
            f"Broadcasting swarm update to {len(self.swarm_subscriptions)} subscribers"
        )

        for connection in self.swarm_subscriptions:
            try:
                await connection.send_json(message)

                # Update message count
                if connection in self.connection_metadata:
                    self.connection_metadata[connection]["message_count"] += 1

            except Exception as e:
                logger.error(f"Error broadcasting to swarm subscriber: {e}")
                disconnected.append(connection)

        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get connection manager statistics

        Returns:
            Dictionary with connection stats
        """
        return {
            "total_connections": len(self.active_connections),
            "evaluation_subscriptions": {
                str(eval_id): len(subs)
                for eval_id, subs in self.evaluation_subscriptions.items()
            },
            "swarm_subscribers": len(self.swarm_subscriptions),
            "total_messages_sent": sum(
                meta["message_count"] for meta in self.connection_metadata.values()
            ),
        }


# Global connection manager instance
connection_manager = ConnectionManager()


async def handle_evaluation_websocket(
    websocket: WebSocket,
    evaluation_id: UUID,
    user_id: Optional[UUID] = None,
) -> None:
    """
    Handle WebSocket connection for a specific evaluation

    Args:
        websocket: WebSocket connection
        evaluation_id: Evaluation to subscribe to
        user_id: Optional authenticated user ID
    """
    await connection_manager.connect(websocket, user_id)
    await connection_manager.subscribe_to_evaluation(websocket, evaluation_id)

    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)

                # Handle client commands
                if message.get("type") == "ping":
                    await connection_manager.send_personal_message(
                        {
                            "type": "pong",
                            "timestamp": datetime.now().isoformat(),
                        },
                        websocket,
                    )

                elif message.get("type") == "unsubscribe":
                    await connection_manager.unsubscribe_from_evaluation(
                        websocket, evaluation_id
                    )
                    break

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received: {data}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for evaluation {evaluation_id}")
        connection_manager.disconnect(websocket)

    except Exception as e:
        logger.error(f"Error in evaluation WebSocket handler: {e}")
        connection_manager.disconnect(websocket)


async def handle_swarm_websocket(
    websocket: WebSocket,
    user_id: Optional[UUID] = None,
) -> None:
    """
    Handle WebSocket connection for swarm status updates

    Args:
        websocket: WebSocket connection
        user_id: Optional authenticated user ID
    """
    await connection_manager.connect(websocket, user_id)
    await connection_manager.subscribe_to_swarm(websocket)

    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)

                # Handle client commands
                if message.get("type") == "ping":
                    await connection_manager.send_personal_message(
                        {
                            "type": "pong",
                            "timestamp": datetime.now().isoformat(),
                        },
                        websocket,
                    )

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received: {data}")

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected from swarm status")
        connection_manager.disconnect(websocket)

    except Exception as e:
        logger.error(f"Error in swarm WebSocket handler: {e}")
        connection_manager.disconnect(websocket)


# ============================================================================
# Event Broadcasting Functions (called by orchestrator)
# ============================================================================


async def broadcast_evaluation_update(
    evaluation_id: UUID,
    update_type: str,
    data: Dict[str, Any],
) -> None:
    """
    Broadcast an evaluation update to subscribers

    Args:
        evaluation_id: Evaluation ID
        update_type: Type of update (state_change, feedback_received, etc.)
        data: Update data
    """
    message = {
        "type": "update",
        "update_type": update_type,
        "evaluation_id": str(evaluation_id),
        "data": data,
        "timestamp": datetime.now().isoformat(),
    }

    await connection_manager.broadcast_to_evaluation(evaluation_id, message)


async def broadcast_swarm_update(
    update_type: str,
    data: Dict[str, Any],
) -> None:
    """
    Broadcast a swarm status update to subscribers

    Args:
        update_type: Type of update (agent_status, metrics, etc.)
        data: Update data
    """
    message = {
        "type": "swarm_update",
        "update_type": update_type,
        "data": data,
        "timestamp": datetime.now().isoformat(),
    }

    await connection_manager.broadcast_to_swarm_subscribers(message)


async def broadcast_notification(
    notification_type: str,
    data: Dict[str, Any],
    evaluation_id: Optional[UUID] = None,
) -> None:
    """
    Broadcast a notification

    Args:
        notification_type: Type of notification
        data: Notification data
        evaluation_id: Optional evaluation ID for targeted notifications
    """
    message = {
        "type": "notification",
        "notification_type": notification_type,
        "evaluation_id": str(evaluation_id) if evaluation_id else None,
        "data": data,
        "timestamp": datetime.now().isoformat(),
    }

    if evaluation_id:
        await connection_manager.broadcast_to_evaluation(evaluation_id, message)
    else:
        await connection_manager.broadcast_to_all(message)
