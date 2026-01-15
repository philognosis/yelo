/**
 * WebSocket Client
 * Real-time communication with the backend
 */

import {
  WebSocketMessage,
  WebSocketMessageType,
  EvaluationEventPayload,
  ProgressEventPayload,
  ErrorEventPayload,
} from '@/types/api';
import { getAuthToken } from './auth';

/**
 * WebSocket Event Handler Type
 */
type EventHandler<T = unknown> = (payload: T) => void;

/**
 * WebSocket Connection Status
 */
export enum ConnectionStatus {
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  DISCONNECTED = 'disconnected',
  RECONNECTING = 'reconnecting',
  FAILED = 'failed',
}

/**
 * WebSocket Client Class
 * Manages WebSocket connection with auto-reconnect
 */
export class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // Start with 1 second
  private maxReconnectDelay = 30000; // Max 30 seconds
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private pingInterval: NodeJS.Timeout | null = null;
  private eventHandlers: Map<WebSocketMessageType, Set<EventHandler>> = new Map();
  private statusHandlers: Set<(status: ConnectionStatus) => void> = new Set();
  private status: ConnectionStatus = ConnectionStatus.DISCONNECTED;

  constructor(url?: string) {
    this.url = url || process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
  }

  /**
   * Connect to WebSocket server
   */
  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.warn('WebSocket is already connected');
      return;
    }

    this.setStatus(ConnectionStatus.CONNECTING);

    try {
      // Add auth token to URL if available
      const token = getAuthToken();
      const wsUrl = token ? `${this.url}?token=${token}` : this.url;

      this.ws = new WebSocket(wsUrl);

      // Connection opened
      this.ws.addEventListener('open', this.handleOpen);

      // Listen for messages
      this.ws.addEventListener('message', this.handleMessage);

      // Connection closed
      this.ws.addEventListener('close', this.handleClose);

      // Connection error
      this.ws.addEventListener('error', this.handleError);
    } catch (error) {
      console.error('WebSocket connection error:', error);
      this.setStatus(ConnectionStatus.FAILED);
      this.scheduleReconnect();
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }

    if (this.ws) {
      this.ws.removeEventListener('open', this.handleOpen);
      this.ws.removeEventListener('message', this.handleMessage);
      this.ws.removeEventListener('close', this.handleClose);
      this.ws.removeEventListener('error', this.handleError);
      this.ws.close();
      this.ws = null;
    }

    this.setStatus(ConnectionStatus.DISCONNECTED);
  }

  /**
   * Send a message through WebSocket
   */
  send<T>(type: WebSocketMessageType, payload: T): void {
    if (this.ws?.readyState !== WebSocket.OPEN) {
      console.error('WebSocket is not connected');
      return;
    }

    const message: WebSocketMessage<T> = {
      type,
      payload,
      timestamp: new Date().toISOString(),
    };

    this.ws.send(JSON.stringify(message));
  }

  /**
   * Subscribe to a specific event type
   */
  on<T = unknown>(type: WebSocketMessageType, handler: EventHandler<T>): () => void {
    if (!this.eventHandlers.has(type)) {
      this.eventHandlers.set(type, new Set());
    }

    const handlers = this.eventHandlers.get(type)!;
    handlers.add(handler as EventHandler);

    // Return unsubscribe function
    return () => {
      handlers.delete(handler as EventHandler);
    };
  }

  /**
   * Subscribe to connection status changes
   */
  onStatusChange(handler: (status: ConnectionStatus) => void): () => void {
    this.statusHandlers.add(handler);

    // Immediately call with current status
    handler(this.status);

    // Return unsubscribe function
    return () => {
      this.statusHandlers.delete(handler);
    };
  }

  /**
   * Get current connection status
   */
  getStatus(): ConnectionStatus {
    return this.status;
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.status === ConnectionStatus.CONNECTED;
  }

  // ==================== Private Methods ====================

  private handleOpen = (): void => {
    console.log('WebSocket connected');
    this.setStatus(ConnectionStatus.CONNECTED);
    this.reconnectAttempts = 0;
    this.reconnectDelay = 1000;

    // Start ping interval to keep connection alive
    this.startPingInterval();
  };

  private handleMessage = (event: MessageEvent): void => {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);
      this.dispatchEvent(message.type, message.payload);
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  };

  private handleClose = (event: CloseEvent): void => {
    console.log('WebSocket closed:', event.code, event.reason);
    this.setStatus(ConnectionStatus.DISCONNECTED);

    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }

    // Attempt to reconnect unless it was a normal closure
    if (event.code !== 1000) {
      this.scheduleReconnect();
    }
  };

  private handleError = (event: Event): void => {
    console.error('WebSocket error:', event);
    this.setStatus(ConnectionStatus.FAILED);
  };

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      this.setStatus(ConnectionStatus.FAILED);
      return;
    }

    this.setStatus(ConnectionStatus.RECONNECTING);
    this.reconnectAttempts++;

    // Exponential backoff
    const delay = Math.min(
      this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1),
      this.maxReconnectDelay
    );

    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

    this.reconnectTimeout = setTimeout(() => {
      this.connect();
    }, delay);
  }

  private startPingInterval(): void {
    // Send ping every 30 seconds to keep connection alive
    this.pingInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.send(WebSocketMessageType.SYSTEM_STATUS, { type: 'ping' });
      }
    }, 30000);
  }

  private dispatchEvent<T>(type: WebSocketMessageType, payload: T): void {
    const handlers = this.eventHandlers.get(type);
    if (handlers) {
      handlers.forEach((handler) => {
        try {
          handler(payload);
        } catch (error) {
          console.error(`Error in event handler for ${type}:`, error);
        }
      });
    }
  }

  private setStatus(status: ConnectionStatus): void {
    this.status = status;
    this.statusHandlers.forEach((handler) => {
      try {
        handler(status);
      } catch (error) {
        console.error('Error in status handler:', error);
      }
    });
  }
}

// Export singleton instance
export const wsClient = new WebSocketClient();

// Export class for testing
export default WebSocketClient;
