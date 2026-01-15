"""
Bloom Dashboard API - Main Application

FastAPI application with routes for evaluation management,
feedback submission, and real-time monitoring.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Query, WebSocket, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from bloom.api.auth import (
    User,
    check_evaluation_access,
    check_peer_access,
    get_current_employee,
    get_current_hr_admin,
    get_current_manager,
    get_current_user,
)
from bloom.api.models import (
    BulkCreateEvaluationsRequest,
    CreateEvaluationRequest,
    DashboardMetricsResponse,
    ErrorResponse,
    EvaluationDetailResponse,
    EvaluationSummaryResponse,
    ManagerDraftResponse,
    PeerSuggestionsResponse,
    SelectPeersRequest,
    SubmitPeerFeedbackRequest,
    SubmitSelfEvaluationRequest,
    SwarmStatusResponse,
    UpdateManagerEvaluationRequest,
)
from bloom.api.websocket import (
    connection_manager,
    handle_evaluation_websocket,
    handle_swarm_websocket,
)
from bloom.models import Employee, Evaluation, EvaluationPhase, EvaluationState
from bloom.orchestrator import BloomOrchestrator

# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Bloom Dashboard API",
    description="AI-powered performance evaluation system with multi-agent orchestration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware for web dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global orchestrator instance (initialized on startup)
orchestrator: Optional[BloomOrchestrator] = None


# ============================================================================
# Lifecycle Events
# ============================================================================


@app.on_event("startup")
async def startup_event():
    """Initialize the Bloom orchestrator on application startup"""
    global orchestrator

    logger.info("Starting Bloom Dashboard API...")

    try:
        from bloom.orchestrator import BloomConfig

        # Initialize orchestrator
        config = BloomConfig(
            num_scribes=2,
            num_context_miners=1,
            num_chasers=1,
            enable_autonomous_mode=True,
            enable_rag=True,
        )

        orchestrator = BloomOrchestrator(config)
        await orchestrator.initialize()

        logger.info("Bloom Dashboard API started successfully")

    except Exception as e:
        logger.error(f"Failed to start Bloom Dashboard API: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown the Bloom orchestrator gracefully"""
    global orchestrator

    logger.info("Shutting down Bloom Dashboard API...")

    if orchestrator:
        await orchestrator.shutdown()

    logger.info("Bloom Dashboard API shutdown complete")


# ============================================================================
# Exception Handlers
# ============================================================================


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with standardized error response"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.detail,
            "timestamp": datetime.now().isoformat(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "detail": str(exc),
            "timestamp": datetime.now().isoformat(),
        },
    )


# ============================================================================
# Health & Status Endpoints
# ============================================================================


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - API information"""
    return {
        "name": "Bloom Dashboard API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "orchestrator_running": orchestrator is not None and orchestrator.is_running,
    }


# ============================================================================
# Evaluation Endpoints
# ============================================================================


@app.get(
    "/evaluations",
    response_model=List[EvaluationSummaryResponse],
    tags=["Evaluations"],
)
async def list_evaluations(
    cycle_name: Optional[str] = Query(None, description="Filter by cycle name"),
    phase: Optional[EvaluationPhase] = Query(None, description="Filter by phase"),
    state: Optional[EvaluationState] = Query(None, description="Filter by state"),
    employee_id: Optional[UUID] = Query(None, description="Filter by employee"),
    manager_id: Optional[UUID] = Query(None, description="Filter by manager"),
    overdue_only: bool = Query(False, description="Show only overdue evaluations"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Result offset"),
    current_user: User = Depends(get_current_employee),
) -> List[EvaluationSummaryResponse]:
    """
    List evaluations with optional filters

    Returns a paginated list of evaluation summaries.
    """
    if not orchestrator or not orchestrator.document_store:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator not initialized",
        )

    # Build query
    query: Dict[str, Any] = {}

    if cycle_name:
        query["cycle_name"] = cycle_name
    if phase:
        query["current_phase"] = phase.value
    if state:
        query["current_state"] = state.value
    if employee_id:
        query["employee_id"] = str(employee_id)
    if manager_id:
        query["manager_id"] = str(manager_id)

    # Fetch evaluations
    eval_docs = await orchestrator.document_store.find(
        collection="evaluations",
        query=query,
        limit=limit,
        offset=offset,
    )

    # Convert to summary responses
    summaries = []
    for doc in eval_docs:
        evaluation = Evaluation(**doc)

        # Get employee and manager names (mock for now)
        employee_name = f"Employee {evaluation.employee_id}"
        manager_name = f"Manager {evaluation.manager_id}"

        # Check if overdue
        is_overdue = any([
            evaluation.is_past_deadline("peer_selection"),
            evaluation.is_past_deadline("peer_feedback"),
            evaluation.is_past_deadline("self_eval"),
            evaluation.is_past_deadline("manager_eval"),
        ])

        if overdue_only and not is_overdue:
            continue

        summary = EvaluationSummaryResponse(
            id=evaluation.id,
            employee_id=evaluation.employee_id,
            employee_name=employee_name,
            manager_id=evaluation.manager_id,
            manager_name=manager_name,
            cycle_name=evaluation.cycle_name,
            current_phase=evaluation.current_phase,
            current_state=evaluation.current_state,
            completion_percentage=evaluation.get_completion_percentage(),
            created_at=evaluation.created_at,
            updated_at=evaluation.updated_at,
            peer_feedback_count=len(evaluation.peer_feedbacks),
            has_self_evaluation=evaluation.self_evaluation is not None,
            has_manager_evaluation=evaluation.manager_evaluation is not None,
            is_overdue=is_overdue,
        )
        summaries.append(summary)

    return summaries


@app.get(
    "/evaluations/{evaluation_id}",
    response_model=EvaluationDetailResponse,
    tags=["Evaluations"],
)
async def get_evaluation(
    evaluation_id: UUID,
    current_user: User = Depends(get_current_employee),
) -> EvaluationDetailResponse:
    """
    Get detailed evaluation information

    Returns complete evaluation data including feedback and state history.
    """
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator not initialized",
        )

    evaluation = await orchestrator.get_evaluation(evaluation_id)
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation {evaluation_id} not found",
        )

    # Check access
    check_evaluation_access(
        current_user,
        evaluation.employee_id,
        evaluation.manager_id,
        require_manager=False,
    )

    # Convert to detail response
    detail = EvaluationDetailResponse(
        id=evaluation.id,
        employee_id=evaluation.employee_id,
        manager_id=evaluation.manager_id,
        cycle_name=evaluation.cycle_name,
        current_phase=evaluation.current_phase,
        current_state=evaluation.current_state,
        completion_percentage=evaluation.get_completion_percentage(),
        suggested_peers=[
            {"peer_id": str(peer_id), "name": f"Peer {peer_id}"}
            for peer_id in evaluation.suggested_peers
        ],
        employee_selected_peers=evaluation.employee_selected_peers,
        manager_approved_peers=evaluation.manager_approved_peers,
        peer_feedbacks=[fb.model_dump() for fb in evaluation.peer_feedbacks],
        self_evaluation=evaluation.self_evaluation.model_dump() if evaluation.self_evaluation else None,
        manager_evaluation=evaluation.manager_evaluation.model_dump() if evaluation.manager_evaluation else None,
        peer_selection_deadline=evaluation.peer_selection_deadline,
        peer_feedback_deadline=evaluation.peer_feedback_deadline,
        self_eval_deadline=evaluation.self_eval_deadline,
        manager_eval_deadline=evaluation.manager_eval_deadline,
        calibration_date=evaluation.calibration_date,
        release_date=evaluation.release_date,
        pending_feedbacks=evaluation.get_pending_feedbacks(),
        state_history=evaluation.state_history,
        created_at=evaluation.created_at,
        updated_at=evaluation.updated_at,
    )

    return detail


@app.post(
    "/evaluations",
    response_model=EvaluationDetailResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Evaluations"],
)
async def create_evaluation(
    request: CreateEvaluationRequest,
    current_user: User = Depends(get_current_hr_admin),
) -> EvaluationDetailResponse:
    """
    Create a new evaluation

    Requires HR Admin role. Starts a new evaluation cycle for an employee.
    """
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator not initialized",
        )

    # Fetch employee data
    employee_doc = await orchestrator.document_store.find_by_id(
        "employees", str(request.employee_id)
    )
    if not employee_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee {request.employee_id} not found",
        )

    employee = Employee(**employee_doc)

    # Start evaluation cycle
    evaluation_ids = await orchestrator.start_evaluation_cycle(
        cycle_name=request.cycle_name,
        employees=[employee],
        start_date=request.start_date,
    )

    if not evaluation_ids:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create evaluation",
        )

    # Return created evaluation
    evaluation = await orchestrator.get_evaluation(evaluation_ids[0])

    return await get_evaluation(evaluation.id, current_user)


@app.post(
    "/evaluations/bulk",
    response_model=List[UUID],
    status_code=status.HTTP_201_CREATED,
    tags=["Evaluations"],
)
async def create_bulk_evaluations(
    request: BulkCreateEvaluationsRequest,
    current_user: User = Depends(get_current_hr_admin),
) -> List[UUID]:
    """
    Create evaluations for multiple employees

    Requires HR Admin role. Starts a new evaluation cycle for a cohort.
    """
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator not initialized",
        )

    # Fetch all employees
    employees = []
    for employee_id in request.employee_ids:
        employee_doc = await orchestrator.document_store.find_by_id(
            "employees", str(employee_id)
        )
        if employee_doc:
            employees.append(Employee(**employee_doc))
        else:
            logger.warning(f"Employee {employee_id} not found, skipping")

    if not employees:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid employees found",
        )

    # Start evaluation cycle
    evaluation_ids = await orchestrator.start_evaluation_cycle(
        cycle_name=request.cycle_name,
        employees=employees,
        start_date=request.start_date,
    )

    return evaluation_ids


@app.get(
    "/evaluations/{evaluation_id}/peer-suggestions",
    response_model=PeerSuggestionsResponse,
    tags=["Evaluations"],
)
async def get_peer_suggestions(
    evaluation_id: UUID,
    current_user: User = Depends(get_current_employee),
) -> PeerSuggestionsResponse:
    """
    Get AI-generated peer reviewer suggestions

    Uses ContextMiner to suggest peers based on collaboration data.
    """
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator not initialized",
        )

    evaluation = await orchestrator.get_evaluation(evaluation_id)
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation {evaluation_id} not found",
        )

    # Check access
    check_evaluation_access(
        current_user,
        evaluation.employee_id,
        evaluation.manager_id,
        require_manager=False,
    )

    # Process peer selection if not done yet
    if not evaluation.suggested_peers:
        result = await orchestrator.process_peer_selection(
            evaluation_id=evaluation_id,
            employee_id=evaluation.employee_id,
        )
        suggested_peers = result.get("suggested_peers", [])
    else:
        # Return existing suggestions
        suggested_peers = [
            {"peer_id": str(peer_id), "name": f"Peer {peer_id}"}
            for peer_id in evaluation.suggested_peers
        ]

    return PeerSuggestionsResponse(
        evaluation_id=evaluation_id,
        suggested_peers=suggested_peers,
        total_suggestions=len(suggested_peers),
    )


@app.put(
    "/evaluations/{evaluation_id}/select-peers",
    response_model=EvaluationDetailResponse,
    tags=["Evaluations"],
)
async def select_peers(
    evaluation_id: UUID,
    request: SelectPeersRequest,
    current_user: User = Depends(get_current_employee),
) -> EvaluationDetailResponse:
    """
    Select peer reviewers for an evaluation

    Employee selects initial peers, manager approves final list.
    """
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator not initialized",
        )

    evaluation = await orchestrator.get_evaluation(evaluation_id)
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation {evaluation_id} not found",
        )

    # Update based on role
    if request.role == "employee":
        # Employee selection
        if current_user.id != evaluation.employee_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the employee can select initial peers",
            )
        evaluation.employee_selected_peers = request.selected_peers

    elif request.role == "manager":
        # Manager approval
        if current_user.id != evaluation.manager_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the manager can approve peers",
            )
        evaluation.manager_approved_peers = request.selected_peers

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role (must be 'employee' or 'manager')",
        )

    # Update evaluation
    await orchestrator._update_evaluation(evaluation)

    return await get_evaluation(evaluation_id, current_user)


@app.put(
    "/evaluations/{evaluation_id}/peer-feedback",
    response_model=EvaluationDetailResponse,
    tags=["Evaluations"],
)
async def submit_peer_feedback(
    evaluation_id: UUID,
    request: SubmitPeerFeedbackRequest,
    current_user: User = Depends(get_current_employee),
) -> EvaluationDetailResponse:
    """
    Submit peer feedback for an evaluation

    Feedback is synthesized by AI into professional format.
    """
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator not initialized",
        )

    evaluation = await orchestrator.get_evaluation(evaluation_id)
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation {evaluation_id} not found",
        )

    # Check peer access
    check_peer_access(current_user, evaluation.manager_approved_peers)

    # Process peer feedback
    feedback = await orchestrator.process_peer_feedback(
        evaluation_id=evaluation_id,
        peer_id=request.peer_id,
        raw_feedback=request.raw_input,
        input_method=request.input_method,
    )

    logger.info(f"Peer feedback submitted for evaluation {evaluation_id}")

    return await get_evaluation(evaluation_id, current_user)


@app.put(
    "/evaluations/{evaluation_id}/self-eval",
    response_model=EvaluationDetailResponse,
    tags=["Evaluations"],
)
async def submit_self_evaluation(
    evaluation_id: UUID,
    request: SubmitSelfEvaluationRequest,
    current_user: User = Depends(get_current_employee),
) -> EvaluationDetailResponse:
    """
    Submit self-evaluation

    Employee's self-assessment is synthesized by AI.
    """
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator not initialized",
        )

    evaluation = await orchestrator.get_evaluation(evaluation_id)
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation {evaluation_id} not found",
        )

    # Check employee access
    if current_user.id != evaluation.employee_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the employee can submit self-evaluation",
        )

    # Create self-evaluation (in production, would use Scribe for synthesis)
    from bloom.models import SelfEvaluation

    self_eval = SelfEvaluation(
        evaluation_id=evaluation_id,
        employee_id=evaluation.employee_id,
        raw_achievements=request.raw_achievements,
        raw_challenges=request.raw_challenges,
        raw_growth_areas=request.raw_growth_areas,
        raw_goals=request.raw_goals,
        uploaded_docs=request.uploaded_docs,
        project_links=request.project_links,
    )

    evaluation.self_evaluation = self_eval
    await orchestrator._update_evaluation(evaluation)

    logger.info(f"Self-evaluation submitted for evaluation {evaluation_id}")

    return await get_evaluation(evaluation_id, current_user)


@app.get(
    "/evaluations/{evaluation_id}/draft",
    response_model=ManagerDraftResponse,
    tags=["Evaluations"],
)
async def get_manager_draft(
    evaluation_id: UUID,
    current_user: User = Depends(get_current_manager),
) -> ManagerDraftResponse:
    """
    Get AI-generated manager evaluation draft

    Uses RAG pipeline to generate evidence-based draft.
    """
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator not initialized",
        )

    evaluation = await orchestrator.get_evaluation(evaluation_id)
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation {evaluation_id} not found",
        )

    # Check manager access
    check_evaluation_access(
        current_user,
        evaluation.employee_id,
        evaluation.manager_id,
        require_manager=True,
    )

    # Generate draft if not exists
    if not evaluation.manager_evaluation or not evaluation.manager_evaluation.ai_draft_summary:
        manager_eval = await orchestrator.generate_manager_draft(evaluation_id)
    else:
        manager_eval = evaluation.manager_evaluation

    return ManagerDraftResponse(
        evaluation_id=evaluation_id,
        ai_draft_summary=manager_eval.ai_draft_summary,
        ai_draft_evidence_map=manager_eval.ai_draft_evidence_map,
        clarifying_questions=manager_eval.ai_questions,
        generated_at=manager_eval.ai_generated_at,
    )


# ============================================================================
# Dashboard Endpoints
# ============================================================================


@app.get(
    "/dashboard/metrics",
    response_model=DashboardMetricsResponse,
    tags=["Dashboard"],
)
async def get_dashboard_metrics(
    current_user: User = Depends(get_current_employee),
) -> DashboardMetricsResponse:
    """
    Get dashboard metrics

    Returns aggregated metrics for the evaluation system.
    """
    if not orchestrator or not orchestrator.document_store:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator not initialized",
        )

    # Fetch all evaluations (in production, would use aggregation pipeline)
    eval_docs = await orchestrator.document_store.find(
        collection="evaluations",
        query={},
        limit=10000,
    )

    evaluations = [Evaluation(**doc) for doc in eval_docs]

    # Calculate metrics
    total = len(evaluations)
    active = sum(1 for e in evaluations if e.current_phase != EvaluationPhase.COMPLETED)
    completed = sum(1 for e in evaluations if e.current_phase == EvaluationPhase.COMPLETED)
    overdue = sum(1 for e in evaluations if any([
        e.is_past_deadline("peer_feedback"),
        e.is_past_deadline("self_eval"),
        e.is_past_deadline("manager_eval"),
    ]))

    # By phase
    by_phase = {}
    for phase in EvaluationPhase:
        by_phase[phase.value] = sum(1 for e in evaluations if e.current_phase == phase)

    # By state
    by_state = {}
    for state in EvaluationState:
        by_state[state.value] = sum(1 for e in evaluations if e.current_state == state)

    # Feedback stats
    total_peer_feedbacks = sum(len(e.peer_feedbacks) for e in evaluations)
    avg_peer_feedbacks = total_peer_feedbacks / total if total > 0 else 0
    self_evals_submitted = sum(1 for e in evaluations if e.self_evaluation is not None)
    manager_drafts = sum(1 for e in evaluations if e.manager_evaluation is not None)

    # Recent activity
    from datetime import timedelta
    seven_days_ago = datetime.now() - timedelta(days=7)
    started_last_7 = sum(1 for e in evaluations if e.created_at >= seven_days_ago)
    completed_last_7 = sum(
        1 for e in evaluations
        if e.completed_at and e.completed_at >= seven_days_ago
    )

    return DashboardMetricsResponse(
        total_evaluations=total,
        active_evaluations=active,
        completed_evaluations=completed,
        overdue_evaluations=overdue,
        evaluations_by_phase=by_phase,
        evaluations_by_state=by_state,
        total_peer_feedbacks=total_peer_feedbacks,
        avg_peer_feedbacks_per_eval=avg_peer_feedbacks,
        self_evaluations_submitted=self_evals_submitted,
        manager_drafts_generated=manager_drafts,
        avg_completion_time_days=None,  # Would calculate from completed evals
        avg_peer_feedback_time_days=None,  # Would calculate from timestamps
        evaluations_started_last_7_days=started_last_7,
        evaluations_completed_last_7_days=completed_last_7,
        calculated_at=datetime.now(),
    )


@app.get(
    "/dashboard/swarm-status",
    response_model=SwarmStatusResponse,
    tags=["Dashboard"],
)
async def get_swarm_status(
    current_user: User = Depends(get_current_hr_admin),
) -> SwarmStatusResponse:
    """
    Get agent swarm status

    Returns detailed status of all agents and system health.
    Requires HR Admin role.
    """
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator not initialized",
        )

    status_data = await orchestrator.get_swarm_status()

    return SwarmStatusResponse(
        orchestrator_id=status_data["orchestrator_id"],
        is_running=status_data["is_running"],
        uptime_seconds=status_data["uptime_seconds"],
        agents=status_data["agents"],
        active_evaluations=status_data["active_evaluations"],
        background_tasks=status_data["background_tasks"],
        database_stats=status_data["database_stats"],
        timestamp=datetime.now(),
    )


# ============================================================================
# WebSocket Endpoints
# ============================================================================


@app.websocket("/ws/evaluations/{evaluation_id}")
async def websocket_evaluation(
    websocket: WebSocket,
    evaluation_id: UUID,
):
    """
    WebSocket endpoint for real-time evaluation updates

    Subscribe to receive real-time updates for a specific evaluation:
    - State changes
    - Feedback submissions
    - Deadline notifications
    - AI draft generation
    """
    # In production, would authenticate WebSocket connection
    # For now, accept all connections
    await handle_evaluation_websocket(websocket, evaluation_id)


@app.websocket("/ws/swarm")
async def websocket_swarm(websocket: WebSocket):
    """
    WebSocket endpoint for real-time swarm status updates

    Subscribe to receive real-time updates about agent swarm:
    - Agent status changes
    - System metrics
    - Performance data
    """
    await handle_swarm_websocket(websocket)


@app.get("/ws/stats", tags=["WebSocket"])
async def websocket_stats():
    """Get WebSocket connection statistics"""
    return connection_manager.get_stats()


# ============================================================================
# Development/Testing Endpoints
# ============================================================================


@app.post("/dev/mock-token", tags=["Development"])
async def create_mock_token(role: str = "employee"):
    """
    Create a mock authentication token for development/testing

    Args:
        role: User role (employee, manager, hr_admin, system_admin)
    """
    from bloom.api.auth import UserRole, create_mock_token

    try:
        user_role = UserRole(role)
        token = create_mock_token(user_role)

        return {
            "token": token,
            "role": user_role.value,
            "note": "This is a mock token for development only",
        }
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: {role}",
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
