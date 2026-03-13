import axios from 'axios';
import type { ConfigPreset, ConversionConfig } from '../types';

const API_BASE = '/api/v1';

// ─────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────

export interface TaskStatus {
  task_id: string;
  status: 'pending' | 'validating' | 'converting' | 'packaging' | 'completed' | 'failed';
  progress: number;
  current_step: string;
  error_message?: string | null;
  output_filename?: string | null;
  created_at: string;
  updated_at: string;
}

// ─────────────────────────────────────────────
// Model API
// ─────────────────────────────────────────────

export const modelApi = {
  /**
   * Upload model + calibration + class yaml files and start conversion.
   * Returns the task_id for polling.
   */
  uploadModel: async (
    modelFile: File,
    config: ConversionConfig,
    calibrationDataset?: File,
    classYaml?: File,
  ): Promise<{ task_id: string; filename: string; file_size: number }> => {
    const formData = new FormData();
    formData.append('file', modelFile);
    formData.append('config', JSON.stringify(config));

    if (calibrationDataset) {
      formData.append('calibration_dataset', calibrationDataset);
    }
    if (classYaml) {
      formData.append('class_yaml', classYaml);
    }

    const response = await axios.post(`${API_BASE}/models/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 1800_000, // 30 minutes (ARM64 模拟环境下 TFLite 转换需要更长时间)
    });
    return response.data;
  },

  /**
   * Download the converted ZIP package as a Blob.
   */
  downloadConvertedModel: async (taskId: string): Promise<Blob> => {
    const response = await axios.get(`${API_BASE}/models/download/${taskId}`, {
      responseType: 'blob',
      timeout: 300_000,
    });
    return response.data;
  },
};

// ─────────────────────────────────────────────
// Task API
// ─────────────────────────────────────────────

export const taskApi = {
  /**
   * Get the current status of a conversion task.
   */
  getTaskStatus: async (taskId: string): Promise<TaskStatus> => {
    const response = await axios.get(`${API_BASE}/tasks/${taskId}`, { timeout: 10_000 });
    return response.data;
  },

  /**
   * Cancel a running task.
   */
  cancelTask: async (taskId: string): Promise<{ message: string; task_id: string }> => {
    const response = await axios.post(`${API_BASE}/tasks/${taskId}/cancel`, { timeout: 10_000 });
    return response.data;
  },

  /**
   * List recent tasks.
   */
  getTasks: async (): Promise<TaskStatus[]> => {
    const response = await axios.get(`${API_BASE}/tasks/`, { timeout: 10_000 });
    return response.data?.tasks ?? [];
  },
};

// ─────────────────────────────────────────────
// Preset API
// ─────────────────────────────────────────────

export const presetApi = {
  getPresets: async (): Promise<ConfigPreset[]> => {
    try {
      const response = await axios.get(`${API_BASE}/presets/`, { timeout: 10_000 });
      return response.data ?? [];
    } catch {
      // Fall back to hardcoded presets when backend is unavailable in dev
      return [];
    }
  },
};
