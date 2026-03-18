export const en = {
  // General Header & Titles
  title: 'NE301 Model Converter',
  subtitle: 'Convert PyTorch/ONNX models to NE301 format',
  
  // Steps
  step1Title: 'Upload Model File',
  step2Title: 'Class Definition File',
  step2Desc: 'Uploading a YAML file can automatically detect class count and names',
  step3Title: 'Calibration Dataset',
  step3Desc: 'Uploading a calibration dataset can improve quantization accuracy',
  
  // Settings & Actions
  modeLabel: 'MODE',
  presetFast: 'Fast Conversion',
  presetBalanced: 'Balanced Mode',
  presetHighAccuracy: 'High Accuracy Mode',
  classesLabel: 'CLASSES',
  buttonStart: 'Start',
  buttonCancel: 'Cancel',
  buttonCancelConversion: 'Cancel Conversion',
  buttonReset: 'Reset',
  buttonDownload: 'Download',
  
  // Post-processing
  postprocessingTitle: 'Post-processing Settings',
  confLabel: 'Confidence Threshold',
  nmsLabel: 'NMS Threshold (IOU)',
  
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

  // Preset Names
  preset256x256: '256×256',

  // Log Messages
  logConnecting: 'Connecting to WebSocket...',
  logConnected: 'WebSocket connected',
  logCompleted: '✅ Conversion completed',
  logFailed: '❌ Conversion failed: {error}',
  logError: 'Error: {message}',
  logWsError: 'WebSocket connection error',
  logWsClosed: 'WebSocket connection closed',
  logTaskCreated: 'Task created: {taskId}',
  logWelcome: 'Welcome to NE301 Model Converter',
  logUploadPrompt: 'Please upload a model file to begin',
  logClassesDetected: 'Detected {count} classes from YAML file',
  logDownloading: 'Downloading converted model...',
  logDownloaded: '✅ Downloaded: {filename}',
  logDownloadFailed: 'Download failed: {error}',
  logCancelling: 'Cancelling task...',
  logCancelled: 'Task cancelled',
  logCancelFailed: 'Cancellation failed: {error}',
  logErrorTitle: 'Error',

  // UI Text
  selected: '✓ Selected:',
  detectedClasses: 'Detected {count} classes',
  viewFullList: 'View full list',
  footerDesc: 'NE301 Model Converter - Convert deep learning models to embedded device formats',

  // Error Messages
  errorUploadFailed: 'Upload failed',
  errorDownloadFailed: 'Download failed',
  errorCancelFailed: 'Cancellation failed',
  errorUnknown: 'Unknown error',
  errorInvalidModelFormat: 'Invalid format. Supported: .pt, .pth, .onnx',
  errorModelTooLarge: 'Model too large. Maximum size: 500MB',
  errorInvalidYamlFormat: 'Invalid format. Supported: .yaml, .yml',
  errorYamlParseFailed: 'Failed to parse YAML file',
  errorInvalidZipFormat: 'Invalid format. Supported: .zip',

  // Setup Page
  setupTitle: 'NE301 Model Converter',
  setupSubtitle: 'Environment Setup Guide',
  setupChecking: 'Checking environment status...',
  setupReadyTitle: 'Environment Ready!',
  setupReadyDesc: 'All dependencies are installed. You can start converting models now.',
  setupBtnHome: 'Enter Home',
  setupBtnRecheck: 'Re-check',
  setupBtnChecking: 'Checking...',
  setupDockerMissingTitle: 'Docker Not Installed',
  setupDockerMissingDesc: 'This tool requires Docker to run conversion containers. Please follow the steps to install Docker:',
  setupMacStepsTitle: 'macOS Installation:',
  setupWinStepsTitle: 'Windows Installation:',
  setupLinuxStepsTitle: 'Linux Installation:',
  setupDockerSteps: [
    'Visit Docker Desktop official website',
    'Download the installer for your platform',
    'Install and start Docker Desktop',
    'Wait until Docker is fully running',
    'Click "Re-check" button below'
  ],
  setupPullingTitle: 'Pulling Tool Image...',
  setupPullingDesc: 'It requires pulling NE301 tool image for the first run. This may take several minutes depending on your network speed.',
  setupPullingNoteTitle: 'Notes:',
  setupPullingNotes: [
    'Image size is about 2-3 GB',
    'Do not close this page while pulling',
    'System will automatically detect when finished',
    'If failed, check network or use a mirror/registry mirror'
  ],
  setupPullingProgress: 'Pulling in background, please wait...',
  setupHelp: 'Need help? Check our',
  setupDocs: 'Documentation',
};

export type TranslationDict = typeof en;
