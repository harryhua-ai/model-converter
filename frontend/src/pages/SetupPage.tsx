import { useState, useEffect } from 'preact/hooks';
import { route } from 'preact-router';

interface EnvStatus {
  docker_installed: boolean;
  image_pulled: boolean;
  ready: boolean;
}

interface SetupPageProps {
  checkInterval?: number;
}

export default function SetupPage({ checkInterval = 3000 }: SetupPageProps) {
  const [status, setStatus] = useState<EnvStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const checkEnvironment = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch('/api/setup/check');
      if (!response.ok) {
        throw new Error('环境检测失败');
      }
      const data = await response.json();
      setStatus(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '未知错误');
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
      <div class="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 class="text-2xl font-bold text-gray-800 mb-4 flex items-center">
          <svg class="w-6 h-6 mr-2 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          Docker 未安装
        </h2>
        <p class="text-gray-600 mb-4">
          本工具需要 Docker 来运行模型转换容器。请按照以下步骤安装 Docker：
        </p>

        {isMac && (
          <div class="bg-blue-50 border-l-4 border-blue-500 p-4 mb-4">
            <h3 class="font-semibold text-blue-800 mb-2">macOS 安装步骤：</h3>
            <ol class="list-decimal list-inside space-y-2 text-blue-700">
              <li>访问 <a href="https://www.docker.com/products/docker-desktop/" target="_blank" rel="noopener noreferrer" class="text-blue-600 underline hover:text-blue-800">Docker Desktop 官网</a></li>
              <li>下载 macOS 版本的 Docker Desktop</li>
              <li>打开下载的 .dmg 文件并拖拽到 Applications 文件夹</li>
              <li>启动 Docker Desktop（首次启动会要求管理员权限）</li>
              <li>等待 Docker 完全启动（菜单栏图标停止闪烁）</li>
              <li>点击下方"重新检测"按钮</li>
            </ol>
          </div>
        )}

        {isWindows && (
          <div class="bg-blue-50 border-l-4 border-blue-500 p-4 mb-4">
            <h3 class="font-semibold text-blue-800 mb-2">Windows 安装步骤：</h3>
            <ol class="list-decimal list-inside space-y-2 text-blue-700">
              <li>访问 <a href="https://www.docker.com/products/docker-desktop/" target="_blank" rel="noopener noreferrer" class="text-blue-600 underline hover:text-blue-800">Docker Desktop 官网</a></li>
              <li>下载 Windows 版本的 Docker Desktop</li>
              <li>运行安装程序并按照提示完成安装</li>
              <li>重启电脑（如果需要）</li>
              <li>启动 Docker Desktop</li>
              <li>等待 Docker 完全启动（系统托盘图标显示运行中）</li>
              <li>点击下方"重新检测"按钮</li>
            </ol>
          </div>
        )}

        {isLinux && (
          <div class="bg-blue-50 border-l-4 border-blue-500 p-4 mb-4">
            <h3 class="font-semibold text-blue-800 mb-2">Linux 安装步骤：</h3>
            <ol class="list-decimal list-inside space-y-2 text-blue-700">
              <li>根据发行版选择安装方式：</li>
              <li class="ml-4">Ubuntu/Debian:
                <code class="block bg-gray-800 text-white p-2 rounded mt-2 text-sm overflow-x-auto">
                  sudo apt-get update<br/>
                  sudo apt-get install docker-ce docker-ce-cli containerd.io
                </code>
              </li>
              <li class="ml-4">CentOS/RHEL:
                <code class="block bg-gray-800 text-white p-2 rounded mt-2 text-sm overflow-x-auto">
                  sudo yum install docker-ce docker-ce-cli containerd.io
                </code>
              </li>
              <li>启动 Docker 服务：<code class="bg-gray-800 text-white px-2 py-1 rounded text-sm">sudo systemctl start docker</code></li>
              <li>（可选）添加用户到 docker 组：<code class="bg-gray-800 text-white px-2 py-1 rounded text-sm">sudo usermod -aG docker $USER</code></li>
              <li>注销并重新登录</li>
              <li>点击下方"重新检测"按钮</li>
            </ol>
          </div>
        )}
      </div>
    );
  };

  const renderImagePullGuide = () => (
    <div class="bg-white rounded-lg shadow-md p-6 mb-6">
      <h2 class="text-2xl font-bold text-gray-800 mb-4 flex items-center">
        <svg class="w-6 h-6 mr-2 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        正在拉取工具镜像...
      </h2>
      <p class="text-gray-600 mb-4">
        首次使用需要从远程仓库拉取 NE301 转换工具镜像。这可能需要几分钟时间，取决于您的网络速度。
      </p>
      <div class="bg-yellow-50 border-l-4 border-yellow-500 p-4 mb-4">
        <h3 class="font-semibold text-yellow-800 mb-2">注意事项：</h3>
        <ul class="list-disc list-inside space-y-1 text-yellow-700">
          <li>镜像大小约 2-3 GB</li>
          <li>拉取期间请勿关闭此页面</li>
          <li>系统会自动检测拉取完成状态</li>
          <li>如果拉取失败，请检查网络连接或使用镜像加速器</li>
        </ul>
      </div>
      <div class="bg-gray-50 rounded-lg p-4">
        <div class="flex items-center">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mr-3"></div>
          <span class="text-gray-700">正在后台自动拉取镜像，请稍候...</span>
        </div>
      </div>
    </div>
  );

  const renderReady = () => (
    <div class="bg-white rounded-lg shadow-md p-6 mb-6">
      <h2 class="text-2xl font-bold text-gray-800 mb-4 flex items-center">
        <svg class="w-6 h-6 mr-2 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        环境就绪！
      </h2>
      <p class="text-gray-600 mb-6">
        所有依赖已安装完成，您可以开始使用模型转换工具。
      </p>
      <div class="flex gap-4">
        <button
          onClick={() => route('/')}
          class="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg transition duration-200 flex items-center justify-center"
        >
          <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
          </svg>
          进入首页
        </button>
      </div>
    </div>
  );

  return (
    <div class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4 sm:px-6 lg:px-8">
      <div class="max-w-3xl mx-auto">
        <div class="text-center mb-8">
          <h1 class="text-4xl font-extrabold text-gray-900 sm:text-5xl sm:tracking-tight lg:text-6xl">
            NE301 模型转换器
          </h1>
          <p class="mt-4 text-xl text-gray-600">
            环境设置向导
          </p>
        </div>

        {error && (
          <div class="bg-red-50 border-l-4 border-red-500 p-4 mb-6">
            <div class="flex">
              <div class="flex-shrink-0">
                <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                </svg>
              </div>
              <div class="ml-3">
                <p class="text-sm text-red-700">{error}</p>
              </div>
            </div>
          </div>
        )}

        {loading && !status && (
          <div class="bg-white rounded-lg shadow-md p-12 mb-6 flex flex-col items-center justify-center">
            <div class="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mb-4"></div>
            <p class="text-gray-600">正在检测环境状态...</p>
          </div>
        )}

        {status && !status.docker_installed && renderDockerInstallGuide()}
        {status && status.docker_installed && !status.image_pulled && renderImagePullGuide()}
        {status && status.ready && renderReady()}

        {status && !status.ready && (
          <div class="flex justify-center">
            <button
              onClick={checkEnvironment}
              disabled={loading}
              class="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-bold py-3 px-8 rounded-lg transition duration-200 flex items-center"
            >
              <svg class={`w-5 h-5 mr-2 ${loading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              {loading ? '检测中...' : '重新检测'}
            </button>
          </div>
        )}

        <div class="mt-8 text-center text-gray-500 text-sm">
          <p>需要帮助？请查看 <a href="https://github.com/yourusername/model-converter" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:underline">项目文档</a></p>
        </div>
      </div>
    </div>
  );
}
