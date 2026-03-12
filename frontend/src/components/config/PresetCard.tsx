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
      'relative p-6 rounded-lg border-2 cursor-pointer transition-all duration-200',
      'hover:shadow-md',
      selected
        ? 'border-primary bg-primary/5'
        : 'border-gray-200 hover:border-primary/50'
    )
  );

  return (
    <div onClick={onSelect} className={cardClass}>
      {/* Selection Indicator */}
      {selected && (
        <div className="absolute top-4 right-4 text-primary">
          <CheckCircle className="w-6 h-6" />
        </div>
      )}

      {/* Preset Name */}
      <h3 className="text-xl font-semibold text-gray-900 mb-2">
        {preset.name}
      </h3>

      {/* Preset Size */}
      <div className="mb-3">
        <span className="inline-block px-3 py-1 bg-primary/10 text-primary rounded-full text-sm font-medium">
          {preset.size}x{preset.size}
        </span>
      </div>

      {/* Preset Description */}
      <p className="text-gray-600 text-sm leading-relaxed">
        {preset.description}
      </p>

      {/* Selected Badge */}
      {selected && (
        <div className="mt-4 text-sm font-medium text-primary">
          已选择
        </div>
      )}
    </div>
  );
}
