/**
 * HR Admin Control Room Types
 * Based on apps/bloom/models/* - Evaluation system overview types
 */

// Evaluation Phases (from evaluation.py)
export enum EvaluationPhase {
  CONTEXT_PEER_SELECTION = 'context_peer_selection',
  DATA_GATHERING = 'data_gathering',
  MANAGER_EVALUATION = 'manager_evaluation',
  CALIBRATION = 'calibration',
  RELEASE_DISCUSSION = 'release_discussion',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled',
}

// Evaluation States (from evaluation.py)
export enum EvaluationState {
  // Phase 1
  CYCLE_STARTED = 'cycle_started',
  PEER_SUGGESTION_GENERATED = 'peer_suggestion_generated',
  EMPLOYEE_PEER_REVIEW = 'employee_peer_review',
  MANAGER_PEER_APPROVAL = 'manager_peer_approval',
  PEER_LIST_LOCKED = 'peer_list_locked',

  // Phase 2
  PEER_FEEDBACK_REQUESTED = 'peer_feedback_requested',
  PEER_FEEDBACK_IN_PROGRESS = 'peer_feedback_in_progress',
  SELF_EVAL_REQUESTED = 'self_eval_requested',
  SELF_EVAL_IN_PROGRESS = 'self_eval_in_progress',
  DATA_GATHERING_COMPLETE = 'data_gathering_complete',

  // Phase 3
  MANAGER_EVAL_STARTED = 'manager_eval_started',
  AI_DRAFT_GENERATED = 'ai_draft_generated',
  MANAGER_REVIEW_IN_PROGRESS = 'manager_review_in_progress',
  MANAGER_EVAL_COMPLETE = 'manager_eval_complete',

  // Phase 4
  CALIBRATION_PENDING = 'calibration_pending',
  CALIBRATION_IN_PROGRESS = 'calibration_in_progress',
  CALIBRATION_COMPLETE = 'calibration_complete',

  // Phase 5
  RELEASE_SCHEDULED = 'release_scheduled',
  RELEASED = 'released',
  DISCUSSION_SCHEDULED = 'discussion_scheduled',
  DISCUSSION_COMPLETE = 'discussion_complete',
  ACKNOWLEDGED = 'acknowledged',
  DECLINED = 'declined',

  // Terminal
  COMPLETED = 'completed',
  CANCELLED = 'cancelled',
}

// Deadline Status (from workflow.py)
export enum DeadlineStatus {
  UPCOMING = 'upcoming',
  APPROACHING = 'approaching',
  DUE_TODAY = 'due_today',
  OVERDUE = 'overdue',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled',
}

// Event Types (from workflow.py)
export enum EventType {
  STATE_CHANGED = 'state_changed',
  PHASE_CHANGED = 'phase_changed',
  PEER_SELECTED = 'peer_selected',
  PEER_APPROVED = 'peer_approved',
  FEEDBACK_SUBMITTED = 'feedback_submitted',
  SELF_EVAL_SUBMITTED = 'self_eval_submitted',
  MANAGER_EVAL_SUBMITTED = 'manager_eval_submitted',
  EVALUATION_RELEASED = 'evaluation_released',
  EMPLOYEE_ACKNOWLEDGED = 'employee_acknowledged',
  EMPLOYEE_DECLINED = 'employee_declined',
  DEADLINE_APPROACHING = 'deadline_approaching',
  DEADLINE_MISSED = 'deadline_missed',
  REMINDER_SENT = 'reminder_sent',
  NOTIFICATION_SENT = 'notification_sent',
  ERROR_OCCURRED = 'error_occurred',
}

/**
 * Single evaluation overview for the control room
 */
export interface EvaluationOverview {
  id: string;
  employee_id: string;
  employee_name: string;
  employee_title: string;
  employee_department: string;
  employee_level: string;
  manager_id: string;
  manager_name: string;
  cycle_name: string;

  // Status
  current_phase: EvaluationPhase;
  current_state: EvaluationState;
  completion_percentage: number;

  // Progress
  peer_selection_complete: boolean;
  peer_feedback_count: number;
  peer_feedback_total: number;
  self_eval_complete: boolean;
  manager_eval_complete: boolean;
  calibration_complete: boolean;

  // Deadlines
  peer_selection_deadline: string | null;
  peer_feedback_deadline: string | null;
  self_eval_deadline: string | null;
  manager_eval_deadline: string | null;
  calibration_date: string | null;
  release_date: string | null;

  // Status flags
  is_overdue: boolean;
  overdue_deadline: string | null;
  is_blocked: boolean;
  blocked_reason: string | null;

  // Timestamps
  created_at: string;
  updated_at: string;
  last_activity_at: string;
}

/**
 * Real-time activity event
 */
export interface ActivityEvent {
  id: string;
  evaluation_id: string;
  employee_name: string;
  event_type: EventType;
  description: string;
  actor_name: string | null;
  actor_type: 'user' | 'agent' | 'system';
  timestamp: string;
  metadata?: Record<string, any>;
}

/**
 * Deadline alert
 */
export interface DeadlineAlert {
  id: string;
  evaluation_id: string;
  employee_name: string;
  deadline_type: string;
  due_date: string;
  status: DeadlineStatus;
  days_remaining: number;
  responsible_user_name: string | null;
}

/**
 * Phase distribution stats
 */
export interface PhaseStats {
  phase: EvaluationPhase;
  count: number;
  percentage: number;
  avg_time_in_phase_days: number;
}

/**
 * Department/Manager stats
 */
export interface DepartmentStats {
  department: string;
  total_evaluations: number;
  completed: number;
  in_progress: number;
  overdue: number;
  avg_completion_percentage: number;
  managers: ManagerStats[];
}

export interface ManagerStats {
  manager_id: string;
  manager_name: string;
  total_evaluations: number;
  completed: number;
  in_progress: number;
  overdue: number;
  avg_completion_percentage: number;
}

/**
 * System health metrics
 */
export interface SystemHealth {
  total_evaluations: number;
  active_evaluations: number;
  completed_evaluations: number;
  cancelled_evaluations: number;
  overdue_count: number;
  approaching_deadline_count: number;
  blocked_count: number;
  avg_completion_time_days: number;
  on_track_percentage: number;
}

/**
 * Control room dashboard data (everything)
 */
export interface ControlRoomData {
  health: SystemHealth;
  evaluations: EvaluationOverview[];
  recent_activity: ActivityEvent[];
  deadline_alerts: DeadlineAlert[];
  phase_distribution: PhaseStats[];
  department_stats: DepartmentStats[];
  last_updated: string;
}
