"""
API Request/Response Models

Pydantic models for FastAPI request and response validation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from bloom.models import (
    EvaluationPhase,
    EvaluationState,
    PromotionEligibility,
    Rating,
)


# ============================================================================
# Request Models
# ============================================================================


class CreateEvaluationRequest(BaseModel):
    """Request to create a new evaluation"""

    employee_id: UUID = Field(..., description="Employee to evaluate")
    manager_id: UUID = Field(..., description="Manager conducting evaluation")
    cycle_name: str = Field(..., description="Evaluation cycle name")
    start_date: Optional[datetime] = Field(None, description="Start date (default: now)")

    class Config:
        json_schema_extra = {
            "example": {
                "employee_id": "550e8400-e29b-41d4-a716-446655440000",
                "manager_id": "550e8400-e29b-41d4-a716-446655440001",
                "cycle_name": "Annual 2024",
            }
        }


class BulkCreateEvaluationsRequest(BaseModel):
    """Request to create evaluations for multiple employees"""

    employee_ids: List[UUID] = Field(..., description="List of employee IDs")
    cycle_name: str = Field(..., description="Evaluation cycle name")
    start_date: Optional[datetime] = Field(None, description="Start date (default: now)")

    class Config:
        json_schema_extra = {
            "example": {
                "employee_ids": [
                    "550e8400-e29b-41d4-a716-446655440000",
                    "550e8400-e29b-41d4-a716-446655440001",
                ],
                "cycle_name": "Q4 2024",
            }
        }


class SubmitPeerFeedbackRequest(BaseModel):
    """Request to submit peer feedback"""

    peer_id: UUID = Field(..., description="Peer providing feedback")
    raw_input: str = Field(..., description="Raw feedback text or transcription")
    input_method: str = Field(default="text", description="Input method (text, voice, form)")
    technical_rating: Optional[Rating] = Field(None, description="Technical skills rating")
    leadership_rating: Optional[Rating] = Field(None, description="Leadership rating")
    communication_rating: Optional[Rating] = Field(None, description="Communication rating")
    collaboration_rating: Optional[Rating] = Field(None, description="Collaboration rating")
    supporting_docs: List[str] = Field(default_factory=list, description="Supporting document URLs")

    class Config:
        json_schema_extra = {
            "example": {
                "peer_id": "550e8400-e29b-41d4-a716-446655440002",
                "raw_input": "Jane did an excellent job leading the API migration project...",
                "input_method": "text",
                "technical_rating": "exceeds",
                "leadership_rating": "meets",
            }
        }


class SubmitSelfEvaluationRequest(BaseModel):
    """Request to submit self-evaluation"""

    raw_achievements: str = Field(..., description="Raw achievements text")
    raw_challenges: Optional[str] = Field(None, description="Raw challenges text")
    raw_growth_areas: Optional[str] = Field(None, description="Raw growth areas text")
    raw_goals: Optional[str] = Field(None, description="Raw goals text")
    uploaded_docs: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Uploaded documents"
    )
    project_links: List[str] = Field(default_factory=list, description="Project links")

    class Config:
        json_schema_extra = {
            "example": {
                "raw_achievements": "Led the API migration from v1 to v2, resulting in 40% performance improvement...",
                "raw_challenges": "Faced challenges with database schema migrations...",
                "uploaded_docs": [
                    {"name": "Q4_Achievements.pdf", "url": "https://..."}
                ],
            }
        }


class UpdateManagerEvaluationRequest(BaseModel):
    """Request to update manager evaluation"""

    final_summary: str = Field(..., description="Final evaluation summary")
    technical_assessment: Optional[str] = Field(None, description="Technical assessment")
    leadership_assessment: Optional[str] = Field(None, description="Leadership assessment")
    growth_opportunities: Optional[str] = Field(None, description="Growth opportunities")
    overall_rating: Rating = Field(..., description="Overall rating")
    technical_rating: Optional[Rating] = None
    leadership_rating: Optional[Rating] = None
    communication_rating: Optional[Rating] = None
    strategic_thinking_rating: Optional[Rating] = None
    promotion_eligibility: PromotionEligibility = Field(
        ...,
        description="Promotion eligibility"
    )
    promotion_justification: Optional[str] = Field(
        None,
        description="Promotion justification"
    )
    manager_responses: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Responses to AI questions"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "final_summary": "Jane demonstrated exceptional technical leadership...",
                "overall_rating": "exceeds",
                "promotion_eligibility": "ready_next_cycle",
                "promotion_justification": "Strong technical skills and emerging leadership...",
            }
        }


class SelectPeersRequest(BaseModel):
    """Request to select peer reviewers"""

    selected_peers: List[UUID] = Field(..., description="Selected peer reviewer IDs")
    role: str = Field(..., description="Role selecting peers (employee or manager)")

    class Config:
        json_schema_extra = {
            "example": {
                "selected_peers": [
                    "550e8400-e29b-41d4-a716-446655440002",
                    "550e8400-e29b-41d4-a716-446655440003",
                ],
                "role": "employee",
            }
        }


# ============================================================================
# Response Models
# ============================================================================


class EvaluationSummaryResponse(BaseModel):
    """Summary response for evaluation list"""

    id: UUID
    employee_id: UUID
    employee_name: str
    manager_id: UUID
    manager_name: str
    cycle_name: str
    current_phase: EvaluationPhase
    current_state: EvaluationState
    completion_percentage: float
    created_at: datetime
    updated_at: datetime
    peer_feedback_count: int
    has_self_evaluation: bool
    has_manager_evaluation: bool
    is_overdue: bool

    class Config:
        json_schema_extra = {
            "example": {
                "id": "eval-123",
                "employee_name": "Jane Doe",
                "manager_name": "John Smith",
                "cycle_name": "Annual 2024",
                "current_phase": "data_gathering",
                "current_state": "peer_feedback_in_progress",
                "completion_percentage": 0.3,
                "peer_feedback_count": 3,
                "has_self_evaluation": True,
                "has_manager_evaluation": False,
                "is_overdue": False,
            }
        }


class EvaluationDetailResponse(BaseModel):
    """Detailed response for a single evaluation"""

    id: UUID
    employee_id: UUID
    manager_id: UUID
    cycle_name: str
    current_phase: EvaluationPhase
    current_state: EvaluationState
    completion_percentage: float

    # Peer selection
    suggested_peers: List[Dict[str, Any]]
    employee_selected_peers: List[UUID]
    manager_approved_peers: List[UUID]

    # Feedback
    peer_feedbacks: List[Dict[str, Any]]
    self_evaluation: Optional[Dict[str, Any]]
    manager_evaluation: Optional[Dict[str, Any]]

    # Deadlines
    peer_selection_deadline: Optional[datetime]
    peer_feedback_deadline: Optional[datetime]
    self_eval_deadline: Optional[datetime]
    manager_eval_deadline: Optional[datetime]
    calibration_date: Optional[datetime]
    release_date: Optional[datetime]

    # Status
    pending_feedbacks: List[UUID]
    state_history: List[Dict[str, Any]]

    created_at: datetime
    updated_at: datetime


class PeerSuggestionsResponse(BaseModel):
    """Response for peer suggestions"""

    evaluation_id: UUID
    suggested_peers: List[Dict[str, Any]]
    total_suggestions: int

    class Config:
        json_schema_extra = {
            "example": {
                "evaluation_id": "eval-123",
                "suggested_peers": [
                    {
                        "peer_id": "peer-1",
                        "name": "Bob Johnson",
                        "relationship_strength": 0.85,
                        "total_hours": 120.5,
                        "reason": "Extensive collaboration on Platform team",
                    }
                ],
                "total_suggestions": 5,
            }
        }


class ManagerDraftResponse(BaseModel):
    """Response for AI-generated manager draft"""

    evaluation_id: UUID
    ai_draft_summary: str
    ai_draft_evidence_map: Dict[str, List[str]]
    clarifying_questions: List[Dict[str, str]]
    generated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "evaluation_id": "eval-123",
                "ai_draft_summary": "Based on analysis of 5 peer reviews and self-evaluation...",
                "ai_draft_evidence_map": {
                    "technical_leadership": ["Peer A mentioned...", "Project X shows..."],
                    "communication": ["Peer B noted...", "Self-eval highlights..."],
                },
                "clarifying_questions": [
                    {
                        "question": "How did Jane handle the database migration challenges?",
                        "context": "Multiple peers mentioned this but details are unclear",
                    }
                ],
            }
        }


class DashboardMetricsResponse(BaseModel):
    """Response for dashboard metrics"""

    total_evaluations: int
    active_evaluations: int
    completed_evaluations: int
    overdue_evaluations: int

    # By phase
    evaluations_by_phase: Dict[str, int]

    # By state
    evaluations_by_state: Dict[str, int]

    # Feedback stats
    total_peer_feedbacks: int
    avg_peer_feedbacks_per_eval: float
    self_evaluations_submitted: int
    manager_drafts_generated: int

    # Timing stats
    avg_completion_time_days: Optional[float]
    avg_peer_feedback_time_days: Optional[float]

    # Recent activity
    evaluations_started_last_7_days: int
    evaluations_completed_last_7_days: int

    calculated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "total_evaluations": 250,
                "active_evaluations": 180,
                "completed_evaluations": 70,
                "overdue_evaluations": 12,
                "evaluations_by_phase": {
                    "context_peer_selection": 20,
                    "data_gathering": 80,
                    "manager_evaluation": 60,
                },
                "total_peer_feedbacks": 850,
                "avg_peer_feedbacks_per_eval": 4.7,
            }
        }


class SwarmStatusResponse(BaseModel):
    """Response for agent swarm status"""

    orchestrator_id: str
    is_running: bool
    uptime_seconds: float

    # Agent status
    agents: Dict[str, Any]

    # System stats
    active_evaluations: int
    background_tasks: int
    database_stats: Dict[str, Any]

    timestamp: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "orchestrator_id": "orch-123",
                "is_running": True,
                "uptime_seconds": 86400.5,
                "agents": {
                    "watchkeeper": {"status": "active", "workload": 0.3},
                    "scribes": [
                        {"id": "scribe-1", "status": "active", "workload": 0.5},
                        {"id": "scribe-2", "status": "active", "workload": 0.4},
                    ],
                },
                "active_evaluations": 180,
                "background_tasks": 5,
            }
        }


class WebSocketMessage(BaseModel):
    """WebSocket message structure"""

    type: str = Field(..., description="Message type (update, notification, error)")
    evaluation_id: Optional[UUID] = Field(None, description="Related evaluation ID")
    data: Dict[str, Any] = Field(..., description="Message payload")
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {
                "type": "update",
                "evaluation_id": "eval-123",
                "data": {
                    "current_state": "peer_feedback_in_progress",
                    "peer_feedbacks_received": 3,
                },
                "timestamp": "2024-01-15T10:30:00",
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response"""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {
                "error": "NotFoundError",
                "message": "Evaluation not found",
                "detail": "Evaluation with ID eval-123 does not exist",
            }
        }
