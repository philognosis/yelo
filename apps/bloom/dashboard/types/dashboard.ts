/**
 * Dashboard Types
 * Types for dashboard metrics, statistics, and visualizations
 */

import { EvaluationPhase, EvaluationState } from './evaluation';

/**
 * Dashboard Metrics
 * Overview metrics for the dashboard
 */
export interface DashboardMetrics {
  // Evaluation metrics
  total_evaluations: number;
  active_evaluations: number;
  completed_evaluations: number;
  failed_evaluations: number;

  // Performance metrics
  average_completion_time_ms: number;
  average_rating_score: number;
  success_rate: number;

  // Activity metrics
  evaluations_today: number;
  evaluations_this_week: number;
  evaluations_this_month: number;

  // Trend data
  trend: TrendData;

  // Last updated
  updated_at: string;
}

/**
 * Trend Data
 * Historical trend information
 */
export interface TrendData {
  evaluations: TimeSeriesData[];
  average_score: TimeSeriesData[];
  completion_time: TimeSeriesData[];
  success_rate: TimeSeriesData[];
}

/**
 * Time Series Data Point
 * Single point in a time series
 */
export interface TimeSeriesData {
  timestamp: string;
  value: number;
  label?: string;
}

/**
 * Phase Distribution
 * Distribution of evaluations across phases
 */
export interface PhaseDistribution {
  phase: EvaluationPhase;
  count: number;
  percentage: number;
}

/**
 * State Distribution
 * Distribution of evaluations across states
 */
export interface StateDistribution {
  state: EvaluationState;
  count: number;
  percentage: number;
}

/**
 * Rating Distribution
 * Distribution of ratings by dimension
 */
export interface RatingDistribution {
  dimension: string;
  average_score: number;
  min_score: number;
  max_score: number;
  std_deviation: number;
  sample_size: number;
}

/**
 * Performance Stats
 * Detailed performance statistics
 */
export interface PerformanceStats {
  total_processing_time_ms: number;
  average_processing_time_ms: number;
  median_processing_time_ms: number;
  p95_processing_time_ms: number;
  p99_processing_time_ms: number;
  fastest_evaluation_ms: number;
  slowest_evaluation_ms: number;
}

/**
 * Quality Metrics
 * Evaluation quality metrics
 */
export interface QualityMetrics {
  average_confidence: number;
  rating_consistency: number;
  analysis_depth_score: number;
  insight_count_average: number;
  anomaly_detection_rate: number;
}

/**
 * Agent Stats
 * Statistics for individual agents
 */
export interface AgentStats {
  agent_id: string;
  agent_name: string;
  agent_type: 'intake' | 'rating' | 'analysis' | 'synthesis';

  // Activity
  total_tasks: number;
  completed_tasks: number;
  failed_tasks: number;

  // Performance
  average_execution_time_ms: number;
  success_rate: number;

  // Status
  status: 'active' | 'idle' | 'busy' | 'offline';
  current_task?: string;
  last_activity_at?: string;
}

/**
 * System Health
 * Overall system health status
 */
export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  uptime_seconds: number;

  // Components
  api_status: 'up' | 'down';
  database_status: 'up' | 'down';
  redis_status: 'up' | 'down';
  websocket_status: 'up' | 'down';

  // Agents
  active_agents: number;
  total_agents: number;

  // Resources
  cpu_usage_percent: number;
  memory_usage_percent: number;
  disk_usage_percent: number;

  // Errors
  error_rate: number;
  last_error_at?: string;

  // Timestamp
  checked_at: string;
}

/**
 * Activity Timeline
 * Timeline of recent activity
 */
export interface ActivityTimeline {
  events: ActivityEvent[];
  total: number;
  page: number;
  page_size: number;
}

/**
 * Activity Event
 * Single activity event
 */
export interface ActivityEvent {
  id: string;
  type: 'evaluation_created' | 'evaluation_completed' | 'evaluation_failed' | 'rating_added' | 'analysis_completed' | 'user_login' | 'system_event';
  title: string;
  description?: string;
  user?: {
    id: string;
    name: string;
    avatar_url?: string;
  };
  resource?: {
    type: string;
    id: string;
    name?: string;
  };
  metadata?: Record<string, unknown>;
  timestamp: string;
}

/**
 * Top Performers
 * Top performing evaluations or users
 */
export interface TopPerformers {
  evaluations: TopEvaluation[];
  users: TopUser[];
  dimensions: TopDimension[];
}

/**
 * Top Evaluation
 * High-scoring evaluation
 */
export interface TopEvaluation {
  id: string;
  prompt_preview: string;
  overall_score: number;
  created_at: string;
  tags?: string[];
}

/**
 * Top User
 * Most active or high-performing user
 */
export interface TopUser {
  id: string;
  name: string;
  avatar_url?: string;
  evaluations_count: number;
  average_score: number;
}

/**
 * Top Dimension
 * Best performing rating dimension
 */
export interface TopDimension {
  dimension: string;
  average_score: number;
  improvement_rate: number;
  sample_size: number;
}

/**
 * Dashboard Filter
 * Filter options for dashboard data
 */
export interface DashboardFilter {
  date_range: {
    start: string;
    end: string;
  };
  phases?: EvaluationPhase[];
  states?: EvaluationState[];
  tags?: string[];
  users?: string[];
}

/**
 * Chart Data
 * Generic chart data structure
 */
export interface ChartData {
  labels: string[];
  datasets: ChartDataset[];
}

/**
 * Chart Dataset
 * Single dataset for charts
 */
export interface ChartDataset {
  label: string;
  data: number[];
  backgroundColor?: string | string[];
  borderColor?: string | string[];
  borderWidth?: number;
}

/**
 * Widget Config
 * Configuration for dashboard widgets
 */
export interface WidgetConfig {
  id: string;
  type: 'metric' | 'chart' | 'list' | 'activity' | 'status';
  title: string;
  size: 'small' | 'medium' | 'large' | 'full';
  position: {
    row: number;
    col: number;
  };
  refresh_interval?: number; // seconds
  config?: Record<string, unknown>;
}

/**
 * Dashboard Layout
 * User's custom dashboard layout
 */
export interface DashboardLayout {
  user_id: string;
  widgets: WidgetConfig[];
  updated_at: string;
}

/**
 * Notification
 * Dashboard notification
 */
export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  action?: {
    label: string;
    url: string;
  };
  is_read: boolean;
  created_at: string;
}

/**
 * Alert
 * System alert or warning
 */
export interface Alert {
  id: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  category: string;
  title: string;
  description: string;
  affected_resources?: string[];
  resolution?: string;
  status: 'active' | 'acknowledged' | 'resolved';
  created_at: string;
  resolved_at?: string;
}
