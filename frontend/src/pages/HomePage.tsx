import { useEffect } from 'preact/hooks';
import { Play, Download, RefreshCw, FileText } from 'lucide-preact';
import ModelUploadArea from '../components/upload/ModelUploadArea';
import ClassYamlUploadArea from '../components/upload/ClassYamlUploadArea';
import CalibrationUploadArea from '../components/upload/CalibrationUploadArea';
import { ProgressBar } from '../components/monitor/ProgressBar';
import { LogTerminal } from '../components/monitor/LogTerminal';
import { CancelButton } from '../components/monitor/CancelButton';
import { useAppStore } from '../store/app';
import { useI18nStore } from '../store/i18n';
import { useConversion } from '../hooks/useConversion';
import { LanguageSwitcher } from '../components/ui/LanguageSwitcher';
import { downloadFile } from '../utils/helpers';

interface Preset {
  id: string;
  name: string;
  size: number;
  description: string;
}

/**
 * 预设配置列表（针对 NE301 优化）
 *
 * NE301 推荐配置：
 * - 256x256: 最佳平衡点，适合大多数应用场景
 */
const PRESETS: Preset[] = [
  {
    id: '256x256',
    name: '256*256',
    size: 256,
    description: 'Recommended for NE301'
  },
];

export default function HomePage() {
  const {
    selectedFile,
    selectedYaml,
    selectedCalibration,
    selectedPreset,
    numClasses,
    classList,
    confidenceThreshold,
    iouThreshold,
    conversionStatus,
    currentTask,
    showLogs,
    setSelectedFile,
    setSelectedYaml,
    setSelectedCalibration,
    setSelectedPreset,
    setNumClasses,
    setClassList,
    setConfidenceThreshold,
    setIouThreshold,
    setConversionStatus,
    setCurrentTask,
    getConfig,
    reset,
  } = useAppStore();

  const { t } = useI18nStore();

  const { state, startConversion, cancelConversion, downloadResult, addLog } =
    useConversion();

  // Sync hook state to store
  useEffect(() => {
    if (state.status && state.status !== conversionStatus) {
      setConversionStatus(state.status);
      // NOTE: taskId is string, store expects ConversionTask object or handle accordingly
      // For now we just sync status, or we could update store to allow ID
    }
  }, [state.status, state.taskId]);

  // 初始化日志
  useEffect(() => {
    addLog(t('logWelcome'));
    addLog(t('logUploadPrompt'));
  }, [addLog, t]);

  // 处理类别检测（从 YAML 文件）
  const handleClassDetected = (numClasses: number, names: string[]) => {
    setNumClasses(numClasses);
    setClassList(names);
    addLog(t('logClassesDetected', { count: numClasses }));
  };

  // Handle start conversion
  const handleStartConversion = async () => {
    if (!selectedFile) {
      addLog(t('errorNoModel'));
      return;
    }

    if (numClasses <= 0) {
      addLog(t('errorNoClasses'));
      return;
    }

    const config = getConfig();

    try {
      await startConversion(
        selectedFile,
        config,
        selectedYaml || undefined,
        selectedCalibration || undefined
      );
    } catch (error) {
      // Error is already handled in useConversion hook
    }
  };

  // Handle download
  const handleDownload = async () => {
    try {
      await downloadResult();
    } catch (error) {
      // Error is already handled in downloadResult
    }
  };

  // 处理重置
  const handleReset = () => {
    reset();
    addLog(t('buttonReset'));
  };

  // 是否可以开始转换
  const canStart = selectedFile !== null && !state.isConverting;

  // 是否显示下载按钮
  const showDownload = conversionStatus === 'completed';

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-purple-50/20 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-100 dark:border-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              {/* Logo */}
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 shadow-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">N</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 dark:from-white dark:to-gray-200 bg-clip-text text-transparent">
                  {t('title')}
                </h1>
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  {t('subtitle')}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <LanguageSwitcher />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-8 items-start">
          {/* Left Column: Upload Steps */}
          <div className="lg:col-span-1 space-y-6">
            {/* Step 1: Upload Model */}
            <section className="card p-6 lg:p-8 hover:shadow-card-hover transition-shadow duration-300 border border-gray-100 dark:border-gray-800">
              <div className="flex items-center gap-3 mb-4">
                <div className="step-indicator bg-gradient-to-br from-primary-500 to-primary-600 shadow-sm">
                  1
                </div>
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {t('step1Title')}
                </h2>
              </div>
              <ModelUploadArea
                onFileSelect={setSelectedFile}
                selectedFile={selectedFile || undefined}
              />
            </section>

            {/* Step 2: Upload YAML (Optional) */}
            <section className="card p-6 lg:p-8 hover:shadow-card-hover transition-shadow duration-300 border border-gray-100 dark:border-gray-800">
              <div className="flex items-center gap-3 mb-4">
                <div className="step-indicator bg-gradient-to-br from-primary-500 to-primary-600 shadow-sm">
                  2
                </div>
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {t('step2Title')}
                </h2>
              </div>
              <ClassYamlUploadArea
                onFileSelect={setSelectedYaml}
                selectedFile={selectedYaml || undefined}
                onClassDetected={handleClassDetected}
              />
            </section>

            {/* Step 3: Upload Calibration Dataset (Optional) */}
            <section className="card p-6 lg:p-8 hover:shadow-card-hover transition-shadow duration-300 border border-gray-100 dark:border-gray-800">
              <div className="flex items-center gap-3 mb-4">
                <div className="step-indicator bg-gradient-to-br from-primary-500 to-primary-600 shadow-sm">
                  3
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                    {t('step3Title')}
                  </h2>
                </div>
              </div>
              <CalibrationUploadArea
                onFileSelect={setSelectedCalibration}
              />
              {selectedCalibration && (
                <div className="mt-3 text-sm text-success-600 dark:text-success-400">
                  {t('selected')} {selectedCalibration.name} ({(selectedCalibration.size / 1024 / 1024).toFixed(2)}MB)
                </div>
              )}
            </section>
          </div>

          {/* Right Column: Configuration, Actions & Logs */}
          <div className="lg:col-span-2 flex flex-col space-y-6 h-[calc(100vh-180px)] min-h-[600px]">
            {/* Top Toolbar: Mode, Classes, Actions */}
            <section className="card p-5 border border-gray-100 dark:border-gray-800 flex flex-wrap items-end justify-between gap-4 hover:shadow-card-hover transition-shadow duration-300">
              <div className="flex gap-4 flex-wrap flex-1 items-end">
                {/* Mode Select */}
                <div className="min-w-[140px] flex-1 sm:flex-none">
                  <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1.5 uppercase tracking-wider">{t('modeLabel')}</label>
                  <select
                    value={selectedPreset}
                    onChange={(e) => setSelectedPreset(e.currentTarget.value)}
                    disabled={state.isConverting}
                    className="w-full px-4 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent text-gray-900 dark:text-white font-medium transition-colors"
                  >
                    {PRESETS.map((p) => (
                      <option key={p.id} value={p.id}>{t('preset256x256')}</option>
                    ))}
                  </select>
                </div>

                {/* Classes */}
                <div className="w-24 flex-none">
                  <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1.5 uppercase tracking-wider">{t('classesLabel')}</label>
                  <input
                    type="number"
                    min="1"
                    max="1000"
                    value={numClasses}
                    onChange={(e) => setNumClasses(parseInt(e.currentTarget.value) || 80)}
                    disabled={state.isConverting}
                    className="w-full px-4 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent text-gray-900 dark:text-white font-medium transition-colors"
                  />
                </div>
              </div>

              {/* Actions */}
            <div className="flex flex-wrap items-center gap-3">
              {canStart && (
                <button onClick={handleStartConversion} disabled={!canStart} className="btn-primary py-2 px-6">
                  <Play className="w-4 h-4 mr-1.5" /> 
                  <span>{t('buttonStart')}</span>
                </button>
              )}

              {state.isConverting && (
                <CancelButton onCancel={cancelConversion} isCancelling={state.isCancelling} />
              )}

              {(conversionStatus !== 'idle' || state.logs.length > 0) && !state.isConverting && (
                <button onClick={handleReset} className="btn-secondary py-2 px-6">
                  <RefreshCw className="w-4 h-4 mr-1.5" /> 
                  <span>{t('buttonReset')}</span>
                </button>
              )}

              {showDownload && (
                <button onClick={handleDownload} className="btn-success py-2 px-6">
                  <Download className="w-4 h-4 mr-1.5" /> 
                  <span>{t('buttonDownload')}</span>
                </button>
              )}
            </div>
          </section>

          {/* Post-processing Config Panel */}
          <section className="card p-6 flex-shrink-0">
            <h3 className="text-sm font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <RefreshCw className="w-4 h-4 text-primary-500" />
              {t('postprocessingTitle')}
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Confidence Threshold */}
              <div>
                <div className="flex justify-between mb-2">
                  <label className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">{t('confLabel')}</label>
                  <span className="text-xs font-bold text-primary-600">{(confidenceThreshold * 100).toFixed(0)}%</span>
                </div>
                <input
                  type="range"
                  min="0.01"
                  max="0.99"
                  step="0.01"
                  value={confidenceThreshold}
                  onChange={(e) => setConfidenceThreshold(parseFloat(e.currentTarget.value))}
                  disabled={state.isConverting}
                  className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-primary-500"
                />
                <div className="flex justify-between mt-1 px-0.5">
                  <span className="text-[10px] text-gray-400">0.01</span>
                  <span className="text-[10px] text-gray-400">0.99</span>
                </div>
              </div>

              {/* IOU Threshold */}
              <div>
                <div className="flex justify-between mb-2">
                  <label className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">{t('nmsLabel')}</label>
                  <span className="text-xs font-bold text-primary-600">{(iouThreshold * 100).toFixed(0)}%</span>
                </div>
                <input
                  type="range"
                  min="0.01"
                  max="0.99"
                  step="0.01"
                  value={iouThreshold}
                  onChange={(e) => setIouThreshold(parseFloat(e.currentTarget.value))}
                  disabled={state.isConverting}
                  className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-primary-500"
                />
                <div className="flex justify-between mt-1 px-0.5">
                  <span className="text-[10px] text-gray-400">0.01</span>
                  <span className="text-[10px] text-gray-400">0.99</span>
                </div>
              </div>
            </div>
          </section>

          {/* Error Message */}
          {state.error && (
            <section className="bg-error-50 dark:bg-error-950/20 border-l-4 border-error-500 rounded-xl p-4 animate-slide-up flex-shrink-0">
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0">
                  <div className="w-6 h-6 rounded-full bg-error-500 flex items-center justify-center">
                    <svg
                      className="w-3.5 h-3.5 text-white"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M6 18L18 6M6 6l12 12"
                      />
                    </svg>
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-bold text-error-800 dark:text-error-400 mb-0.5">
                    {t('errorTitle')}
                  </h4>
                  <p className="text-sm text-error-700 dark:text-error-300">
                    {state.error}
                  </p>
                </div>
              </div>
            </section>
          )}

          {/* Progress Bar - Removed per user request */}

          {/* Log Terminal area */}
          <div className="flex-1 min-h-0 flex">
            <LogTerminal logs={state.logs} className="h-full" />
          </div>
        </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="mt-8 py-6 bg-transparent border-t border-transparent">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-sm text-gray-500 dark:text-gray-500">
          <p>{t('footerDesc')}</p>
        </div>
      </footer>
    </div>
  );
}
