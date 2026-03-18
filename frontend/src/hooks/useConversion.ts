import { useState, useCallback, useRef, useEffect } from 'preact/hooks';
import { modelApi } from '../services/api';
import { downloadFile } from '../utils/helpers';
import { useI18nStore } from '../store/i18n';
import type { ConversionConfig } from '../types';

interface ConversionState {
  isConverting: boolean;
  isCancelling: boolean;
  progress: number;
  currentStep: string;
  logs: string[];
  error: string | null;
  taskId: string | null;
  status: 'idle' | 'converting' | 'completed' | 'failed';
}

interface UseConversionReturn {
  state: ConversionState;
  startConversion: (
    modelFile: File,
    config: ConversionConfig,
    yamlFile?: File,
    calibrationFile?: File
  ) => Promise<void>;
  cancelConversion: () => Promise<void>;
  downloadResult: () => Promise<void>;
  reset: () => void;
  addLog: (log: string) => void;
}

/**
 * 转换逻辑 Hook
 */
export function useConversion(): UseConversionReturn {
  const { t } = useI18nStore();
  const [state, setState] = useState<ConversionState>({
    isConverting: false,
    isCancelling: false,
    progress: 0,
    currentStep: '',
    logs: [],
    error: null,
    taskId: null,
    status: 'idle',
  });

  // WebSocket 连接引用
  const wsRef = useRef<WebSocket | null>(null);

  const updateState = useCallback((updates: Partial<ConversionState>) => {
    setState(prev => ({ ...prev, ...updates }));
  }, []);

  const addLog = useCallback((log: string) => {
    setState(prev => ({
      ...prev,
      logs: [...prev.logs, log],
    }));
  }, []);

  // 连接 WebSocket
  const connectWebSocket = useCallback((taskId: string) => {
    // 关闭现有连接
    if (wsRef.current) {
      wsRef.current.close();
    }

    // 构建 WebSocket URL
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/ws`;

    addLog(t('logConnecting'));

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      addLog(t('logConnected'));
      // 订阅任务
      const subscribeMessage = JSON.stringify({
        action: 'subscribe',
        task_id: taskId
      });
      ws.send(subscribeMessage);
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);

        if (message.type === 'log') {
          // Receive and display logs
          addLog(message.log);
        } else if (message.type === 'progress') {
          // Update progress
          updateState({
            progress: message.progress,
            currentStep: message.step
          });
        } else if (message.type === 'status') {
          // Status update
          const status = message.data?.status;
          if (status === 'completed') {
            updateState({
              isConverting: false,
              progress: message.data?.progress || 100,
              currentStep: message.data?.current_step || 'Completed',
              status: 'completed'
            });
            addLog(t('logCompleted'));
          } else if (status === 'failed') {
            updateState({
              isConverting: false,
              error: message.data?.error || t('errorTitle'),
              status: 'failed'
            });
            addLog(t('logFailed', { error: message.data?.error || t('errorUnknown') }));
          } else {
            // Other statuses (running, pending)
            updateState({
              progress: message.data?.progress || 0,
              currentStep: message.data?.current_step || ''
            });
          }
        } else if (message.type === 'error') {
          addLog(t('logError', { message: message.data?.message || t('errorUnknown') }));
        }
      } catch (err) {
        // Failed to parse WebSocket message
      }
    };

    ws.onerror = (error) => {
      addLog(t('logWsError'));
    };

    ws.onclose = () => {
      addLog(t('logWsClosed'));
      wsRef.current = null;
    };

    return ws;
  }, [addLog, updateState, t]);

  // 清理 WebSocket 连接
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const startConversion = useCallback(
    async (
      modelFile: File,
      config: ConversionConfig,
      yamlFile?: File,
      calibrationFile?: File
    ) => {
      try {
        // 重置状态
        updateState({
          isConverting: true,
          isCancelling: false,
          progress: 0,
          currentStep: 'Initializing...',
          logs: [],
          error: null,
          status: 'converting',
        });

        addLog(t('welcomeMsg'));

        // 上传模型并启动转换
        const response = await modelApi.uploadModel(
          modelFile,
          config,
          yamlFile,
          calibrationFile
        );
        const taskId = response.task_id;

        addLog(t('logTaskCreated', { taskId }));
        updateState({ taskId });

        // Connect to WebSocket for real-time logs
        connectWebSocket(taskId);
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : t('errorTitle');
        updateState({
          isConverting: false,
          error: errorMessage,
          status: 'failed',
        });
        addLog(t('logError', { message: errorMessage }));
      }
    },
    [updateState, addLog, connectWebSocket, t]
  );

  const cancelConversion = useCallback(async () => {
    if (!state.taskId) return;

    try {
      updateState({ isCancelling: true });
      addLog(t('logCancelling'));

      await modelApi.cancelTask(state.taskId);

      updateState({
        isConverting: false,
        isCancelling: false,
        status: 'idle',
        taskId: null,
      });

      addLog(t('logCancelled'));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : t('errorTitle');
      updateState({ isCancelling: false });
      addLog(t('logCancelFailed', { error: errorMessage }));
      throw error;
    }
  }, [state.taskId, updateState, addLog, t]);

  const downloadResult = useCallback(async () => {
    if (!state.taskId) return;

    try {
      addLog(t('logDownloading'));
      const blob = await modelApi.downloadModel(state.taskId);
      const filename = `converted_model_${state.taskId}.bin`;
      downloadFile(blob, filename);
      addLog(t('logDownloaded', { filename }));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : t('errorTitle');
      addLog(t('logDownloadFailed', { error: errorMessage }));
      throw error;
    }
  }, [state.taskId, addLog, t]);

  const reset = useCallback(() => {
    setState({
      isConverting: false,
      isCancelling: false,
      progress: 0,
      currentStep: '',
      logs: [],
      error: null,
      taskId: null,
      status: 'idle',
    });
  }, []);

  return {
    state,
    startConversion,
    cancelConversion,
    downloadResult,
    reset,
    addLog,
  };
}
