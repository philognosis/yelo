/**
 * useDashboardMetrics Hook
 * Hook for fetching dashboard metrics and statistics
 */

import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { DashboardMetrics, DashboardFilter, SystemHealth, AgentStats } from '@/types/dashboard';
import { useWebSocket } from './useWebSocket';
import { WebSocketMessageType } from '@/types/api';
import { useQueryClient } from '@tanstack/react-query';

/**
 * Query key factory for dashboard
 */
export const dashboardKeys = {
  all: ['dashboard'] as const,
  metrics: (filter?: DashboardFilter) => [...dashboardKeys.all, 'metrics', filter] as const,
  health: () => [...dashboardKeys.all, 'health'] as const,
  agents: () => [...dashboardKeys.all, 'agents'] as const,
};

/**
 * Hook Options
 */
interface UseDashboardMetricsOptions {
  // Filter for metrics
  filter?: DashboardFilter;

  // Enable/disable the query
  enabled?: boolean;

  // Refetch interval in milliseconds
  refetchInterval?: number;

  // Enable real-time updates
  realtime?: boolean;
}

/**
 * Hook for fetching dashboard metrics
 */
export function useDashboardMetrics(options: UseDashboardMetricsOptions = {}) {
  const queryClient = useQueryClient();
  const {
    filter,
    enabled = true,
    refetchInterval = 60000, // 1 minute default
    realtime = true,
  } = options;

  // Fetch dashboard metrics
  const query = useQuery({
    queryKey: dashboardKeys.metrics(filter),
    queryFn: async () => {
      const response = await apiClient.getDashboardMetrics(filter);

      if (!response.success || !response.data) {
        throw new Error(response.error?.message || 'Failed to fetch dashboard metrics');
      }

      return response.data as DashboardMetrics;
    },
    enabled,
    refetchInterval,
    staleTime: 30000, // 30 seconds
  }) as UseQueryResult<DashboardMetrics, Error>;

  // Subscribe to real-time updates
  const { isConnected } = useWebSocket({
    enabled: realtime,
    handlers: {
      // Evaluation events - invalidate metrics
      [WebSocketMessageType.EVALUATION_CREATED]: () => {
        queryClient.invalidateQueries({ queryKey: dashboardKeys.metrics() });
      },
      [WebSocketMessageType.EVALUATION_COMPLETED]: () => {
        queryClient.invalidateQueries({ queryKey: dashboardKeys.metrics() });
      },
      [WebSocketMessageType.EVALUATION_FAILED]: () => {
        queryClient.invalidateQueries({ queryKey: dashboardKeys.metrics() });
      },
    },
  });

  return {
    // Query data
    metrics: query.data,

    // Query state
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    isSuccess: query.isSuccess,
    isFetching: query.isFetching,

    // Real-time status
    isRealtime: isConnected,

    // Refetch
    refetch: query.refetch,
  };
}

/**
 * Hook for fetching system health
 */
export function useSystemHealth(options: { enabled?: boolean; refetchInterval?: number } = {}) {
  const queryClient = useQueryClient();
  const { enabled = true, refetchInterval = 30000 } = options;

  const query = useQuery({
    queryKey: dashboardKeys.health(),
    queryFn: async () => {
      const response = await apiClient.getSystemHealth();

      if (!response.success || !response.data) {
        throw new Error(response.error?.message || 'Failed to fetch system health');
      }

      return response.data as SystemHealth;
    },
    enabled,
    refetchInterval,
    staleTime: 15000, // 15 seconds
  }) as UseQueryResult<SystemHealth, Error>;

  // Subscribe to system status updates
  const { isConnected } = useWebSocket({
    enabled,
    handlers: {
      [WebSocketMessageType.SYSTEM_STATUS]: () => {
        queryClient.invalidateQueries({ queryKey: dashboardKeys.health() });
      },
    },
  });

  return {
    health: query.data,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    isRealtime: isConnected,
    refetch: query.refetch,
  };
}

/**
 * Hook for fetching agent statistics
 */
export function useAgentStats(options: { enabled?: boolean; refetchInterval?: number } = {}) {
  const queryClient = useQueryClient();
  const { enabled = true, refetchInterval = 30000 } = options;

  const query = useQuery({
    queryKey: dashboardKeys.agents(),
    queryFn: async () => {
      const response = await apiClient.getAgentStats();

      if (!response.success || !response.data) {
        throw new Error(response.error?.message || 'Failed to fetch agent stats');
      }

      return response.data as AgentStats[];
    },
    enabled,
    refetchInterval,
    staleTime: 15000, // 15 seconds
  }) as UseQueryResult<AgentStats[], Error>;

  // Subscribe to agent status updates
  const { isConnected } = useWebSocket({
    enabled,
    handlers: {
      [WebSocketMessageType.AGENT_STATUS]: () => {
        queryClient.invalidateQueries({ queryKey: dashboardKeys.agents() });
      },
    },
  });

  return {
    agents: query.data || [],
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    isRealtime: isConnected,
    refetch: query.refetch,
  };
}
