export interface ConversionConfig {
  model_type: 'YOLOv8' | 'YOLOX';
  input_size: 256 | 480 | 640;
  num_classes: number;
  confidence_threshold: number;
  quantization: 'int8';
  use_calibration: boolean;
}

export interface ConversionTask {
  task_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  current_step: string;
  config: ConversionConfig;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  error_message?: string;
  output_filename?: string;
}

export interface EnvironmentStatus {
  status: 'ready' | 'docker_not_installed' | 'image_pull_required' | 'not_configured';
  mode: 'docker' | 'none';
  message: string;
  image_size?: string;
  estimated_time?: string;
  error?: string;
  guide?: Record<string, unknown>;
}
