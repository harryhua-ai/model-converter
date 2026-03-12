import { useEffect, useRef, useState } from 'preact/hooks';
import { ConversionTask } from '../types';

interface WebSocketMessage {
  type: 'progress' | 'log' | 'status' | 'error' | 'complete';
  data: {
    task_id?: string;
    progress?: number;
    current_step?: string;
    message?: string;
    status?: string;
    error?: string;
  };
}

interface UseWebSocketOptions {
  onProgress?: (progress: number, step: string) => void;
  onLog?: (log: string) => void;
  onStatusChange?: (status: string) => void;
  onError?: (error: string) => void;
  onComplete?: () => void;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  error: string | null;
  reconnect: () => void;
  disconnect: () => void;
}

/**
 * WebSocket Hook - 连接到后端 WebSocket 服务
 */
export function useWebSocket(
  taskId: string | null,
  options: UseWebSocketOptions = {}
): UseWebSocketReturn {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number>();

  const {
    onProgress,
    onLog,
    onStatusChange,
    onError,
    onComplete,
  } = options;

  // 连接 WebSocket
  const connect = () => {
    if (!taskId) return;

    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const wsUrl = `${protocol}//${host}/api/ws`;

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        setError(null);

        // 订阅任务更新
        ws.send(JSON.stringify({
          type: 'subscribe',
          task_id: taskId,
        }));
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);

          switch (message.type) {
            case 'progress':
              if (message.data.progress !== undefined && message.data.current_step) {
                onProgress?.(message.data.progress, message.data.current_step);
              }
              break;

            case 'log':
              if (message.data.message) {
                onLog?.(message.data.message);
              }
              break;

            case 'status':
              if (message.data.status) {
                onStatusChange?.(message.data.status);
              }
              break;

            case 'error':
              if (message.data.error) {
                setError(message.data.error);
                onError?.(message.data.error);
              }
              break;

            case 'complete':
              onComplete?.();
              break;
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError('WebSocket 连接错误');
        setIsConnected(false);
      };

      ws.onclose = () => {
        setIsConnected(false);
      };
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'WebSocket 连接失败';
      setError(errorMessage);
      setIsConnected(false);
    }
  };

  // 断开连接
  const disconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsConnected(false);
  };

  // 重新连接
  const reconnect = () => {
    disconnect();
    connect();
  };

  // 当 taskId 改变时重新连接
  useEffect(() => {
    if (taskId) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [taskId]);

  // 清理
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, []);

  return {
    isConnected,
    error,
    reconnect,
    disconnect,
  };
}

/**
 * 使用轮询作为备用方案 (当 WebSocket 不可用时)
 */
export function usePolling(
  taskId: string | null,
  enabled: boolean,
  interval: number = 1000
) {
  const [task, setTask] = useState<ConversionTask | null>(null);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<number>();

  useEffect(() => {
    if (!taskId || !enabled) return;

    const poll = async () => {
      try {
        const response = await fetch(`/api/tasks/${taskId}`);
        if (!response.ok) {
          throw new Error('获取任务状态失败');
        }
        const data = await response.json();
        setTask(data);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : '轮询失败';
        setError(errorMessage);
      }
    };

    poll(); // 立即执行一次
    intervalRef.current = window.setInterval(poll, interval);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [taskId, enabled, interval]);

  return { task, error };
}
