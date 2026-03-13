import { CheckCircle } from 'lucide-preact';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export interface Preset {
  id: string;
  name: string;
  size: number;
  description: string;
}

interface PresetCardProps {
  preset: Preset;
  selected: boolean;
  onSelect: () => void;
}

export function PresetCard({ preset, selected, onSelect }: PresetCardProps) {
  const cardClass = twMerge(
    clsx(
      'relative p-6 rounded-xl border-2 cursor-pointer transition-all duration-300 animate-fade-in',
      selected
        ? 'border-primary-500 bg-gradient-to-br from-primary-50 to-accent-50 shadow-md hover:shadow-lg'
        : 'border-gray-200 hover:border-primary-300 hover:scale-[1.02]'
    )
  );

  const sizeBadgeClass = twMerge(
    clsx(
      'inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium transition-all duration-300',
      selected
        ? 'bg-gradient-to-r from-primary-500 to-primary-600 text-white shadow-md'
        : 'bg-gray-100 hover:bg-primary-100'
    )
  );

  return (
    <div onClick={onSelect} className={cardClass}>
      {/* Selection Indicator */}
      {selected && (
        <div className="absolute top-4 right-4 w-8 h-8 rounded-full bg-gradient-to-br from-success-500 to-success-600 shadow-lg flex items-center justify-center animate-scale-in">
          <CheckCircle className="w-5 h-5 text-white" />
        </div>
      )}

      {/* Preset Name */}
      <h3 className="text-xl font-semibold text-gray-900 mb-2">
        {preset.name}
      </h3>

      {/* Preset Size Badge */}
      <div className="mb-3">
        <span className={sizeBadgeClass}>
          <span className="w-2 h-2 rounded-full bg-current animate-pulse-slow" />
          {preset.size}x{preset.size}
        </span>
      </div>

      {/* Preset Description */}
      <p className="text-gray-600 text-sm leading-relaxed">
        {preset.description}
      </p>

      {/* Selected Badge with Bottom Decoration */}
      {selected && (
        <div className="mt-4 animate-slide-up">
          <div className="flex items-center gap-2 text-sm font-medium text-primary-600">
            <div className="flex-1 h-0.5 bg-gradient-to-r from-primary-500 to-transparent" />
            <span>已选择</span>
            <div className="flex-1 h-0.5 bg-gradient-to-l from-primary-500 to-transparent" />
          </div>
        </div>
      )}
    </div>
  );
}
