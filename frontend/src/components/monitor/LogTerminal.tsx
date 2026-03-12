import { useEffect, useRef } from 'preact/hooks';
import { cn } from './utils';

interface LogTerminalProps {
  logs: string[];
  className?: string;
}

export function LogTerminal({ logs, className }: LogTerminalProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div
      class={cn(
        'w-full bg-gray-900 dark:bg-gray-950 rounded-lg',
        'border border-gray-700 dark:border-gray-800',
        'shadow-inner overflow-hidden',
        className
      )}
    >
      <div class="px-4 py-2 bg-gray-800 dark:bg-gray-900 border-b border-gray-700">
        <div class="flex items-center gap-2">
          <div class="flex gap-1.5">
            <div class="w-3 h-3 rounded-full bg-red-500" />
            <div class="w-3 h-3 rounded-full bg-yellow-500" />
            <div class="w-3 h-3 rounded-full bg-green-500" />
          </div>
          <span class="text-xs font-mono text-gray-400 ml-2">转换日志</span>
        </div>
      </div>

      <div
        ref={scrollRef}
        class="h-64 overflow-y-auto p-4 font-mono text-sm"
      >
        {logs.length === 0 ? (
          <div class="text-gray-500 dark:text-gray-600 italic">
            等待日志输出...
          </div>
        ) : (
          <div class="space-y-1">
            {logs.map((log, index) => (
              <div
                key={index}
                class="text-gray-300 dark:text-gray-400 whitespace-pre-wrap break-words"
              >
                <span class="text-gray-500 dark:text-gray-600 mr-2">
                  [{String(index + 1).padStart(3, '0')}]
                </span>
                {log}
              </div>
            ))}
          </div>
        )}
      </div>

      <div class="px-4 py-2 bg-gray-800 dark:bg-gray-900 border-t border-gray-700 text-xs text-gray-500 font-mono">
        共 {logs.length} 条日志
      </div>
    </div>
  );
}
