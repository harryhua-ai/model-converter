export const en = {
  // General Header & Titles
  title: 'NE301 Model Converter',
  subtitle: 'Convert PyTorch/ONNX models to NE301 format',
  
  // Steps
  step1Title: 'Upload Model File',
  step2Title: 'Class Definition File (Optional)',
  step3Title: 'Calibration Dataset (Optional)',
  step3Desc: 'Uploading a calibration dataset can improve quantization accuracy',
  
  // Settings & Actions
  modeLabel: 'MODE',
  presetFast: 'Fast Conversion',
  presetBalanced: 'Balanced Mode',
  presetHighAccuracy: 'High Accuracy Mode',
  classesLabel: 'CLASSES',
  buttonStart: 'Start',
  buttonCancel: 'Cancel',
  buttonReset: 'Reset',
  buttonDownload: 'Download',
  
  // Monitor & Logs
  progressTitle: 'Conversion Progress',
  errorTitle: 'Conversion Failed',
  terminalTitle: 'conversion.log',
  exportLogs: 'Export',
  waitingLogs: 'Waiting for logs...',
  totalLogs: 'logs total',
  runningStatus: 'Running',
  idleStatus: 'Idle',

  // Progress Steps
  step1Export: 'Export TFLite',
  step2Quantize: 'Quantize Model',
  step3Prepare: 'Prepare NE301',
  step4Build: 'NE301 Build',
  
  // Messages and Notifications
  welcomeMsg: 'Welcome to NE301 Model Converter',
  uploadPrompt: 'Please upload a model file to begin',
  errorNoModel: 'Error: Please select a model file first',
  errorNoClasses: 'Error: Number of classes must be greater than 0',
  errorClassDetected: 'Detected {count} classes from YAML file',
  
  // File Upload Area
  dragDropModel: 'Drag & drop model file',
  supportFormatModel: 'Supports .pt, .onnx, .h5',
  fileSelected: 'Selected:',
  changeFile: 'Change',
  browseFile: 'click to browse',
  dragDropYaml: 'Drag & drop class configuration',
  supportFormatYaml: 'Supports .yaml, .yml',
  detectingClasses: 'Detecting classes...',
  dragDropZip: 'Drag & drop image dataset',
  supportFormatZip: 'Supports .zip, .tar.gz',
};

export type TranslationDict = typeof en;
