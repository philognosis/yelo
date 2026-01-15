/**
 * useEvaluations Hook
 * Hook for fetching and managing list of evaluations with React Query
 */

import { useQuery, useMutation, useQueryClient, UseQueryResult } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { EvaluationSummary, EvaluationFilter, EvaluationSort } from '@/types/evaluation';
import {
  CreateEvaluationRequest,
  PaginatedResponse,
  ListEvaluationsRequest,
} from '@/types/api';
import { evaluationKeys } from './useEvaluation';
import { useWebSocket } from './useWebSocket';
import { WebSocketMessageType } from '@/types/api';
import { useState } from 'react';

/**
 * Hook Options
 */
interface UseEvaluationsOptions {
  // Initial pagination
  initialPage?: number;
  initialPageSize?: number;

  // Initial filters
  initialFilter?: EvaluationFilter;
  initialSort?: EvaluationSort;

  // Enable/disable the query
  enabled?: boolean;

  // Enable real-time updates
  realtime?: boolean;
}

/**
 * Hook for fetching list of evaluations
 */
export function useEvaluations(options: UseEvaluationsOptions = {}) {
  const queryClient = useQueryClient();
  const {
    initialPage = 1,
    initialPageSize = 20,
    initialFilter,
    initialSort = { field: 'created_at', order: 'desc' },
    enabled = true,
    realtime = true,
  } = options;

  // Pagination state
  const [page, setPage] = useState(initialPage);
  const [pageSize, setPageSize] = useState(initialPageSize);

  // Filter and sort state
  const [filter, setFilter] = useState<EvaluationFilter | undefined>(initialFilter);
  const [sort, setSort] = useState<EvaluationSort>(initialSort);

  // Build query params
  const queryParams: ListEvaluationsRequest = {
    page,
    page_size: pageSize,
    sort,
    filter,
  };

  // Fetch evaluations query
  const query = useQuery({
    queryKey: evaluationKeys.list(queryParams),
    queryFn: async () => {
      const response = await apiClient.getEvaluations(queryParams);

      if (!response.success || !response.data) {
        throw new Error(response.error?.message || 'Failed to fetch evaluations');
      }

      return response.data;
    },
    enabled,
    staleTime: 30000, // 30 seconds
    placeholderData: (previousData) => previousData, // Keep previous data while loading
  }) as UseQueryResult<PaginatedResponse<EvaluationSummary>, Error>;

  // Subscribe to real-time updates
  const { isConnected } = useWebSocket({
    enabled: realtime,
    handlers: {
      // New evaluation created
      [WebSocketMessageType.EVALUATION_CREATED]: () => {
        queryClient.invalidateQueries({ queryKey: evaluationKeys.lists() });
      },

      // Evaluation updated
      [WebSocketMessageType.EVALUATION_UPDATED]: () => {
        queryClient.invalidateQueries({ queryKey: evaluationKeys.lists() });
      },

      // Evaluation deleted
      [WebSocketMessageType.EVALUATION_DELETED]: () => {
        queryClient.invalidateQueries({ queryKey: evaluationKeys.lists() });
      },

      // Evaluation completed
      [WebSocketMessageType.EVALUATION_COMPLETED]: () => {
        queryClient.invalidateQueries({ queryKey: evaluationKeys.lists() });
      },

      // Evaluation failed
      [WebSocketMessageType.EVALUATION_FAILED]: () => {
        queryClient.invalidateQueries({ queryKey: evaluationKeys.lists() });
      },
    },
  });

  // Create evaluation mutation
  const createMutation = useMutation({
    mutationFn: async (data: CreateEvaluationRequest) => {
      const response = await apiClient.createEvaluation(data);

      if (!response.success || !response.data) {
        throw new Error(response.error?.message || 'Failed to create evaluation');
      }

      return response.data;
    },
    onSuccess: () => {
      // Invalidate list queries to refetch
      queryClient.invalidateQueries({ queryKey: evaluationKeys.lists() });
    },
  });

  // Pagination helpers
  const goToPage = (newPage: number) => {
    if (newPage >= 1 && (!query.data || newPage <= query.data.total_pages)) {
      setPage(newPage);
    }
  };

  const nextPage = () => {
    if (query.data?.has_next) {
      setPage((prev) => prev + 1);
    }
  };

  const previousPage = () => {
    if (query.data?.has_prev) {
      setPage((prev) => prev - 1);
    }
  };

  const changePageSize = (newSize: number) => {
    setPageSize(newSize);
    setPage(1); // Reset to first page
  };

  // Filter helpers
  const updateFilter = (newFilter: Partial<EvaluationFilter>) => {
    setFilter((prev) => ({ ...prev, ...newFilter }));
    setPage(1); // Reset to first page when filter changes
  };

  const clearFilter = () => {
    setFilter(undefined);
    setPage(1);
  };

  // Sort helpers
  const updateSort = (newSort: EvaluationSort) => {
    setSort(newSort);
    setPage(1); // Reset to first page when sort changes
  };

  return {
    // Query data
    evaluations: query.data?.items || [],
    pagination: query.data
      ? {
          page: query.data.page,
          pageSize: query.data.page_size,
          total: query.data.total,
          totalPages: query.data.total_pages,
          hasNext: query.data.has_next,
          hasPrev: query.data.has_prev,
        }
      : null,

    // Query state
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    isSuccess: query.isSuccess,
    isFetching: query.isFetching,

    // Real-time status
    isRealtime: isConnected,

    // Current state
    currentPage: page,
    currentPageSize: pageSize,
    currentFilter: filter,
    currentSort: sort,

    // Pagination actions
    goToPage,
    nextPage,
    previousPage,
    changePageSize,

    // Filter actions
    updateFilter,
    clearFilter,

    // Sort actions
    updateSort,

    // Create mutation
    create: createMutation.mutate,
    createAsync: createMutation.mutateAsync,
    isCreating: createMutation.isPending,
    createError: createMutation.error,

    // Refetch
    refetch: query.refetch,
  };
}
