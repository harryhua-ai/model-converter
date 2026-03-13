import type { ConfigPreset } from '../../types';
import { cn } from '../../utils/cn';
import { CheckCircle2 } from 'lucide-preact';

interface PresetCardProps {
  preset: ConfigPreset;
  isSelected: boolean;
  onClick: () => void;
}

export function PresetCard({ preset, isSelected, onClick }: PresetCardProps) {
  return (
    <div
      onClick={onClick}
      className={cn(
        "relative p-5 rounded-lg border cursor-pointer transition-all duration-200 bg-white group hover:shadow-md overflow-hidden",
        isSelected
          ? "border-[#ee5d35] shadow-md ring-1 ring-[#ee5d35]"
          : "border-slate-200 hover:border-slate-300"
      )}
    >
      {/* 选中高亮边带 */}
      <div 
        className={cn(
          "absolute left-0 top-0 bottom-0 w-1 transition-colors duration-200",
          isSelected ? "bg-[#ee5d35]" : "bg-transparent group-hover:bg-slate-200"
        )} 
      />

      <div className="pl-2">
        <div className="flex items-start justify-between mb-2">
          <h4 className="font-bold text-slate-900">{preset.name}</h4>
          {isSelected && (
            <div className="w-5 h-5 rounded-full bg-[#ee5d35] flex items-center justify-center shrink-0">
              <CheckCircle2 className="w-3 h-3 text-white" />
            </div>
          )}
        </div>
        
        <p className="text-sm text-slate-500 line-clamp-2 mb-4 h-10">
          {preset.description}
        </p>
        
        <div className="flex flex-wrap gap-2">
          <span className="px-2 py-1 bg-slate-100 text-slate-700 text-xs font-mono rounded">
            {preset.config.input_width}×{preset.config.input_height}
          </span>
          <span className="px-2 py-1 bg-slate-100 text-slate-700 text-xs font-medium rounded">
            {preset.config.model_type}
          </span>
          <span className={cn(
            "px-2 py-1 text-xs font-bold rounded border",
            preset.config.quantization_type === 'int8' 
              ? "bg-orange-50 text-[#ee5d35] border-orange-200"
              : "bg-slate-50 text-slate-600 border-slate-200"
          )}>
            {preset.config.quantization_type}
          </span>
        </div>
      </div>
    </div>
  );
}
