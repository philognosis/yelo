"""
Employee Data Models

Defines the core business entities for employee records, skills, certifications,
and interaction metrics used by the Context Miner agent.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class EmployeeLevel(str, Enum):
    """Employee level/grade"""

    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L4 = "L4"
    L5 = "L5"
    L6 = "L6"


class EmployeeRole(str, Enum):
    """Employee role type"""

    INDIVIDUAL_CONTRIBUTOR = "individual_contributor"
    MANAGER = "manager"
    SENIOR_MANAGER = "senior_manager"
    DIRECTOR = "director"
    VP = "vp"
    EXECUTIVE = "executive"


class SkillArea(str, Enum):
    """Skill domain areas"""

    TECHNICAL = "technical"
    LEADERSHIP = "leadership"
    COMMUNICATION = "communication"
    STRATEGIC = "strategic"
    DOMAIN_KNOWLEDGE = "domain_knowledge"
    PROCESS = "process"


class SkillLevel(str, Enum):
    """Skill proficiency levels"""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
    MASTER = "master"


class Person(BaseModel):
    """
    Core employee record

    This is the foundational entity representing an employee in the system.
    """

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Work email address")
    title: str = Field(..., description="Job title")
    location: str = Field(..., description="Office location or remote")
    region: str = Field(..., description="Geographic region (e.g., LATAM, APAC, EMEA, NAM)")

    # Hierarchy
    level: EmployeeLevel = Field(..., description="Employee level (L1-L6)")
    sub_level: int = Field(default=0, description="Sub-level (0-2)", ge=0, le=2)
    role: EmployeeRole = Field(..., description="Role type")
    manager_id: Optional[UUID] = Field(None, description="Manager's employee ID")

    # Timestamps
    hire_date: date = Field(..., description="Date of hire")
    last_promotion_date: Optional[date] = Field(None, description="Date of last promotion")

    # Status
    is_active: bool = Field(default=True)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Jane Doe",
                "email": "jane.doe@company.com",
                "title": "Senior Software Engineer",
                "location": "San Francisco, CA",
                "region": "NAM",
                "level": "L3",
                "sub_level": 2,
                "role": "individual_contributor",
                "hire_date": "2020-06-15",
            }
        }


class Skill(BaseModel):
    """
    Employee skill/competency record

    Tracks specific skills with proficiency levels and areas.
    """

    id: UUID = Field(default_factory=uuid4)
    person_id: UUID = Field(..., description="Employee ID")
    name: str = Field(..., description="Skill name (e.g., 'Python', 'Team Leadership')")
    level: SkillLevel = Field(..., description="Proficiency level")
    area: SkillArea = Field(..., description="Skill domain")
    sub_type: Optional[str] = Field(None, description="Skill sub-category")

    # Evidence
    acquired_date: Optional[date] = Field(None, description="When skill was acquired")
    last_used_date: Optional[date] = Field(None, description="Last time skill was used")
    evidence_links: List[str] = Field(default_factory=list, description="Links to work demonstrating skill")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {
                "person_id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Python",
                "level": "expert",
                "area": "technical",
                "sub_type": "Programming Language",
            }
        }


class Certification(BaseModel):
    """
    External certification record

    Tracks professional certifications with validity periods.
    """

    id: UUID = Field(default_factory=uuid4)
    person_id: UUID = Field(..., description="Employee ID")
    name: str = Field(..., description="Certification name")
    issuer: str = Field(..., description="Issuing organization")

    # Dates
    passed_on: date = Field(..., description="Date certification was obtained")
    valid_till: Optional[date] = Field(None, description="Expiration date (if applicable)")

    # Related skills
    skills_earned: List[str] = Field(
        default_factory=list,
        description="Skills acquired or validated by this certification"
    )

    # Evidence
    certificate_url: Optional[str] = Field(None, description="Link to certificate")
    credential_id: Optional[str] = Field(None, description="Credential ID for verification")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "AWS Solutions Architect - Professional",
                "issuer": "Amazon Web Services",
                "passed_on": "2023-03-15",
                "valid_till": "2026-03-15",
                "skills_earned": ["Cloud Architecture", "AWS Services", "Security Best Practices"],
            }
        }


class Training(BaseModel):
    """
    Internal or external training record

    Tracks completed training programs and courses.
    """

    id: UUID = Field(default_factory=uuid4)
    person_id: UUID = Field(..., description="Employee ID")
    name: str = Field(..., description="Training/course name")
    provider: str = Field(..., description="Training provider")
    training_type: str = Field(..., description="Type (internal, external, online, instructor-led)")

    # Dates
    started_on: Optional[date] = Field(None, description="Start date")
    completed_on: date = Field(..., description="Completion date")
    valid_till: Optional[date] = Field(None, description="Validity period (for compliance training)")

    # Outcomes
    skills_earned: List[str] = Field(
        default_factory=list,
        description="Skills acquired from training"
    )
    score: Optional[float] = Field(None, description="Test score or grade", ge=0, le=100)

    # Metadata
    duration_hours: Optional[int] = Field(None, description="Total hours", ge=0)
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Advanced Leadership Program",
                "provider": "Internal L&D",
                "training_type": "instructor-led",
                "completed_on": "2023-09-30",
                "skills_earned": ["Strategic Planning", "Team Management", "Executive Communication"],
                "duration_hours": 40,
            }
        }


class CalendarMetric(BaseModel):
    """
    Peer interaction metrics from calendar data

    Used by Context Miner to quantify depth of relationship with peers.
    Tracks meeting time between two people over various time periods.
    """

    id: UUID = Field(default_factory=uuid4)
    person_id: UUID = Field(..., description="Primary employee ID")
    peer_id: UUID = Field(..., description="Peer employee ID")

    # Meeting metrics (in hours)
    total_hours: float = Field(default=0.0, description="Total meeting hours (all time)", ge=0)
    total_last_yr: float = Field(default=0.0, description="Meeting hours in last year", ge=0)
    total_ytd: float = Field(default=0.0, description="Meeting hours year-to-date", ge=0)
    total_last_2_years: float = Field(default=0.0, description="Meeting hours in last 2 years", ge=0)
    total_previous_two_yrs: float = Field(default=0.0, description="Meeting hours 2-4 years ago", ge=0)

    # Meeting counts
    total_days: int = Field(default=0, description="Number of days with meetings", ge=0)
    total_meetings: int = Field(default=0, description="Total number of meetings", ge=0)

    # Metadata
    last_meeting_date: Optional[date] = Field(None, description="Most recent meeting")
    relationship_strength: Optional[float] = Field(
        None,
        description="Calculated relationship strength score (0-1)",
        ge=0,
        le=1,
    )
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {
                "person_id": "550e8400-e29b-41d4-a716-446655440000",
                "peer_id": "550e8400-e29b-41d4-a716-446655440001",
                "total_hours": 45.5,
                "total_last_yr": 30.0,
                "total_ytd": 12.5,
                "total_days": 28,
                "total_meetings": 42,
                "relationship_strength": 0.85,
            }
        }


class TeamHours(BaseModel):
    """
    Group interaction metrics

    Used to determine project involvement and team impact.
    Tracks time spent with specific teams/projects.
    """

    id: UUID = Field(default_factory=uuid4)
    person_id: UUID = Field(..., description="Employee ID")
    team_id: UUID = Field(..., description="Team/Project ID")
    team_name: str = Field(..., description="Team/Project name")
    group: str = Field(..., description="Group/Department name")

    # Time metrics (in hours)
    hours: float = Field(default=0.0, description="Hours this period", ge=0)
    total_hours: float = Field(default=0.0, description="Total hours (all time)", ge=0)
    total_last_yr: float = Field(default=0.0, description="Hours in last year", ge=0)
    total_ytd: float = Field(default=0.0, description="Hours year-to-date", ge=0)
    total_last_2_years: float = Field(default=0.0, description="Hours in last 2 years", ge=0)
    total_previous_two_yrs: float = Field(default=0.0, description="Hours 2-4 years ago", ge=0)

    # Activity counts
    total_days: int = Field(default=0, description="Number of days active", ge=0)

    # Metadata
    role_in_team: Optional[str] = Field(None, description="Role/responsibility in team")
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {
                "person_id": "550e8400-e29b-41d4-a716-446655440000",
                "team_id": "team-123",
                "team_name": "Platform Engineering",
                "group": "Engineering",
                "total_hours": 520.0,
                "total_last_yr": 400.0,
                "total_ytd": 180.0,
                "role_in_team": "Tech Lead",
            }
        }


class Employee(BaseModel):
    """
    Complete employee record with all associated data

    Aggregates Person with their skills, certifications, trainings, and metrics.
    This is the primary entity used by agents.
    """

    person: Person
    skills: List[Skill] = Field(default_factory=list)
    certifications: List[Certification] = Field(default_factory=list)
    trainings: List[Training] = Field(default_factory=list)
    calendar_metrics: List[CalendarMetric] = Field(default_factory=list)
    team_hours: List[TeamHours] = Field(default_factory=list)

    def get_manager(self) -> Optional[UUID]:
        """Get manager ID"""
        return self.person.manager_id

    def get_level_tuple(self) -> tuple[str, int]:
        """Get (level, sub_level) tuple for evaluation triggering"""
        return (self.person.level.value, self.person.sub_level)

    def get_suggested_peers(self, min_relationship_strength: float = 0.5) -> List[UUID]:
        """
        Get suggested peer reviewers based on calendar metrics

        Args:
            min_relationship_strength: Minimum relationship strength threshold

        Returns:
            List of peer UUIDs sorted by relationship strength
        """
        peers = [
            (metric.peer_id, metric.relationship_strength or 0.0)
            for metric in self.calendar_metrics
            if (metric.relationship_strength or 0.0) >= min_relationship_strength
        ]

        # Sort by strength descending
        peers.sort(key=lambda x: x[1], reverse=True)

        return [peer_id for peer_id, _ in peers]

    def get_team_involvement(self) -> Dict[str, float]:
        """
        Get team involvement summary

        Returns:
            Dict mapping team names to total hours
        """
        return {
            team.team_name: team.total_hours
            for team in self.team_hours
        }

    def get_skills_by_area(self, area: SkillArea) -> List[Skill]:
        """Get skills filtered by area"""
        return [skill for skill in self.skills if skill.area == area]

    def get_active_certifications(self) -> List[Certification]:
        """Get certifications that are still valid"""
        today = date.today()
        return [
            cert for cert in self.certifications
            if cert.valid_till is None or cert.valid_till >= today
        ]

    class Config:
        json_schema_extra = {
            "example": {
                "person": {
                    "name": "Jane Doe",
                    "email": "jane.doe@company.com",
                    "title": "Senior Software Engineer",
                    "level": "L3",
                    "sub_level": 2,
                    "role": "individual_contributor",
                },
                "skills": [
                    {
                        "name": "Python",
                        "level": "expert",
                        "area": "technical",
                    }
                ],
            }
        }
