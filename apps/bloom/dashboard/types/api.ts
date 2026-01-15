/**
 * API Types
 * Request and response types for API communication
 */

import { Evaluation, EvaluationFilter, EvaluationSort, EvaluationSummary } from './evaluation';
import { User, UserSummary } from './user';

/**
 * API Response Wrapper
 * Standard wrapper for all API responses
 */
export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: ApiError;
  metadata?: ResponseMetadata;
}

/**
 * API Error
 * Standard error structure
 */
export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
  field?: string;
  timestamp: string;
}

/**
 * Response Metadata
 * Additional metadata for responses
 */
export interface ResponseMetadata {
  request_id?: string;
  timestamp: string;
  duration_ms?: number;
  version?: string;
}

/**
 * Pagination Parameters
 * Standard pagination query parameters
 */
export interface PaginationParams {
  page: number;
  page_size: number;
  sort?: EvaluationSort;
}

/**
 * Paginated Response
 * Response with pagination metadata
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

/**
 * Create Evaluation Request
 * Request body for creating a new evaluation
 */
export interface CreateEvaluationRequest {
  prompt: string;
  response: string;
  context?: Record<string, unknown>;
  tags?: string[];
  priority?: 'low' | 'medium' | 'high' | 'critical';
  category?: string;
}

/**
 * Update Evaluation Request
 * Request body for updating an evaluation
 */
export interface UpdateEvaluationRequest {
  tags?: string[];
  priority?: string;
  category?: string;
  metadata?: Record<string, unknown>;
}

/**
 * List Evaluations Request
 * Query parameters for listing evaluations
 */
export interface ListEvaluationsRequest extends PaginationParams {
  filter?: EvaluationFilter;
}

/**
 * Evaluation Response
 * Response containing a single evaluation
 */
export type EvaluationResponse = ApiResponse<Evaluation>;

/**
 * Evaluations List Response
 * Response containing multiple evaluations
 */
export type EvaluationsListResponse = ApiResponse<PaginatedResponse<EvaluationSummary>>;

/**
 * User Response
 * Response containing a single user
 */
export type UserResponse = ApiResponse<User>;

/**
 * Users List Response
 * Response containing multiple users
 */
export type UsersListResponse = ApiResponse<PaginatedResponse<UserSummary>>;

/**
 * WebSocket Message
 * Standard structure for WebSocket messages
 */
export interface WebSocketMessage<T = unknown> {
  type: WebSocketMessageType;
  payload: T;
  timestamp: string;
  id?: string;
}

/**
 * WebSocket Message Type
 * Types of messages sent over WebSocket
 */
export enum WebSocketMessageType {
  // Connection
  CONNECTED = 'connected',
  DISCONNECTED = 'disconnected',
  ERROR = 'error',

  // Evaluation events
  EVALUATION_CREATED = 'evaluation_created',
  EVALUATION_UPDATED = 'evaluation_updated',
  EVALUATION_DELETED = 'evaluation_deleted',
  EVALUATION_PHASE_CHANGED = 'evaluation_phase_changed',
  EVALUATION_STATE_CHANGED = 'evaluation_state_changed',
  EVALUATION_PROGRESS = 'evaluation_progress',
  EVALUATION_COMPLETED = 'evaluation_completed',
  EVALUATION_FAILED = 'evaluation_failed',

  // Rating events
  RATING_ADDED = 'rating_added',
  RATING_UPDATED = 'rating_updated',

  // Analysis events
  ANALYSIS_STARTED = 'analysis_started',
  ANALYSIS_COMPLETED = 'analysis_completed',

  // Synthesis events
  SYNTHESIS_STARTED = 'synthesis_started',
  SYNTHESIS_COMPLETED = 'synthesis_completed',

  // System events
  SYSTEM_STATUS = 'system_status',
  AGENT_STATUS = 'agent_status',
}

/**
 * Evaluation Event Payload
 * Payload for evaluation-related WebSocket events
 */
export interface EvaluationEventPayload {
  evaluation_id: string;
  evaluation?: Evaluation;
  changes?: Partial<Evaluation>;
}

/**
 * Progress Event Payload
 * Payload for progress updates
 */
export interface ProgressEventPayload {
  evaluation_id: string;
  progress: number;
  current_step: string;
  message?: string;
}

/**
 * Error Event Payload
 * Payload for error events
 */
export interface ErrorEventPayload {
  code: string;
  message: string;
  details?: Record<string, unknown>;
  evaluation_id?: string;
}

/**
 * HTTP Method
 * Supported HTTP methods
 */
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

/**
 * Request Config
 * Configuration for API requests
 */
export interface RequestConfig {
  method: HttpMethod;
  url: string;
  data?: unknown;
  params?: Record<string, unknown>;
  headers?: Record<string, string>;
  timeout?: number;
  retries?: number;
}

/**
 * Health Check Response
 * System health status
 */
export interface HealthCheckResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  version: string;
  timestamp: string;
  components: {
    database: ComponentHealth;
    redis: ComponentHealth;
    agents: ComponentHealth;
  };
}

/**
 * Component Health
 * Health status of individual components
 */
export interface ComponentHealth {
  status: 'up' | 'down' | 'degraded';
  message?: string;
  latency_ms?: number;
}

/**
 * Batch Operation Request
 * Request for batch operations
 */
export interface BatchOperationRequest<T> {
  operations: Array<{
    action: 'create' | 'update' | 'delete';
    data: T;
    id?: string;
  }>;
}

/**
 * Batch Operation Response
 * Response for batch operations
 */
export interface BatchOperationResponse<T> {
  results: Array<{
    success: boolean;
    data?: T;
    error?: ApiError;
  }>;
  total: number;
  successful: number;
  failed: number;
}

/**
 * Export Request
 * Request for exporting data
 */
export interface ExportRequest {
  format: 'json' | 'csv' | 'xlsx' | 'pdf';
  filter?: EvaluationFilter;
  fields?: string[];
  include_metadata?: boolean;
}

/**
 * Export Response
 * Response for export requests
 */
export interface ExportResponse {
  url: string;
  filename: string;
  format: string;
  size_bytes: number;
  expires_at: string;
}
