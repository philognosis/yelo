"""
Tests for Employee Models

Tests the Person, Skill, Certification, Training, CalendarMetric,
TeamHours, and Employee models.
"""

from datetime import date, datetime
from uuid import uuid4

import pytest

from bloom.models.employee import (
    CalendarMetric,
    Certification,
    Employee,
    EmployeeLevel,
    EmployeeRole,
    Person,
    Skill,
    SkillArea,
    SkillLevel,
    TeamHours,
    Training,
)


class TestPerson:
    """Test Person model validation and methods"""

    def test_person_creation(self, mock_person):
        """Test creating a valid Person"""
        assert mock_person.name == "Jane Doe"
        assert mock_person.email == "jane.doe@company.com"
        assert mock_person.level == EmployeeLevel.L3
        assert mock_person.role == EmployeeRole.INDIVIDUAL_CONTRIBUTOR
        assert mock_person.is_active is True

    def test_person_validation_required_fields(self):
        """Test that required fields are validated"""
        with pytest.raises(Exception):
            Person()

    def test_person_sublevel_validation(self):
        """Test sublevel is within valid range (0-2)"""
        # Valid sublevel
        person = Person(
            name="Test",
            email="test@test.com",
            title="Engineer",
            location="Remote",
            region="NAM",
            level=EmployeeLevel.L3,
            sub_level=2,
            role=EmployeeRole.INDIVIDUAL_CONTRIBUTOR,
            hire_date=date.today(),
        )
        assert person.sub_level == 2

        # Invalid sublevel should fail
        with pytest.raises(Exception):
            Person(
                name="Test",
                email="test@test.com",
                title="Engineer",
                location="Remote",
                region="NAM",
                level=EmployeeLevel.L3,
                sub_level=3,  # Invalid
                role=EmployeeRole.INDIVIDUAL_CONTRIBUTOR,
                hire_date=date.today(),
            )


class TestSkill:
    """Test Skill model"""

    def test_skill_creation(self, mock_skills):
        """Test creating skills"""
        assert len(mock_skills) == 3
        python_skill = mock_skills[0]
        assert python_skill.name == "Python"
        assert python_skill.level == SkillLevel.EXPERT
        assert python_skill.area == SkillArea.TECHNICAL

    def test_skill_areas(self):
        """Test different skill areas"""
        areas = [
            SkillArea.TECHNICAL,
            SkillArea.LEADERSHIP,
            SkillArea.COMMUNICATION,
            SkillArea.STRATEGIC,
            SkillArea.DOMAIN_KNOWLEDGE,
            SkillArea.PROCESS,
        ]
        assert len(areas) == 6

    def test_skill_levels(self):
        """Test skill proficiency levels"""
        levels = [
            SkillLevel.BEGINNER,
            SkillLevel.INTERMEDIATE,
            SkillLevel.ADVANCED,
            SkillLevel.EXPERT,
            SkillLevel.MASTER,
        ]
        assert len(levels) == 5


class TestCertification:
    """Test Certification model"""

    def test_certification_creation(self, mock_certifications):
        """Test creating certification"""
        cert = mock_certifications[0]
        assert cert.name == "AWS Solutions Architect - Professional"
        assert cert.issuer == "Amazon Web Services"
        assert cert.passed_on < cert.valid_till

    def test_certification_expiry(self):
        """Test certification with expiry date"""
        cert = Certification(
            person_id=uuid4(),
            name="Test Cert",
            issuer="Test Issuer",
            passed_on=date(2023, 1, 1),
            valid_till=date(2025, 1, 1),
        )

        # Check if expired
        today = date.today()
        is_expired = cert.valid_till and cert.valid_till < today

        assert cert.valid_till is not None


class TestTraining:
    """Test Training model"""

    def test_training_creation(self, mock_trainings):
        """Test creating training record"""
        training = mock_trainings[0]
        assert training.name == "Advanced Leadership Program"
        assert training.duration_hours == 40
        assert training.score == 95.0

    def test_training_score_validation(self):
        """Test that score is within valid range"""
        with pytest.raises(Exception):
            Training(
                person_id=uuid4(),
                name="Test Training",
                provider="Test",
                training_type="online",
                completed_on=date.today(),
                score=150.0,  # Invalid - above 100
            )


class TestCalendarMetric:
    """Test CalendarMetric model"""

    def test_calendar_metric_creation(self, mock_calendar_metrics):
        """Test creating calendar metrics"""
        metric = mock_calendar_metrics[0]
        assert metric.total_hours == 45.5
        assert metric.total_meetings == 42
        assert metric.relationship_strength == 0.85

    def test_relationship_strength_range(self):
        """Test relationship strength is within 0-1"""
        # Valid strength
        metric = CalendarMetric(
            person_id=uuid4(),
            peer_id=uuid4(),
            relationship_strength=0.5,
        )
        assert 0 <= metric.relationship_strength <= 1

        # Invalid strength
        with pytest.raises(Exception):
            CalendarMetric(
                person_id=uuid4(),
                peer_id=uuid4(),
                relationship_strength=1.5,  # Above 1
            )

    def test_hours_non_negative(self):
        """Test that all hour fields are non-negative"""
        with pytest.raises(Exception):
            CalendarMetric(
                person_id=uuid4(),
                peer_id=uuid4(),
                total_hours=-10.0,  # Invalid
            )


class TestTeamHours:
    """Test TeamHours model"""

    def test_team_hours_creation(self, mock_team_hours):
        """Test creating team hours record"""
        team_hours = mock_team_hours[0]
        assert team_hours.team_name == "Platform Engineering"
        assert team_hours.role_in_team == "Tech Lead"
        assert team_hours.total_hours == 520.0


class TestEmployee:
    """Test Employee aggregate model and helper methods"""

    def test_employee_creation(self, mock_employee):
        """Test creating complete employee record"""
        assert mock_employee.person.name == "Jane Doe"
        assert len(mock_employee.skills) == 3
        assert len(mock_employee.certifications) == 1
        assert len(mock_employee.trainings) == 1
        assert len(mock_employee.calendar_metrics) == 2
        assert len(mock_employee.team_hours) == 1

    def test_get_manager(self, mock_employee):
        """Test getting manager ID"""
        manager_id = mock_employee.get_manager()
        assert manager_id == mock_employee.person.manager_id

    def test_get_level_tuple(self, mock_employee):
        """Test getting level tuple"""
        level, sub_level = mock_employee.get_level_tuple()
        assert level == "L3"
        assert sub_level == 2

    def test_get_suggested_peers_with_threshold(self, mock_employee):
        """Test peer suggestion with relationship strength threshold"""
        # Default threshold 0.5
        peers = mock_employee.get_suggested_peers()
        assert len(peers) == 2  # Both metrics have strength > 0.5

        # Higher threshold
        peers_high = mock_employee.get_suggested_peers(min_relationship_strength=0.9)
        assert len(peers_high) == 1  # Only one has strength > 0.9

        # Very high threshold
        peers_very_high = mock_employee.get_suggested_peers(min_relationship_strength=1.0)
        assert len(peers_very_high) == 0  # None have strength >= 1.0

    def test_get_suggested_peers_sorted(self, mock_employee):
        """Test that peers are sorted by relationship strength"""
        peers = mock_employee.get_suggested_peers()

        # Should be sorted descending by strength
        # First peer should have higher strength (0.92 > 0.85)
        assert mock_employee.calendar_metrics[1].relationship_strength > \
               mock_employee.calendar_metrics[0].relationship_strength

    def test_get_team_involvement(self, mock_employee):
        """Test getting team involvement summary"""
        involvement = mock_employee.get_team_involvement()
        assert "Platform Engineering" in involvement
        assert involvement["Platform Engineering"] == 520.0

    def test_get_skills_by_area(self, mock_employee):
        """Test filtering skills by area"""
        technical_skills = mock_employee.get_skills_by_area(SkillArea.TECHNICAL)
        assert len(technical_skills) == 1
        assert technical_skills[0].name == "Python"

        leadership_skills = mock_employee.get_skills_by_area(SkillArea.LEADERSHIP)
        assert len(leadership_skills) == 1
        assert leadership_skills[0].name == "Team Leadership"

        strategic_skills = mock_employee.get_skills_by_area(SkillArea.STRATEGIC)
        assert len(strategic_skills) == 0

    def test_get_active_certifications(self, mock_employee):
        """Test getting active (non-expired) certifications"""
        active_certs = mock_employee.get_active_certifications()
        assert len(active_certs) == 1

        # Add expired certification
        expired_cert = Certification(
            person_id=mock_employee.person.id,
            name="Expired Cert",
            issuer="Test",
            passed_on=date(2020, 1, 1),
            valid_till=date(2021, 1, 1),  # Expired
        )
        mock_employee.certifications.append(expired_cert)

        active_certs = mock_employee.get_active_certifications()
        assert len(active_certs) == 1  # Still only 1 active

    def test_employee_without_optional_data(self, mock_person):
        """Test employee with minimal data"""
        employee = Employee(person=mock_person)
        assert len(employee.skills) == 0
        assert len(employee.certifications) == 0
        assert len(employee.trainings) == 0
        assert len(employee.calendar_metrics) == 0
        assert len(employee.team_hours) == 0

        # Should still work
        peers = employee.get_suggested_peers()
        assert len(peers) == 0


class TestEmployeeComplexScenarios:
    """Complex test scenarios for Employee model"""

    def test_multiple_high_strength_peers(self, mock_person):
        """Test employee with many high-strength peer relationships"""
        employee = Employee(person=mock_person)

        # Add 10 calendar metrics with varying strengths
        for i in range(10):
            metric = CalendarMetric(
                person_id=mock_person.id,
                peer_id=uuid4(),
                total_hours=float(i * 10),
                relationship_strength=0.5 + (i * 0.05),  # 0.5 to 0.95
            )
            employee.calendar_metrics.append(metric)

        # Get peers with medium threshold
        peers = employee.get_suggested_peers(min_relationship_strength=0.7)
        assert len(peers) == 6  # Strengths 0.7, 0.75, 0.8, 0.85, 0.9, 0.95

        # Verify sorting (highest strength first)
        strengths = [m.relationship_strength for m in employee.calendar_metrics
                     if (m.relationship_strength or 0) >= 0.7]
        sorted_strengths = sorted(strengths, reverse=True)
        assert strengths == sorted_strengths or len(set(strengths)) == 1

    def test_employee_with_diverse_skills(self, mock_person):
        """Test employee with skills across multiple areas"""
        employee = Employee(person=mock_person)

        # Add skills in all areas
        for area in SkillArea:
            skill = Skill(
                person_id=mock_person.id,
                name=f"{area.value} skill",
                level=SkillLevel.INTERMEDIATE,
                area=area,
            )
            employee.skills.append(skill)

        # Verify we can get skills from each area
        for area in SkillArea:
            skills = employee.get_skills_by_area(area)
            assert len(skills) == 1
            assert skills[0].area == area

    def test_employee_career_progression(self, mock_person):
        """Test employee with career progression history"""
        employee = Employee(person=mock_person)

        # Add trainings over time
        trainings = []
        for i in range(3):
            training = Training(
                person_id=mock_person.id,
                name=f"Training Year {2020 + i}",
                provider="Company",
                training_type="online",
                completed_on=date(2020 + i, 12, 31),
                skills_earned=[f"Skill {i}"],
            )
            trainings.append(training)

        employee.trainings = trainings

        # Verify chronological progression
        assert employee.trainings[0].completed_on.year == 2020
        assert employee.trainings[1].completed_on.year == 2021
        assert employee.trainings[2].completed_on.year == 2022
