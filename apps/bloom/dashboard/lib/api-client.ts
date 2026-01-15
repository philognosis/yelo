/**
 * API Client
 * Axios-based API client with authentication and error handling
 */

import axios, { AxiosInstance, AxiosError, AxiosRequestConfig, AxiosResponse } from 'axios';
import {
  ApiResponse,
  ApiError,
  CreateEvaluationRequest,
  UpdateEvaluationRequest,
  ListEvaluationsRequest,
  EvaluationResponse,
  EvaluationsListResponse,
  HealthCheckResponse,
  ExportRequest,
  ExportResponse,
} from '@/types/api';
import { Evaluation } from '@/types/evaluation';
import { getAuthToken, clearAuth } from './auth';

/**
 * API Client Class
 * Handles all API communication with authentication
 */
class ApiClient {
  private client: AxiosInstance;
  private baseURL: string;

  constructor() {
    this.baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    // Create axios instance with default config
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 30000, // 30 seconds
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor - Add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = getAuthToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor - Handle errors
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        // Handle 401 - Unauthorized
        if (error.response?.status === 401) {
          clearAuth();
          if (typeof window !== 'undefined') {
            window.location.href = '/login';
          }
        }

        // Transform error to ApiError format
        const apiError: ApiError = {
          code: error.code || 'UNKNOWN_ERROR',
          message: error.message || 'An unexpected error occurred',
          timestamp: new Date().toISOString(),
        };

        if (error.response?.data) {
          const data = error.response.data as Partial<ApiError>;
          apiError.code = data.code || apiError.code;
          apiError.message = data.message || apiError.message;
          apiError.details = data.details;
          apiError.field = data.field;
        }

        return Promise.reject(apiError);
      }
    );
  }

  /**
   * Generic request method
   */
  private async request<T>(config: AxiosRequestConfig): Promise<ApiResponse<T>> {
    try {
      const response: AxiosResponse<ApiResponse<T>> = await this.client.request(config);
      return response.data;
    } catch (error) {
      const apiError = error as ApiError;
      return {
        success: false,
        error: apiError,
      };
    }
  }

  // ==================== Health Check ====================

  /**
   * Check API health status
   */
  async healthCheck(): Promise<HealthCheckResponse> {
    const response = await this.request<HealthCheckResponse>({
      method: 'GET',
      url: '/health',
    });
    return response.data!;
  }

  // ==================== Evaluations ====================

  /**
   * Get all evaluations with optional filters
   */
  async getEvaluations(params?: ListEvaluationsRequest): Promise<EvaluationsListResponse> {
    return this.request<EvaluationsListResponse['data']>({
      method: 'GET',
      url: '/api/evaluations',
      params,
    });
  }

  /**
   * Get a single evaluation by ID
   */
  async getEvaluation(id: string): Promise<EvaluationResponse> {
    return this.request<Evaluation>({
      method: 'GET',
      url: `/api/evaluations/${id}`,
    });
  }

  /**
   * Create a new evaluation
   */
  async createEvaluation(data: CreateEvaluationRequest): Promise<EvaluationResponse> {
    return this.request<Evaluation>({
      method: 'POST',
      url: '/api/evaluations',
      data,
    });
  }

  /**
   * Update an existing evaluation
   */
  async updateEvaluation(
    id: string,
    data: UpdateEvaluationRequest
  ): Promise<EvaluationResponse> {
    return this.request<Evaluation>({
      method: 'PATCH',
      url: `/api/evaluations/${id}`,
      data,
    });
  }

  /**
   * Delete an evaluation
   */
  async deleteEvaluation(id: string): Promise<ApiResponse<void>> {
    return this.request<void>({
      method: 'DELETE',
      url: `/api/evaluations/${id}`,
    });
  }

  /**
   * Cancel a running evaluation
   */
  async cancelEvaluation(id: string): Promise<EvaluationResponse> {
    return this.request<Evaluation>({
      method: 'POST',
      url: `/api/evaluations/${id}/cancel`,
    });
  }

  /**
   * Retry a failed evaluation
   */
  async retryEvaluation(id: string): Promise<EvaluationResponse> {
    return this.request<Evaluation>({
      method: 'POST',
      url: `/api/evaluations/${id}/retry`,
    });
  }

  /**
   * Export evaluations
   */
  async exportEvaluations(params: ExportRequest): Promise<ExportResponse> {
    const response = await this.request<ExportResponse>({
      method: 'POST',
      url: '/api/evaluations/export',
      data: params,
    });
    return response.data!;
  }

  // ==================== Dashboard & Metrics ====================

  /**
   * Get dashboard metrics
   */
  async getDashboardMetrics(filter?: Record<string, unknown>): Promise<ApiResponse> {
    return this.request({
      method: 'GET',
      url: '/api/dashboard/metrics',
      params: filter,
    });
  }

  /**
   * Get system health
   */
  async getSystemHealth(): Promise<ApiResponse> {
    return this.request({
      method: 'GET',
      url: '/api/system/health',
    });
  }

  /**
   * Get agent statistics
   */
  async getAgentStats(): Promise<ApiResponse> {
    return this.request({
      method: 'GET',
      url: '/api/agents/stats',
    });
  }

  // ==================== User Management ====================

  /**
   * Get current user profile
   */
  async getCurrentUser(): Promise<ApiResponse> {
    return this.request({
      method: 'GET',
      url: '/api/users/me',
    });
  }

  /**
   * Update current user profile
   */
  async updateCurrentUser(data: Record<string, unknown>): Promise<ApiResponse> {
    return this.request({
      method: 'PATCH',
      url: '/api/users/me',
      data,
    });
  }

  /**
   * Update user preferences
   */
  async updateUserPreferences(data: Record<string, unknown>): Promise<ApiResponse> {
    return this.request({
      method: 'PATCH',
      url: '/api/users/me/preferences',
      data,
    });
  }

  // ==================== Authentication ====================

  /**
   * Login
   */
  async login(email: string, password: string): Promise<ApiResponse> {
    return this.request({
      method: 'POST',
      url: '/api/auth/login',
      data: { email, password },
    });
  }

  /**
   * Logout
   */
  async logout(): Promise<ApiResponse> {
    return this.request({
      method: 'POST',
      url: '/api/auth/logout',
    });
  }

  /**
   * Refresh token
   */
  async refreshToken(refreshToken: string): Promise<ApiResponse> {
    return this.request({
      method: 'POST',
      url: '/api/auth/refresh',
      data: { refresh_token: refreshToken },
    });
  }

  /**
   * Request password reset
   */
  async requestPasswordReset(email: string): Promise<ApiResponse> {
    return this.request({
      method: 'POST',
      url: '/api/auth/password-reset/request',
      data: { email },
    });
  }

  /**
   * Confirm password reset
   */
  async confirmPasswordReset(token: string, newPassword: string): Promise<ApiResponse> {
    return this.request({
      method: 'POST',
      url: '/api/auth/password-reset/confirm',
      data: { token, new_password: newPassword },
    });
  }
}

// Export singleton instance
export const apiClient = new ApiClient();

// Export class for testing
export default ApiClient;
