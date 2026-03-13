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
    console.log('[DEBUG] connectWebSocket 被调用, taskId:', taskId);

    // 关闭现有连接
    if (wsRef.current) {
      console.log('[DEBUG] 关闭现有 WebSocket 连接');
      wsRef.current.close();
    }

    // 构建 WebSocket URL
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/ws`;
    console.log('[DEBUG] WebSocket URL:', wsUrl);

    console.log('[DEBUG] 调用 addLog(正在连接 WebSocket...)');
    addLog('正在连接 WebSocket...');

    console.log('[DEBUG] 创建 WebSocket 实例');
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;
    console.log('[DEBUG] WebSocket 实例已创建');

    ws.onopen = () => {
      console.log('[DEBUG] WebSocket onopen 触发');
      addLog('WebSocket 已连接');
      // 订阅任务
      const subscribeMessage = JSON.stringify({
        action: 'subscribe',
        task_id: taskId
      });
      console.log('[DEBUG] 发送订阅消息:', subscribeMessage);
      ws.send(subscribeMessage);
      console.log('[DEBUG] 订阅消息已发送');
    };

    ws.onmessage = (event) => {
      console.log('[DEBUG] WebSocket onmessage 触发, data:', event.data);
      try {
        const message = JSON.parse(event.data);
        console.log('[DEBUG] 解析后的消息:', message);

        if (message.type === 'log') {
          // 接收并显示日志
          addLog(message.log);
        } else if (message.type === 'progress') {
          // 更新进度
          console.log('[DEBUG] 更新进度:', message.progress, message.step);
          updateState({
            progress: message.progress,
            currentStep: message.step
          });
        } else if (message.type === 'status') {
          // 状态更新
          console.log('[DEBUG] 收到状态更新:', message.data);
          const status = message.data?.status;
          if (status === 'completed') {
            console.log('[DEBUG] 任务完成，更新状态');
            updateState({
              isConverting: false,
              progress: message.data?.progress || 100,
              currentStep: message.data?.current_step || 'Completed',
              status: 'completed'
            });
            addLog('✅ 转换完成');
          } else if (status === 'failed') {
            console.log('[DEBUG] 任务失败');
            updateState({
              isConverting: false,
              error: message.data?.error || t('errorTitle'),
              status: 'failed'
            });
            addLog(`❌ 转换失败: ${message.data?.error || '未知错误'}`);
          } else {
            // 其他状态（如 running, pending）
            console.log('[DEBUG] 任务状态:', status);
            updateState({
              progress: message.data?.progress || 0,
              currentStep: message.data?.current_step || ''
            });
          }
        } else if (message.type === 'error') {
          console.log('[DEBUG] 收到错误消息');
          addLog(`错误: ${message.data?.message || '未知错误'}`);
        }
      } catch (err) {
        console.error('WebSocket 消息解析失败:', err);
      }
    };

    ws.onerror = (error) => {
      console.error('[DEBUG] WebSocket onerror 触发:', error);
      addLog('WebSocket 连接错误');
    };

    ws.onclose = () => {
      console.log('[DEBUG] WebSocket onclose 触发');
      addLog('WebSocket 连接关闭');
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
      console.log('[DEBUG] startConversion 开始执行');
      try {
        // 重置状态
        console.log('[DEBUG] 重置状态');
        updateState({
          isConverting: true,
          isCancelling: false,
          progress: 0,
          currentStep: 'Initializing...',
          logs: [],
          error: null,
          status: 'converting',
        });

        console.log('[DEBUG] 调用 addLog(welcomeMsg)');
        addLog(t('welcomeMsg'));

        // 上传模型并启动转换
        console.log('[DEBUG] 准备上传模型');
        const response = await modelApi.uploadModel(
          modelFile,
          config,
          yamlFile,
          calibrationFile
        );
        const taskId = response.task_id;
        console.log('[DEBUG] 收到 taskId:', taskId);

        console.log('[DEBUG] 调用 addLog(任务已创建)');
        addLog(`任务已创建: ${taskId}`);
        updateState({ taskId });

        // 连接 WebSocket 接收实时日志
        console.log('[DEBUG] 准备连接 WebSocket, taskId:', taskId);
        connectWebSocket(taskId);
        console.log('[DEBUG] connectWebSocket 调用完成');
      } catch (error) {
        console.error('[DEBUG] startConversion 捕获到错误:', error);
        const errorMessage = error instanceof Error ? error.message : t('errorTitle');
        updateState({
          isConverting: false,
          error: errorMessage,
          status: 'failed',
        });
        addLog(`错误: ${errorMessage}`);
      }
    },
    [updateState, addLog, connectWebSocket, t]
  );

  const cancelConversion = useCallback(async () => {
    if (!state.taskId) return;

    try {
      updateState({ isCancelling: true });
      addLog('Cancelling task...');

      await modelApi.cancelTask(state.taskId);

      updateState({
        isConverting: false,
        isCancelling: false,
        status: 'idle',
        taskId: null,
      });

      addLog('Task cancelled');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : t('errorTitle');
      updateState({ isCancelling: false });
      addLog(`Cancellation failed: ${errorMessage}`);
      throw error;
    }
  }, [state.taskId, updateState, addLog]);

  const downloadResult = useCallback(async () => {
    if (!state.taskId) return;

    try {
      addLog('Downloading converted model...');
      const blob = await modelApi.downloadModel(state.taskId);
      const filename = `converted_model_${state.taskId}.bin`;
      downloadFile(blob, filename);
      addLog(`✅ Downloaded: ${filename}`);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : t('errorTitle');
      addLog(`Download failed: ${errorMessage}`);
      throw error;
    }
  }, [state.taskId, addLog]);

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
