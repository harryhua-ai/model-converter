import { useState, useEffect } from 'preact/hooks';
import type { ConversionConfig } from '../../types';
import i18n from '../../i18n';

interface CustomConfigFormProps {
  initialConfig?: ConversionConfig;
  onChange: (config: ConversionConfig) => void;
}

export function CustomConfigForm({ initialConfig, onChange }: CustomConfigFormProps) {
  const [localConfig, setLocalConfig] = useState<ConversionConfig>({
    model_name: initialConfig?.model_name || 'custom_model',
    model_type: initialConfig?.model_type || 'YOLOv8',
    input_width: initialConfig?.input_width || 640,
    input_height: initialConfig?.input_height || 640,
    quantization_type: initialConfig?.quantization_type || 'int8',
    num_classes: initialConfig?.num_classes || 80,
    confidence_threshold: initialConfig?.confidence_threshold || 0.25,
    use_custom_calibration: initialConfig?.use_custom_calibration || false,
  });

  // Notify parent only when localConfig changes, but avoid loops
  useEffect(() => {
    const timer = setTimeout(() => {
      onChange(localConfig);
    }, 100);
    return () => clearTimeout(timer);
  }, [localConfig]);

  const handleChange = (e: Event) => {
    const target = e.target as HTMLInputElement | HTMLSelectElement;
    const { name, value, type } = target;
    
    let parsedValue: string | number | boolean = value;
    
    if (type === 'number') {
      parsedValue = value === '' ? 0 : Number(value);
    }

    setLocalConfig(prev => ({
      ...prev,
      [name]: parsedValue
    }));
  };

  return (
    <div className="bg-white p-6 rounded-lg border border-slate-200">
      <h4 className="text-sm font-bold text-slate-800 mb-4 border-b border-slate-100 pb-2">{i18n.t('config.custom_title')}</h4>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Model Name */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-600">{i18n.t('config.model_name')}</label>
          <input
            type="text"
            name="model_name"
            value={localConfig.model_name}
            onChange={handleChange}
            className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-[#ee5d35] focus:border-[#ee5d35]"
            placeholder={i18n.t('config.model_name_placeholder')}
          />
        </div>

        {/* Model Type */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-600">{i18n.t('config.model_type')}</label>
          <select
            name="model_type"
            value={localConfig.model_type}
            onChange={handleChange}
            className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-[#ee5d35] focus:border-[#ee5d35]"
          >
            <option value="YOLOv8">YOLOv8 (Ultralytics)</option>
            <option value="YOLOX">YOLOX Nano</option>
          </select>
        </div>

        {/* Input Width & Height */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-600">{i18n.t('config.input_width')}</label>
            <input
              type="number"
              name="input_width"
              value={localConfig.input_width}
              onChange={handleChange}
              min="32"
              step="32"
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-[#ee5d35] focus:border-[#ee5d35]"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-600">{i18n.t('config.input_height')}</label>
            <input
              type="number"
              name="input_height"
              value={localConfig.input_height}
              onChange={handleChange}
              min="32"
              step="32"
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-[#ee5d35] focus:border-[#ee5d35]"
            />
          </div>
        </div>


        {/* Num Classes */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-600">{i18n.t('config.num_classes')}</label>
          <input
            type="number"
            name="num_classes"
            value={localConfig.num_classes}
            onChange={handleChange}
            min="1"
            max="1000"
            className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-[#ee5d35] focus:border-[#ee5d35]"
          />
        </div>

        {/* Confidence Threshold */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-600">{i18n.t('config.conf_thresh')}</label>
          <div className="flex items-center gap-3">
             <input
              type="range"
              name="confidence_threshold"
              value={localConfig.confidence_threshold}
              onChange={handleChange}
              min="0.01"
              max="0.99"
              step="0.01"
              className="flex-1 accent-[#ee5d35]"
            />
            <span className="text-xs font-mono bg-slate-100 px-2 py-1 rounded border border-slate-200 min-w-[3rem] text-center">
              {localConfig.confidence_threshold}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
