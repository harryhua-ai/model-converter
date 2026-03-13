import { useState, useEffect, useRef } from 'preact/hooks';
import { useAppStore } from '../store/app';
import { modelApi, taskApi } from '../services/api';
import type { ConversionConfig } from '../types';

import { FileUploadArea } from '../components/upload/FileUploadArea';
import { CalibrationUploadArea } from '../components/upload/CalibrationUploadArea';
import { PresetCard } from '../components/presets/PresetCard';
import { CustomConfigForm } from '../components/presets/CustomConfigForm';
import { useToast } from '../components/ui/Toast';
import { cn } from '../utils/cn';
import i18n from '../i18n';
import {
  Settings,
  Settings2,
  Play,
  Download,
  Layout,
  Upload,
  CheckCircle2,
  AlertCircle,
  Terminal,
  Cpu,
  X as XIcon,
  Square
} from 'lucide-preact';

export default function HomePage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [calibrationFile, setCalibrationFile] = useState<File | null>(null);
  const [classYamlFile, setClassYamlFile] = useState<File | null>(null);
  
  // Configuration State
  const [activeTab, setActiveTab] = useState<'preset' | 'custom'>('preset');
  const [selectedPresetId, setSelectedPresetId] = useState<string>('yolov8n-256');
  const [logs, setLogs] = useState<string[]>([]);
  const logEndRef = useRef<HTMLDivElement>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const [config, setConfig] = useState<ConversionConfig | null>(null);
  const [customConfig, setCustomConfig] = useState<ConversionConfig | null>(null);
  
  const presets = useAppStore((state) => state.presets);
  const isLoadingPresets = useAppStore((state) => state.isLoadingPresets);
  const { success, error } = useToast();

  // Auto-scroll logs
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  // Clean up polling on unmount
  useEffect(() => {
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, []);

  const addLog = (message: string) => {
    const time = new Date().toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
    setLogs(prev => {
      const newLogs = [...prev, `[${time}] ${message}`];
      // Limit logs to 500 lines to prevent memory issues
      return newLogs.length > 500 ? newLogs.slice(-500) : newLogs;
    });
  };

  // 1. Initialize config with first preset
  useEffect(() => {
    if (presets.length > 0 && !config) {
      applyPreset(selectedPresetId || presets[0].id);
    }
  }, [presets, config]);

  // 2. Sync custom config if tab changes
  useEffect(() => {
     if (activeTab === 'custom' && !customConfig && presets.length > 0) {
       setCustomConfig(config || presets[0].config);
     }
  }, [activeTab, presets, config]);
  
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState('');
  const [isCompleted, setIsCompleted] = useState(false);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [taskStartTime, setTaskStartTime] = useState<number | null>(null); // Track task start time

  // Maximum task duration (30 minutes in milliseconds)
  const MAX_TASK_DURATION = 30 * 60 * 1000;

  // --- Handlers ---
  const handleModelSelect = (file: File) => {
    if (file.size > 500 * 1024 * 1024) {
      error(i18n.t('toast.file_too_large'));
      return;
    }
    setSelectedFile(file);
    success(i18n.t('toast.model_selected'));
  };

  const handleCalibSelect = (file: File) => {
    if (!file.name.endsWith('.zip')) {
      error(i18n.t('toast.calib_must_be_zip'));
      return;
    }
    if (file.size > 1024 * 1024 * 1024) {
      error(i18n.t('toast.calib_too_large'));
      return;
    }
    setCalibrationFile(file);
    success(i18n.t('toast.calib_selected'));
  };

  const applyPreset = (presetId: string) => {
    const preset = presets.find((p) => p.id === presetId);
    if (preset) {
      setConfig({
        ...preset.config,
        use_custom_calibration: !!calibrationFile,
        calibration_dataset_filename: calibrationFile?.name,
      });
      setSelectedPresetId(presetId);
    }
  };

  const handleCustomConfigChange = (newConfig: ConversionConfig) => {
    setCustomConfig(newConfig);
    setConfig({
      ...newConfig,
      use_custom_calibration: !!calibrationFile,
      calibration_dataset_filename: calibrationFile?.name,
    });
  };

  const handleSubmit = async () => {
    if (!selectedFile) {
      error(i18n.t('toast.error_no_model'));
      return;
    }
    if (!calibrationFile) {
      error('Please upload a calibration dataset (ZIP) — required for INT8 quantization');
      return;
    }
    if (!classYamlFile) {
      error('Please upload class config (data.yaml) — required for INT8 quantization accuracy');
      return;
    }
    if (!config) {
      error(i18n.t('toast.error_no_config'));
      return;
    }

    // Stop any existing polling
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }

    setIsUploading(true);
    setUploadProgress(0);
    setIsCompleted(false);
    setLogs([]);
    addLog('Uploading files to backend...');

    try {
      const finalConfig = {
        ...config,
        quantization_type: 'int8' as const,
        use_custom_calibration: true,
        calibration_dataset_filename: calibrationFile.name,
      };

      // Upload to real backend
      const response = await modelApi.uploadModel(
        selectedFile,
        finalConfig,
        calibrationFile ?? undefined,
        classYamlFile ?? undefined,
      );

      const newTaskId = response.task_id;
      setTaskId(newTaskId);
      setTaskStartTime(Date.now()); // Record task start time
      addLog(`Task created: ${newTaskId}`);
      addLog('Conversion started. Polling for progress...');
      setUploadStatus('Converting...');
      setUploadProgress(5);

      // Poll every 2 seconds with timeout protection
      let lastStep = '';
      pollingRef.current = setInterval(async () => {
        try {
          // Check if task has exceeded maximum duration
          if (taskStartTime && (Date.now() - taskStartTime > MAX_TASK_DURATION)) {
            clearInterval(pollingRef.current!);
            pollingRef.current = null;
            setIsUploading(false);
            addLog('✗ Task timed out (exceeded 30 minutes)');
            error('Task timed out. Please try again or contact support.');
            return;
          }

          const status = await taskApi.getTaskStatus(newTaskId);

          setUploadProgress(status.progress ?? 0);

          // Log new steps
          if (status.current_step && status.current_step !== lastStep) {
            lastStep = status.current_step;
            addLog(status.current_step);
            setUploadStatus(status.current_step);
          }

          if (status.status === 'completed') {
            clearInterval(pollingRef.current!);
            pollingRef.current = null;
            setIsCompleted(true);
            setIsUploading(false);
            setUploadStatus('');
            addLog('✓ Conversion completed successfully!');
            success('Conversion completed! Ready to download.');
          } else if (status.status === 'failed') {
            clearInterval(pollingRef.current!);
            pollingRef.current = null;
            setIsUploading(false);
            setUploadStatus('');
            const errMsg = status.error_message ?? 'Unknown error';
            addLog(`✗ Conversion failed: ${errMsg}`);
            error(`Conversion failed: ${errMsg}`);
          }
        } catch (pollErr) {
          addLog(`Polling error: ${pollErr instanceof Error ? pollErr.message : String(pollErr)}`);
        }
      }, 2000);

    } catch (err) {
      const msg = err instanceof Error ? err.message : i18n.t('toast.network_error');
      error(msg);
      addLog(`ERROR: ${msg}`);
      setIsUploading(false);
      setUploadStatus('');
    }
  };

  const handleDownload = async () => {
    if (!taskId) return;
    try {
      addLog('Downloading firmware package...');
      const blob = await modelApi.downloadConvertedModel(taskId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `ne301_${taskId.slice(0, 8)}.zip`;
      a.click();
      URL.revokeObjectURL(url);
      addLog('Download started.');
    } catch (err) {
      error(err instanceof Error ? err.message : 'Download failed');
    }
  };

  const handleStop = async () => {
    if (!taskId) return;

    try {
      addLog('Cancelling task...');
      await taskApi.cancelTask(taskId);
      addLog('Task cancelled successfully.');

      // Stop polling
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }

      setIsUploading(false);
      setUploadStatus('');
      success('Task cancelled');
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to cancel task';
      error(msg);
      addLog(`ERROR: ${msg}`);
    }
  };

  let currentStep = 1;
  if (selectedFile) currentStep = 2;
  if (selectedFile && calibrationFile) currentStep = 3;
  if (currentStep === 3 && config) currentStep = 4;

  return (
    <div className="min-h-screen bg-slate-50 selection:bg-[#ee5d35]/20 selection:text-slate-900 pb-20">
      
      {/* --- Minimalist Hero Section --- */}
      <div className="w-full bg-[#111] border-b border-[#222]">
        <div className="max-w-6xl mx-auto px-4 py-4 md:py-6 relative overflow-hidden">
          <div className="absolute top-0 right-0 p-4 md:p-6 opacity-10 pointer-events-none">
            <Cpu size={240} strokeWidth={0.5} className="text-white" />
          </div>
          
          <div className="relative z-10">
            <h1 className="text-2xl md:text-3xl font-black text-white tracking-tight mb-2 flex flex-wrap gap-2 items-center">
              {i18n.t('home.hero_title_1')}
              <span className="text-[#ee5d35] whitespace-nowrap">{i18n.t('home.hero_title_highlight')}</span>
              {i18n.t('home.hero_title_2')}
            </h1>
            
            <p className="text-xs md:text-sm text-slate-400 max-w-2xl leading-relaxed font-light">
              {i18n.t('home.hero_subtitle')}
            </p>
          </div>
        </div>
      </div>

      {/* --- Main Content Container --- */}
      <div className="max-w-[1600px] mx-auto px-4 -mt-4 relative z-20">
        
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 mb-8 items-stretch">
          
          {/* 1. Uploads Column (Model + Calibration) - 3/12 */}
          <div className="flex flex-col gap-6 xl:col-span-3">
            <FileUploadArea 
              onFileSelect={handleModelSelect}
              selectedFile={selectedFile}
              onRemove={() => { setSelectedFile(null); setConfig(null); }}
            />
            
            <CalibrationUploadArea 
              selectedFile={calibrationFile}
              onFileSelect={handleCalibSelect}
              onRemove={() => setCalibrationFile(null)}
            />
          </div>

          {/* 2. Configuration - Center (5/12) */}
          <div className="flex flex-col h-full xl:col-span-5">
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 md:p-8 flex flex-col h-full border-t-4 border-t-[#ee5d35]">
              <div className="flex flex-col gap-4 mb-6 border-b border-slate-100 pb-6 shrink-0">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-slate-900 flex items-center justify-center shrink-0">
                    <Settings className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-slate-900">{i18n.t('config.title')}</h3>
                    <p className="text-sm text-slate-500">{i18n.t('config.desc')}</p>
                  </div>
                </div>

                {/* Toggle preset vs custom */}
                <div className="flex w-full bg-slate-100 p-1 rounded-md border border-slate-200 relative z-30">
                  <button
                    onClick={() => { 
                      setActiveTab('preset'); 
                      const pId = selectedPresetId || (presets.length > 0 ? presets[0].id : 'yolov8n');
                      applyPreset(pId);
                    }}
                    className={cn(
                      "flex-1 justify-center px-4 py-2 text-sm font-bold rounded-md transition-all flex items-center gap-2",
                      activeTab === 'preset' ? "bg-white text-[#ee5d35] shadow-sm ring-1 ring-slate-200" : "text-slate-500 hover:text-slate-700"
                    )}
                  >
                    <Layout className="w-4 h-4" />
                    {i18n.t('config.preset_tab')}
                  </button>
                  <button
                    onClick={() => setActiveTab('custom')}
                    className={cn(
                      "flex-1 justify-center px-4 py-2 text-sm font-bold rounded-md transition-all flex items-center gap-2 border-0",
                      activeTab === 'custom' ? "bg-white text-[#ee5d35] shadow-sm ring-1 ring-slate-200" : "text-slate-500 hover:text-slate-700"
                    )}
                  >
                    <Settings2 className="w-4 h-4" />
                    {i18n.t('config.custom_tab')}
                  </button>
                </div>

                {/* Class Config (data.yaml) Upload - Integrated here! */}
                <div className="mt-2">
                   <label className="block cursor-pointer group">
                    <div
                      className={cn(
                        "border border-dashed rounded-lg p-3 transition-all",
                        classYamlFile
                          ? "border-emerald-400 bg-emerald-50/50"
                          : "border-slate-200 hover:border-emerald-300 hover:bg-emerald-50/20 bg-slate-50/30"
                      )}
                      onDragOver={(e) => e.preventDefault()}
                      onDrop={(e) => {
                        e.preventDefault();
                        const f = e.dataTransfer?.files[0];
                        if (f) setClassYamlFile(f);
                      }}
                    >
                      {classYamlFile ? (
                        <div className="flex items-center justify-between gap-3 text-emerald-700">
                          <div className="flex items-center gap-2 min-w-0">
                            <div className="w-8 h-8 rounded bg-emerald-100 flex items-center justify-center shrink-0">
                               <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                            </div>
                            <span className="text-xs font-bold truncate">{classYamlFile.name}</span>
                          </div>
                          <button
                            onClick={(e) => { e.preventDefault(); e.stopPropagation(); setClassYamlFile(null); }}
                            className="w-6 h-6 rounded-full hover:bg-red-50 text-slate-400 hover:text-red-500 transition-colors flex items-center justify-center shrink-0"
                          >
                            <XIcon size={14} />
                          </button>
                        </div>
                      ) : (
                        <div className="flex items-center justify-center gap-2 text-slate-400 py-1">
                          <Upload className="w-4 h-4 group-hover:text-emerald-500 transition-colors" />
                          <span className="text-xs font-semibold text-slate-500 group-hover:text-emerald-600 transition-colors">Upload dataset.yaml (Class Names)</span>
                        </div>
                      )}
                      <input
                        type="file"
                        accept=".yaml,.yml"
                        className="hidden"
                        onChange={(e) => {
                          const f = (e.target as HTMLInputElement).files?.[0];
                          if (f) setClassYamlFile(f);
                        }}
                      />
                    </div>
                  </label>
                </div>
              </div>

              {/* Config Mode Content */}
              <div className="flex-1 mt-6 relative">
                <div 
                  className={cn(
                    "grid grid-cols-1 gap-4 overflow-y-auto max-h-[500px] pr-2 custom-scrollbar transition-opacity duration-300",
                    activeTab === 'preset' ? "opacity-100 h-auto" : "opacity-0 h-0 pointer-events-none hidden"
                  )}
                >
                  {presets && presets.length > 0 ? (
                    presets.map((preset) => (
                      <div key={preset.id} className="animate-in fade-in slide-in-from-bottom-2 duration-300">
                        <PresetCard 
                          preset={preset}
                          isSelected={selectedPresetId === preset.id}
                          onClick={() => applyPreset(preset.id)}
                        />
                      </div>
                    ))
                  ) : (
                    <div className="flex flex-col items-center justify-center py-20 text-slate-400 italic text-sm gap-3">
                      <AlertCircle className="w-8 h-8 opacity-20" />
                      {isLoadingPresets ? 'Loading presets...' : 'No presets found.'}
                    </div>
                  )}
                </div>

                <div 
                  className={cn(
                    "transition-opacity duration-300",
                    activeTab === 'custom' ? "opacity-100 h-auto" : "opacity-0 h-0 pointer-events-none hidden"
                  )}
                >
                  <CustomConfigForm 
                    initialConfig={customConfig || undefined}
                    onChange={handleCustomConfigChange}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* 3. Execution & Summary - 4/12 */}
          <div className="flex flex-col h-full xl:col-span-4">
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 md:p-8 flex flex-col h-full bg-slate-50/30">
              <div className="flex items-center justify-between gap-3 mb-6 border-b border-slate-100 pb-6 shrink-0">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#ee5d35] to-orange-600 flex items-center justify-center shadow-inner">
                    <Play className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-slate-900">{i18n.t('actions.execute_task')}</h3>
                    <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold opacity-70">NE301 Core Conversion</p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {!isUploading ? (
                    <button
                      onClick={handleSubmit}
                      disabled={!selectedFile || !calibrationFile || !classYamlFile || !config || isUploading}
                      className="group relative flex items-center gap-2 px-4 py-2 bg-[#ee5d35] text-white rounded-lg font-bold text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-orange-600 transition-all shadow-md shadow-orange-500/20"
                    >
                      <div className="w-5 h-5 rounded-full bg-white/20 flex items-center justify-center group-hover:scale-110 transition-transform">
                        <Play className="w-3 h-3 text-white fill-current" />
                      </div>
                      <span className="tracking-wider uppercase">START</span>
                    </button>
                  ) : (
                    <>
                      <button
                        onClick={handleSubmit}
                        disabled
                        className="group relative flex items-center gap-2 px-4 py-2 bg-slate-700 text-white rounded-lg font-bold text-sm cursor-not-allowed"
                      >
                        <div className="animate-spin h-4 w-4 border-2 border-white/20 border-t-white rounded-full" />
                        <span className="animate-pulse">{uploadStatus || 'Processing...'}</span>
                      </button>

                      <button
                        onClick={handleStop}
                        className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg font-bold text-sm hover:bg-red-700 transition-all shadow-md"
                        title="Stop conversion"
                      >
                        <Square className="w-4 h-4 fill-current" />
                        <span className="tracking-wider uppercase">STOP</span>
                      </button>
                    </>
                  )}

                  {isCompleted && taskId && (
                    <button
                      onClick={handleDownload}
                      className="flex items-center gap-2 px-4 py-2 bg-slate-900 text-white rounded-lg font-bold text-sm hover:bg-black transition-all shadow-md animate-in slide-in-from-right-2 duration-300"
                    >
                      <Download className="w-4 h-4" />
                      <span className="tracking-wider uppercase">DOWNLOAD</span>
                    </button>
                  )}
                </div>
              </div>

              {/* Progress UI */}
              {isUploading && (
                <div className="mb-8 shrink-0 animate-in fade-in slide-in-from-top-2 duration-300">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">{i18n.t('tasks.progress')}</span>
                    <span className="text-sm font-mono font-bold text-[#ee5d35]">{uploadProgress}%</span>
                  </div>
                  <div className="w-full h-3 bg-slate-200 rounded-full overflow-hidden p-0.5 border border-slate-100">
                    <div 
                      className="h-full bg-gradient-to-r from-[#ee5d35] to-orange-400 rounded-full transition-all duration-300 ease-out" 
                      style={{ width: `${uploadProgress}%` }} 
                    />
                  </div>
                </div>
              )}

              {/* Logs area */}
              <div className="flex-1 flex flex-col min-h-0 bg-slate-900 rounded-xl border border-slate-800 shadow-2xl overflow-hidden ring-1 ring-white/5">
                <div className="flex items-center bg-slate-800/50 px-4 py-2 border-b border-slate-800 shrink-0">
                  <div className="flex gap-1.5 mr-4">
                    <div className="w-2.5 h-2.5 rounded-full bg-[#ee5d35]/30" />
                    <div className="w-2.5 h-2.5 rounded-full bg-[#ee5d35]/20" />
                    <div className="w-2.5 h-2.5 rounded-full bg-[#ee5d35]/10" />
                  </div>
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest font-mono flex items-center gap-2">
                    <Terminal className="w-3 h-3" />
                    CONVERTER_CORE_V1
                  </span>
                </div>

                <div className="flex-1 overflow-y-auto p-4 font-mono text-[11px] leading-relaxed custom-scrollbar max-h-[400px]">
                  {logs.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-slate-600 gap-3 opacity-50">
                      <Terminal className="w-10 h-10" />
                      <p className="font-bold tracking-tighter uppercase">Ready for Deployment</p>
                    </div>
                  ) : (
                    <div className="space-y-1.5">
                      {logs.map((msg, i) => (
                        <div key={i} className={cn(
                          "flex gap-3",
                          msg.includes('ERROR') || msg.includes('✗') ? "text-red-400" :
                          msg.includes('✓') || msg.includes('success') ? "text-emerald-400" : "text-slate-300"
                        )}>
                          <span className="opacity-30 select-none whitespace-nowrap shrink-0">[{i+1}]</span>
                          <span className="break-all">{msg}</span>
                        </div>
                      ))}
                      <div ref={logEndRef} />
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
