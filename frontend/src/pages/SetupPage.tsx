import { useState, useEffect } from 'preact/hooks';
import { route } from 'preact-router';
import { useI18nStore } from '../store/i18n';

interface EnvStatus {
  docker_installed: boolean;
  image_pulled: boolean;
  ready: boolean;
}

interface SetupPageProps {
  checkInterval?: number;
}

export default function SetupPage({ checkInterval = 3000 }: SetupPageProps) {
  const { t } = useI18nStore();
  const [status, setStatus] = useState<EnvStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const checkEnvironment = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch('/api/setup/check');
      if (!response.ok) {
        throw new Error(t('errorUnknown'));
      }
      const data = await response.json();
      setStatus(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('errorUnknown'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkEnvironment();
  }, []);

  // 自动轮询检查环境状态
  useEffect(() => {
    if (status && !status.ready) {
      const timer = setInterval(checkEnvironment, checkInterval);
      return () => clearInterval(timer);
    }
  }, [status, checkInterval]);

  const renderDockerInstallGuide = () => {
    const platform = navigator.platform.toLowerCase();
    const isMac = platform.includes('mac');
    const isWindows = platform.includes('win');
    const isLinux = !isMac && !isWindows;

    return (
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center">
          <svg className="w-6 h-6 mr-2 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          {t('setupDockerMissingTitle')}
        </h2>
        <p className="text-gray-600 mb-4">
          {t('setupDockerMissingDesc')}
        </p>

        {isMac && (
          <div className="bg-blue-50 border-l-4 border-blue-500 p-4 mb-4">
            <h3 className="font-semibold text-blue-800 mb-2">{t('setupMacStepsTitle')}</h3>
            <ol className="list-decimal list-inside space-y-2 text-blue-700">
              {(t('setupDockerSteps') as unknown as string[]).map((step, idx) => (
                <li key={idx}>{step}</li>
              ))}
            </ol>
          </div>
        )}

        {isWindows && (
          <div className="bg-blue-50 border-l-4 border-blue-500 p-4 mb-4">
            <h3 className="font-semibold text-blue-800 mb-2">{t('setupWinStepsTitle')}</h3>
            <ol className="list-decimal list-inside space-y-2 text-blue-700">
              {(t('setupDockerSteps') as unknown as string[]).map((step, idx) => (
                <li key={idx}>{step}</li>
              ))}
            </ol>
          </div>
        )}

        {isLinux && (
          <div className="bg-blue-50 border-l-4 border-blue-500 p-4 mb-4">
            <h3 className="font-semibold text-blue-800 mb-2">{t('setupLinuxStepsTitle')}</h3>
            <ol className="list-decimal list-inside space-y-2 text-blue-700">
              <li>Open your terminal and run matching commands:</li>
              <li className="ml-4">Ubuntu/Debian:
                <code className="block bg-gray-800 text-white p-2 rounded mt-2 text-sm overflow-x-auto">
                  sudo apt-get update<br/>
                  sudo apt-get install docker-ce docker-ce-cli containerd.io
                </code>
              </li>
              <li className="ml-4">CentOS/RHEL:
                <code className="block bg-gray-800 text-white p-2 rounded mt-2 text-sm overflow-x-auto">
                  sudo yum install docker-ce docker-ce-cli containerd.io
                </code>
              </li>
            </ol>
          </div>
        )}
      </div>
    );
  };

  const renderImagePullGuide = () => (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center">
        <svg className="w-6 h-6 mr-2 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        {t('setupPullingTitle')}
      </h2>
      <p className="text-gray-600 mb-4">
        {t('setupPullingDesc')}
      </p>
      <div className="bg-yellow-50 border-l-4 border-yellow-500 p-4 mb-4">
        <h3 className="font-semibold text-yellow-800 mb-2">{t('setupPullingNoteTitle')}</h3>
        <ul className="list-disc list-inside space-y-1 text-yellow-700">
          {(t('setupPullingNotes') as unknown as string[]).map((note, idx) => (
            <li key={idx}>{note}</li>
          ))}
        </ul>
      </div>
      <div className="bg-gray-50 rounded-lg p-4">
        <div className="flex items-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mr-3"></div>
          <span className="text-gray-700">{t('setupPullingProgress')}</span>
        </div>
      </div>
    </div>
  );

  const renderReady = () => (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center">
        <svg className="w-6 h-6 mr-2 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        {t('setupReadyTitle')}
      </h2>
      <p className="text-gray-600 mb-6">
        {t('setupReadyDesc')}
      </p>
      <div className="flex gap-4">
        <button
          onClick={() => route('/')}
          className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg transition duration-200 flex items-center justify-center"
        >
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
          </svg>
          {t('setupBtnHome')}
        </button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-extrabold text-gray-900 sm:text-5xl sm:tracking-tight lg:text-6xl">
            {t('setupTitle')}
          </h1>
          <p className="mt-4 text-xl text-gray-600">
            {t('setupSubtitle')}
          </p>
        </div>

        {error && (
          <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-6">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            </div>
          </div>
        )}

        {loading && !status && (
          <div className="bg-white rounded-lg shadow-md p-12 mb-6 flex flex-col items-center justify-center">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mb-4"></div>
            <p className="text-gray-600">{t('setupChecking')}</p>
          </div>
        )}

        {status && !status.docker_installed && renderDockerInstallGuide()}
        {status && status.docker_installed && !status.image_pulled && renderImagePullGuide()}
        {status && status.ready && renderReady()}

        {status && !status.ready && (
          <div className="flex justify-center">
            <button
              onClick={checkEnvironment}
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-bold py-3 px-8 rounded-lg transition duration-200 flex items-center"
            >
              <svg className={`w-5 h-5 mr-2 ${loading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              {loading ? t('setupBtnChecking') : t('setupBtnRecheck')}
            </button>
          </div>
        )}

        <div className="mt-8 text-center text-gray-500 text-sm">
          <p>{t('setupHelp')} <a href="https://github.com/yourusername/model-converter" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">{t('setupDocs')}</a></p>
        </div>
      </div>
    </div>
  );
}
