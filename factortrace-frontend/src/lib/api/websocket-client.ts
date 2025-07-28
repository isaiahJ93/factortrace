import { emissionsKeys } from "@/lib/api/elite-client";
import { useEffect, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';

interface WebSocketMessage {
  type: 'emission_update' | 'voucher_update' | 'notification';
  data: any;
  timestamp: string;
}

export class EliteWebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private messageHandlers = new Map<string, Set<(data: any) => void>>();
  
  constructor(private url: string) {}
  
  connect() {
    try {
      this.ws = new WebSocket(this.url);
      
      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
        this.startHeartbeat();
      };
      
      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };
      
      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      
      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.stopHeartbeat();
        this.reconnect();
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      this.reconnect();
    }
  }
  
  private reconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }
    
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
    
    setTimeout(() => {
      this.connect();
    }, delay);
  }
  
  private startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000); // 30 seconds
  }
  
  private stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }
  
  private handleMessage(message: WebSocketMessage) {
    const handlers = this.messageHandlers.get(message.type);
    if (handlers) {
      handlers.forEach(handler => handler(message.data));
    }
  }
  
  subscribe(type: string, handler: (data: any) => void) {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, new Set());
    }
    this.messageHandlers.get(type)!.add(handler);
    
    // Return unsubscribe function
    return () => {
      const handlers = this.messageHandlers.get(type);
      if (handlers) {
        handlers.delete(handler);
      }
    };
  }
  
  send(message: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected, queuing message');
      // Implement message queue if needed
    }
  }
  
  disconnect() {
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

// React hook for WebSocket
export function useWebSocket() {
  const queryClient = useQueryClient();
  const wsRef = useRef<EliteWebSocketClient | null>(null);
  
  useEffect(() => {
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';
    wsRef.current = new EliteWebSocketClient(wsUrl);
    wsRef.current.connect();
    
    // Subscribe to emission updates
    const unsubEmissions = wsRef.current.subscribe('emission_update', (data) => {
      // Update React Query cache
      queryClient.invalidateQueries({ queryKey: emissionsKeys.all });
    });
    
    // Subscribe to voucher updates
    const unsubVouchers = wsRef.current.subscribe('voucher_update', (data) => {
      queryClient.invalidateQueries({ queryKey: ['vouchers'] });
    });
    
    return () => {
      unsubEmissions();
      unsubVouchers();
      wsRef.current?.disconnect();
    };
  }, [queryClient]);
  
  return wsRef.current;
}