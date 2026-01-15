"""
Calendar Integration

Provides calendar integration for Bloom (G-Suite/Outlook):
- Fetch meeting data for CalendarMetrics
- Analyze meeting patterns and relationships
- Schedule evaluation release discussions
- Create calendar events
- Check availability

Features:
- Multi-provider support (Google Calendar, Outlook)
- Async operations
- Meeting analytics
- Attendee relationship analysis
- Time zone handling
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from loguru import logger
from pydantic import BaseModel, Field


class CalendarProvider(str, Enum):
    """Calendar service provider"""

    GOOGLE = "google"
    OUTLOOK = "outlook"
    EXCHANGE = "exchange"


class MeetingType(str, Enum):
    """Type of calendar meeting"""

    ONE_ON_ONE = "one_on_one"
    TEAM_MEETING = "team_meeting"
    ALL_HANDS = "all_hands"
    INTERVIEW = "interview"
    EXTERNAL = "external"
    OTHER = "other"


class CalendarConfig(BaseModel):
    """Calendar integration configuration"""

    provider: CalendarProvider

    # Provider-specific credentials
    google_credentials_path: Optional[str] = None
    google_calendar_id: str = "primary"

    outlook_client_id: Optional[str] = None
    outlook_client_secret: Optional[str] = None
    outlook_tenant_id: Optional[str] = None

    # Features
    max_events_per_request: int = Field(default=2500)
    cache_duration_minutes: int = Field(default=60)
    include_declined_events: bool = Field(default=False)


class CalendarEvent(BaseModel):
    """Calendar event/meeting"""

    id: str
    summary: str
    description: Optional[str] = None
    location: Optional[str] = None

    # Timing
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    is_all_day: bool = False
    timezone: str = "UTC"

    # Participants
    organizer_email: str
    organizer_name: Optional[str] = None
    attendees: List[str] = Field(default_factory=list, description="Attendee emails")
    required_attendees: List[str] = Field(default_factory=list)
    optional_attendees: List[str] = Field(default_factory=list)
    total_attendees: int

    # Status
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None
    response_status: str = "accepted"  # accepted, declined, tentative, needsAction
    is_cancelled: bool = False

    # Classification
    meeting_type: Optional[MeetingType] = None
    is_external: bool = False
    is_one_on_one: bool = False

    # Metadata
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def calculate_duration(self) -> int:
        """
        Calculate meeting duration in minutes

        Returns:
            Duration in minutes
        """
        delta = self.end_time - self.start_time
        return int(delta.total_seconds() / 60)

    def classify_meeting_type(self) -> MeetingType:
        """
        Classify meeting type based on attendees and title

        Returns:
            Meeting type classification
        """
        # One-on-one detection
        if self.total_attendees == 2:
            self.is_one_on_one = True
            return MeetingType.ONE_ON_ONE

        # External meeting detection
        if self.is_external:
            return MeetingType.EXTERNAL

        # Pattern matching on title
        summary_lower = self.summary.lower()

        if any(keyword in summary_lower for keyword in ["interview", "candidate"]):
            return MeetingType.INTERVIEW
        elif any(keyword in summary_lower for keyword in ["all hands", "town hall", "company"]):
            return MeetingType.ALL_HANDS
        elif self.total_attendees > 10:
            return MeetingType.TEAM_MEETING

        return MeetingType.OTHER


class MeetingAnalytics(BaseModel):
    """Meeting analytics for a user"""

    user_email: str
    period_start: datetime
    period_end: datetime

    # Meeting counts
    total_meetings: int = 0
    total_days_with_meetings: int = 0
    total_hours: float = 0.0

    # Meeting breakdown
    one_on_one_count: int = 0
    one_on_one_hours: float = 0.0
    team_meeting_count: int = 0
    team_meeting_hours: float = 0.0
    external_meeting_count: int = 0
    external_meeting_hours: float = 0.0

    # Peer relationships (email -> hours)
    peer_meeting_hours: Dict[str, float] = Field(default_factory=dict)
    peer_meeting_counts: Dict[str, int] = Field(default_factory=dict)
    peer_meeting_days: Dict[str, int] = Field(default_factory=dict)

    # Team involvement (team/project name -> hours)
    team_hours: Dict[str, float] = Field(default_factory=dict)

    # Patterns
    average_meeting_duration: float = 0.0
    busiest_day_of_week: Optional[str] = None
    busiest_hour_of_day: Optional[int] = None


class CalendarIntegration:
    """
    Calendar Integration Client

    Handles calendar operations for Bloom including:
    - Fetching meeting data for metrics
    - Analyzing peer relationships
    - Scheduling evaluation discussions
    - Availability checking
    """

    def __init__(self, config: CalendarConfig):
        """
        Initialize calendar integration

        Args:
            config: Calendar configuration
        """
        self.config = config
        self.provider = config.provider

        # Cache
        self._event_cache: Dict[str, List[CalendarEvent]] = {}
        self._cache_timestamps: Dict[str, datetime] = {}

        logger.info(f"Calendar integration initialized (provider: {self.provider.value})")

    async def get_events(
        self,
        user_email: str,
        start_date: datetime,
        end_date: datetime,
        use_cache: bool = True,
    ) -> List[CalendarEvent]:
        """
        Get calendar events for user in date range

        Args:
            user_email: User email address
            start_date: Start of date range
            end_date: End of date range
            use_cache: Whether to use cached data

        Returns:
            List of calendar events

        Raises:
            RuntimeError: If fetch fails
        """
        cache_key = f"{user_email}:{start_date.date()}:{end_date.date()}"

        # Check cache
        if use_cache and cache_key in self._event_cache:
            cache_time = self._cache_timestamps[cache_key]
            age_minutes = (datetime.now() - cache_time).total_seconds() / 60

            if age_minutes < self.config.cache_duration_minutes:
                logger.debug(f"Using cached events for {user_email}")
                return self._event_cache[cache_key]

        logger.info(
            f"Fetching calendar events for {user_email} "
            f"from {start_date.date()} to {end_date.date()}"
        )

        try:
            # Fetch from provider
            if self.provider == CalendarProvider.GOOGLE:
                events = await self._fetch_google_events(user_email, start_date, end_date)
            elif self.provider == CalendarProvider.OUTLOOK:
                events = await self._fetch_outlook_events(user_email, start_date, end_date)
            else:
                raise RuntimeError(f"Unsupported calendar provider: {self.provider}")

            # Cache results
            self._event_cache[cache_key] = events
            self._cache_timestamps[cache_key] = datetime.now()

            logger.info(f"Fetched {len(events)} events for {user_email}")
            return events

        except Exception as e:
            logger.error(f"Failed to fetch calendar events: {e}")
            raise RuntimeError(f"Calendar fetch failed: {e}")

    async def _fetch_google_events(
        self,
        user_email: str,
        start_date: datetime,
        end_date: datetime,
    ) -> List[CalendarEvent]:
        """
        Fetch events from Google Calendar (simulated)

        Args:
            user_email: User email
            start_date: Start date
            end_date: End date

        Returns:
            List of events
        """
        # In production, use Google Calendar API
        logger.debug("Fetching from Google Calendar")
        await asyncio.sleep(0.1)  # Simulate API call

        # Return simulated data
        return []

    async def _fetch_outlook_events(
        self,
        user_email: str,
        start_date: datetime,
        end_date: datetime,
    ) -> List[CalendarEvent]:
        """
        Fetch events from Outlook Calendar (simulated)

        Args:
            user_email: User email
            start_date: Start date
            end_date: End date

        Returns:
            List of events
        """
        # In production, use Microsoft Graph API
        logger.debug("Fetching from Outlook Calendar")
        await asyncio.sleep(0.1)

        return []

    async def analyze_meetings(
        self,
        user_email: str,
        start_date: datetime,
        end_date: datetime,
        company_domain: str,
    ) -> MeetingAnalytics:
        """
        Analyze meeting patterns for user

        Args:
            user_email: User email address
            start_date: Analysis period start
            end_date: Analysis period end
            company_domain: Company email domain for external detection

        Returns:
            Meeting analytics
        """
        logger.info(f"Analyzing meetings for {user_email}")

        # Get events
        events = await self.get_events(user_email, start_date, end_date)

        # Initialize analytics
        analytics = MeetingAnalytics(
            user_email=user_email,
            period_start=start_date,
            period_end=end_date,
        )

        # Track unique days
        meeting_days: Set[str] = set()
        day_of_week_counts: Dict[int, int] = {i: 0 for i in range(7)}
        hour_of_day_counts: Dict[int, int] = {i: 0 for i in range(24)}

        # Process each event
        for event in events:
            # Skip declined events if configured
            if not self.config.include_declined_events:
                if event.response_status == "declined":
                    continue

            # Skip cancelled events
            if event.is_cancelled:
                continue

            # Calculate duration
            duration_hours = event.duration_minutes / 60.0

            # Update totals
            analytics.total_meetings += 1
            analytics.total_hours += duration_hours

            # Track day
            day_key = event.start_time.date().isoformat()
            meeting_days.add(day_key)

            # Track day of week and hour
            day_of_week_counts[event.start_time.weekday()] += 1
            hour_of_day_counts[event.start_time.hour] += 1

            # Classify meeting type
            meeting_type = event.classify_meeting_type()
            event.meeting_type = meeting_type

            # Update type-specific counts
            if meeting_type == MeetingType.ONE_ON_ONE:
                analytics.one_on_one_count += 1
                analytics.one_on_one_hours += duration_hours
            elif meeting_type == MeetingType.TEAM_MEETING:
                analytics.team_meeting_count += 1
                analytics.team_meeting_hours += duration_hours
            elif meeting_type == MeetingType.EXTERNAL:
                analytics.external_meeting_count += 1
                analytics.external_meeting_hours += duration_hours

            # Analyze attendees for peer relationships
            for attendee_email in event.attendees:
                # Skip self
                if attendee_email.lower() == user_email.lower():
                    continue

                # Check if external
                if not attendee_email.endswith(f"@{company_domain}"):
                    event.is_external = True
                    continue

                # Track peer interaction
                if attendee_email not in analytics.peer_meeting_hours:
                    analytics.peer_meeting_hours[attendee_email] = 0.0
                    analytics.peer_meeting_counts[attendee_email] = 0
                    analytics.peer_meeting_days[attendee_email] = 0

                analytics.peer_meeting_hours[attendee_email] += duration_hours
                analytics.peer_meeting_counts[attendee_email] += 1

                # Track unique days with this peer
                peer_day_key = f"{attendee_email}:{day_key}"
                if peer_day_key not in meeting_days:
                    analytics.peer_meeting_days[attendee_email] += 1
                    meeting_days.add(peer_day_key)

        # Calculate derived metrics
        analytics.total_days_with_meetings = len([d for d in meeting_days if ":" not in d])

        if analytics.total_meetings > 0:
            analytics.average_meeting_duration = (
                analytics.total_hours * 60 / analytics.total_meetings
            )

        # Find busiest patterns
        if day_of_week_counts:
            busiest_day = max(day_of_week_counts.items(), key=lambda x: x[1])
            day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            analytics.busiest_day_of_week = day_names[busiest_day[0]]

        if hour_of_day_counts:
            busiest_hour = max(hour_of_day_counts.items(), key=lambda x: x[1])
            analytics.busiest_hour_of_day = busiest_hour[0]

        logger.info(
            f"Meeting analysis complete: {analytics.total_meetings} meetings, "
            f"{analytics.total_hours:.1f} hours over {analytics.total_days_with_meetings} days"
        )

        return analytics

    async def get_peer_metrics(
        self,
        user_email: str,
        peer_email: str,
        lookback_years: int = 4,
        company_domain: str = "company.com",
    ) -> Dict[str, float]:
        """
        Get meeting metrics between two people

        Args:
            user_email: Primary user email
            peer_email: Peer user email
            lookback_years: Years of history to analyze
            company_domain: Company email domain

        Returns:
            Dictionary with meeting metrics
        """
        logger.info(f"Calculating peer metrics: {user_email} <-> {peer_email}")

        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * lookback_years)

        # Get all events
        events = await self.get_events(user_email, start_date, end_date)

        # Filter events with peer
        peer_events = [
            event for event in events
            if peer_email.lower() in [a.lower() for a in event.attendees]
            and not event.is_cancelled
        ]

        # Calculate metrics
        total_hours = sum(event.duration_minutes / 60.0 for event in peer_events)

        # Time period breakdowns
        now = datetime.now()
        one_year_ago = now - timedelta(days=365)
        two_years_ago = now - timedelta(days=365 * 2)

        last_year_events = [e for e in peer_events if e.start_time >= one_year_ago]
        ytd_events = [
            e for e in peer_events
            if e.start_time.year == now.year
        ]
        last_2_years_events = [e for e in peer_events if e.start_time >= two_years_ago]
        previous_2_years_events = [
            e for e in peer_events
            if two_years_ago <= e.start_time < one_year_ago
        ]

        # Calculate hours for each period
        metrics = {
            "total_hours": total_hours,
            "total_last_yr": sum(e.duration_minutes / 60.0 for e in last_year_events),
            "total_ytd": sum(e.duration_minutes / 60.0 for e in ytd_events),
            "total_last_2_years": sum(e.duration_minutes / 60.0 for e in last_2_years_events),
            "total_previous_two_yrs": sum(e.duration_minutes / 60.0 for e in previous_2_years_events),
            "total_meetings": len(peer_events),
            "total_days": len(set(e.start_time.date() for e in peer_events)),
        }

        # Calculate relationship strength (0-1 scale)
        # Based on: recency, frequency, and duration
        if total_hours > 0:
            recency_score = metrics["total_ytd"] / max(metrics["total_last_2_years"], 1)
            frequency_score = min(metrics["total_meetings"] / 50, 1.0)  # 50+ meetings = max
            duration_score = min(total_hours / 100, 1.0)  # 100+ hours = max

            relationship_strength = (
                recency_score * 0.4 +
                frequency_score * 0.3 +
                duration_score * 0.3
            )
            metrics["relationship_strength"] = min(relationship_strength, 1.0)
        else:
            metrics["relationship_strength"] = 0.0

        logger.info(
            f"Peer metrics calculated: {metrics['total_meetings']} meetings, "
            f"{total_hours:.1f} hours, strength: {metrics['relationship_strength']:.2f}"
        )

        return metrics

    async def schedule_meeting(
        self,
        title: str,
        start_time: datetime,
        duration_minutes: int,
        attendee_emails: List[str],
        description: Optional[str] = None,
        location: Optional[str] = None,
        organizer_email: Optional[str] = None,
    ) -> CalendarEvent:
        """
        Schedule a new meeting

        Args:
            title: Meeting title
            start_time: Meeting start time
            duration_minutes: Duration in minutes
            attendee_emails: List of attendee emails
            description: Meeting description
            location: Meeting location (physical or video link)
            organizer_email: Organizer email (defaults to service account)

        Returns:
            Created calendar event

        Raises:
            RuntimeError: If creation fails
        """
        logger.info(f"Scheduling meeting: {title} at {start_time}")

        end_time = start_time + timedelta(minutes=duration_minutes)

        # Create event
        event = CalendarEvent(
            id=f"event_{datetime.now().timestamp()}",
            summary=title,
            description=description,
            location=location,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration_minutes,
            organizer_email=organizer_email or "bloom@company.com",
            attendees=attendee_emails,
            total_attendees=len(attendee_emails) + 1,  # +1 for organizer
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        try:
            # Create via provider
            if self.provider == CalendarProvider.GOOGLE:
                await self._create_google_event(event)
            elif self.provider == CalendarProvider.OUTLOOK:
                await self._create_outlook_event(event)

            logger.info(f"Meeting scheduled successfully (id: {event.id})")
            return event

        except Exception as e:
            logger.error(f"Failed to schedule meeting: {e}")
            raise RuntimeError(f"Meeting scheduling failed: {e}")

    async def _create_google_event(self, event: CalendarEvent) -> None:
        """Create Google Calendar event (simulated)"""
        logger.debug("Creating Google Calendar event")
        await asyncio.sleep(0.1)

    async def _create_outlook_event(self, event: CalendarEvent) -> None:
        """Create Outlook Calendar event (simulated)"""
        logger.debug("Creating Outlook Calendar event")
        await asyncio.sleep(0.1)

    async def check_availability(
        self,
        user_email: str,
        start_time: datetime,
        end_time: datetime,
    ) -> bool:
        """
        Check if user is available during time slot

        Args:
            user_email: User email
            start_time: Slot start time
            end_time: Slot end time

        Returns:
            True if available
        """
        # Get events during this time
        events = await self.get_events(user_email, start_time, end_time, use_cache=False)

        # Check for conflicts
        for event in events:
            if event.response_status == "declined" or event.is_cancelled:
                continue

            # Check overlap
            if event.start_time < end_time and event.end_time > start_time:
                logger.debug(f"Conflict found: {event.summary}")
                return False

        return True

    async def find_available_slots(
        self,
        user_emails: List[str],
        duration_minutes: int,
        search_start: datetime,
        search_end: datetime,
        working_hours_start: int = 9,
        working_hours_end: int = 17,
    ) -> List[datetime]:
        """
        Find available time slots for multiple users

        Args:
            user_emails: List of user emails
            duration_minutes: Required duration
            search_start: Search period start
            search_end: Search period end
            working_hours_start: Start of working hours (hour)
            working_hours_end: End of working hours (hour)

        Returns:
            List of available start times
        """
        logger.info(
            f"Finding {duration_minutes}min slots for {len(user_emails)} users"
        )

        available_slots: List[datetime] = []

        # Iterate through days
        current_day = search_start.replace(hour=working_hours_start, minute=0, second=0)

        while current_day < search_end:
            # Skip weekends
            if current_day.weekday() >= 5:  # Saturday or Sunday
                current_day += timedelta(days=1)
                continue

            # Check each hour slot
            for hour in range(working_hours_start, working_hours_end):
                slot_start = current_day.replace(hour=hour, minute=0)
                slot_end = slot_start + timedelta(minutes=duration_minutes)

                # Check if all users are available
                all_available = True
                for email in user_emails:
                    if not await self.check_availability(email, slot_start, slot_end):
                        all_available = False
                        break

                if all_available:
                    available_slots.append(slot_start)

            current_day += timedelta(days=1)

        logger.info(f"Found {len(available_slots)} available slots")
        return available_slots

    def get_stats(self) -> Dict[str, Any]:
        """
        Get integration statistics

        Returns:
            Statistics dictionary
        """
        return {
            "cached_users": len(self._event_cache),
            "provider": self.provider.value,
        }
