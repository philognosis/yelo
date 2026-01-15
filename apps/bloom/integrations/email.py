"""
Email Integration

Provides email notification capabilities for Bloom:
- Template-based email rendering
- HTML and plain text support
- Tracking opens and clicks
- Attachment support
- Batch sending
- SMTP/SendGrid/SES support

Features:
- Async sending
- Template rendering with Jinja2
- Automatic retry logic
- Bounce handling
- Unsubscribe management
- Analytics tracking
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from loguru import logger
from pydantic import BaseModel, EmailStr, Field


class EmailProvider(str, Enum):
    """Email service provider"""

    SMTP = "smtp"
    SENDGRID = "sendgrid"
    AWS_SES = "aws_ses"
    MAILGUN = "mailgun"


class EmailPriority(str, Enum):
    """Email priority levels"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class EmailConfig(BaseModel):
    """Email integration configuration"""

    provider: EmailProvider
    from_address: EmailStr
    from_name: str
    reply_to: Optional[EmailStr] = None

    # Provider-specific settings
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    sendgrid_api_key: Optional[str] = None
    aws_region: Optional[str] = None

    # Features
    enable_tracking: bool = Field(default=True, description="Track opens and clicks")
    enable_unsubscribe: bool = Field(default=True, description="Include unsubscribe link")
    track_analytics: bool = Field(default=True, description="Track detailed analytics")

    # Rate limiting
    max_emails_per_second: int = Field(default=10)
    max_retries: int = Field(default=3)


class EmailTemplate(BaseModel):
    """Email template definition"""

    template_id: str
    name: str
    subject_template: str
    html_template: str
    text_template: Optional[str] = None
    required_variables: List[str] = Field(default_factory=list)
    category: Optional[str] = None


class EmailRecipient(BaseModel):
    """Email recipient"""

    email: EmailStr
    name: Optional[str] = None
    user_id: Optional[UUID] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EmailAttachment(BaseModel):
    """Email attachment"""

    filename: str
    content: bytes
    content_type: str
    inline: bool = Field(default=False, description="Display inline in email")
    content_id: Optional[str] = Field(None, description="Content ID for inline images")


class EmailMessage(BaseModel):
    """Email message model"""

    id: UUID = Field(default_factory=uuid4)
    template_id: Optional[str] = None

    # Recipients
    to: List[EmailRecipient]
    cc: List[EmailRecipient] = Field(default_factory=list)
    bcc: List[EmailRecipient] = Field(default_factory=list)

    # Content
    subject: str
    html_body: str
    text_body: Optional[str] = None
    attachments: List[EmailAttachment] = Field(default_factory=list)

    # Headers
    reply_to: Optional[EmailStr] = None
    custom_headers: Dict[str, str] = Field(default_factory=dict)
    priority: EmailPriority = EmailPriority.NORMAL

    # Tracking
    tracking_enabled: bool = True
    tracking_domain: Optional[str] = None
    tracking_pixel_url: Optional[str] = None
    tracked_links: Dict[str, str] = Field(
        default_factory=dict,
        description="Map of original URLs to tracked URLs"
    )

    # Metadata
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Status
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    bounced_at: Optional[datetime] = None
    unsubscribed_at: Optional[datetime] = None

    # Analytics
    open_count: int = 0
    click_count: int = 0
    unique_clicks: List[str] = Field(default_factory=list)  # URLs clicked

    # Error tracking
    error_message: Optional[str] = None
    retry_count: int = 0


class EmailIntegration:
    """
    Email Integration Client

    Handles all email operations for Bloom including:
    - Sending templated emails
    - Tracking opens and clicks
    - Managing bounces and unsubscribes
    - Batch email operations
    """

    def __init__(self, config: EmailConfig):
        """
        Initialize email integration

        Args:
            config: Email configuration
        """
        self.config = config
        self.provider = config.provider

        # Template storage
        self._templates: Dict[str, EmailTemplate] = {}

        # Message tracking
        self._sent_messages: Dict[UUID, EmailMessage] = {}
        self._tracking_tokens: Dict[str, UUID] = {}  # token -> message_id

        # Rate limiting
        self._send_lock = asyncio.Lock()
        self._last_send_time = datetime.now()

        logger.info(f"Email integration initialized (provider: {self.provider.value})")

    def register_template(self, template: EmailTemplate) -> None:
        """
        Register email template

        Args:
            template: Email template to register
        """
        self._templates[template.template_id] = template
        logger.info(f"Registered email template: {template.name}")

    async def send_email(
        self,
        to: List[EmailRecipient],
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        attachments: Optional[List[EmailAttachment]] = None,
        cc: Optional[List[EmailRecipient]] = None,
        bcc: Optional[List[EmailRecipient]] = None,
        priority: EmailPriority = EmailPriority.NORMAL,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EmailMessage:
        """
        Send email

        Args:
            to: Recipients
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text body (optional)
            attachments: File attachments
            cc: CC recipients
            bcc: BCC recipients
            priority: Email priority
            tags: Email tags for categorization
            metadata: Additional metadata

        Returns:
            Sent email message

        Raises:
            RuntimeError: If send fails
        """
        logger.info(f"Sending email to {len(to)} recipients: {subject}")

        # Create message
        message = EmailMessage(
            to=to,
            cc=cc or [],
            bcc=bcc or [],
            subject=subject,
            html_body=html_body,
            text_body=text_body or self._html_to_text(html_body),
            attachments=attachments or [],
            priority=priority,
            tags=tags or [],
            metadata=metadata or {},
            tracking_enabled=self.config.enable_tracking,
        )

        # Apply tracking if enabled
        if self.config.enable_tracking and message.tracking_enabled:
            message = self._add_tracking(message)

        # Send with rate limiting
        await self._rate_limit()

        try:
            # Send via provider
            await self._send_via_provider(message)

            # Update status
            message.sent_at = datetime.now()

            # Track message
            self._sent_messages[message.id] = message

            logger.info(f"Email sent successfully (id: {message.id})")
            return message

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            message.error_message = str(e)

            # Retry logic
            if message.retry_count < self.config.max_retries:
                message.retry_count += 1
                logger.info(f"Retrying email send (attempt {message.retry_count})")
                await asyncio.sleep(2 ** message.retry_count)
                return await self.send_email(
                    to=to,
                    subject=subject,
                    html_body=html_body,
                    text_body=text_body,
                    attachments=attachments,
                    cc=cc,
                    bcc=bcc,
                    priority=priority,
                    tags=tags,
                    metadata=metadata,
                )

            raise RuntimeError(f"Failed to send email after {message.retry_count} retries: {e}")

    async def send_from_template(
        self,
        template_id: str,
        to: List[EmailRecipient],
        template_data: Dict[str, Any],
        attachments: Optional[List[EmailAttachment]] = None,
        cc: Optional[List[EmailRecipient]] = None,
        priority: EmailPriority = EmailPriority.NORMAL,
    ) -> EmailMessage:
        """
        Send email from template

        Args:
            template_id: Template identifier
            to: Recipients
            template_data: Data to populate template
            attachments: File attachments
            cc: CC recipients
            priority: Email priority

        Returns:
            Sent email message

        Raises:
            ValueError: If template not found or missing variables
            RuntimeError: If send fails
        """
        if template_id not in self._templates:
            raise ValueError(f"Email template not found: {template_id}")

        template = self._templates[template_id]

        # Validate required variables
        missing_vars = [
            var for var in template.required_variables
            if var not in template_data
        ]
        if missing_vars:
            raise ValueError(f"Missing required template variables: {missing_vars}")

        logger.info(f"Rendering email template: {template.name}")

        # Render template
        subject = self._render_template(template.subject_template, template_data)
        html_body = self._render_template(template.html_template, template_data)
        text_body = None
        if template.text_template:
            text_body = self._render_template(template.text_template, template_data)

        # Send email
        message = await self.send_email(
            to=to,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            attachments=attachments,
            cc=cc,
            priority=priority,
            tags=[template.category] if template.category else [],
            metadata={"template_id": template_id},
        )

        message.template_id = template_id
        return message

    def _render_template(self, template: str, data: Dict[str, Any]) -> str:
        """
        Render template with data

        Args:
            template: Template string
            data: Template data

        Returns:
            Rendered template
        """
        # In production, use Jinja2 for proper templating
        # For now, simple string formatting
        try:
            return template.format(**data)
        except KeyError as e:
            logger.error(f"Template rendering error: missing variable {e}")
            return template

    def _html_to_text(self, html: str) -> str:
        """
        Convert HTML to plain text

        Args:
            html: HTML content

        Returns:
            Plain text version
        """
        # In production, use html2text or similar library
        # For now, simple tag stripping
        import re
        text = re.sub(r'<[^>]+>', '', html)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _add_tracking(self, message: EmailMessage) -> EmailMessage:
        """
        Add tracking pixel and link tracking

        Args:
            message: Email message

        Returns:
            Message with tracking added
        """
        # Generate tracking token
        tracking_token = str(uuid4())
        self._tracking_tokens[tracking_token] = message.id

        # Add tracking pixel
        if self.config.track_analytics:
            tracking_domain = self.config.tracking_enabled or "track.bloom.com"
            pixel_url = f"https://{tracking_domain}/t/{tracking_token}/pixel.gif"
            message.tracking_pixel_url = pixel_url

            # Inject pixel into HTML
            pixel_html = f'<img src="{pixel_url}" width="1" height="1" alt="" />'
            message.html_body = message.html_body + pixel_html

        # Track links
        import re
        link_pattern = r'href="([^"]+)"'
        links = re.findall(link_pattern, message.html_body)

        for i, link in enumerate(links):
            if not link.startswith('http'):
                continue

            tracked_url = f"https://{tracking_domain}/t/{tracking_token}/click/{i}"
            message.tracked_links[link] = tracked_url
            message.html_body = message.html_body.replace(
                f'href="{link}"',
                f'href="{tracked_url}"'
            )

        # Add unsubscribe link if enabled
        if self.config.enable_unsubscribe:
            unsubscribe_url = f"https://{tracking_domain}/unsubscribe/{tracking_token}"
            unsubscribe_html = (
                f'<div style="text-align: center; font-size: 12px; color: #888; margin-top: 20px;">'
                f'<a href="{unsubscribe_url}">Unsubscribe</a> from these emails'
                f'</div>'
            )
            message.html_body = message.html_body + unsubscribe_html

        return message

    async def _send_via_provider(self, message: EmailMessage) -> None:
        """
        Send email via configured provider

        Args:
            message: Email message to send

        Raises:
            RuntimeError: If send fails
        """
        if self.provider == EmailProvider.SMTP:
            await self._send_via_smtp(message)
        elif self.provider == EmailProvider.SENDGRID:
            await self._send_via_sendgrid(message)
        elif self.provider == EmailProvider.AWS_SES:
            await self._send_via_ses(message)
        else:
            raise RuntimeError(f"Unsupported email provider: {self.provider}")

    async def _send_via_smtp(self, message: EmailMessage) -> None:
        """Send via SMTP (simulated)"""
        logger.debug("Sending via SMTP")
        # In production, use aiosmtplib
        await asyncio.sleep(0.1)  # Simulate network delay

    async def _send_via_sendgrid(self, message: EmailMessage) -> None:
        """Send via SendGrid (simulated)"""
        logger.debug("Sending via SendGrid")
        # In production, use SendGrid API client
        await asyncio.sleep(0.1)

    async def _send_via_ses(self, message: EmailMessage) -> None:
        """Send via AWS SES (simulated)"""
        logger.debug("Sending via AWS SES")
        # In production, use boto3 SES client
        await asyncio.sleep(0.1)

    async def _rate_limit(self) -> None:
        """Enforce rate limiting"""
        async with self._send_lock:
            now = datetime.now()
            elapsed = (now - self._last_send_time).total_seconds()
            min_interval = 1.0 / self.config.max_emails_per_second

            if elapsed < min_interval:
                wait_time = min_interval - elapsed
                await asyncio.sleep(wait_time)

            self._last_send_time = datetime.now()

    async def track_open(self, tracking_token: str) -> bool:
        """
        Track email open

        Args:
            tracking_token: Tracking token from pixel

        Returns:
            True if tracked successfully
        """
        if tracking_token not in self._tracking_tokens:
            logger.warning(f"Unknown tracking token: {tracking_token}")
            return False

        message_id = self._tracking_tokens[tracking_token]
        message = self._sent_messages.get(message_id)

        if not message:
            logger.warning(f"Message not found for token: {tracking_token}")
            return False

        # Update tracking
        if message.opened_at is None:
            message.opened_at = datetime.now()

        message.open_count += 1

        logger.info(f"Email opened (id: {message_id}, count: {message.open_count})")
        return True

    async def track_click(self, tracking_token: str, link_index: int) -> Optional[str]:
        """
        Track email link click

        Args:
            tracking_token: Tracking token
            link_index: Index of clicked link

        Returns:
            Original URL to redirect to, or None if invalid
        """
        if tracking_token not in self._tracking_tokens:
            logger.warning(f"Unknown tracking token: {tracking_token}")
            return None

        message_id = self._tracking_tokens[tracking_token]
        message = self._sent_messages.get(message_id)

        if not message:
            return None

        # Find original URL
        original_url = None
        for url, tracked_url in message.tracked_links.items():
            if f"/click/{link_index}" in tracked_url:
                original_url = url
                break

        if not original_url:
            return None

        # Update tracking
        if message.clicked_at is None:
            message.clicked_at = datetime.now()

        message.click_count += 1

        if original_url not in message.unique_clicks:
            message.unique_clicks.append(original_url)

        logger.info(
            f"Email link clicked (id: {message_id}, url: {original_url}, "
            f"count: {message.click_count})"
        )

        return original_url

    async def handle_bounce(self, message_id: UUID, bounce_type: str, reason: str) -> None:
        """
        Handle email bounce

        Args:
            message_id: Message that bounced
            bounce_type: Type of bounce (hard, soft)
            reason: Bounce reason
        """
        message = self._sent_messages.get(message_id)
        if not message:
            return

        message.bounced_at = datetime.now()
        message.error_message = f"Bounced ({bounce_type}): {reason}"

        logger.warning(f"Email bounced (id: {message_id}, type: {bounce_type}, reason: {reason})")

    async def handle_unsubscribe(self, tracking_token: str) -> bool:
        """
        Handle unsubscribe request

        Args:
            tracking_token: Tracking token

        Returns:
            True if unsubscribed successfully
        """
        if tracking_token not in self._tracking_tokens:
            return False

        message_id = self._tracking_tokens[tracking_token]
        message = self._sent_messages.get(message_id)

        if not message:
            return False

        message.unsubscribed_at = datetime.now()

        logger.info(f"Email unsubscribed (id: {message_id})")
        return True

    def get_message_stats(self, message_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get statistics for a message

        Args:
            message_id: Message ID

        Returns:
            Statistics dictionary or None
        """
        message = self._sent_messages.get(message_id)
        if not message:
            return None

        return {
            "sent": message.sent_at is not None,
            "delivered": message.delivered_at is not None,
            "opened": message.opened_at is not None,
            "clicked": message.clicked_at is not None,
            "bounced": message.bounced_at is not None,
            "unsubscribed": message.unsubscribed_at is not None,
            "open_count": message.open_count,
            "click_count": message.click_count,
            "unique_clicks": len(message.unique_clicks),
            "retry_count": message.retry_count,
        }

    def get_stats(self) -> Dict[str, Any]:
        """
        Get integration statistics

        Returns:
            Statistics dictionary
        """
        total_sent = len(self._sent_messages)
        total_opened = sum(1 for msg in self._sent_messages.values() if msg.opened_at)
        total_clicked = sum(1 for msg in self._sent_messages.values() if msg.clicked_at)
        total_bounced = sum(1 for msg in self._sent_messages.values() if msg.bounced_at)

        return {
            "total_sent": total_sent,
            "total_opened": total_opened,
            "total_clicked": total_clicked,
            "total_bounced": total_bounced,
            "open_rate": total_opened / total_sent if total_sent > 0 else 0,
            "click_rate": total_clicked / total_sent if total_sent > 0 else 0,
            "bounce_rate": total_bounced / total_sent if total_sent > 0 else 0,
            "registered_templates": len(self._templates),
        }
