"""
Git Integration

Provides Git integration for Bloom (GitHub/GitLab):
- Fetch contribution metrics
- Analyze code review participation
- Track commits, PRs, and reviews
- Calculate code collaboration patterns
- Measure engineering impact

Features:
- Multi-platform support (GitHub, GitLab, Bitbucket)
- Async operations
- Contribution analysis
- Code review metrics
- Team collaboration tracking
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from loguru import logger
from pydantic import BaseModel, Field


class GitProvider(str, Enum):
    """Git service provider"""

    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"


class PRState(str, Enum):
    """Pull request state"""

    OPEN = "open"
    MERGED = "merged"
    CLOSED = "closed"
    DRAFT = "draft"


class ReviewState(str, Enum):
    """Code review state"""

    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    COMMENTED = "commented"
    PENDING = "pending"


class GitConfig(BaseModel):
    """Git integration configuration"""

    provider: GitProvider
    base_url: Optional[str] = Field(None, description="Custom instance URL (for self-hosted)")

    # Authentication
    access_token: str
    organization: Optional[str] = Field(None, description="GitHub org or GitLab group")

    # Features
    max_results_per_page: int = Field(default=100)
    cache_duration_minutes: int = Field(default=30)
    include_forks: bool = Field(default=False)
    include_archived: bool = Field(default=False)


class Commit(BaseModel):
    """Git commit"""

    sha: str
    message: str
    author_email: str
    author_name: str
    committer_email: str
    committer_name: str

    # Timing
    authored_at: datetime
    committed_at: datetime

    # Repository
    repo_name: str
    repo_full_name: str
    branch: Optional[str] = None

    # Metrics
    additions: int = 0
    deletions: int = 0
    changed_files: int = 0
    total_changes: int = 0

    # URL
    url: Optional[str] = None


class PullRequest(BaseModel):
    """Pull request / Merge request"""

    id: str
    number: int
    title: str
    description: Optional[str] = None
    state: PRState

    # Repository
    repo_name: str
    repo_full_name: str

    # People
    author_email: str
    author_name: str
    merged_by_email: Optional[str] = None
    merged_by_name: Optional[str] = None

    # Branches
    source_branch: str
    target_branch: str

    # Timestamps
    created_at: datetime
    updated_at: datetime
    merged_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

    # Metrics
    additions: int = 0
    deletions: int = 0
    changed_files: int = 0
    commits_count: int = 0
    comments_count: int = 0

    # Reviews
    reviews: List[Dict[str, Any]] = Field(default_factory=list)
    reviewers: List[str] = Field(default_factory=list, description="Reviewer emails")
    approved_by: List[str] = Field(default_factory=list)
    changes_requested_by: List[str] = Field(default_factory=list)

    # Labels and metadata
    labels: List[str] = Field(default_factory=list)
    is_draft: bool = False

    # URL
    url: Optional[str] = None

    def get_time_to_merge(self) -> Optional[timedelta]:
        """
        Calculate time from creation to merge

        Returns:
            Time delta or None if not merged
        """
        if not self.merged_at:
            return None
        return self.merged_at - self.created_at


class CodeReview(BaseModel):
    """Code review on a pull request"""

    id: str
    pr_number: int
    repo_name: str

    # Reviewer
    reviewer_email: str
    reviewer_name: str

    # Review details
    state: ReviewState
    body: Optional[str] = None
    comments_count: int = 0

    # Timestamps
    submitted_at: datetime

    # URL
    url: Optional[str] = None


class ContributionMetrics(BaseModel):
    """Git contribution metrics for a user"""

    user_email: str
    period_start: datetime
    period_end: datetime

    # Commit metrics
    total_commits: int = 0
    total_additions: int = 0
    total_deletions: int = 0
    total_files_changed: int = 0

    # Repository involvement
    repositories: Set[str] = Field(default_factory=set)
    primary_repositories: List[str] = Field(
        default_factory=list,
        description="Top 5 repos by commits"
    )

    # Pull request metrics
    prs_created: int = 0
    prs_merged: int = 0
    prs_closed_without_merge: int = 0
    average_pr_size: float = 0.0  # Lines changed
    average_time_to_merge_hours: float = 0.0

    # Code review metrics
    reviews_given: int = 0
    reviews_received: int = 0
    approvals_given: int = 0
    change_requests_given: int = 0
    review_comments_made: int = 0

    # Collaboration
    collaborators: Set[str] = Field(
        default_factory=set,
        description="Emails of people reviewed code with"
    )
    pr_collaborators: Set[str] = Field(
        default_factory=set,
        description="Emails of people who reviewed user's PRs"
    )

    # Activity patterns
    busiest_day_of_week: Optional[str] = None
    most_active_hour: Optional[int] = None


class GitIntegration:
    """
    Git Integration Client

    Handles Git operations for Bloom including:
    - Fetching contribution metrics
    - Analyzing code review patterns
    - Tracking team collaboration
    """

    def __init__(self, config: GitConfig):
        """
        Initialize Git integration

        Args:
            config: Git configuration
        """
        self.config = config
        self.provider = config.provider

        # Determine base URL
        if config.base_url:
            self.base_url = config.base_url.rstrip("/")
        elif config.provider == GitProvider.GITHUB:
            self.base_url = "https://api.github.com"
        elif config.provider == GitProvider.GITLAB:
            self.base_url = "https://gitlab.com/api/v4"
        elif config.provider == GitProvider.BITBUCKET:
            self.base_url = "https://api.bitbucket.org/2.0"
        else:
            self.base_url = ""

        # Cache
        self._commit_cache: Dict[str, List[Commit]] = {}
        self._pr_cache: Dict[str, List[PullRequest]] = {}
        self._cache_timestamps: Dict[str, datetime] = {}

        logger.info(f"Git integration initialized (provider: {self.provider.value})")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        retry_count: int = 0,
    ) -> Any:
        """
        Make Git API request

        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            retry_count: Retry attempt

        Returns:
            API response

        Raises:
            RuntimeError: If request fails
        """
        try:
            # In production, use aiohttp with proper authentication
            logger.debug(f"Git API {method} {endpoint}")
            await asyncio.sleep(0.1)  # Simulate API call

            # Simulated response
            return []

        except Exception as e:
            logger.error(f"Git API error: {e}")

            if retry_count < 3:
                await asyncio.sleep(2 ** retry_count)
                return await self._make_request(method, endpoint, params, retry_count + 1)

            raise RuntimeError(f"Git API request failed: {e}")

    async def get_user_commits(
        self,
        user_email: str,
        start_date: datetime,
        end_date: datetime,
        repositories: Optional[List[str]] = None,
    ) -> List[Commit]:
        """
        Get commits by user in date range

        Args:
            user_email: User email address
            start_date: Start of date range
            end_date: End of date range
            repositories: Optional list of specific repos

        Returns:
            List of commits

        Raises:
            RuntimeError: If fetch fails
        """
        cache_key = f"commits:{user_email}:{start_date.date()}:{end_date.date()}"

        # Check cache
        if cache_key in self._commit_cache:
            cache_time = self._cache_timestamps.get(cache_key)
            if cache_time:
                age_minutes = (datetime.now() - cache_time).total_seconds() / 60
                if age_minutes < self.config.cache_duration_minutes:
                    return self._commit_cache[cache_key]

        logger.info(f"Fetching commits for {user_email}")

        commits: List[Commit] = []

        # Get repositories to search
        repos_to_search = repositories or await self._get_user_repositories(user_email)

        # Fetch commits from each repo
        for repo_name in repos_to_search:
            try:
                repo_commits = await self._fetch_repo_commits(
                    repo_name,
                    user_email,
                    start_date,
                    end_date,
                )
                commits.extend(repo_commits)
            except Exception as e:
                logger.warning(f"Failed to fetch commits from {repo_name}: {e}")
                continue

        # Cache results
        self._commit_cache[cache_key] = commits
        self._cache_timestamps[cache_key] = datetime.now()

        logger.info(f"Found {len(commits)} commits for {user_email}")
        return commits

    async def _get_user_repositories(self, user_email: str) -> List[str]:
        """Get repositories user has access to (simulated)"""
        # In production, fetch from API
        return []

    async def _fetch_repo_commits(
        self,
        repo_name: str,
        user_email: str,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Commit]:
        """Fetch commits from a repository (simulated)"""
        # In production, use provider-specific API
        await asyncio.sleep(0.1)
        return []

    async def get_user_pull_requests(
        self,
        user_email: str,
        start_date: datetime,
        end_date: datetime,
        repositories: Optional[List[str]] = None,
        include_reviewed: bool = True,
    ) -> Dict[str, List[PullRequest]]:
        """
        Get pull requests created and reviewed by user

        Args:
            user_email: User email address
            start_date: Start of date range
            end_date: End of date range
            repositories: Optional list of specific repos
            include_reviewed: Include PRs user reviewed

        Returns:
            Dictionary with 'created' and 'reviewed' PR lists

        Raises:
            RuntimeError: If fetch fails
        """
        logger.info(f"Fetching pull requests for {user_email}")

        created_prs: List[PullRequest] = []
        reviewed_prs: List[PullRequest] = []

        # Get repositories
        repos_to_search = repositories or await self._get_user_repositories(user_email)

        # Fetch PRs from each repo
        for repo_name in repos_to_search:
            try:
                # Get created PRs
                repo_created = await self._fetch_repo_prs(
                    repo_name,
                    author_email=user_email,
                    start_date=start_date,
                    end_date=end_date,
                )
                created_prs.extend(repo_created)

                # Get reviewed PRs
                if include_reviewed:
                    repo_reviewed = await self._fetch_repo_prs(
                        repo_name,
                        reviewer_email=user_email,
                        start_date=start_date,
                        end_date=end_date,
                    )
                    reviewed_prs.extend(repo_reviewed)

            except Exception as e:
                logger.warning(f"Failed to fetch PRs from {repo_name}: {e}")
                continue

        logger.info(
            f"Found {len(created_prs)} created PRs and {len(reviewed_prs)} reviewed PRs"
        )

        return {
            "created": created_prs,
            "reviewed": reviewed_prs,
        }

    async def _fetch_repo_prs(
        self,
        repo_name: str,
        author_email: Optional[str] = None,
        reviewer_email: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[PullRequest]:
        """Fetch pull requests from repository (simulated)"""
        # In production, use provider-specific API
        await asyncio.sleep(0.1)
        return []

    async def get_contribution_metrics(
        self,
        user_email: str,
        start_date: datetime,
        end_date: datetime,
        repositories: Optional[List[str]] = None,
    ) -> ContributionMetrics:
        """
        Calculate comprehensive contribution metrics

        Args:
            user_email: User email address
            start_date: Analysis period start
            end_date: Analysis period end
            repositories: Optional list of specific repos

        Returns:
            Contribution metrics
        """
        logger.info(f"Calculating contribution metrics for {user_email}")

        # Initialize metrics
        metrics = ContributionMetrics(
            user_email=user_email,
            period_start=start_date,
            period_end=end_date,
        )

        # Get commits
        commits = await self.get_user_commits(
            user_email,
            start_date,
            end_date,
            repositories,
        )

        # Process commits
        repo_commit_counts: Dict[str, int] = {}
        day_of_week_counts: Dict[int, int] = {i: 0 for i in range(7)}
        hour_counts: Dict[int, int] = {i: 0 for i in range(24)}

        for commit in commits:
            metrics.total_commits += 1
            metrics.total_additions += commit.additions
            metrics.total_deletions += commit.deletions
            metrics.total_files_changed += commit.changed_files

            # Track repos
            metrics.repositories.add(commit.repo_full_name)
            repo_commit_counts[commit.repo_full_name] = repo_commit_counts.get(commit.repo_full_name, 0) + 1

            # Track patterns
            day_of_week_counts[commit.authored_at.weekday()] += 1
            hour_counts[commit.authored_at.hour] += 1

        # Get top repositories
        sorted_repos = sorted(repo_commit_counts.items(), key=lambda x: x[1], reverse=True)
        metrics.primary_repositories = [repo for repo, _ in sorted_repos[:5]]

        # Get pull requests
        prs = await self.get_user_pull_requests(
            user_email,
            start_date,
            end_date,
            repositories,
        )

        created_prs = prs["created"]
        reviewed_prs = prs["reviewed"]

        # Process created PRs
        total_pr_lines = 0
        total_merge_time_hours = 0.0
        merged_count = 0

        for pr in created_prs:
            metrics.prs_created += 1

            if pr.state == PRState.MERGED:
                metrics.prs_merged += 1
                merged_count += 1

                # Calculate merge time
                time_to_merge = pr.get_time_to_merge()
                if time_to_merge:
                    total_merge_time_hours += time_to_merge.total_seconds() / 3600

            elif pr.state == PRState.CLOSED:
                metrics.prs_closed_without_merge += 1

            # Track PR size
            total_pr_lines += pr.additions + pr.deletions

            # Track PR reviewers as collaborators
            for reviewer in pr.reviewers:
                if reviewer.lower() != user_email.lower():
                    metrics.pr_collaborators.add(reviewer)

        # Calculate averages
        if metrics.prs_created > 0:
            metrics.average_pr_size = total_pr_lines / metrics.prs_created

        if merged_count > 0:
            metrics.average_time_to_merge_hours = total_merge_time_hours / merged_count

        # Process reviewed PRs
        for pr in reviewed_prs:
            metrics.reviews_received += 1

            # Find user's reviews
            for review in pr.reviews:
                if review.get("reviewer_email", "").lower() == user_email.lower():
                    metrics.reviews_given += 1
                    metrics.review_comments_made += review.get("comments_count", 0)

                    if review.get("state") == ReviewState.APPROVED.value:
                        metrics.approvals_given += 1
                    elif review.get("state") == ReviewState.CHANGES_REQUESTED.value:
                        metrics.change_requests_given += 1

            # Track PR author as collaborator
            if pr.author_email.lower() != user_email.lower():
                metrics.collaborators.add(pr.author_email)

        # Calculate activity patterns
        if day_of_week_counts:
            busiest_day = max(day_of_week_counts.items(), key=lambda x: x[1])
            day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            metrics.busiest_day_of_week = day_names[busiest_day[0]]

        if hour_counts:
            busiest_hour = max(hour_counts.items(), key=lambda x: x[1])
            metrics.most_active_hour = busiest_hour[0]

        logger.info(
            f"Metrics calculated: {metrics.total_commits} commits, "
            f"{metrics.prs_created} PRs created, {metrics.reviews_given} reviews given"
        )

        return metrics

    async def get_code_review_metrics(
        self,
        user_email: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """
        Get detailed code review metrics

        Args:
            user_email: User email address
            start_date: Analysis period start
            end_date: Analysis period end

        Returns:
            Code review metrics dictionary
        """
        logger.info(f"Calculating code review metrics for {user_email}")

        prs = await self.get_user_pull_requests(
            user_email,
            start_date,
            end_date,
            include_reviewed=True,
        )

        reviewed_prs = prs["reviewed"]

        # Calculate metrics
        total_reviews = 0
        total_comments = 0
        approvals = 0
        change_requests = 0
        response_times: List[float] = []

        for pr in reviewed_prs:
            for review in pr.reviews:
                if review.get("reviewer_email", "").lower() == user_email.lower():
                    total_reviews += 1
                    total_comments += review.get("comments_count", 0)

                    state = review.get("state")
                    if state == ReviewState.APPROVED.value:
                        approvals += 1
                    elif state == ReviewState.CHANGES_REQUESTED.value:
                        change_requests += 1

                    # Calculate response time (PR creation to review submission)
                    review_time = review.get("submitted_at")
                    if review_time and pr.created_at:
                        delta = review_time - pr.created_at
                        response_times.append(delta.total_seconds() / 3600)

        # Calculate average response time
        avg_response_hours = 0.0
        if response_times:
            avg_response_hours = sum(response_times) / len(response_times)

        return {
            "total_reviews": total_reviews,
            "total_comments": total_comments,
            "approvals": approvals,
            "change_requests": change_requests,
            "approval_rate": approvals / total_reviews if total_reviews > 0 else 0,
            "average_comments_per_review": total_comments / total_reviews if total_reviews > 0 else 0,
            "average_response_time_hours": avg_response_hours,
        }

    async def get_repository_contributors(
        self,
        repo_name: str,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Dict[str, Any]]:
        """
        Get contributors to a repository

        Args:
            repo_name: Repository name
            start_date: Period start
            end_date: Period end

        Returns:
            List of contributor statistics
        """
        logger.info(f"Fetching contributors for {repo_name}")

        # In production, fetch from API
        await asyncio.sleep(0.1)

        # Simulated response
        return []

    def get_stats(self) -> Dict[str, Any]:
        """
        Get integration statistics

        Returns:
            Statistics dictionary
        """
        return {
            "cached_commits": sum(len(commits) for commits in self._commit_cache.values()),
            "cached_prs": sum(len(prs) for prs in self._pr_cache.values()),
            "provider": self.provider.value,
            "base_url": self.base_url,
        }
