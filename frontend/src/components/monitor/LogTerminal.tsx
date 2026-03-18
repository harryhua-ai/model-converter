import { useEffect, useRef } from 'preact/hooks';
import { cn } from './utils';
import { FileText } from 'lucide-preact';
import { useI18nStore } from '../../store/i18n';

interface LogTerminalProps {
  logs: string[];
  className?: string;
}

export function LogTerminal({ logs, className }: LogTerminalProps) {
  const { t } = useI18nStore();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div
      className={cn(
        'w-full flex flex-col rounded-xl overflow-hidden',
        'bg-gradient-to-br from-gray-900 to-gray-950',
        'border border-gray-700 dark:border-gray-800',
        'shadow-2xl',
        className
      )}
    >
      {/* 终端头部 */}
      <div className="px-4 py-3 bg-gradient-to-r from-gray-800 to-gray-850 border-b border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* macOS 风格窗口控制 */}
            <div className="flex gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500 hover:bg-red-400 transition-colors cursor-pointer" />
              <div className="w-3 h-3 rounded-full bg-yellow-500 hover:bg-yellow-400 transition-colors cursor-pointer" />
              <div className="w-3 h-3 rounded-full bg-green-500 hover:bg-green-400 transition-colors cursor-pointer" />
            </div>
            <span className="text-xs font-mono text-gray-400">{t('terminalTitle')}</span>
          </div>

          {/* 导出按钮 */}
          <button className="text-xs text-primary-400 hover:text-primary-300 flex items-center gap-1.5 px-2 py-1 rounded hover:bg-white/5 transition-colors">
            <FileText className="w-3.5 h-3.5" />
            {t('exportLogs')}
          </button>
        </div>
      </div>

      {/* 日志内容 */}
      <div
        ref={scrollRef}
        className="flex-1 min-h-[16rem] overflow-y-auto p-4 font-mono text-sm custom-scrollbar"
      >
        {logs.length === 0 ? (
          <div className="text-gray-500 dark:text-gray-600 italic animate-pulse">
            {t('waitingLogs')}
          </div>
        ) : (
          <div className="space-y-1">
            {logs.map((log, index) => (
              <div
                key={index}
                className="group flex items-start gap-3 text-gray-300 hover:text-gray-200 transition-colors animate-slide-up"
                style={{ animationDelay: `${index * 20}ms` }}
              >
                {/* 行号 */}
                <span className="flex-shrink-0 w-8 text-right text-gray-600 font-mono text-xs select-none">
                  {String(index + 1).padStart(3, '0')}
                </span>

                {/* 日志内容 */}
                <span className="flex-1 break-words">
                  {log.includes('错误') || log.includes('失败') || log.includes('Error') || log.includes('Failed') ? (
                    <span className="text-error-400">{log}</span>
                  ) : log.includes('完成') || log.includes('成功') || log.includes('Completed') || log.includes('Success') ? (
                    <span className="text-success-400">{log}</span>
                  ) : log.includes('警告') || log.includes('Warning') ? (
                    <span className="text-warning-400">{log}</span>
                  ) : (
                    <span>{log}</span>
                  )}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 底部状态栏 */}
      <div className="px-4 py-2 bg-gradient-to-r from-gray-800 to-gray-850 border-t border-gray-700 flex items-center justify-between text-xs">
        <span className="text-gray-500 font-mono">
          {t('totalLogs')} <span className="text-primary-400 font-semibold">{logs.length}</span>
        </span>
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${logs.length > 0 ? 'bg-success-500 animate-pulse' : 'bg-gray-600'}`} />
          <span className="text-gray-500">{logs.length > 0 ? t('runningStatus') : t('idleStatus')}</span>
        </div>
      </div>
    </div>
  );
}
