import { create } from 'zustand';
import type { ConfigPreset } from '../types';
import { presetApi, taskApi, type TaskStatus } from '../services/api';
import i18n, { type Language } from '../i18n';

interface AppState {
  presets: ConfigPreset[];
  tasks: TaskStatus[];
  isLoadingPresets: boolean;
  isLoadingTasks: boolean;
  error: string | null;
  language: Language;
  
  fetchPresets: () => Promise<void>;
  fetchTasks: () => Promise<void>;
  updateTaskProgress: (taskId: string, progress: number, status?: TaskStatus['status']) => void;
  setLanguage: (lang: Language) => void;
}

// Default presets for the UI until backend loaded
const DEFAULT_PRESETS: ConfigPreset[] = [
  {
    id: 'yolov8n',
    name: 'YOLOv8 Nano (INT8)',
    description: 'Official YOLOv8n, 640px. Optimized for NE301 (STM32N6).',
    config: {
      model_name: 'yolov8n_edge',
      model_type: 'YOLOv8',
      input_width: 640,
      input_height: 640,
      quantization_type: 'int8',
      num_classes: 80,
      confidence_threshold: 0.25
    }
  },
  {
    id: 'yoloxn',
    name: 'YOLOX Nano (INT8)',
    description: 'YOLOX Nano, 480px. High efficiency, low latency.',
    config: {
      model_name: 'yoloxn_edge',
      model_type: 'YOLOX',
      input_width: 480,
      input_height: 480,
      quantization_type: 'int8',
      num_classes: 80,
      confidence_threshold: 0.25
    }
  }
];

export const useAppStore = create<AppState>((set, get) => ({
  presets: DEFAULT_PRESETS,
  tasks: [],
  isLoadingPresets: false,
  isLoadingTasks: false,
  error: null,
  language: 'en',

  fetchPresets: async () => {
    set({ isLoadingPresets: true, error: null });
    try {
      const backendPresets = await presetApi.getPresets();
      // Only overwrite if we actually got something, otherwise keep defaults
      if (backendPresets && backendPresets.length > 0) {
        set({ presets: backendPresets, isLoadingPresets: false });
      } else {
        set({ presets: DEFAULT_PRESETS, isLoadingPresets: false });
      }
    } catch (error) {
       console.error('[Store Error] Failed to fetch presets:', error instanceof Error ? error.message : 'Unknown error');
       set({ 
         isLoadingPresets: false,
         // Keep defaults on error instead of clearing them
         presets: DEFAULT_PRESETS,
         error: error instanceof Error ? error.message : 'An error occurred while fetching presets.'
       });
    }
  },

  fetchTasks: async () => {
    // Avoid re-triggering loader extensively
    if (get().tasks.length === 0) set({ isLoadingTasks: true, error: null });
    try {
      const tasks = await taskApi.getTasks();
      set({ tasks, isLoadingTasks: false });
    } catch (error) {
       console.error('[Store Error] Failed to fetch tasks:', error instanceof Error ? error.message : 'Unknown error');
       set({ 
         isLoadingTasks: false,
         error: error instanceof Error ? error.message : 'An error occurred while fetching tasks.'
       });
    }
  },

  updateTaskProgress: (taskId, progress, status) => {
    set((state) => ({
      tasks: state.tasks.map((task) => 
        task.task_id === taskId 
          ? { ...task, progress, status: status || task.status }
          : task
      ),
    }));
  },

  setLanguage: (lang) => {
    i18n.locale(lang);
    set({ language: lang });
    // Re-fetch items that might have hardcoded mock translations
    get().fetchPresets();
  },
}));
