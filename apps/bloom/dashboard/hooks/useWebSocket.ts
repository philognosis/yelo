/**
 * useWebSocket Hook
 * React hook for WebSocket connections with automatic reconnection
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { wsClient, ConnectionStatus } from '@/lib/websocket';
import { WebSocketMessageType } from '@/types/api';

/**
 * Event Handler Type
 */
type EventHandler<T = unknown> = (payload: T) => void;

/**
 * Hook Options
 */
interface UseWebSocketOptions {
  // Enable/disable WebSocket connection
  enabled?: boolean;

  // Event handlers
  handlers?: Partial<Record<WebSocketMessageType, EventHandler>>;

  // Auto-connect on mount
  autoConnect?: boolean;

  // Auto-disconnect on unmount
  autoDisconnect?: boolean;
}

/**
 * Hook for WebSocket connections
 */
export function useWebSocket(options: UseWebSocketOptions = {}) {
  const {
    enabled = true,
    handlers = {},
    autoConnect = true,
    autoDisconnect = true,
  } = options;

  const [status, setStatus] = useState<ConnectionStatus>(wsClient.getStatus());
  const [lastMessage, setLastMessage] = useState<{ type: WebSocketMessageType; payload: unknown } | null>(null);
  const unsubscribersRef = useRef<Array<() => void>>([]);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (enabled) {
      wsClient.connect();
    }
  }, [enabled]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    wsClient.disconnect();
  }, []);

  // Send message
  const send = useCallback(<T,>(type: WebSocketMessageType, payload: T) => {
    wsClient.send(type, payload);
  }, []);

  // Subscribe to status changes
  useEffect(() => {
    const unsubscribe = wsClient.onStatusChange((newStatus) => {
      setStatus(newStatus);
    });

    return () => {
      unsubscribe();
    };
  }, []);

  // Subscribe to event handlers
  useEffect(() => {
    // Clear previous subscriptions
    unsubscribersRef.current.forEach((unsubscribe) => unsubscribe());
    unsubscribersRef.current = [];

    // Subscribe to new handlers
    Object.entries(handlers).forEach(([type, handler]) => {
      if (handler) {
        const unsubscribe = wsClient.on(type as WebSocketMessageType, (payload) => {
          // Update last message
          setLastMessage({ type: type as WebSocketMessageType, payload });
          // Call handler
          handler(payload);
        });
        unsubscribersRef.current.push(unsubscribe);
      }
    });

    // Cleanup on unmount or when handlers change
    return () => {
      unsubscribersRef.current.forEach((unsubscribe) => unsubscribe());
      unsubscribersRef.current = [];
    };
  }, [handlers]);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect && enabled) {
      connect();
    }

    // Auto-disconnect on unmount
    return () => {
      if (autoDisconnect) {
        disconnect();
      }
    };
  }, [autoConnect, autoDisconnect, enabled, connect, disconnect]);

  return {
    // Connection status
    status,
    isConnected: status === ConnectionStatus.CONNECTED,
    isConnecting: status === ConnectionStatus.CONNECTING,
    isReconnecting: status === ConnectionStatus.RECONNECTING,
    isDisconnected: status === ConnectionStatus.DISCONNECTED,
    isFailed: status === ConnectionStatus.FAILED,

    // Last received message
    lastMessage,

    // Actions
    connect,
    disconnect,
    send,
  };
}

/**
 * Hook for subscribing to a specific evaluation's events
 */
export function useEvaluationEvents(evaluationId: string | null, enabled = true) {
  const [progress, setProgress] = useState<number | null>(null);
  const [phase, setPhase] = useState<string | null>(null);
  const [state, setState] = useState<string | null>(null);
  const [isComplete, setIsComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handlers = {
    [WebSocketMessageType.EVALUATION_PROGRESS]: (payload: { evaluation_id: string; progress: number }) => {
      if (payload.evaluation_id === evaluationId) {
        setProgress(payload.progress);
      }
    },
    [WebSocketMessageType.EVALUATION_PHASE_CHANGED]: (payload: { evaluation_id: string; phase?: string }) => {
      if (payload.evaluation_id === evaluationId && payload.phase) {
        setPhase(payload.phase);
      }
    },
    [WebSocketMessageType.EVALUATION_STATE_CHANGED]: (payload: { evaluation_id: string; state?: string }) => {
      if (payload.evaluation_id === evaluationId && payload.state) {
        setState(payload.state);
      }
    },
    [WebSocketMessageType.EVALUATION_COMPLETED]: (payload: { evaluation_id: string }) => {
      if (payload.evaluation_id === evaluationId) {
        setIsComplete(true);
        setProgress(100);
      }
    },
    [WebSocketMessageType.EVALUATION_FAILED]: (payload: { evaluation_id: string; error?: string }) => {
      if (payload.evaluation_id === evaluationId) {
        setError(payload.error || 'Evaluation failed');
        setIsComplete(true);
      }
    },
  };

  const ws = useWebSocket({
    enabled: enabled && !!evaluationId,
    handlers,
  });

  // Reset state when evaluation ID changes
  useEffect(() => {
    setProgress(null);
    setPhase(null);
    setState(null);
    setIsComplete(false);
    setError(null);
  }, [evaluationId]);

  return {
    ...ws,
    progress,
    phase,
    state,
    isComplete,
    error,
  };
}
