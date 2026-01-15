/**
 * Evaluation Types
 * Core types for the IRAS evaluation system
 */

/**
 * Evaluation Phase
 * Represents the current phase in the IRAS evaluation workflow
 */
export enum EvaluationPhase {
  INTAKE = 'intake',
  RATING = 'rating',
  ANALYSIS = 'analysis',
  SYNTHESIS = 'synthesis',
  COMPLETE = 'complete',
  FAILED = 'failed',
}

/**
 * Evaluation State
 * Represents the current state of an evaluation
 */
export enum EvaluationState {
  PENDING = 'pending',
  IN_PROGRESS = 'in_progress',
  WAITING = 'waiting',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
}

/**
 * Rating Dimension
 * Standard dimensions used for evaluating responses
 */
export enum RatingDimension {
  ACCURACY = 'accuracy',
  RELEVANCE = 'relevance',
  COMPLETENESS = 'completeness',
  CLARITY = 'clarity',
  COHERENCE = 'coherence',
  DEPTH = 'depth',
}

/**
 * Rating
 * Individual rating for a specific dimension
 */
export interface Rating {
  dimension: RatingDimension | string;
  score: number; // 0-10 scale
  confidence: number; // 0-1 scale
  rationale: string;
  evidence?: string[];
  agent_id?: string;
  timestamp?: string;
}

/**
 * Analysis Result
 * Results from the analysis phase
 */
export interface AnalysisResult {
  patterns: Pattern[];
  insights: Insight[];
  correlations: Correlation[];
  anomalies: Anomaly[];
  summary: string;
  confidence: number;
  timestamp: string;
}

/**
 * Pattern
 * Identified pattern in the ratings or data
 */
export interface Pattern {
  type: string;
  description: string;
  occurrences: number;
  significance: number;
  examples?: string[];
}

/**
 * Insight
 * Actionable insight derived from analysis
 */
export interface Insight {
  category: string;
  description: string;
  impact: 'high' | 'medium' | 'low';
  recommendation?: string;
  supporting_evidence?: string[];
}

/**
 * Correlation
 * Relationship between different ratings or dimensions
 */
export interface Correlation {
  dimension1: string;
  dimension2: string;
  coefficient: number; // -1 to 1
  strength: 'strong' | 'moderate' | 'weak';
  description: string;
}

/**
 * Anomaly
 * Unusual or unexpected finding
 */
export interface Anomaly {
  type: string;
  severity: 'critical' | 'warning' | 'info';
  description: string;
  affected_dimensions?: string[];
  recommendation?: string;
}

/**
 * Synthesis Result
 * Final synthesis combining all analysis results
 */
export interface SynthesisResult {
  overall_score: number;
  confidence: number;
  key_findings: string[];
  recommendations: string[];
  strengths: string[];
  weaknesses: string[];
  summary: string;
  timestamp: string;
}

/**
 * Evaluation Metadata
 * Additional metadata about the evaluation
 */
export interface EvaluationMetadata {
  created_at: string;
  updated_at: string;
  created_by: string;
  tags?: string[];
  priority?: 'low' | 'medium' | 'high' | 'critical';
  category?: string;
  source?: string;
  [key: string]: unknown;
}

/**
 * Evaluation
 * Complete evaluation object representing the entire IRAS workflow
 */
export interface Evaluation {
  id: string;
  phase: EvaluationPhase;
  state: EvaluationState;

  // Input data
  prompt: string;
  response: string;
  context?: Record<string, unknown>;

  // Phase results
  ratings: Rating[];
  analysis?: AnalysisResult;
  synthesis?: SynthesisResult;

  // Progress tracking
  progress: number; // 0-100
  current_step?: string;
  steps_completed: string[];
  steps_remaining: string[];

  // Error handling
  error?: {
    message: string;
    code?: string;
    phase?: EvaluationPhase;
    timestamp: string;
  };

  // Metadata
  metadata: EvaluationMetadata;

  // Timing
  started_at?: string;
  completed_at?: string;
  duration_ms?: number;
}

/**
 * Evaluation Summary
 * Condensed version of evaluation for list views
 */
export interface EvaluationSummary {
  id: string;
  phase: EvaluationPhase;
  state: EvaluationState;
  progress: number;
  overall_score?: number;
  created_at: string;
  updated_at: string;
  prompt_preview: string; // First 100 chars
  tags?: string[];
  priority?: string;
}

/**
 * Evaluation Filter
 * Filter criteria for querying evaluations
 */
export interface EvaluationFilter {
  phases?: EvaluationPhase[];
  states?: EvaluationState[];
  tags?: string[];
  priority?: string[];
  created_after?: string;
  created_before?: string;
  search?: string;
}

/**
 * Evaluation Sort
 * Sort options for evaluation lists
 */
export interface EvaluationSort {
  field: 'created_at' | 'updated_at' | 'progress' | 'priority' | 'overall_score';
  order: 'asc' | 'desc';
}
