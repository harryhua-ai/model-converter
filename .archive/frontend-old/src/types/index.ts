export type ModelType = 'YOLOv8' | 'YOLOX';
export type QuantizationType = 'int8';
export type InputDataType = 'uint8';

export interface ConversionConfig {
  model_name: string;
  model_type: ModelType;
  model_version?: string;
  input_width: number;
  input_height: number;
  input_data_type?: InputDataType;
  /** Always 'int8' — platform only supports INT8 quantization */
  quantization_type: QuantizationType;
  num_classes: number;
  confidence_threshold: number;
  use_custom_calibration?: boolean;
  calibration_dataset_filename?: string;
}

export interface ConfigPreset {
  id: string;
  name: string;
  description: string;
  config: ConversionConfig;
}

// Note: Task and WSMessage below are legacy types kept for compatibility.
// For real API calls use TaskStatus from services/api.ts instead.
export interface Task {
  task_id: string;
  config: ConversionConfig;
  status: string;
  progress: number;
  message?: string;
  created_at: string;
  updated_at: string;
  result_filename?: string;
}

export interface WSMessage {
  task_id: string;
  status: string;
  progress: number;
  message?: string;
}
