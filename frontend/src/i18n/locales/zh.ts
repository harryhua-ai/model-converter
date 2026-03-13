import type { TranslationDict } from './en';

export const zh: TranslationDict = {
  // General Header & Titles
  title: 'NE301 模型转换器',
  subtitle: '将 PyTorch/ONNX 模型转换为 NE301 格式',
  
  // Steps
  step1Title: '上传模型文件',
  step2Title: '类别定义文件（可选）',
  step3Title: '校准数据集（可选）',
  step3Desc: '上传校准图片集可提高量化精度',
  
  // Settings & Actions
  modeLabel: '模式 (MODE)',
  presetFast: '快速转换',
  presetBalanced: '平衡模式',
  presetHighAccuracy: '高精度模式',
  classesLabel: '类别数',
  buttonStart: '开始',
  buttonCancel: '取消',
  buttonReset: '重置',
  buttonDownload: '下载',
  
  // Monitor & Logs
  progressTitle: '进度',
  errorTitle: '转换失败',
  terminalTitle: '转换日志',
  exportLogs: '导出',
  waitingLogs: '等待日志输出...',
  totalLogs: '共',
  runningStatus: '运行中',
  idleStatus: '待机',
  
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
};
