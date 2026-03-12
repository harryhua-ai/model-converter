import { cn } from './utils';

interface ProgressBarProps {
  progress: number;
  status: string;
  className?: string;
}

export function ProgressBar({ progress, status, className }: ProgressBarProps) {
  const clampedProgress = Math.min(100, Math.max(0, progress));

  return (
    <div class={cn('w-full', className)}>
      <div class="flex items-center justify-between mb-2">
        <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
          转换进度
        </span>
        <span class="text-sm font-semibold text-indigo-600 dark:text-indigo-400">
          {clampedProgress}%
        </span>
      </div>

      <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 overflow-hidden">
        <div
          class={cn(
            'h-full transition-all duration-300 ease-out rounded-full',
            'bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500',
            'shadow-lg'
          )}
          style={{ width: `${clampedProgress}%` }}
        />
      </div>

      <div class="mt-2 text-xs text-gray-600 dark:text-gray-400 text-center">
        {status}
      </div>
    </div>
  );
}
