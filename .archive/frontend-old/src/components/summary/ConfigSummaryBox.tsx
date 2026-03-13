import type { ConversionConfig } from '../../types';
import i18n from '../../i18n';

interface ConfigSummaryBoxProps {
  config: ConversionConfig;
}

export function ConfigSummaryBox({ config }: ConfigSummaryBoxProps) {
  return (
    <div className="bg-slate-900 rounded-xl shadow-lg border border-slate-800 p-6 md:p-8 mt-6">
      <div className="flex items-center gap-3 mb-6">
        <svg className="w-6 h-6 text-[#ee5d35]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
        </svg>
        <h3 className="text-xl font-bold text-white">{i18n.t('config.summary_title')}</h3>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6 bg-slate-800/50 p-6 rounded-lg border border-slate-700">
        <div className="space-y-1">
          <p className="text-xs text-slate-400 font-medium tracking-wide">{i18n.t('config.model_name')}</p>
          <p className="text-sm font-semibold text-slate-200">{config.model_name || '--'}</p>
        </div>
        <div className="space-y-1">
          <p className="text-xs text-slate-400 font-medium tracking-wide">{i18n.t('config.model_type')}</p>
          <p className="text-sm font-semibold text-slate-200">{config.model_type}</p>
        </div>
        <div className="space-y-1">
          <p className="text-xs text-slate-400 font-medium tracking-wide">{i18n.t('config.input_width').split(' ')[0]} / {i18n.t('config.input_height').split(' ')[0]}</p>
          <p className="text-sm font-semibold text-slate-200">
            {config.input_width} × {config.input_height}
          </p>
        </div>
        <div className="space-y-1">
          <p className="text-xs text-slate-400 font-medium tracking-wide">{i18n.t('config.quant_type')}</p>
          <div className="inline-flex items-center px-2 py-0.5 mt-0.5 text-xs font-bold rounded bg-[#ee5d35]/20 text-[#ee5d35] border border-[#ee5d35]/30">
            {config.quantization_type}
          </div>
        </div>
        <div className="space-y-1">
          <p className="text-xs text-slate-400 font-medium tracking-wide">{i18n.t('config.num_classes')}</p>
          <p className="text-sm font-semibold text-slate-200">{config.num_classes}</p>
        </div>
        <div className="space-y-1">
          <p className="text-xs text-slate-400 font-medium tracking-wide">{i18n.t('config.conf_thresh')}</p>
          <p className="text-sm font-semibold text-slate-200">{config.confidence_threshold}</p>
        </div>
        <div className="space-y-1 col-span-2">
          <p className="text-xs text-slate-400 font-medium tracking-wide">{i18n.t('config.calib_dataset')}</p>
          <p className="text-sm font-semibold text-slate-200 truncate">
            {config.calibration_dataset_filename || i18n.t('config.default_calib')}
          </p>
        </div>
      </div>
    </div>
  );
}
