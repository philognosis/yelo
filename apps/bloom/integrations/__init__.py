"""
Enterprise Integrations

Provides integrations with enterprise systems for Bloom:
- Slack: Team communication and notifications
- Email: Email notifications and tracking
- Calendar: Meeting data and scheduling (G-Suite/Outlook)
- Jira: Project involvement tracking
- Git: Code contribution metrics (GitHub/GitLab)

All integrations support:
- Async operations
- Error handling and retries
- Rate limiting
- Credential management
- Comprehensive logging
"""

from bloom.integrations.calendar import CalendarIntegration
from bloom.integrations.email import EmailIntegration
from bloom.integrations.git import GitIntegration
from bloom.integrations.jira import JiraIntegration
from bloom.integrations.slack import SlackIntegration

__all__ = [
    "SlackIntegration",
    "EmailIntegration",
    "CalendarIntegration",
    "JiraIntegration",
    "GitIntegration",
]
