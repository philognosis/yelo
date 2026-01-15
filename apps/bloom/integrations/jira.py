"""
Jira Integration

Provides Jira integration for Bloom:
- Fetch project involvement data
- Track completed work and contributions
- Analyze ticket/story metrics
- Sprint participation tracking
- Cross-functional collaboration metrics

Features:
- Async operations
- Multi-project support
- Custom field handling
- Advanced JQL queries
- Rate limiting and caching
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from loguru import logger
from pydantic import BaseModel, Field


class IssueType(str, Enum):
    """Jira issue types"""

    STORY = "story"
    TASK = "task"
    BUG = "bug"
    EPIC = "epic"
    SUBTASK = "subtask"
    SPIKE = "spike"


class IssueStatus(str, Enum):
    """Jira issue status"""

    TODO = "to_do"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    DONE = "done"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class JiraConfig(BaseModel):
    """Jira integration configuration"""

    base_url: str = Field(..., description="Jira instance URL")
    username: str
    api_token: str
    cloud: bool = Field(default=True, description="True for Jira Cloud, False for Server")

    # Features
    max_results_per_page: int = Field(default=100)
    cache_duration_minutes: int = Field(default=30)
    max_retries: int = Field(default=3)


class JiraIssue(BaseModel):
    """Jira issue/ticket"""

    key: str = Field(..., description="Issue key (e.g., 'PROJ-123')")
    id: str
    summary: str
    description: Optional[str] = None

    # Type and status
    issue_type: IssueType
    status: IssueStatus
    priority: Optional[str] = None

    # Project info
    project_key: str
    project_name: str

    # People
    assignee_email: Optional[str] = None
    assignee_name: Optional[str] = None
    reporter_email: Optional[str] = None
    reporter_name: Optional[str] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

    # Sprint/Epic
    sprint_id: Optional[str] = None
    sprint_name: Optional[str] = None
    epic_key: Optional[str] = None
    epic_name: Optional[str] = None

    # Metrics
    story_points: Optional[float] = None
    original_estimate_hours: Optional[float] = None
    time_spent_hours: Optional[float] = None
    remaining_hours: Optional[float] = None

    # Labels and components
    labels: List[str] = Field(default_factory=list)
    components: List[str] = Field(default_factory=list)

    # Custom fields
    custom_fields: Dict[str, Any] = Field(default_factory=dict)

    # Links
    url: Optional[str] = None


class ProjectInvolvement(BaseModel):
    """User involvement in a Jira project"""

    user_email: str
    project_key: str
    project_name: str

    # Period
    period_start: datetime
    period_end: datetime

    # Issue counts
    total_issues: int = 0
    stories_completed: int = 0
    tasks_completed: int = 0
    bugs_fixed: int = 0

    # Points/estimates
    total_story_points: float = 0.0
    total_hours_logged: float = 0.0

    # Collaboration
    issues_created: int = 0
    issues_assigned: int = 0
    issues_reviewed: int = 0  # Based on comments

    # Sprint participation
    sprints_participated: List[str] = Field(default_factory=list)
    active_sprints: int = 0

    # Epics
    epics_involved: List[str] = Field(default_factory=list)

    # Team interaction
    collaborators: Set[str] = Field(default_factory=set)  # Emails of people worked with


class JiraIntegration:
    """
    Jira Integration Client

    Handles Jira operations for Bloom including:
    - Fetching project involvement data
    - Tracking completed work
    - Analyzing collaboration patterns
    """

    def __init__(self, config: JiraConfig):
        """
        Initialize Jira integration

        Args:
            config: Jira configuration
        """
        self.config = config
        self.base_url = config.base_url.rstrip("/")

        # Cache
        self._issue_cache: Dict[str, JiraIssue] = {}
        self._query_cache: Dict[str, List[JiraIssue]] = {}
        self._cache_timestamps: Dict[str, datetime] = {}

        logger.info(f"Jira integration initialized (url: {self.base_url})")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        retry_count: int = 0,
    ) -> Dict[str, Any]:
        """
        Make Jira API request

        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            retry_count: Current retry attempt

        Returns:
            API response

        Raises:
            RuntimeError: If request fails
        """
        try:
            # In production, use aiohttp with proper authentication
            logger.debug(f"Jira API {method} {endpoint}")
            await asyncio.sleep(0.1)  # Simulate API call

            # Simulated response
            return {"issues": [], "total": 0}

        except Exception as e:
            logger.error(f"Jira API error: {e}")

            if retry_count < self.config.max_retries:
                await asyncio.sleep(2 ** retry_count)
                return await self._make_request(method, endpoint, params, retry_count + 1)

            raise RuntimeError(f"Jira API request failed: {e}")

    async def search_issues(
        self,
        jql: str,
        max_results: Optional[int] = None,
        use_cache: bool = True,
    ) -> List[JiraIssue]:
        """
        Search issues using JQL

        Args:
            jql: JQL query string
            max_results: Maximum results to return
            use_cache: Whether to use cached results

        Returns:
            List of matching issues

        Raises:
            RuntimeError: If search fails
        """
        cache_key = f"jql:{jql}:{max_results}"

        # Check cache
        if use_cache and cache_key in self._query_cache:
            cache_time = self._cache_timestamps[cache_key]
            age_minutes = (datetime.now() - cache_time).total_seconds() / 60

            if age_minutes < self.config.cache_duration_minutes:
                logger.debug(f"Using cached JQL results")
                return self._query_cache[cache_key]

        logger.info(f"Searching Jira issues: {jql}")

        issues: List[JiraIssue] = []
        start_at = 0
        max_per_page = self.config.max_results_per_page

        while True:
            # Build request
            params = {
                "jql": jql,
                "startAt": start_at,
                "maxResults": max_per_page,
                "fields": "*all",
            }

            # Make request
            response = await self._make_request("GET", "/rest/api/3/search", params)

            # Parse issues
            for issue_data in response.get("issues", []):
                issue = self._parse_issue(issue_data)
                issues.append(issue)
                self._issue_cache[issue.key] = issue

            # Check pagination
            total = response.get("total", 0)
            start_at += len(response.get("issues", []))

            if max_results and len(issues) >= max_results:
                issues = issues[:max_results]
                break

            if start_at >= total:
                break

        # Cache results
        self._query_cache[cache_key] = issues
        self._cache_timestamps[cache_key] = datetime.now()

        logger.info(f"Found {len(issues)} issues")
        return issues

    def _parse_issue(self, data: Dict[str, Any]) -> JiraIssue:
        """
        Parse Jira API issue data into JiraIssue

        Args:
            data: Raw issue data from API

        Returns:
            Parsed JiraIssue
        """
        fields = data.get("fields", {})

        # Parse dates
        created_at = self._parse_datetime(fields.get("created"))
        updated_at = self._parse_datetime(fields.get("updated"))
        resolved_at = self._parse_datetime(fields.get("resolutiondate"))

        # Parse assignee
        assignee = fields.get("assignee", {})
        assignee_email = None
        assignee_name = None
        if assignee:
            assignee_email = assignee.get("emailAddress")
            assignee_name = assignee.get("displayName")

        # Parse reporter
        reporter = fields.get("reporter", {})
        reporter_email = reporter.get("emailAddress") if reporter else None
        reporter_name = reporter.get("displayName") if reporter else None

        # Parse project
        project = fields.get("project", {})
        project_key = project.get("key", "")
        project_name = project.get("name", "")

        # Parse issue type
        issue_type_data = fields.get("issuetype", {})
        issue_type_name = issue_type_data.get("name", "").lower()
        try:
            issue_type = IssueType(issue_type_name)
        except ValueError:
            issue_type = IssueType.TASK  # Default

        # Parse status
        status_data = fields.get("status", {})
        status_name = status_data.get("name", "").lower().replace(" ", "_")
        try:
            status = IssueStatus(status_name)
        except ValueError:
            status = IssueStatus.TODO  # Default

        # Parse sprint
        sprint_field = fields.get("sprint") or fields.get("customfield_10020")
        sprint_id = None
        sprint_name = None
        if sprint_field:
            if isinstance(sprint_field, list) and len(sprint_field) > 0:
                sprint_id = str(sprint_field[0].get("id", ""))
                sprint_name = sprint_field[0].get("name")
            elif isinstance(sprint_field, dict):
                sprint_id = str(sprint_field.get("id", ""))
                sprint_name = sprint_field.get("name")

        # Parse epic
        epic_link = fields.get("customfield_10014") or fields.get("parent", {}).get("key")
        epic_name = None
        if epic_link and isinstance(epic_link, dict):
            epic_link = epic_link.get("key")
            epic_name = epic_link.get("fields", {}).get("summary")

        return JiraIssue(
            key=data["key"],
            id=data["id"],
            summary=fields.get("summary", ""),
            description=fields.get("description"),
            issue_type=issue_type,
            status=status,
            priority=fields.get("priority", {}).get("name"),
            project_key=project_key,
            project_name=project_name,
            assignee_email=assignee_email,
            assignee_name=assignee_name,
            reporter_email=reporter_email,
            reporter_name=reporter_name,
            created_at=created_at or datetime.now(),
            updated_at=updated_at or datetime.now(),
            resolved_at=resolved_at,
            sprint_id=sprint_id,
            sprint_name=sprint_name,
            epic_key=epic_link,
            epic_name=epic_name,
            story_points=fields.get("customfield_10016"),  # Common story points field
            time_spent_hours=self._seconds_to_hours(fields.get("timespent")),
            original_estimate_hours=self._seconds_to_hours(fields.get("timeoriginalestimate")),
            remaining_hours=self._seconds_to_hours(fields.get("timeremaining")),
            labels=fields.get("labels", []),
            components=[c.get("name") for c in fields.get("components", [])],
            url=f"{self.base_url}/browse/{data['key']}",
        )

    def _parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse Jira datetime string"""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception:
            return None

    def _seconds_to_hours(self, seconds: Optional[int]) -> Optional[float]:
        """Convert seconds to hours"""
        if seconds is None:
            return None
        return seconds / 3600.0

    async def get_user_involvement(
        self,
        user_email: str,
        start_date: datetime,
        end_date: datetime,
        project_keys: Optional[List[str]] = None,
    ) -> List[ProjectInvolvement]:
        """
        Get user's project involvement

        Args:
            user_email: User email address
            start_date: Analysis period start
            end_date: Analysis period end
            project_keys: Optional list of specific projects

        Returns:
            List of project involvements
        """
        logger.info(f"Analyzing Jira involvement for {user_email}")

        # Build JQL query
        jql_parts = [
            f"(assignee = '{user_email}' OR reporter = '{user_email}')",
            f"AND updated >= '{start_date.strftime('%Y-%m-%d')}'",
            f"AND updated <= '{end_date.strftime('%Y-%m-%d')}'",
        ]

        if project_keys:
            projects_str = ", ".join(project_keys)
            jql_parts.append(f"AND project IN ({projects_str})")

        jql = " ".join(jql_parts)

        # Fetch issues
        issues = await self.search_issues(jql)

        # Group by project
        projects: Dict[str, ProjectInvolvement] = {}

        for issue in issues:
            project_key = issue.project_key

            # Initialize project if needed
            if project_key not in projects:
                projects[project_key] = ProjectInvolvement(
                    user_email=user_email,
                    project_key=project_key,
                    project_name=issue.project_name,
                    period_start=start_date,
                    period_end=end_date,
                )

            involvement = projects[project_key]
            involvement.total_issues += 1

            # Count by type and completion
            if issue.status in [IssueStatus.DONE, IssueStatus.CLOSED]:
                if issue.issue_type == IssueType.STORY:
                    involvement.stories_completed += 1
                elif issue.issue_type == IssueType.TASK:
                    involvement.tasks_completed += 1
                elif issue.issue_type == IssueType.BUG:
                    involvement.bugs_fixed += 1

            # Add story points
            if issue.story_points:
                involvement.total_story_points += issue.story_points

            # Add time logged
            if issue.time_spent_hours:
                involvement.total_hours_logged += issue.time_spent_hours

            # Track creation vs assignment
            if issue.reporter_email and issue.reporter_email.lower() == user_email.lower():
                involvement.issues_created += 1

            if issue.assignee_email and issue.assignee_email.lower() == user_email.lower():
                involvement.issues_assigned += 1

            # Track sprint participation
            if issue.sprint_name and issue.sprint_name not in involvement.sprints_participated:
                involvement.sprints_participated.append(issue.sprint_name)

            # Track epics
            if issue.epic_key and issue.epic_key not in involvement.epics_involved:
                involvement.epics_involved.append(issue.epic_key)

            # Track collaborators
            if issue.assignee_email and issue.assignee_email.lower() != user_email.lower():
                involvement.collaborators.add(issue.assignee_email)
            if issue.reporter_email and issue.reporter_email.lower() != user_email.lower():
                involvement.collaborators.add(issue.reporter_email)

        # Calculate active sprints (sprints in last 30 days)
        recent_cutoff = end_date - timedelta(days=30)
        for involvement in projects.values():
            # This would need actual sprint date data
            involvement.active_sprints = len(involvement.sprints_participated)

        logger.info(f"Analyzed {len(projects)} projects with {sum(p.total_issues for p in projects.values())} total issues")

        return list(projects.values())

    async def get_issue(self, issue_key: str, use_cache: bool = True) -> Optional[JiraIssue]:
        """
        Get single issue by key

        Args:
            issue_key: Issue key (e.g., 'PROJ-123')
            use_cache: Whether to use cached data

        Returns:
            Issue or None if not found
        """
        # Check cache
        if use_cache and issue_key in self._issue_cache:
            return self._issue_cache[issue_key]

        logger.debug(f"Fetching Jira issue: {issue_key}")

        try:
            response = await self._make_request("GET", f"/rest/api/3/issue/{issue_key}")
            issue = self._parse_issue(response)
            self._issue_cache[issue_key] = issue
            return issue

        except Exception as e:
            logger.error(f"Failed to fetch issue {issue_key}: {e}")
            return None

    async def get_sprint_metrics(
        self,
        sprint_id: str,
    ) -> Dict[str, Any]:
        """
        Get metrics for a sprint

        Args:
            sprint_id: Sprint ID

        Returns:
            Sprint metrics
        """
        logger.info(f"Fetching sprint metrics: {sprint_id}")

        # Search for sprint issues
        jql = f"sprint = {sprint_id}"
        issues = await self.search_issues(jql)

        # Calculate metrics
        total_points = sum(i.story_points or 0 for i in issues)
        completed_points = sum(
            i.story_points or 0 for i in issues
            if i.status in [IssueStatus.DONE, IssueStatus.CLOSED]
        )

        participants = set()
        for issue in issues:
            if issue.assignee_email:
                participants.add(issue.assignee_email)

        return {
            "sprint_id": sprint_id,
            "total_issues": len(issues),
            "completed_issues": sum(1 for i in issues if i.status in [IssueStatus.DONE, IssueStatus.CLOSED]),
            "total_points": total_points,
            "completed_points": completed_points,
            "completion_rate": completed_points / total_points if total_points > 0 else 0,
            "participants": list(participants),
            "participant_count": len(participants),
        }

    def get_stats(self) -> Dict[str, Any]:
        """
        Get integration statistics

        Returns:
            Statistics dictionary
        """
        return {
            "cached_issues": len(self._issue_cache),
            "cached_queries": len(self._query_cache),
            "base_url": self.base_url,
        }
