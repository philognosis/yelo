"""
Slack Integration

Provides Slack messaging capabilities for Bloom notifications:
- Send channel messages
- Send direct messages
- Interactive buttons and responses
- Voice note transcription link sharing
- Message threading
- Rich formatting with blocks

Features:
- Async support
- Automatic retries with exponential backoff
- Rate limiting
- Error handling
- Message tracking
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from loguru import logger
from pydantic import BaseModel, Field


class SlackConfig(BaseModel):
    """Slack integration configuration"""

    bot_token: str = Field(..., description="Slack bot OAuth token")
    app_token: Optional[str] = Field(None, description="Slack app-level token (for socket mode)")
    signing_secret: str = Field(..., description="Slack signing secret for request verification")
    workspace_id: str = Field(..., description="Slack workspace ID")

    # Rate limiting
    max_requests_per_minute: int = Field(default=60, description="API rate limit")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    retry_delay_seconds: float = Field(default=1.0, description="Initial retry delay")

    # Features
    enable_threading: bool = Field(default=True, description="Enable message threading")
    enable_notifications: bool = Field(default=True, description="Enable @mention notifications")


class SlackMessage(BaseModel):
    """Slack message model"""

    id: UUID
    channel_id: str
    user_id: Optional[str] = None
    text: str
    blocks: Optional[List[Dict[str, Any]]] = None
    thread_ts: Optional[str] = Field(None, description="Thread timestamp for replies")
    attachments: Optional[List[Dict[str, Any]]] = None

    # Tracking
    sent_at: Optional[datetime] = None
    slack_ts: Optional[str] = Field(None, description="Slack message timestamp")
    permalink: Optional[str] = None

    # Interactions
    has_buttons: bool = False
    button_responses: List[Dict[str, Any]] = Field(default_factory=list)


class SlackUser(BaseModel):
    """Slack user profile"""

    user_id: str
    email: str
    real_name: str
    display_name: str
    is_bot: bool = False
    is_admin: bool = False
    avatar_url: Optional[str] = None


class SlackIntegration:
    """
    Slack Integration Client

    Handles all Slack API interactions for Bloom including:
    - Sending messages and DMs
    - Interactive components (buttons, menus)
    - Voice note transcription links
    - User lookup and management
    """

    def __init__(self, config: SlackConfig):
        """
        Initialize Slack integration

        Args:
            config: Slack configuration
        """
        self.config = config
        self.bot_token = config.bot_token
        self.signing_secret = config.signing_secret

        # Rate limiting
        self._request_timestamps: List[datetime] = []
        self._rate_limit_lock = asyncio.Lock()

        # Cache
        self._user_cache: Dict[str, SlackUser] = {}
        self._channel_cache: Dict[str, Dict[str, Any]] = {}

        # Message tracking
        self._sent_messages: Dict[UUID, SlackMessage] = {}

        logger.info("Slack integration initialized")

    async def _check_rate_limit(self) -> None:
        """
        Check and enforce rate limiting

        Raises:
            RuntimeError: If rate limit exceeded
        """
        async with self._rate_limit_lock:
            now = datetime.now()
            cutoff = now - timedelta(minutes=1)

            # Remove old timestamps
            self._request_timestamps = [
                ts for ts in self._request_timestamps if ts > cutoff
            ]

            # Check if at limit
            if len(self._request_timestamps) >= self.config.max_requests_per_minute:
                # Calculate wait time
                oldest = self._request_timestamps[0]
                wait_seconds = 60 - (now - oldest).total_seconds()
                logger.warning(f"Rate limit reached, waiting {wait_seconds:.1f}s")
                await asyncio.sleep(wait_seconds)

            # Add current request
            self._request_timestamps.append(now)

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        retry_count: int = 0,
    ) -> Dict[str, Any]:
        """
        Make Slack API request with retries

        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request payload
            retry_count: Current retry attempt

        Returns:
            API response data

        Raises:
            RuntimeError: If request fails after retries
        """
        await self._check_rate_limit()

        try:
            # In production, this would use aiohttp or httpx
            # For now, we'll simulate the request
            logger.debug(f"Slack API {method} {endpoint}")

            # Simulate successful response
            response = {
                "ok": True,
                "ts": datetime.now().timestamp(),
                "message": data,
            }

            return response

        except Exception as e:
            logger.error(f"Slack API error: {e}")

            # Retry with exponential backoff
            if retry_count < self.config.max_retries:
                delay = self.config.retry_delay_seconds * (2 ** retry_count)
                logger.info(f"Retrying in {delay}s (attempt {retry_count + 1})")
                await asyncio.sleep(delay)
                return await self._make_request(method, endpoint, data, retry_count + 1)

            raise RuntimeError(f"Slack API request failed: {e}")

    async def send_message(
        self,
        channel_id: str,
        text: str,
        blocks: Optional[List[Dict[str, Any]]] = None,
        thread_ts: Optional[str] = None,
        notification_id: Optional[UUID] = None,
    ) -> SlackMessage:
        """
        Send message to Slack channel

        Args:
            channel_id: Channel ID (e.g., 'C1234567890')
            text: Message text (also used as fallback for blocks)
            blocks: Optional Block Kit blocks for rich formatting
            thread_ts: Optional thread timestamp to reply in thread
            notification_id: Optional notification ID for tracking

        Returns:
            Sent message details

        Raises:
            RuntimeError: If send fails
        """
        logger.info(f"Sending Slack message to channel {channel_id}")

        # Build request payload
        payload = {
            "channel": channel_id,
            "text": text,
        }

        if blocks:
            payload["blocks"] = blocks

        if thread_ts and self.config.enable_threading:
            payload["thread_ts"] = thread_ts

        # Send message
        response = await self._make_request("POST", "chat.postMessage", payload)

        # Create message record
        message = SlackMessage(
            id=notification_id or UUID(int=0),  # Placeholder
            channel_id=channel_id,
            text=text,
            blocks=blocks,
            thread_ts=thread_ts,
            sent_at=datetime.now(),
            slack_ts=str(response.get("ts")),
            has_buttons=blocks is not None and any(
                block.get("type") == "actions" for block in blocks
            ) if blocks else False,
        )

        # Track message
        if notification_id:
            self._sent_messages[notification_id] = message

        logger.info(f"Message sent successfully (ts: {message.slack_ts})")
        return message

    async def send_dm(
        self,
        user_id: str,
        text: str,
        blocks: Optional[List[Dict[str, Any]]] = None,
        notification_id: Optional[UUID] = None,
    ) -> SlackMessage:
        """
        Send direct message to user

        Args:
            user_id: Slack user ID
            text: Message text
            blocks: Optional Block Kit blocks
            notification_id: Optional notification ID

        Returns:
            Sent message details

        Raises:
            RuntimeError: If send fails
        """
        logger.info(f"Sending Slack DM to user {user_id}")

        # Open DM channel
        dm_response = await self._make_request(
            "POST",
            "conversations.open",
            {"users": user_id}
        )

        channel_id = dm_response.get("channel", {}).get("id")
        if not channel_id:
            raise RuntimeError(f"Failed to open DM channel for user {user_id}")

        # Send message to DM channel
        return await self.send_message(
            channel_id=channel_id,
            text=text,
            blocks=blocks,
            notification_id=notification_id,
        )

    async def send_interactive_message(
        self,
        channel_id: str,
        text: str,
        buttons: List[Dict[str, str]],
        notification_id: Optional[UUID] = None,
    ) -> SlackMessage:
        """
        Send message with interactive buttons

        Args:
            channel_id: Channel ID or user ID for DM
            text: Message text
            buttons: List of button definitions [{"text": "...", "value": "...", "style": "..."}]
            notification_id: Optional notification ID

        Returns:
            Sent message details

        Example:
            buttons = [
                {"text": "Approve", "value": "approve", "style": "primary"},
                {"text": "Reject", "value": "reject", "style": "danger"},
            ]
        """
        logger.info(f"Sending interactive message with {len(buttons)} buttons")

        # Build Block Kit blocks with buttons
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": text,
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": btn["text"],
                        },
                        "value": btn["value"],
                        "action_id": f"button_{btn['value']}",
                        "style": btn.get("style", "default"),
                    }
                    for btn in buttons
                ]
            }
        ]

        return await self.send_message(
            channel_id=channel_id,
            text=text,
            blocks=blocks,
            notification_id=notification_id,
        )

    async def send_voice_note_link(
        self,
        channel_id: str,
        transcription_url: str,
        context: str,
        user_mention: Optional[str] = None,
    ) -> SlackMessage:
        """
        Send voice note transcription link

        Args:
            channel_id: Channel ID or user ID
            transcription_url: URL to voice note transcription
            context: Context message (e.g., "Provide feedback for...")
            user_mention: Optional user ID to mention

        Returns:
            Sent message details
        """
        logger.info(f"Sending voice note link to {channel_id}")

        # Build message with link
        mention = f"<@{user_mention}> " if user_mention else ""
        text = (
            f"{mention}{context}\n\n"
            f"Record your feedback using voice: {transcription_url}\n\n"
            f"_Your voice note will be automatically transcribed and formatted._"
        )

        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{mention}*{context}*",
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Record your feedback using voice:",
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Record Voice Feedback",
                            "emoji": True,
                        },
                        "url": transcription_url,
                        "action_id": "voice_feedback",
                        "style": "primary",
                    }
                ]
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "_Your voice note will be automatically transcribed and formatted._",
                    }
                ]
            }
        ]

        return await self.send_message(
            channel_id=channel_id,
            text=text,
            blocks=blocks,
        )

    async def handle_button_response(
        self,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Handle button interaction response

        Args:
            payload: Slack interaction payload

        Returns:
            Response data
        """
        action = payload.get("actions", [{}])[0]
        action_id = action.get("action_id")
        value = action.get("value")
        user_id = payload.get("user", {}).get("id")
        message_ts = payload.get("message", {}).get("ts")

        logger.info(f"Button clicked: {action_id}={value} by user {user_id}")

        # Track response
        response_data = {
            "action_id": action_id,
            "value": value,
            "user_id": user_id,
            "message_ts": message_ts,
            "timestamp": datetime.now().isoformat(),
        }

        # Find message and record response
        for msg in self._sent_messages.values():
            if msg.slack_ts == message_ts:
                msg.button_responses.append(response_data)
                break

        return response_data

    async def get_user_by_email(self, email: str) -> Optional[SlackUser]:
        """
        Get Slack user by email address

        Args:
            email: User email address

        Returns:
            Slack user or None if not found
        """
        # Check cache
        if email in self._user_cache:
            return self._user_cache[email]

        logger.debug(f"Looking up Slack user by email: {email}")

        try:
            response = await self._make_request(
                "GET",
                "users.lookupByEmail",
                {"email": email}
            )

            user_data = response.get("user", {})
            if not user_data:
                logger.warning(f"Slack user not found for email: {email}")
                return None

            # Parse user data
            profile = user_data.get("profile", {})
            user = SlackUser(
                user_id=user_data["id"],
                email=profile.get("email", email),
                real_name=profile.get("real_name", ""),
                display_name=profile.get("display_name", ""),
                is_bot=user_data.get("is_bot", False),
                is_admin=user_data.get("is_admin", False),
                avatar_url=profile.get("image_192"),
            )

            # Cache user
            self._user_cache[email] = user

            logger.info(f"Found Slack user: {user.display_name} ({user.user_id})")
            return user

        except Exception as e:
            logger.error(f"Failed to lookup user by email: {e}")
            return None

    async def update_message(
        self,
        channel_id: str,
        message_ts: str,
        text: str,
        blocks: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        """
        Update existing message

        Args:
            channel_id: Channel containing message
            message_ts: Message timestamp
            text: New message text
            blocks: New blocks (optional)

        Returns:
            True if updated successfully
        """
        logger.info(f"Updating Slack message {message_ts}")

        payload = {
            "channel": channel_id,
            "ts": message_ts,
            "text": text,
        }

        if blocks:
            payload["blocks"] = blocks

        try:
            await self._make_request("POST", "chat.update", payload)
            return True
        except Exception as e:
            logger.error(f"Failed to update message: {e}")
            return False

    async def delete_message(
        self,
        channel_id: str,
        message_ts: str,
    ) -> bool:
        """
        Delete message

        Args:
            channel_id: Channel containing message
            message_ts: Message timestamp

        Returns:
            True if deleted successfully
        """
        logger.info(f"Deleting Slack message {message_ts}")

        try:
            await self._make_request(
                "POST",
                "chat.delete",
                {"channel": channel_id, "ts": message_ts}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete message: {e}")
            return False

    async def add_reaction(
        self,
        channel_id: str,
        message_ts: str,
        emoji: str,
    ) -> bool:
        """
        Add emoji reaction to message

        Args:
            channel_id: Channel containing message
            message_ts: Message timestamp
            emoji: Emoji name (without colons, e.g., 'thumbsup')

        Returns:
            True if added successfully
        """
        logger.debug(f"Adding reaction :{emoji}: to message {message_ts}")

        try:
            await self._make_request(
                "POST",
                "reactions.add",
                {
                    "channel": channel_id,
                    "timestamp": message_ts,
                    "name": emoji,
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to add reaction: {e}")
            return False

    async def get_message_permalink(
        self,
        channel_id: str,
        message_ts: str,
    ) -> Optional[str]:
        """
        Get permanent link to message

        Args:
            channel_id: Channel containing message
            message_ts: Message timestamp

        Returns:
            Permalink URL or None
        """
        try:
            response = await self._make_request(
                "GET",
                "chat.getPermalink",
                {
                    "channel": channel_id,
                    "message_ts": message_ts,
                }
            )
            return response.get("permalink")
        except Exception as e:
            logger.error(f"Failed to get permalink: {e}")
            return None

    def format_user_mention(self, user_id: str) -> str:
        """
        Format user mention for Slack

        Args:
            user_id: Slack user ID

        Returns:
            Formatted mention string
        """
        return f"<@{user_id}>"

    def format_channel_mention(self, channel_id: str) -> str:
        """
        Format channel mention for Slack

        Args:
            channel_id: Slack channel ID

        Returns:
            Formatted mention string
        """
        return f"<#{channel_id}>"

    def format_link(self, url: str, text: str) -> str:
        """
        Format link for Slack

        Args:
            url: URL
            text: Link text

        Returns:
            Formatted link string
        """
        return f"<{url}|{text}>"

    def get_stats(self) -> Dict[str, Any]:
        """
        Get integration statistics

        Returns:
            Statistics dictionary
        """
        return {
            "total_messages_sent": len(self._sent_messages),
            "cached_users": len(self._user_cache),
            "cached_channels": len(self._channel_cache),
            "recent_requests": len(self._request_timestamps),
        }
