import { useState, useCallback } from 'preact/hooks';
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

  const updateState = useCallback((updates: Partial<ConversionState>) => {
    setState(prev => ({ ...prev, ...updates }));
  }, []);

  const addLog = useCallback((log: string) => {
    setState(prev => ({
      ...prev,
      logs: [...prev.logs, log],
    }));
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
          currentStep: 'Initializing...', // Or keep English here and let UI translate if needed, but we're mostly putting strings in logs
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

        addLog(`Task created: ${taskId}`);
        updateState({ taskId });

        // 轮询任务状态 (WebSocket 连接在 HomePage 组件中处理)
        await pollTaskStatus(taskId);
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : t('errorTitle');
        updateState({
          isConverting: false,
          error: errorMessage,
          status: 'failed',
        });
        addLog(`Error: ${errorMessage}`);
      }
    },
    [updateState, addLog]
  );

  const pollTaskStatus = useCallback(async (taskId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const taskStatus = await modelApi.getTaskStatus(taskId);

        // 更新进度和状态
        updateState({
          progress: taskStatus.progress,
          currentStep: taskStatus.current_step,
          status: taskStatus.status as 'idle' | 'converting' | 'completed' | 'failed',
        });

        // 检查任务状态
        if (taskStatus.status === 'completed') {
          clearInterval(pollInterval);
          updateState({
            isConverting: false,
            progress: 100,
            currentStep: 'Completed',
          });
          addLog('✅ Conversion completed');
        } else if (taskStatus.status === 'failed') {
          clearInterval(pollInterval);
          updateState({
            isConverting: false,
            error: taskStatus.error_message || t('errorTitle'),
            status: 'failed',
          });
          addLog(`❌ Failed: ${taskStatus.error_message || 'Unknown error'}`);
        } else if (taskStatus.status === 'running') {
          addLog(`${taskStatus.current_step} (${taskStatus.progress}%)`);
        }
      } catch (error) {
        clearInterval(pollInterval);
        const errorMessage = error instanceof Error ? error.message : t('errorTitle');
        updateState({
          isConverting: false,
          error: errorMessage,
          status: 'failed',
        });
        addLog(`Error: ${errorMessage}`);
      }
    }, 1000);

    // 清理函数
    return () => clearInterval(pollInterval);
  }, [updateState, addLog]);

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
