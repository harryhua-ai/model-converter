import { create } from 'zustand';
import type { ConversionConfig, ConversionTask } from '../types';

/**
 * 预设配置
 */
export const PRESETS: Record<string, Omit<ConversionConfig, 'num_classes'>> = {
  fast: {
    model_type: 'YOLOv8',
    input_size: 256,
    confidence_threshold: 0.25,
    quantization: 'int8',
    use_calibration: false,
  },
  balanced: {
    model_type: 'YOLOv8',
    input_size: 480,
    confidence_threshold: 0.25,
    quantization: 'int8',
    use_calibration: true,
  },
  high_accuracy: {
    model_type: 'YOLOX',
    input_size: 640,
    confidence_threshold: 0.3,
    quantization: 'int8',
    use_calibration: true,
  },
};

/**
 * 应用状态
 */
interface AppState {
  // 文件选择
  selectedFile: File | null;
  selectedYaml: File | null;
  selectedCalibration: File | null;

  // 配置
  selectedPreset: string;
  numClasses: number;
  modelType: 'YOLOv8' | 'YOLOX';
  inputSize: 256 | 480 | 640;
  confidenceThreshold: number;
  quantization: 'int8';
  useCalibration: boolean;

  // 转换状态
  conversionStatus: 'idle' | 'converting' | 'completed' | 'failed';
  currentTask: ConversionTask | null;

  // UI 状态
  showLogs: boolean;

  // Actions
  setSelectedFile: (file: File | null) => void;
  setSelectedYaml: (file: File | null) => void;
  setSelectedCalibration: (file: File | null) => void;
  setSelectedPreset: (preset: string) => void;
  setNumClasses: (numClasses: number) => void;
  setModelType: (modelType: 'YOLOv8' | 'YOLOX') => void;
  setInputSize: (size: 256 | 480 | 640) => void;
  setConfidenceThreshold: (threshold: number) => void;
  setQuantization: (quantization: 'int8') => void;
  setUseCalibration: (useCalibration: boolean) => void;
  setConversionStatus: (status: 'idle' | 'converting' | 'completed' | 'failed') => void;
  setCurrentTask: (task: ConversionTask | null) => void;
  setShowLogs: (show: boolean) => void;
  reset: () => void;

  // 获取完整配置
  getConfig: () => ConversionConfig;
}

/**
 * 初始状态
 */
const initialState = {
  selectedFile: null,
  selectedYaml: null,
  selectedCalibration: null,
  selectedPreset: 'balanced',
  numClasses: 80,
  modelType: 'YOLOv8' as const,
  inputSize: 480 as const,
  confidenceThreshold: 0.25,
  quantization: 'int8' as const,
  useCalibration: true,
  conversionStatus: 'idle' as const,
  currentTask: null,
  showLogs: false,
};

/**
 * 创建 Zustand store
 */
export const useAppStore = create<AppState>((set, get) => ({
  ...initialState,

  setSelectedFile: (file) => set({ selectedFile: file }),

  setSelectedYaml: (file) => set({ selectedYaml: file }),

  setSelectedCalibration: (file) => set({ selectedCalibration: file }),

  setSelectedPreset: (preset) => {
    const presetConfig = PRESETS[preset];
    if (presetConfig) {
      set({
        selectedPreset: preset,
        modelType: presetConfig.model_type,
        inputSize: presetConfig.input_size,
        confidenceThreshold: presetConfig.confidence_threshold,
        quantization: presetConfig.quantization,
        useCalibration: presetConfig.use_calibration,
      });
    }
  },

  setNumClasses: (numClasses) => set({ numClasses }),

  setModelType: (modelType) => set({ modelType }),

  setInputSize: (inputSize) => set({ inputSize }),

  setConfidenceThreshold: (confidenceThreshold) => set({ confidenceThreshold }),

  setQuantization: (quantization) => set({ quantization }),

  setUseCalibration: (useCalibration) => set({ useCalibration }),

  setConversionStatus: (conversionStatus) => set({ conversionStatus }),

  setCurrentTask: (currentTask) => set({ currentTask }),

  setShowLogs: (showLogs) => set({ showLogs }),

  reset: () => set(initialState),

  getConfig: () => {
    const state = get();
    return {
      model_type: state.modelType,
      input_size: state.inputSize,
      num_classes: state.numClasses,
      confidence_threshold: state.confidenceThreshold,
      quantization: state.quantization,
      use_calibration: state.useCalibration,
    };
  },
}));
