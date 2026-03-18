import { X, StopCircle } from 'lucide-preact';
import { cn } from './utils';
import { useI18nStore } from '../../store/i18n';

interface CancelButtonProps {
  onCancel: () => void;
  isCancelling?: boolean;
  className?: string;
}

export function CancelButton({
  onCancel,
  isCancelling = false,
  className
}: CancelButtonProps) {
  const { t } = useI18nStore();

  return (
    <button
      onClick={onCancel}
      disabled={isCancelling}
      class={cn(
        'group relative inline-flex items-center justify-center gap-2',
        'px-6 py-3 rounded-lg font-semibold text-sm',
        'transition-all duration-200 ease-in-out',
        'focus:outline-none focus:ring-2 focus:ring-offset-2',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        'bg-red-500 hover:bg-red-600 active:bg-red-700',
        'text-white shadow-md hover:shadow-lg',
        'focus:ring-red-500 dark:focus:ring-offset-gray-900',
        className
      )}
    >
      {isCancelling ? (
        <>
          <div class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          <span>{t('cancelling')}</span>
        </>
      ) : (
        <>
          <StopCircle class="w-5 h-5 transition-transform group-hover:scale-110" />
          <span>{t('cancelConversion')}</span>
        </>
      )}

      <div class="absolute inset-0 rounded-lg ring-2 ring-white/20 group-hover:ring-white/40 transition-all duration-200 pointer-events-none" />
    </button>
  );
}
