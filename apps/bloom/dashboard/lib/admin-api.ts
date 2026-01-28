/**
 * HR Admin Control Room API
 * Mock service that simulates data from Postgres based on models/
 */

import {
  ControlRoomData,
  EvaluationOverview,
  ActivityEvent,
  DeadlineAlert,
  PhaseStats,
  DepartmentStats,
  ManagerStats,
  SystemHealth,
  EvaluationPhase,
  EvaluationState,
  DeadlineStatus,
  EventType,
} from '@/types/admin';

/**
 * Generate mock control room data
 * In production, this would query your Postgres database
 */
export async function getControlRoomData(): Promise<ControlRoomData> {
  // Simulate API delay
  await new Promise((resolve) => setTimeout(resolve, 500));

  // Generate mock evaluations
  const evaluations: EvaluationOverview[] = [
    // Phase 1: Peer Selection
    {
      id: 'eval-001',
      employee_id: 'emp-001',
      employee_name: 'Sarah Johnson',
      employee_title: 'Senior Software Engineer',
      employee_department: 'Engineering',
      employee_level: 'L4',
      manager_id: 'mgr-001',
      manager_name: 'Michael Chen',
      cycle_name: 'H2 2024',
      current_phase: EvaluationPhase.CONTEXT_PEER_SELECTION,
      current_state: EvaluationState.EMPLOYEE_PEER_REVIEW,
      completion_percentage: 15,
      peer_selection_complete: false,
      peer_feedback_count: 0,
      peer_feedback_total: 5,
      self_eval_complete: false,
      manager_eval_complete: false,
      calibration_complete: false,
      peer_selection_deadline: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString(),
      peer_feedback_deadline: null,
      self_eval_deadline: null,
      manager_eval_deadline: null,
      calibration_date: null,
      release_date: null,
      is_overdue: false,
      overdue_deadline: null,
      is_blocked: false,
      blocked_reason: null,
      created_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
      updated_at: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
      last_activity_at: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
    },

    // Phase 2: Data Gathering
    {
      id: 'eval-002',
      employee_id: 'emp-002',
      employee_name: 'David Martinez',
      employee_title: 'Product Manager',
      employee_department: 'Product',
      employee_level: 'L5',
      manager_id: 'mgr-002',
      manager_name: 'Emily Watson',
      cycle_name: 'H2 2024',
      current_phase: EvaluationPhase.DATA_GATHERING,
      current_state: EvaluationState.PEER_FEEDBACK_IN_PROGRESS,
      completion_percentage: 35,
      peer_selection_complete: true,
      peer_feedback_count: 3,
      peer_feedback_total: 5,
      self_eval_complete: false,
      manager_eval_complete: false,
      calibration_complete: false,
      peer_selection_deadline: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
      peer_feedback_deadline: new Date(Date.now() + 4 * 24 * 60 * 60 * 1000).toISOString(),
      self_eval_deadline: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
      manager_eval_deadline: null,
      calibration_date: null,
      release_date: null,
      is_overdue: false,
      overdue_deadline: null,
      is_blocked: false,
      blocked_reason: null,
      created_at: new Date(Date.now() - 12 * 24 * 60 * 60 * 1000).toISOString(),
      updated_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      last_activity_at: new Date(Date.now() - 45 * 60 * 1000).toISOString(),
    },

    // Phase 2: Overdue case
    {
      id: 'eval-003',
      employee_id: 'emp-003',
      employee_name: 'Jessica Lee',
      employee_title: 'UX Designer',
      employee_department: 'Design',
      employee_level: 'L3',
      manager_id: 'mgr-003',
      manager_name: 'Robert Kim',
      cycle_name: 'H2 2024',
      current_phase: EvaluationPhase.DATA_GATHERING,
      current_state: EvaluationState.SELF_EVAL_REQUESTED,
      completion_percentage: 28,
      peer_selection_complete: true,
      peer_feedback_count: 5,
      peer_feedback_total: 5,
      self_eval_complete: false,
      manager_eval_complete: false,
      calibration_complete: false,
      peer_selection_deadline: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString(),
      peer_feedback_deadline: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
      self_eval_deadline: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
      manager_eval_deadline: null,
      calibration_date: null,
      release_date: null,
      is_overdue: true,
      overdue_deadline: 'self_eval_deadline',
      is_blocked: false,
      blocked_reason: null,
      created_at: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000).toISOString(),
      updated_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
      last_activity_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
    },

    // Phase 3: Manager Evaluation
    {
      id: 'eval-004',
      employee_id: 'emp-004',
      employee_name: 'Alex Thompson',
      employee_title: 'Engineering Manager',
      employee_department: 'Engineering',
      employee_level: 'L6',
      manager_id: 'mgr-004',
      manager_name: 'Jennifer Liu',
      cycle_name: 'H2 2024',
      current_phase: EvaluationPhase.MANAGER_EVALUATION,
      current_state: EvaluationState.AI_DRAFT_GENERATED,
      completion_percentage: 62,
      peer_selection_complete: true,
      peer_feedback_count: 6,
      peer_feedback_total: 6,
      self_eval_complete: true,
      manager_eval_complete: false,
      calibration_complete: false,
      peer_selection_deadline: new Date(Date.now() - 20 * 24 * 60 * 60 * 1000).toISOString(),
      peer_feedback_deadline: new Date(Date.now() - 12 * 24 * 60 * 60 * 1000).toISOString(),
      self_eval_deadline: new Date(Date.now() - 8 * 24 * 60 * 60 * 1000).toISOString(),
      manager_eval_deadline: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString(),
      calibration_date: null,
      release_date: null,
      is_overdue: false,
      overdue_deadline: null,
      is_blocked: false,
      blocked_reason: null,
      created_at: new Date(Date.now() - 25 * 24 * 60 * 60 * 1000).toISOString(),
      updated_at: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
      last_activity_at: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
    },

    // Phase 4: Calibration
    {
      id: 'eval-005',
      employee_id: 'emp-005',
      employee_name: 'Maria Garcia',
      employee_title: 'Data Scientist',
      employee_department: 'Data',
      employee_level: 'L4',
      manager_id: 'mgr-005',
      manager_name: 'James Wilson',
      cycle_name: 'H2 2024',
      current_phase: EvaluationPhase.CALIBRATION,
      current_state: EvaluationState.CALIBRATION_IN_PROGRESS,
      completion_percentage: 78,
      peer_selection_complete: true,
      peer_feedback_count: 5,
      peer_feedback_total: 5,
      self_eval_complete: true,
      manager_eval_complete: true,
      calibration_complete: false,
      peer_selection_deadline: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
      peer_feedback_deadline: new Date(Date.now() - 22 * 24 * 60 * 60 * 1000).toISOString(),
      self_eval_deadline: new Date(Date.now() - 18 * 24 * 60 * 60 * 1000).toISOString(),
      manager_eval_deadline: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
      calibration_date: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString(),
      release_date: null,
      is_overdue: false,
      overdue_deadline: null,
      is_blocked: false,
      blocked_reason: null,
      created_at: new Date(Date.now() - 35 * 24 * 60 * 60 * 1000).toISOString(),
      updated_at: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
      last_activity_at: new Date(Date.now() - 20 * 60 * 1000).toISOString(),
    },

    // Phase 5: Release/Discussion
    {
      id: 'eval-006',
      employee_id: 'emp-006',
      employee_name: 'Kevin Patel',
      employee_title: 'DevOps Engineer',
      employee_department: 'Engineering',
      employee_level: 'L3',
      manager_id: 'mgr-001',
      manager_name: 'Michael Chen',
      cycle_name: 'H2 2024',
      current_phase: EvaluationPhase.RELEASE_DISCUSSION,
      current_state: EvaluationState.DISCUSSION_SCHEDULED,
      completion_percentage: 92,
      peer_selection_complete: true,
      peer_feedback_count: 4,
      peer_feedback_total: 4,
      self_eval_complete: true,
      manager_eval_complete: true,
      calibration_complete: true,
      peer_selection_deadline: new Date(Date.now() - 40 * 24 * 60 * 60 * 1000).toISOString(),
      peer_feedback_deadline: new Date(Date.now() - 32 * 24 * 60 * 60 * 1000).toISOString(),
      self_eval_deadline: new Date(Date.now() - 28 * 24 * 60 * 60 * 1000).toISOString(),
      manager_eval_deadline: new Date(Date.now() - 12 * 24 * 60 * 60 * 1000).toISOString(),
      calibration_date: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
      release_date: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
      is_overdue: false,
      overdue_deadline: null,
      is_blocked: false,
      blocked_reason: null,
      created_at: new Date(Date.now() - 45 * 24 * 60 * 60 * 1000).toISOString(),
      updated_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
      last_activity_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    },

    // Completed
    {
      id: 'eval-007',
      employee_id: 'emp-007',
      employee_name: 'Rachel Wong',
      employee_title: 'Product Designer',
      employee_department: 'Design',
      employee_level: 'L4',
      manager_id: 'mgr-003',
      manager_name: 'Robert Kim',
      cycle_name: 'H2 2024',
      current_phase: EvaluationPhase.COMPLETED,
      current_state: EvaluationState.ACKNOWLEDGED,
      completion_percentage: 100,
      peer_selection_complete: true,
      peer_feedback_count: 5,
      peer_feedback_total: 5,
      self_eval_complete: true,
      manager_eval_complete: true,
      calibration_complete: true,
      peer_selection_deadline: new Date(Date.now() - 50 * 24 * 60 * 60 * 1000).toISOString(),
      peer_feedback_deadline: new Date(Date.now() - 42 * 24 * 60 * 60 * 1000).toISOString(),
      self_eval_deadline: new Date(Date.now() - 38 * 24 * 60 * 60 * 1000).toISOString(),
      manager_eval_deadline: new Date(Date.now() - 20 * 24 * 60 * 60 * 1000).toISOString(),
      calibration_date: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString(),
      release_date: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
      is_overdue: false,
      overdue_deadline: null,
      is_blocked: false,
      blocked_reason: null,
      created_at: new Date(Date.now() - 55 * 24 * 60 * 60 * 1000).toISOString(),
      updated_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
      last_activity_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
    },

    // More evaluations for variety
    ...generateAdditionalEvaluations(),
  ];

  // Generate recent activity
  const recent_activity: ActivityEvent[] = [
    {
      id: 'activity-001',
      evaluation_id: 'eval-004',
      employee_name: 'Alex Thompson',
      event_type: EventType.STATE_CHANGED,
      description: 'AI draft generated for manager review',
      actor_name: 'Draft Generator Agent',
      actor_type: 'agent',
      timestamp: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
    },
    {
      id: 'activity-002',
      evaluation_id: 'eval-002',
      employee_name: 'David Martinez',
      event_type: EventType.FEEDBACK_SUBMITTED,
      description: 'Peer feedback submitted by Sarah J.',
      actor_name: 'Sarah J.',
      actor_type: 'user',
      timestamp: new Date(Date.now() - 45 * 60 * 1000).toISOString(),
    },
    {
      id: 'activity-003',
      evaluation_id: 'eval-001',
      employee_name: 'Sarah Johnson',
      event_type: EventType.PEER_SELECTED,
      description: 'Selected 3 of 5 peer reviewers',
      actor_name: 'Sarah Johnson',
      actor_type: 'user',
      timestamp: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
    },
    {
      id: 'activity-004',
      evaluation_id: 'eval-005',
      employee_name: 'Maria Garcia',
      event_type: EventType.STATE_CHANGED,
      description: 'Moved to calibration phase',
      actor_name: 'Workflow Orchestrator',
      actor_type: 'system',
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    },
    {
      id: 'activity-005',
      evaluation_id: 'eval-006',
      employee_name: 'Kevin Patel',
      event_type: EventType.EVALUATION_RELEASED,
      description: 'Evaluation released to employee',
      actor_name: 'Michael Chen',
      actor_type: 'user',
      timestamp: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    },
  ];

  // Generate deadline alerts
  const deadline_alerts: DeadlineAlert[] = [
    {
      id: 'deadline-001',
      evaluation_id: 'eval-003',
      employee_name: 'Jessica Lee',
      deadline_type: 'Self-Evaluation',
      due_date: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
      status: DeadlineStatus.OVERDUE,
      days_remaining: -1,
      responsible_user_name: 'Jessica Lee',
    },
    {
      id: 'deadline-002',
      evaluation_id: 'eval-001',
      employee_name: 'Sarah Johnson',
      deadline_type: 'Peer Selection',
      due_date: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString(),
      status: DeadlineStatus.APPROACHING,
      days_remaining: 2,
      responsible_user_name: 'Sarah Johnson',
    },
    {
      id: 'deadline-003',
      evaluation_id: 'eval-002',
      employee_name: 'David Martinez',
      deadline_type: 'Peer Feedback',
      due_date: new Date(Date.now() + 4 * 24 * 60 * 60 * 1000).toISOString(),
      status: DeadlineStatus.APPROACHING,
      days_remaining: 4,
      responsible_user_name: 'Various peers',
    },
  ];

  // Calculate phase distribution
  const phase_distribution: PhaseStats[] = Object.values(EvaluationPhase)
    .filter(phase => phase !== EvaluationPhase.CANCELLED)
    .map(phase => {
      const count = evaluations.filter(e => e.current_phase === phase).length;
      return {
        phase,
        count,
        percentage: (count / evaluations.length) * 100,
        avg_time_in_phase_days: Math.random() * 10 + 5, // Mock
      };
    });

  // Calculate department stats
  const department_stats: DepartmentStats[] = [
    {
      department: 'Engineering',
      total_evaluations: evaluations.filter(e => e.employee_department === 'Engineering').length,
      completed: evaluations.filter(e => e.employee_department === 'Engineering' && e.current_phase === EvaluationPhase.COMPLETED).length,
      in_progress: evaluations.filter(e => e.employee_department === 'Engineering' && e.current_phase !== EvaluationPhase.COMPLETED).length,
      overdue: evaluations.filter(e => e.employee_department === 'Engineering' && e.is_overdue).length,
      avg_completion_percentage: 65,
      managers: [
        {
          manager_id: 'mgr-001',
          manager_name: 'Michael Chen',
          total_evaluations: 2,
          completed: 0,
          in_progress: 2,
          overdue: 0,
          avg_completion_percentage: 54,
        },
      ],
    },
    {
      department: 'Design',
      total_evaluations: evaluations.filter(e => e.employee_department === 'Design').length,
      completed: evaluations.filter(e => e.employee_department === 'Design' && e.current_phase === EvaluationPhase.COMPLETED).length,
      in_progress: evaluations.filter(e => e.employee_department === 'Design' && e.current_phase !== EvaluationPhase.COMPLETED).length,
      overdue: evaluations.filter(e => e.employee_department === 'Design' && e.is_overdue).length,
      avg_completion_percentage: 64,
      managers: [
        {
          manager_id: 'mgr-003',
          manager_name: 'Robert Kim',
          total_evaluations: 2,
          completed: 1,
          in_progress: 1,
          overdue: 1,
          avg_completion_percentage: 64,
        },
      ],
    },
  ];

  // Calculate system health
  const health: SystemHealth = {
    total_evaluations: evaluations.length,
    active_evaluations: evaluations.filter(e => e.current_phase !== EvaluationPhase.COMPLETED && e.current_phase !== EvaluationPhase.CANCELLED).length,
    completed_evaluations: evaluations.filter(e => e.current_phase === EvaluationPhase.COMPLETED).length,
    cancelled_evaluations: evaluations.filter(e => e.current_phase === EvaluationPhase.CANCELLED).length,
    overdue_count: evaluations.filter(e => e.is_overdue).length,
    approaching_deadline_count: deadline_alerts.filter(a => a.status === DeadlineStatus.APPROACHING).length,
    blocked_count: evaluations.filter(e => e.is_blocked).length,
    avg_completion_time_days: 42,
    on_track_percentage: Math.round(((evaluations.length - evaluations.filter(e => e.is_overdue).length) / evaluations.length) * 100),
  };

  return {
    health,
    evaluations,
    recent_activity,
    deadline_alerts,
    phase_distribution,
    department_stats,
    last_updated: new Date().toISOString(),
  };
}

/**
 * Generate additional mock evaluations for variety
 */
function generateAdditionalEvaluations(): EvaluationOverview[] {
  const names = [
    'Emma Davis', 'James Brown', 'Sophia Miller', 'William Jones', 'Olivia Taylor',
    'Lucas Anderson', 'Ava Thomas', 'Mason Jackson', 'Isabella White', 'Ethan Harris'
  ];
  const titles = [
    'Software Engineer', 'Senior Engineer', 'Staff Engineer', 'Product Manager',
    'Designer', 'Data Analyst', 'QA Engineer', 'Tech Lead'
  ];
  const departments = ['Engineering', 'Product', 'Design', 'Data', 'QA'];
  const phases = Object.values(EvaluationPhase).filter(p => p !== EvaluationPhase.CANCELLED);

  return names.slice(0, 5).map((name, i) => {
    const phase = phases[Math.floor(Math.random() * phases.length)];
    const isOverdue = Math.random() > 0.8;

    return {
      id: `eval-${100 + i}`,
      employee_id: `emp-${100 + i}`,
      employee_name: name,
      employee_title: titles[Math.floor(Math.random() * titles.length)],
      employee_department: departments[Math.floor(Math.random() * departments.length)],
      employee_level: `L${Math.floor(Math.random() * 4) + 2}`,
      manager_id: `mgr-${Math.floor(Math.random() * 5) + 1}`,
      manager_name: 'Manager Name',
      cycle_name: 'H2 2024',
      current_phase: phase,
      current_state: EvaluationState.CYCLE_STARTED,
      completion_percentage: Math.floor(Math.random() * 100),
      peer_selection_complete: Math.random() > 0.5,
      peer_feedback_count: Math.floor(Math.random() * 5),
      peer_feedback_total: 5,
      self_eval_complete: Math.random() > 0.5,
      manager_eval_complete: Math.random() > 0.7,
      calibration_complete: Math.random() > 0.8,
      peer_selection_deadline: new Date(Date.now() + (Math.random() * 10 - 5) * 24 * 60 * 60 * 1000).toISOString(),
      peer_feedback_deadline: null,
      self_eval_deadline: null,
      manager_eval_deadline: null,
      calibration_date: null,
      release_date: null,
      is_overdue: isOverdue,
      overdue_deadline: isOverdue ? 'peer_selection_deadline' : null,
      is_blocked: Math.random() > 0.9,
      blocked_reason: null,
      created_at: new Date(Date.now() - Math.random() * 60 * 24 * 60 * 60 * 1000).toISOString(),
      updated_at: new Date(Date.now() - Math.random() * 24 * 60 * 60 * 1000).toISOString(),
      last_activity_at: new Date(Date.now() - Math.random() * 24 * 60 * 60 * 1000).toISOString(),
    };
  });
}
