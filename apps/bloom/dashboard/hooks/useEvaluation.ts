/**
 * useEvaluation Hook
 * Hook for fetching and managing a single evaluation with React Query
 */

import { useQuery, useMutation, useQueryClient, UseQueryResult } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { Evaluation } from '@/types/evaluation';
import { EvaluationResponse, UpdateEvaluationRequest } from '@/types/api';
import { useWebSocket } from './useWebSocket';
import { WebSocketMessageType } from '@/types/api';
import { useEffect } from 'react';

/**
 * Query key factory for evaluations
 */
export const evaluationKeys = {
  all: ['evaluations'] as const,
  lists: () => [...evaluationKeys.all, 'list'] as const,
  list: (filters: unknown) => [...evaluationKeys.lists(), filters] as const,
  details: () => [...evaluationKeys.all, 'detail'] as const,
  detail: (id: string) => [...evaluationKeys.details(), id] as const,
};

/**
 * Hook Options
 */
interface UseEvaluationOptions {
  // Enable/disable the query
  enabled?: boolean;
  // Refetch interval in milliseconds
  refetchInterval?: number | false;
  // Enable real-time updates via WebSocket
  realtime?: boolean;
}

/**
 * Hook for fetching a single evaluation
 */
export function useEvaluation(
  evaluationId: string | null,
  options: UseEvaluationOptions = {}
) {
  const queryClient = useQueryClient();
  const {
    enabled = true,
    refetchInterval = false,
    realtime = true,
  } = options;

  // Fetch evaluation query
  const query = useQuery({
    queryKey: evaluationKeys.detail(evaluationId || ''),
    queryFn: async () => {
      if (!evaluationId) {
        throw new Error('Evaluation ID is required');
      }

      const response = await apiClient.getEvaluation(evaluationId);

      if (!response.success || !response.data) {
        throw new Error(response.error?.message || 'Failed to fetch evaluation');
      }

      return response.data;
    },
    enabled: enabled && !!evaluationId,
    refetchInterval,
    staleTime: 30000, // 30 seconds
  }) as UseQueryResult<Evaluation, Error>;

  // Subscribe to real-time updates
  const { isConnected } = useWebSocket({
    enabled: realtime && !!evaluationId,
    handlers: {
      // Evaluation updated
      [WebSocketMessageType.EVALUATION_UPDATED]: (payload: { evaluation_id: string; evaluation?: Evaluation }) => {
        if (payload.evaluation_id === evaluationId) {
          queryClient.invalidateQueries({ queryKey: evaluationKeys.detail(evaluationId) });
        }
      },

      // Phase changed
      [WebSocketMessageType.EVALUATION_PHASE_CHANGED]: (payload: { evaluation_id: string }) => {
        if (payload.evaluation_id === evaluationId) {
          queryClient.invalidateQueries({ queryKey: evaluationKeys.detail(evaluationId) });
        }
      },

      // State changed
      [WebSocketMessageType.EVALUATION_STATE_CHANGED]: (payload: { evaluation_id: string }) => {
        if (payload.evaluation_id === evaluationId) {
          queryClient.invalidateQueries({ queryKey: evaluationKeys.detail(evaluationId) });
        }
      },

      // Progress update
      [WebSocketMessageType.EVALUATION_PROGRESS]: (payload: { evaluation_id: string; progress: number }) => {
        if (payload.evaluation_id === evaluationId) {
          // Optimistically update progress
          queryClient.setQueryData<Evaluation>(
            evaluationKeys.detail(evaluationId),
            (old) => old ? { ...old, progress: payload.progress } : old
          );
        }
      },

      // Completed
      [WebSocketMessageType.EVALUATION_COMPLETED]: (payload: { evaluation_id: string }) => {
        if (payload.evaluation_id === evaluationId) {
          queryClient.invalidateQueries({ queryKey: evaluationKeys.detail(evaluationId) });
        }
      },

      // Failed
      [WebSocketMessageType.EVALUATION_FAILED]: (payload: { evaluation_id: string }) => {
        if (payload.evaluation_id === evaluationId) {
          queryClient.invalidateQueries({ queryKey: evaluationKeys.detail(evaluationId) });
        }
      },
    },
  });

  // Update evaluation mutation
  const updateMutation = useMutation({
    mutationFn: async (data: UpdateEvaluationRequest) => {
      if (!evaluationId) {
        throw new Error('Evaluation ID is required');
      }

      const response = await apiClient.updateEvaluation(evaluationId, data);

      if (!response.success || !response.data) {
        throw new Error(response.error?.message || 'Failed to update evaluation');
      }

      return response.data;
    },
    onSuccess: (data) => {
      // Update cache
      queryClient.setQueryData<Evaluation>(
        evaluationKeys.detail(evaluationId!),
        data
      );
      // Invalidate list queries
      queryClient.invalidateQueries({ queryKey: evaluationKeys.lists() });
    },
  });

  // Cancel evaluation mutation
  const cancelMutation = useMutation({
    mutationFn: async () => {
      if (!evaluationId) {
        throw new Error('Evaluation ID is required');
      }

      const response = await apiClient.cancelEvaluation(evaluationId);

      if (!response.success || !response.data) {
        throw new Error(response.error?.message || 'Failed to cancel evaluation');
      }

      return response.data;
    },
    onSuccess: (data) => {
      queryClient.setQueryData<Evaluation>(
        evaluationKeys.detail(evaluationId!),
        data
      );
      queryClient.invalidateQueries({ queryKey: evaluationKeys.lists() });
    },
  });

  // Retry evaluation mutation
  const retryMutation = useMutation({
    mutationFn: async () => {
      if (!evaluationId) {
        throw new Error('Evaluation ID is required');
      }

      const response = await apiClient.retryEvaluation(evaluationId);

      if (!response.success || !response.data) {
        throw new Error(response.error?.message || 'Failed to retry evaluation');
      }

      return response.data;
    },
    onSuccess: (data) => {
      queryClient.setQueryData<Evaluation>(
        evaluationKeys.detail(evaluationId!),
        data
      );
      queryClient.invalidateQueries({ queryKey: evaluationKeys.lists() });
    },
  });

  // Delete evaluation mutation
  const deleteMutation = useMutation({
    mutationFn: async () => {
      if (!evaluationId) {
        throw new Error('Evaluation ID is required');
      }

      const response = await apiClient.deleteEvaluation(evaluationId);

      if (!response.success) {
        throw new Error(response.error?.message || 'Failed to delete evaluation');
      }

      return true;
    },
    onSuccess: () => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: evaluationKeys.detail(evaluationId!) });
      // Invalidate list queries
      queryClient.invalidateQueries({ queryKey: evaluationKeys.lists() });
    },
  });

  return {
    // Query data
    evaluation: query.data,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    isSuccess: query.isSuccess,

    // Real-time status
    isRealtime: isConnected,

    // Mutations
    update: updateMutation.mutate,
    updateAsync: updateMutation.mutateAsync,
    isUpdating: updateMutation.isPending,
    updateError: updateMutation.error,

    cancel: cancelMutation.mutate,
    cancelAsync: cancelMutation.mutateAsync,
    isCancelling: cancelMutation.isPending,
    cancelError: cancelMutation.error,

    retry: retryMutation.mutate,
    retryAsync: retryMutation.mutateAsync,
    isRetrying: retryMutation.isPending,
    retryError: retryMutation.error,

    delete: deleteMutation.mutate,
    deleteAsync: deleteMutation.mutateAsync,
    isDeleting: deleteMutation.isPending,
    deleteError: deleteMutation.error,

    // Refetch
    refetch: query.refetch,
  };
}
