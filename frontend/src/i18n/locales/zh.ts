import type { TranslationDict } from './en';

export const zh: TranslationDict = {
  // General Header & Titles
  title: 'NE301 模型转换器',
  subtitle: '将 PyTorch/ONNX 模型转换为 NE301 格式',
  
  // Steps
  step1Title: '上传模型文件',
  step2Title: '类别定义文件',
  step2Desc: '上传 YAML 文件可以自动识别类别数量和名称',
  step3Title: '校准数据集',
  step3Desc: '上传校准图片集可提高量化精度',
  
  // Settings & Actions
  modeLabel: '模式 (MODE)',
  presetFast: '快速转换',
  presetBalanced: '平衡模式',
  presetHighAccuracy: '高精度模式',
  classesLabel: '类别数',
  buttonStart: '开始',
  buttonCancel: '取消',
  buttonCancelConversion: '取消转换',
  buttonReset: '重置',
  buttonDownload: '下载',
  
  // Post-processing
  postprocessingTitle: '后处理设置',
  confLabel: '置信度阈值',
  nmsLabel: 'NMS 阈值 (IOU)',
  
  // Monitor & Logs
  progressTitle: '进度',
  errorTitle: '转换失败',
  terminalTitle: '转换日志',
  exportLogs: '导出',
  waitingLogs: '等待日志输出...',
  totalLogs: '共',
  runningStatus: '运行中',
  idleStatus: '待机',

  // Progress Steps
  step1Export: '转换 TFLite',
  step2Quantize: '量化模型',
  step3Prepare: '准备 NE301',
  step4Build: 'NE301 编译打包',
  
  // Messages and Notifications
  welcomeMsg: '欢迎使用 NE301 模型转换器',
  uploadPrompt: '请上传模型文件开始转换',
  errorNoModel: '错误: 请先选择模型文件',
  errorNoClasses: '错误: 类别数必须大于 0',
  errorClassDetected: '从 YAML 文件识别到 {count} 个类别',
  
  // File Upload Area
  dragDropModel: '拖拽模型文件到此处，或',
  supportFormatModel: '支持 .pt, .onnx, .h5 格式',
  fileSelected: '已选择:',
  changeFile: '更改文件',
  browseFile: '点击上传',
  dragDropYaml: '拖拽类别配置文件到此处，或',
  supportFormatYaml: '支持 .yaml, .yml 格式',
  detectingClasses: '正在识别类别...',
  dragDropZip: '拖拽图片数据集到此处，或',
  supportFormatZip: '支持 .zip, .tar.gz 格式',

  // Preset Names
  preset256x256: '256×256',

  // Log Messages
  logConnecting: '正在连接 WebSocket...',
  logConnected: 'WebSocket 已连接',
  logCompleted: '✅ 转换完成',
  logFailed: '❌ 转换失败: {error}',
  logError: '错误: {message}',
  logWsError: 'WebSocket 连接错误',
  logWsClosed: 'WebSocket 连接关闭',
  logTaskCreated: '任务已创建: {taskId}',
  logWelcome: '欢迎使用 NE301 模型转换器',
  logUploadPrompt: '请上传模型文件开始转换',
  logClassesDetected: '从 YAML 文件识别到 {count} 个类别',
  logDownloading: '正在下载转换后的模型...',
  logDownloaded: '✅ 已下载: {filename}',
  logDownloadFailed: '下载失败: {error}',
  logCancelling: '正在取消任务...',
  logCancelled: '任务已取消',
  logCancelFailed: '取消失败: {error}',
  logErrorTitle: '错误',

  // UI Text
  selected: '✓ 已选择:',
  detectedClasses: '已识别 {count} 个类别',
  viewFullList: '查看完整列表',
  footerDesc: 'NE301 模型转换器 - 将深度学习模型转换为嵌入式设备格式',

  // Error Messages
  errorUploadFailed: '上传失败',
  errorDownloadFailed: '下载失败',
  errorCancelFailed: '取消失败',
  errorUnknown: '未知错误',
  errorInvalidModelFormat: '文件格式不支持。请上传 .pt、.pth 或 .onnx 文件。',
  errorModelTooLarge: '文件大小超过限制。最大支持 500MB。',
  errorInvalidYamlFormat: '文件格式不支持。请上传 .yaml 或 .yml 文件。',
  errorYamlParseFailed: 'YAML 解析失败',
  errorInvalidZipFormat: '文件格式不支持。请上传 .zip 文件。',

  // Setup Page
  setupTitle: 'NE301 模型转换器',
  setupSubtitle: '环境设置向导',
  setupChecking: '正在检测环境状态...',
  setupReadyTitle: '环境就绪！',
  setupReadyDesc: '所有依赖已安装完成，您可以开始使用模型转换工具。',
  setupBtnHome: '进入首页',
  setupBtnRecheck: '重新检测',
  setupBtnChecking: '检测中...',
  setupDockerMissingTitle: 'Docker 未安装',
  setupDockerMissingDesc: '本工具需要 Docker 来运行模型转换容器。请按照以下步骤安装 Docker：',
  setupMacStepsTitle: 'macOS 安装步骤：',
  setupWinStepsTitle: 'Windows 安装步骤：',
  setupLinuxStepsTitle: 'Linux 安装步骤：',
  setupDockerSteps: [
    '访问 Docker Desktop 官网',
    '下载对应平台的安装包',
    '安装并启动 Docker Desktop',
    '等待 Docker 完全启动',
    '点击下方“重新检测”按钮'
  ],
  setupPullingTitle: '正在拉取工具镜像...',
  setupPullingDesc: '首次使用需要拉取 NE301 转换组件镜像。这可能需要几分钟时间，取决于您的网络速度。',
  setupPullingNoteTitle: '注意事项：',
  setupPullingNotes: [
    '镜像大小约 2-3 GB',
    '拉取期间请勿关闭此页面',
    '系统会自动检测完成状态',
    '如果失败，请检查网络或使用镜像加速器'
  ],
  setupPullingProgress: '正在后台自动拉取镜像，请稍候...',
  setupHelp: '需要帮助？请查看',
  setupDocs: '项目文档',
};
