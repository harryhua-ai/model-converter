import axios, { AxiosError } from 'axios';

const API_BASE = '/api';

/**
 * API 错误响应
 */
interface ApiError {
  detail: string;
  error?: string;
  message?: string;
}

/**
 * 转换响应
 */
interface ConversionResponse {
  task_id: string;
  status: string;
  message: string;
}

/**
 * 任务状态响应
 */
interface TaskStatusResponse {
  task_id: string;
  status: string;
  progress: number;
  current_step: string;
  config: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  error_message?: string;
  output_filename?: string;
}

/**
 * 上传模型并启动转换
 */
export async function uploadModel(
  modelFile: File,
  config: Record<string, unknown>,
  yamlFile?: File,
  calibrationFile?: File
): Promise<ConversionResponse> {
  try {
    const formData = new FormData();
    formData.append('model_file', modelFile);
    formData.append('config', JSON.stringify(config));

    if (yamlFile) {
      formData.append('yaml_file', yamlFile);
    }

    if (calibrationFile) {
      formData.append('calibration_dataset', calibrationFile);
    }

    const response = await axios.post<ConversionResponse>(
      `${API_BASE}/convert`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );

    return response.data;
  } catch (error) {
    const apiError = error as AxiosError<ApiError>;

    // 格式化错误消息（处理数组和对象）
    const formatErrorMessage = (detail: any): string => {
      if (typeof detail === 'string') return detail;
      if (Array.isArray(detail)) {
        return detail.map((e: any) => e.msg || JSON.stringify(e)).join('; ');
      }
      if (typeof detail === 'object' && detail !== null) {
        return JSON.stringify(detail);
      }
      return '未知错误';
    };

    const message = formatErrorMessage(apiError.response?.data?.detail) ||
                    apiError.message ||
                    '上传失败';
    throw new Error(message);
  }
}

/**
 * 获取任务状态
 */
export async function getTaskStatus(taskId: string): Promise<TaskStatusResponse> {
  try {
    const response = await axios.get<TaskStatusResponse>(
      `${API_BASE}/tasks/${taskId}`
    );
    return response.data;
  } catch (error) {
    const apiError = error as AxiosError<ApiError>;
    const message = apiError.response?.data?.detail || apiError.message || '获取任务状态失败';
    throw new Error(message);
  }
}

/**
 * 下载转换后的模型
 */
export async function downloadModel(taskId: string): Promise<Blob> {
  try {
    const response = await axios.get(`${API_BASE}/tasks/${taskId}/download`, {
      responseType: 'blob',
    });

    return response.data;
  } catch (error) {
    const apiError = error as AxiosError<ApiError>;
    const message = apiError.response?.data?.detail || apiError.message || '下载失败';
    throw new Error(message);
  }
}

/**
 * 取消任务
 */
export async function cancelTask(taskId: string): Promise<{ message: string }> {
  try {
    const response = await axios.post<{ message: string }>(
      `${API_BASE}/tasks/${taskId}/cancel`
    );
    return response.data;
  } catch (error) {
    const apiError = error as AxiosError<ApiError>;
    const message = apiError.response?.data?.detail || apiError.message || '取消任务失败';
    throw new Error(message);
  }
}

/**
 * 获取环境状态
 */
export async function getEnvironmentStatus(): Promise<{
  status: string;
  mode: string;
  message: string;
  image_size?: string;
  estimated_time?: string;
}> {
  try {
    const response = await axios.get(`${API_BASE}/environment/status`);
    return response.data;
  } catch (error) {
    const apiError = error as AxiosError<ApiError>;
    const message = apiError.response?.data?.detail || apiError.message || '获取环境状态失败';
    throw new Error(message);
  }
}

/**
 * 导出 API 对象
 */
export const modelApi = {
  uploadModel,
  getTaskStatus,
  downloadModel,
  cancelTask,
  getEnvironmentStatus,
};
