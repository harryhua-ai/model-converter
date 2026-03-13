import { useEffect, useState } from 'preact/hooks';
import { route } from 'preact-router';
import { useAppStore } from '../store/app';
import { taskApi, modelApi, type TaskStatus } from '../services/api';
import { cn } from '../utils/cn';
import i18n from '../i18n';

interface TaskDetailPageProps {
  taskId?: string;
}

export default function TaskDetailPage({ taskId }: TaskDetailPageProps) {
  const [task, setTask] = useState<TaskStatus | null>(null);
  const tasks = useAppStore((state) => state.tasks);

  useEffect(() => {
    if (!taskId) return;
    
    // Attempt to find in local store
    const localTask = tasks.find(t => t.task_id === taskId);
    if (localTask) {
      setTask(localTask);
    } else {
      // Fallback fetch
      taskApi.getTaskStatus(taskId).then(setTask);
    }
  }, [taskId, tasks]);

  if (!task) {
     return <div className="p-12 text-center text-slate-500 animate-pulse">{i18n.t('tasks.loading')}</div>;
  }

  const isDone = task.status === 'completed';
  const isFailed = task.status === 'failed';

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 md:py-12">
      <button
        onClick={() => route('/tasks')}
        className="flex items-center gap-2 text-sm text-slate-500 hover:text-slate-900 mb-8 transition-colors"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
        </svg>
        {i18n.t('tasks.back_to_list')}
      </button>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className={cn(
          "p-6 md:p-8 border-b border-slate-200 text-white",
          isDone ? "bg-green-600" : isFailed ? "bg-red-600" : "bg-slate-900"
        )}>
           <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold mb-1">{task.task_id.slice(0, 8)} {i18n.t('tasks.unknown_model')}</h2>
                <div className="flex items-center gap-3 text-sm opacity-90 font-mono">
                  <span>ID: {task.task_id}</span>
                  <span>•</span>
                  <span className="uppercase">{task.status}</span>
                </div>
              </div>
              <div className="text-4xl font-black opacity-20">{task.progress}%</div>
           </div>
        </div>

        <div className="p-6 md:p-8">
          <div className="mb-8">
            <div className="flex justify-between text-sm mb-2 font-bold text-slate-700">
               <span>{i18n.t('tasks.progress')}</span>
               <span>{task.progress}%</span>
            </div>
            <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden">
              <div 
                className={cn(
                  "h-full rounded-full transition-all duration-500",
                  isDone ? "bg-green-500" : isFailed ? "bg-red-500" : "bg-[#ee5d35]"
                )}
                style={{ width: `${task.progress}%` }}
              />
            </div>
            {task.current_step && (
              <p className="mt-3 text-sm text-slate-600 bg-slate-50 p-3 rounded-md font-mono">
                &gt; {task.current_step}
              </p>
            )}
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 mb-8 pt-8 border-t border-slate-100">
             <div>
                <p className="text-xs font-semibold text-slate-400 mb-1">{i18n.t('config.model_type')}</p>
                <p className="text-sm font-bold text-slate-900">—</p>
             </div>
             <div>
                <p className="text-xs font-semibold text-slate-400 mb-1">{i18n.t('config.quant_type')}</p>
                <p className="text-sm font-bold text-slate-900 uppercase">int8</p>
             </div>
             <div>
                <p className="text-xs font-semibold text-slate-400 mb-1">{i18n.t('config.input_width').split(' ')[0]}</p>
                <p className="text-sm font-bold text-slate-900">—</p>
             </div>
             <div>
                <p className="text-xs font-semibold text-slate-400 mb-1">{i18n.t('tasks.created_at')}</p>
                <p className="text-sm font-bold text-slate-900">{new Date(task.created_at).toLocaleTimeString()}</p>
             </div>
          </div>

          {isDone && (
            <div className="pt-8 border-t border-slate-100 flex justify-end">
               <button 
                 onClick={() => {
                   // Mock download invocation
                   modelApi.downloadConvertedModel(task.task_id);
                 }}
                 className="flex items-center gap-2 px-6 py-3 bg-[#ee5d35] text-white rounded-lg font-bold hover:bg-orange-600 transition-colors shadow-lg shadow-orange-500/20"
               >
                 <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                 下载部署包 (NE301)
               </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
