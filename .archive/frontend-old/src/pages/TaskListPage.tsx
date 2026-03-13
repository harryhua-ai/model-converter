import { useAppStore } from '../store/app';
import { route } from 'preact-router';
import { type TaskStatus } from '../services/api';
import { cn } from '../utils/cn';
import i18n from '../i18n';

export default function TaskListPage() {
  const tasks = useAppStore((state) => state.tasks);

  const getStatusDisplay = (status: TaskStatus['status']) => {
    switch (status) {
      case 'completed':
        return { label: i18n.t('tasks.status_completed'), className: 'text-green-600 bg-green-50 border-green-200' };
      case 'failed':
        return { label: i18n.t('tasks.status_failed'), className: 'text-red-600 bg-red-50 border-red-200' };
      case 'converting':
        return { label: i18n.t('tasks.status_converting'), className: 'text-[#ee5d35] bg-orange-50 border-orange-200' };
      default:
        return { label: i18n.t('tasks.status_pending'), className: 'text-slate-600 bg-slate-50 border-slate-200' };
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 md:py-12">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-black text-slate-900 tracking-tight">{i18n.t('tasks.title')}</h2>
          <p className="text-slate-500 mt-1">{i18n.t('tasks.subtitle')}</p>
        </div>
        <button
          onClick={() => route('/')}
          className="flex items-center gap-2 px-4 py-2 bg-slate-900 text-white rounded-md text-sm font-semibold hover:bg-slate-800 transition-colors"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          {i18n.t('tasks.new_task')}
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        {tasks.length === 0 ? (
           <div className="p-12 text-center text-slate-500">
             <p>{i18n.t('tasks.empty')}</p>
           </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {tasks.map((task) => {
              const statusInfo = getStatusDisplay(task.status);
              return (
                <div 
                  key={task.task_id} 
                  className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 hover:bg-slate-50 transition-colors cursor-pointer"
                  onClick={() => route(`/tasks/${task.task_id}`)}
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="font-bold text-slate-900">{task.task_id.slice(0, 8)} {i18n.t('tasks.unknown_model')}</span>
                      <span className={cn("px-2.5 py-0.5 text-xs font-bold rounded border", statusInfo.className)}>
                        {statusInfo.label}
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-4 text-xs text-slate-500">
                      <span className="font-mono bg-slate-100 px-1.5 py-0.5 rounded">ID: {task.task_id.substring(0, 8)}...</span>
                      <span>{new Date(task.created_at).toLocaleString()}</span>
                      <span>{task.current_step || task.status}</span>
                    </div>
                  </div>
                  
                  <div className="w-full sm:w-48 shrink-0">
                    <div className="flex justify-between text-xs mb-1 font-medium">
                      <span className="text-slate-600">{i18n.t('tasks.progress')}</span>
                      <span className={task.status === 'converting' ? 'text-[#ee5d35]' : 'text-slate-900'}>{task.progress}%</span>
                    </div>
                    <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div 
                        className={cn(
                          "h-full rounded-full transition-all duration-500",
                          task.status === 'completed' ? "bg-green-500" : task.status === 'failed' ? "bg-red-500" : "bg-[#ee5d35]"
                        )}
                        style={{ width: `${task.progress}%` }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
