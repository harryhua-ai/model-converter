import { useEffect } from 'preact/hooks';
import { Router } from 'preact-router';
import { useAppStore } from './store/app';

import HomePage from './pages/HomePage';
import TaskListPage from './pages/TaskListPage';
import TaskDetailPage from './pages/TaskDetailPage';
import { ToastProvider } from './components/ui/Toast';
import i18n, { type Language } from './i18n';
import './styles/index.css';

function App() {
  const { fetchPresets, fetchTasks, language, setLanguage } = useAppStore();

  useEffect(() => {
    // 初始加载基础数据
    fetchPresets();
    fetchTasks();
  }, [fetchPresets, fetchTasks]);

  // 定期刷新任务列表（简单的轮询机制，后续可改为 WebSocket）
  useEffect(() => {
    const interval = setInterval(() => {
      fetchTasks();
    }, 5000);
    return () => clearInterval(interval);
  }, [fetchTasks]);

  return (
    <ToastProvider>
    <div className="min-h-screen bg-white">
      {/* 顶部导航栏 */}
      <header className="border-b border-slate-200">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-bold tracking-tight text-slate-900 border-l-4 border-[#ee5d35] pl-3">
              {i18n.t('app.title')}
            </h1>
            <nav className="flex items-center gap-6">
              <a
                href="/"
                className="text-sm font-medium hover:text-[#ee5d35] transition-colors"
                onClick={(e) => {
                  e.preventDefault();
                  window.location.href = '/';
                }}
              >
                {i18n.t('app.workbench')}
              </a>
              <a
                href="/tasks"
                className="text-sm font-medium hover:text-[#ee5d35] transition-colors text-slate-600"
                onClick={(e) => {
                  e.preventDefault();
                  window.location.href = '/tasks';
                }}
              >
                {i18n.t('app.deployments')}
              </a>
              {/* Language Switcher */}
              <div className="flex items-center bg-slate-100 rounded-md p-0.5 border border-slate-200">
                <button
                  onClick={() => setLanguage('en')}
                  className={`px-2 py-1 text-xs font-bold rounded-sm transition-colors ${language === 'en' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
                >
                  EN
                </button>
                <button
                  onClick={() => setLanguage('zh')}
                  className={`px-2 py-1 text-xs font-bold rounded-sm transition-colors ${language === 'zh' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
                >
                  中简
                </button>
              </div>
            </nav>
          </div>
        </div>
      </header>

      {/* 路由内容区 */}
      <main className="flex-1">
        <Router>
          <HomePage path="/" />
          <TaskListPage path="/tasks" />
          <TaskDetailPage path="/tasks/:taskId" />
        </Router>
      </main>

      {/* 页脚 */}
      <footer className="border-t mt-auto">
        <div className="container mx-auto px-4 py-6 text-center text-sm text-slate-500">
          <p>{i18n.t('app.footer')}</p>
        </div>
      </footer>
    </div>
    </ToastProvider>
  );
}

export default App;
