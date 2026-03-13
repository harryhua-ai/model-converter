import { cn } from './utils';
import { useI18nStore } from '../../store/i18n';

interface ProgressBarProps {
  progress: number;
  status: string;
  className?: string;
}

export function ProgressBar({ progress, status, className }: ProgressBarProps) {
  const { t } = useI18nStore();
  const clampedProgress = Math.min(100, Math.max(0, progress));

  // 定义步骤阈值
  const steps = [
    { label: t('step1Export') || 'Export TFLite', threshold: 0 },
    { label: t('step2Quantize') || 'Quantize Model', threshold: 30 },
    { label: t('step3Prepare') || 'Prepare NE301', threshold: 70 },
    { label: t('step4Build') || 'NE301 Build', threshold: 100 },
  ];

  return (
    <div class={cn('w-full', className)}>
      <div class="flex items-center justify-between mb-2">
        <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
          {t('progressTitle') || 'Conversion Progress'}
        </span>
        <span class="text-sm font-semibold text-primary-600 dark:text-primary-400">
          {clampedProgress}%
        </span>
      </div>

      <div class="w-full bg-gray-100 dark:bg-gray-700 rounded-full h-3 overflow-hidden relative">
        <div
          class={cn(
            'h-full transition-all duration-300 ease-out rounded-full relative',
            'bg-gradient-to-r from-primary-500 via-accent-500 to-primary-600',
            'shadow-lg'
          )}
          style={{ width: `${clampedProgress}%` }}
        >
          {/* 进度条高光 */}
          <div class="absolute right-0 top-0 bottom-0 w-1 bg-white/50 blur-[2px]" />
        </div>
      </div>

      {/* 步骤指示器 */}
      <div class="flex items-center justify-between mt-4 px-2">
        {steps.map((step) => {
          const isActive = clampedProgress >= step.threshold;
          const isCurrent = clampedProgress >= step.threshold && (step.threshold === 0 || clampedProgress < steps[steps.indexOf(step) + 1]?.threshold || 100);

          return (
            <div
              key={step.label}
              class={cn(
                'flex flex-col items-center gap-1 transition-all duration-300',
                isActive ? 'text-primary-600' : 'text-gray-400',
                isCurrent && 'scale-110'
              )}
            >
              <div
                class={cn(
                  'w-2 h-2 rounded-full transition-all duration-300',
                  isCurrent
                    ? 'bg-primary-500 scale-125 shadow-md shadow-primary-500/50'
                    : isActive
                    ? 'bg-primary-400'
                    : 'bg-gray-300'
                )}
              />
              <span class="text-xs font-medium">{step.label}</span>
            </div>
          );
        })}
      </div>

      <div class="mt-3 text-xs text-gray-600 dark:text-gray-400 text-center">
        {status}
      </div>
    </div>
  );
}
