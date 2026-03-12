import { useEffect } from 'preact/hooks';
import { Play, Download, RefreshCw, FileText } from 'lucide-preact';
import ModelUploadArea from '../components/upload/ModelUploadArea';
import ClassYamlUploadArea from '../components/upload/ClassYamlUploadArea';
import CalibrationUploadArea from '../components/upload/CalibrationUploadArea';
import { PresetCard, Preset } from '../components/config/PresetCard';
import { ProgressBar } from '../components/monitor/ProgressBar';
import { LogTerminal } from '../components/monitor/LogTerminal';
import { CancelButton } from '../components/monitor/CancelButton';
import { useAppStore } from '../store/app';
import { useConversion } from '../hooks/useConversion';
import { useWebSocket } from '../hooks/useWebSocket';
import { downloadFile } from '../utils/helpers';

/**
 * 预设配置列表
 */
const PRESETS: Preset[] = [
  {
    id: 'fast',
    name: '快速转换',
    size: 256,
    description: '最快的转换速度，适合快速验证。模型精度略低，文件大小较小。',
  },
  {
    id: 'balanced',
    name: '平衡模式',
    size: 480,
    description: '速度与精度的最佳平衡。推荐大多数场景使用，兼顾性能和准确度。',
  },
  {
    id: 'high_accuracy',
    name: '高精度模式',
    size: 640,
    description: '最高精度，适合对准确度要求高的场景。转换时间较长，模型文件较大。',
  },
];

export default function HomePage() {
  const {
    selectedFile,
    selectedYaml,
    selectedCalibration,
    selectedPreset,
    numClasses,
    conversionStatus,
    currentTask,
    showLogs,
    setSelectedFile,
    setSelectedYaml,
    setSelectedCalibration,
    setSelectedPreset,
    setNumClasses,
    setConversionStatus,
    setCurrentTask,
    getConfig,
    reset,
  } = useAppStore();

  const { state, startConversion, cancelConversion, downloadResult, addLog } =
    useConversion();

  // WebSocket 连接
  const { isConnected } = useWebSocket(currentTask?.task_id ?? null, {
    onProgress: (progress, step) => {
      // 进度更新在 useConversion 中通过轮询处理
    },
    onLog: (log) => {
      addLog(log);
    },
    onStatusChange: (status) => {
      setConversionStatus(
        status as 'idle' | 'converting' | 'completed' | 'failed'
      );
    },
    onError: (error) => {
      addLog(`错误: ${error}`);
    },
    onComplete: () => {
      setConversionStatus('completed');
      addLog('转换完成!');
    },
  });

  // 初始化日志
  useEffect(() => {
    addLog('欢迎使用 NE301 模型转换器');
    addLog('请上传模型文件开始转换');
  }, []);

  // 处理类别检测（从 YAML 文件）
  const handleClassDetected = (numClasses: number, names: string[]) => {
    setNumClasses(numClasses);
    addLog(`从 YAML 文件识别到 ${numClasses} 个类别`);
  };

  // 处理开始转换
  const handleStartConversion = async () => {
    if (!selectedFile) {
      addLog('错误: 请先选择模型文件');
      return;
    }

    if (numClasses <= 0) {
      addLog('错误: 类别数必须大于 0');
      return;
    }

    const config = getConfig();
    await startConversion(
      selectedFile,
      config,
      selectedYaml || undefined,
      selectedCalibration || undefined
    );
  };

  // 处理下载
  const handleDownload = async () => {
    try {
      await downloadResult();
    } catch (error) {
      console.error('下载失败:', error);
    }
  };

  // 处理重置
  const handleReset = () => {
    reset();
    addLog('已重置');
  };

  // 是否可以开始转换
  const canStart = selectedFile !== null && !state.isConverting;

  // 是否显示下载按钮
  const showDownload = conversionStatus === 'completed';

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                NE301 模型转换器
              </h1>
              <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                将 PyTorch/ONNX 模型转换为 NE301 格式
              </p>
            </div>
            <div className="flex items-center gap-2">
              <div
                className={`w-3 h-3 rounded-full ${
                  isConnected ? 'bg-green-500' : 'bg-red-500'
                }`}
              />
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {isConnected ? '已连接' : '未连接'}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column: Upload and Configuration */}
          <div className="lg:col-span-2 space-y-6">
            {/* Step 1: Upload Model */}
            <section className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center font-bold">
                  1
                </div>
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  上传模型文件
                </h2>
              </div>
              <ModelUploadArea
                onFileSelect={setSelectedFile}
                selectedFile={selectedFile || undefined}
              />
            </section>

            {/* Step 2: Upload YAML (Optional) */}
            <section className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center font-bold">
                  2
                </div>
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  上传类别定义文件（可选）
                </h2>
              </div>
              <ClassYamlUploadArea
                onFileSelect={setSelectedYaml}
                selectedFile={selectedYaml || undefined}
                onClassDetected={handleClassDetected}
              />
            </section>

            {/* Step 2.5: Upload Calibration Dataset (Optional) */}
            <section className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-8 h-8 bg-orange-500 text-white rounded-full flex items-center justify-center font-bold">
                  2.5
                </div>
                <div>
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                    上传校准数据集（可选）
                  </h2>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    上传校准图片集可提高量化精度
                  </p>
                </div>
              </div>
              <CalibrationUploadArea
                onFileSelect={setSelectedCalibration}
              />
              {selectedCalibration && (
                <div className="mt-3 text-sm text-green-600 dark:text-green-400">
                  ✓ 已选择: {selectedCalibration.name} ({(selectedCalibration.size / 1024 / 1024).toFixed(2)}MB)
                </div>
              )}
            </section>

            {/* Step 3: Select Preset */}
            <section className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center font-bold">
                  3
                </div>
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  选择转换预设
                </h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                {PRESETS.map((preset) => (
                  <PresetCard
                    key={preset.id}
                    preset={preset}
                    selected={selectedPreset === preset.id}
                    onSelect={() => setSelectedPreset(preset.id)}
                  />
                ))}
              </div>

              {/* Number of Classes */}
              <div className="mt-6">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  类别数量
                </label>
                <input
                  type="number"
                  min="1"
                  max="1000"
                  value={numClasses}
                  onChange={(e) =>
                    setNumClasses(parseInt(e.currentTarget.value) || 80)
                  }
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                  disabled={state.isConverting}
                />
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  模型输出的类别数（例如 COCO 数据集为 80）
                </p>
              </div>
            </section>

            {/* Action Buttons */}
            <section className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
              <div className="flex flex-wrap gap-4">
                {canStart && (
                  <button
                    onClick={handleStartConversion}
                    disabled={!canStart}
                    className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold rounded-lg transition-colors"
                  >
                    <Play className="w-5 h-5" />
                    开始转换
                  </button>
                )}

                {state.isConverting && (
                  <CancelButton
                    onCancel={cancelConversion}
                    isCancelling={state.isCancelling}
                  />
                )}

                {showDownload && (
                  <button
                    onClick={handleDownload}
                    className="inline-flex items-center gap-2 px-6 py-3 bg-green-600 hover:bg-green-700 text-white font-semibold rounded-lg transition-colors"
                  >
                    <Download className="w-5 h-5" />
                    下载模型
                  </button>
                )}

                {(conversionStatus !== 'idle' || state.logs.length > 0) && (
                  <button
                    onClick={handleReset}
                    className="inline-flex items-center gap-2 px-6 py-3 bg-gray-600 hover:bg-gray-700 text-white font-semibold rounded-lg transition-colors"
                  >
                    <RefreshCw className="w-5 h-5" />
                    重置
                  </button>
                )}
              </div>
            </section>
          </div>

          {/* Right Column: Progress and Logs */}
          <div className="space-y-6">
            {/* Progress Bar */}
            {state.isConverting && (
              <section className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  转换进度
                </h3>
                <ProgressBar
                  progress={state.progress}
                  status={state.currentStep}
                />
              </section>
            )}

            {/* Error Message */}
            {state.error && (
              <section className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0">
                    <svg
                      className="w-6 h-6 text-red-600 dark:text-red-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-red-800 dark:text-red-400 mb-1">
                      转换失败
                    </h4>
                    <p className="text-sm text-red-700 dark:text-red-300">
                      {state.error}
                    </p>
                  </div>
                </div>
              </section>
            )}

            {/* Log Terminal */}
            <section className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  转换日志
                </h3>
                <button
                  onClick={() => {
                    // 可以添加清空日志的功能
                  }}
                  className="text-sm text-blue-600 hover:text-blue-700"
                >
                  <FileText className="w-4 h-4 inline mr-1" />
                  导出
                </button>
              </div>
              <LogTerminal logs={state.logs} />
            </section>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="mt-12 py-6 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-sm text-gray-600 dark:text-gray-400">
          <p>NE301 Model Converter - 将深度学习模型转换为嵌入式设备格式</p>
        </div>
      </footer>
    </div>
  );
}
