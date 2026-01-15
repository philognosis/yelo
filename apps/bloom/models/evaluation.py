"""
Evaluation Data Models

Defines the evaluation workflow states, ratings, feedback, and complete evaluation records.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class EvaluationPhase(str, Enum):
    """Evaluation workflow phases"""

    CONTEXT_PEER_SELECTION = "context_peer_selection"  # Phase 1
    DATA_GATHERING = "data_gathering"  # Phase 2
    MANAGER_EVALUATION = "manager_evaluation"  # Phase 3
    CALIBRATION = "calibration"  # Phase 4
    RELEASE_DISCUSSION = "release_discussion"  # Phase 5
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class EvaluationState(str, Enum):
    """Detailed evaluation states within phases"""

    # Phase 1 states
    CYCLE_STARTED = "cycle_started"
    PEER_SUGGESTION_GENERATED = "peer_suggestion_generated"
    EMPLOYEE_PEER_REVIEW = "employee_peer_review"
    MANAGER_PEER_APPROVAL = "manager_peer_approval"
    PEER_LIST_LOCKED = "peer_list_locked"

    # Phase 2 states
    PEER_FEEDBACK_REQUESTED = "peer_feedback_requested"
    PEER_FEEDBACK_IN_PROGRESS = "peer_feedback_in_progress"
    SELF_EVAL_REQUESTED = "self_eval_requested"
    SELF_EVAL_IN_PROGRESS = "self_eval_in_progress"
    DATA_GATHERING_COMPLETE = "data_gathering_complete"

    # Phase 3 states
    MANAGER_EVAL_STARTED = "manager_eval_started"
    AI_DRAFT_GENERATED = "ai_draft_generated"
    MANAGER_REVIEW_IN_PROGRESS = "manager_review_in_progress"
    MANAGER_EVAL_COMPLETE = "manager_eval_complete"

    # Phase 4 states
    CALIBRATION_PENDING = "calibration_pending"
    CALIBRATION_IN_PROGRESS = "calibration_in_progress"
    CALIBRATION_COMPLETE = "calibration_complete"

    # Phase 5 states
    RELEASE_SCHEDULED = "release_scheduled"
    RELEASED = "released"
    DISCUSSION_SCHEDULED = "discussion_scheduled"
    DISCUSSION_COMPLETE = "discussion_complete"
    ACKNOWLEDGED = "acknowledged"
    DECLINED = "declined"

    # Terminal states
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Rating(str, Enum):
    """Performance ratings"""

    EXCEPTIONAL = "exceptional"  # Far exceeds expectations
    EXCEEDS = "exceeds"  # Exceeds expectations
    MEETS = "meets"  # Meets expectations
    DEVELOPING = "developing"  # Developing / needs improvement
    NOT_MEETING = "not_meeting"  # Not meeting expectations


class PromotionEligibility(str, Enum):
    """Promotion readiness assessment"""

    READY_NOW = "ready_now"  # Ready for immediate promotion
    READY_NEXT_CYCLE = "ready_next_cycle"  # Ready in next evaluation cycle
    DEVELOPING = "developing"  # Needs more time/development
    NOT_READY = "not_ready"  # Not ready for promotion


class FeedbackSource(str, Enum):
    """Source of feedback"""

    PEER = "peer"
    MANAGER = "manager"
    SELF = "self"
    SKIP_LEVEL = "skip_level"
    DIRECT_REPORT = "direct_report"
    STAKEHOLDER = "stakeholder"


class PeerFeedback(BaseModel):
    """
    Feedback from a peer reviewer

    Stores raw input (voice/text) and AI-synthesized professional version.
    """

    id: UUID = Field(default_factory=uuid4)
    evaluation_id: UUID = Field(..., description="Associated evaluation")
    peer_id: UUID = Field(..., description="Peer providing feedback")
    peer_name: str = Field(..., description="Peer's name (for display)")

    # Raw input
    raw_input: str = Field(..., description="Original dictation or text input")
    input_method: str = Field(default="text", description="How feedback was provided (voice, text, form)")

    # Synthesized output
    synthesized_feedback: Optional[str] = Field(
        None,
        description="AI-cleaned professional version of feedback"
    )

    # Structured ratings (optional)
    technical_rating: Optional[Rating] = Field(None, description="Technical skills rating")
    leadership_rating: Optional[Rating] = Field(None, description="Leadership rating")
    communication_rating: Optional[Rating] = Field(None, description="Communication rating")
    collaboration_rating: Optional[Rating] = Field(None, description="Collaboration rating")

    # Metadata
    submitted_at: datetime = Field(default_factory=datetime.now)
    synthesized_at: Optional[datetime] = Field(None, description="When AI synthesis was completed")
    is_anonymous: bool = Field(default=False, description="Whether feedback is anonymous to employee")

    # Evidence links
    supporting_docs: List[str] = Field(default_factory=list, description="Links to supporting documents")

    class Config:
        json_schema_extra = {
            "example": {
                "peer_name": "John Smith",
                "raw_input": "Jane did a great job on the API migration project. She handled the database issues really well.",
                "technical_rating": "exceeds",
                "leadership_rating": "meets",
            }
        }


class SelfEvaluation(BaseModel):
    """
    Employee self-evaluation

    Captures employee's own assessment with supporting evidence.
    """

    id: UUID = Field(default_factory=uuid4)
    evaluation_id: UUID = Field(..., description="Associated evaluation")
    employee_id: UUID = Field(..., description="Employee being evaluated")

    # Raw input
    raw_achievements: str = Field(..., description="Raw dictation/text of achievements")
    raw_challenges: Optional[str] = Field(None, description="Raw input about challenges faced")
    raw_growth_areas: Optional[str] = Field(None, description="Raw input about growth areas")
    raw_goals: Optional[str] = Field(None, description="Raw input about future goals")

    # Synthesized output
    synthesized_achievements: Optional[str] = Field(
        None,
        description="AI-cleaned professional version"
    )
    synthesized_challenges: Optional[str] = None
    synthesized_growth_areas: Optional[str] = None
    synthesized_goals: Optional[str] = None

    # Supporting evidence
    uploaded_docs: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Uploaded documents (PDFs, decks, etc.)"
    )
    project_links: List[str] = Field(default_factory=list, description="Links to projects/PRs")

    # Metadata
    submitted_at: datetime = Field(default_factory=datetime.now)
    synthesized_at: Optional[datetime] = Field(None)

    class Config:
        json_schema_extra = {
            "example": {
                "raw_achievements": "Led the API migration from v1 to v2, resulting in 40% performance improvement...",
                "uploaded_docs": [
                    {"name": "API_Migration_Deck.pdf", "url": "https://..."},
                    {"name": "Q3_Metrics.pdf", "url": "https://..."},
                ],
            }
        }


class ManagerEvaluation(BaseModel):
    """
    Manager's evaluation of employee

    Includes AI-assisted draft, manager input, and final assessment.
    """

    id: UUID = Field(default_factory=uuid4)
    evaluation_id: UUID = Field(..., description="Associated evaluation")
    manager_id: UUID = Field(..., description="Manager providing evaluation")
    employee_id: UUID = Field(..., description="Employee being evaluated")

    # AI-Generated Draft
    ai_draft_summary: Optional[str] = Field(
        None,
        description="AI-generated first draft based on all inputs"
    )
    ai_draft_evidence_map: Optional[Dict[str, List[str]]] = Field(
        None,
        description="Map of qualities to evidence citations"
    )
    ai_generated_at: Optional[datetime] = None

    # AI Questions and Manager Responses
    ai_questions: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Questions asked by AI to fill gaps"
    )
    manager_responses: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Manager's responses to AI questions"
    )

    # Manager's Final Input
    final_summary: str = Field(..., description="Manager's final evaluation summary")
    technical_assessment: Optional[str] = Field(None, description="Technical skills assessment")
    leadership_assessment: Optional[str] = Field(None, description="Leadership assessment")
    growth_opportunities: Optional[str] = Field(None, description="Areas for growth")

    # Ratings
    overall_rating: Rating = Field(..., description="Overall performance rating")
    technical_rating: Optional[Rating] = None
    leadership_rating: Optional[Rating] = None
    communication_rating: Optional[Rating] = None
    strategic_thinking_rating: Optional[Rating] = None

    # Promotion
    promotion_eligibility: PromotionEligibility = Field(
        ...,
        description="Promotion readiness assessment"
    )
    promotion_justification: Optional[str] = Field(
        None,
        description="Justification for promotion recommendation"
    )

    # Calibration changes
    pre_calibration_rating: Optional[Rating] = Field(
        None,
        description="Rating before calibration committee"
    )
    calibration_notes: Optional[str] = Field(
        None,
        description="Notes from calibration committee"
    )

    # Metadata
    draft_started_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    calibrated_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "ai_draft_summary": "Based on analysis of 5 peer reviews and self-evaluation...",
                "final_summary": "Jane demonstrated exceptional technical leadership on the API migration...",
                "overall_rating": "exceeds",
                "promotion_eligibility": "ready_next_cycle",
            }
        }


class Evaluation(BaseModel):
    """
    Complete evaluation record

    Central entity tracking an employee's evaluation through the entire workflow.
    """

    id: UUID = Field(default_factory=uuid4)
    employee_id: UUID = Field(..., description="Employee being evaluated")
    manager_id: UUID = Field(..., description="Primary manager")
    cycle_name: str = Field(..., description="Evaluation cycle name (e.g., 'Q4 2024', 'Annual 2024')")

    # Workflow state
    current_phase: EvaluationPhase = Field(
        default=EvaluationPhase.CONTEXT_PEER_SELECTION,
        description="Current phase"
    )
    current_state: EvaluationState = Field(
        default=EvaluationState.CYCLE_STARTED,
        description="Current detailed state"
    )

    # Peer selection
    suggested_peers: List[UUID] = Field(default_factory=list, description="AI-suggested peer reviewers")
    employee_selected_peers: List[UUID] = Field(default_factory=list, description="Employee-selected peers")
    manager_approved_peers: List[UUID] = Field(default_factory=list, description="Final approved peer list")

    # Feedback collections
    peer_feedbacks: List[PeerFeedback] = Field(default_factory=list)
    self_evaluation: Optional[SelfEvaluation] = None
    manager_evaluation: Optional[ManagerEvaluation] = None

    # Deadlines
    peer_selection_deadline: Optional[datetime] = None
    peer_feedback_deadline: Optional[datetime] = None
    self_eval_deadline: Optional[datetime] = None
    manager_eval_deadline: Optional[datetime] = None
    calibration_date: Optional[datetime] = None
    release_date: Optional[datetime] = None

    # Release and acknowledgment
    released_at: Optional[datetime] = None
    discussion_scheduled_at: Optional[datetime] = None
    discussion_completed_at: Optional[datetime] = None
    employee_acknowledged: bool = False
    employee_declined: bool = False
    employee_response: Optional[str] = None
    employee_response_at: Optional[datetime] = None

    # Committee review (if declined)
    committee_review_requested: bool = False
    committee_decision: Optional[str] = None
    committee_decision_at: Optional[datetime] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # State history
    state_history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="History of state transitions"
    )

    def add_state_transition(
        self,
        new_state: EvaluationState,
        new_phase: Optional[EvaluationPhase] = None,
        reason: Optional[str] = None,
    ) -> None:
        """Record a state transition"""
        transition = {
            "from_state": self.current_state,
            "to_state": new_state,
            "from_phase": self.current_phase,
            "to_phase": new_phase or self.current_phase,
            "timestamp": datetime.now().isoformat(),
            "reason": reason,
        }

        self.state_history.append(transition)
        self.current_state = new_state

        if new_phase:
            self.current_phase = new_phase

        self.updated_at = datetime.now()

    def get_completion_percentage(self) -> float:
        """Calculate completion percentage based on phase"""
        phase_weights = {
            EvaluationPhase.CONTEXT_PEER_SELECTION: 0.1,
            EvaluationPhase.DATA_GATHERING: 0.3,
            EvaluationPhase.MANAGER_EVALUATION: 0.5,
            EvaluationPhase.CALIBRATION: 0.7,
            EvaluationPhase.RELEASE_DISCUSSION: 0.9,
            EvaluationPhase.COMPLETED: 1.0,
        }

        return phase_weights.get(self.current_phase, 0.0)

    def is_past_deadline(self, deadline_type: str) -> bool:
        """Check if a specific deadline has passed"""
        deadline_map = {
            "peer_selection": self.peer_selection_deadline,
            "peer_feedback": self.peer_feedback_deadline,
            "self_eval": self.self_eval_deadline,
            "manager_eval": self.manager_eval_deadline,
        }

        deadline = deadline_map.get(deadline_type)
        if deadline is None:
            return False

        return datetime.now() > deadline

    def get_pending_feedbacks(self) -> List[UUID]:
        """Get list of peers who haven't submitted feedback"""
        submitted_peer_ids = {fb.peer_id for fb in self.peer_feedbacks}
        return [
            peer_id
            for peer_id in self.manager_approved_peers
            if peer_id not in submitted_peer_ids
        ]

    class Config:
        json_schema_extra = {
            "example": {
                "employee_id": "550e8400-e29b-41d4-a716-446655440000",
                "manager_id": "550e8400-e29b-41d4-a716-446655440001",
                "cycle_name": "Annual 2024",
                "current_phase": "data_gathering",
                "current_state": "peer_feedback_in_progress",
            }
        }
