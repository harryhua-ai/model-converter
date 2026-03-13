import { useState } from 'preact/hooks';
import { FileText, CheckCircle, AlertCircle } from 'lucide-preact';
import * as yaml from 'js-yaml';

interface ClassYamlUploadAreaProps {
  onFileSelect: (file: File | null) => void;
  selectedFile?: File;
  onClassDetected?: (numClasses: number, names: string[]) => void;
}

interface YamlData {
  nc?: number;
  names?: string[];
  classes?: Array<{ name: string; id?: number }>;
}

export default function ClassYamlUploadArea({
  onFileSelect,
  selectedFile,
  onClassDetected,
}: ClassYamlUploadAreaProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string>('');
  const [preview, setPreview] = useState<string>('');
  const [parsedClasses, setParsedClasses] = useState<{ numClasses: number; names: string[] } | null>(null);

  const validateFile = (file: File): boolean => {
    // 检查文件格式
    const fileName = file.name.toLowerCase();
    if (!fileName.endsWith('.yaml') && !fileName.endsWith('.yml')) {
      setError('文件格式不支持。请上传 .yaml 或 .yml 文件。');
      return false;
    }

    setError('');
    return true;
  };

  const readFilePreview = (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target?.result as string;
      // 只预览前 500 个字符
      setPreview(content.substring(0, 500) + (content.length > 500 ? '...' : ''));

      // 解析 YAML 内容
      try {
        const data = yaml.load(content) as YamlData;

        let numClasses = 0;
        let names: string[] = [];

        // YOLO 格式: names 数组 + nc 字段
        if (data.names && Array.isArray(data.names)) {
          names = data.names;
          numClasses = data.nc || names.length;
        }
        // 替代格式: classes 数组
        else if (data.classes && Array.isArray(data.classes)) {
          names = data.classes.map((c) => c.name);
          numClasses = names.length;
        }

        if (numClasses > 0 && names.length > 0) {
          setParsedClasses({ numClasses, names });
          // 通知父组件
          onClassDetected?.(numClasses, names);
        }
      } catch (err) {
        console.warn('YAML 解析失败:', err);
        // 不阻塞文件选择，只是无法自动提取类别信息
      }
    };
    reader.readAsText(file);
  };

  const handleDragOver = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = (e.dataTransfer?.files || []) as FileList;
    if (files.length > 0) {
      const file = files[0];
      if (validateFile(file)) {
        onFileSelect(file);
        readFilePreview(file);
      }
    }
  };

  const handleFileInput = (e: Event) => {
    const target = e.target as HTMLInputElement;
    const files = target.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (validateFile(file)) {
        onFileSelect(file);
        readFilePreview(file);
      }
    }
  };

  const handleClick = () => {
    const input = document.getElementById('yaml-file-input') as HTMLInputElement;
    input?.click();
  };

  const handleRemove = () => {
    onFileSelect(null);
    setPreview('');
    setError('');
    setParsedClasses(null);
  };

  return (
    <div className="animate-fade-in">
      <div className="mb-3">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          类别定义文件（可选）
        </label>
        <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">
          上传 .yaml/.yml 文件定义模型输出的类别（用于目标检测模型）。如不需要可跳过。
        </p>
      </div>

      {!selectedFile ? (
        <div
          className={`upload-zone hover:scale-[1.02] transition-transform duration-200 ${
            isDragging
              ? 'border-primary-500 bg-primary-50 dark:bg-primary-950/20'
              : 'border-gray-300 dark:border-gray-600'
          }`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={handleClick}
        >
          <input
            id="yaml-file-input"
            type="file"
            accept=".yaml,.yml"
            className="hidden"
            onChange={handleFileInput}
          />
          <div
            className={`mx-auto w-20 h-20 rounded-2xl bg-gradient-to-br flex items-center justify-center mb-4 transition-all duration-200 ${
              isDragging
                ? 'from-primary-500 to-primary-600 scale-110 shadow-glow'
                : 'from-primary-100 to-accent-100 dark:from-primary-900/30 dark:to-accent-900/30'
            }`}
          >
            <FileText
              className={`${
                isDragging ? 'text-white' : 'text-primary-600 dark:text-primary-400'
              }`}
              size={32}
            />
          </div>
          <p className="text-lg font-medium text-gray-700 dark:text-gray-300 mb-2">
            上传类别定义文件
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            支持 .yaml、.yml 格式
          </p>
        </div>
      ) : (
        <div className="border border-gray-300 dark:border-gray-600 rounded-xl p-4 bg-white dark:bg-gray-800 shadow-card animate-scale-in">
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-100 to-accent-100 dark:from-primary-900/30 dark:to-accent-900/30 flex items-center justify-center">
                <FileText className="w-6 h-6 text-primary-600 dark:text-primary-400" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-700 dark:text-gray-300">{selectedFile.name}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {(selectedFile.size / 1024).toFixed(2)} KB
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={handleRemove}
              className="text-sm text-error-600 hover:text-error-700 dark:text-error-400 dark:hover:text-error-300 font-medium px-3 py-1 rounded-lg hover:bg-error-50 dark:hover:bg-error-950/20 transition-colors"
            >
              移除
            </button>
          </div>

          {preview && (
            <div className="mt-3">
              <p className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-2">文件预览：</p>
              <pre className="bg-gray-50 dark:bg-gray-900 p-3 rounded-xl text-xs text-gray-700 dark:text-gray-300 overflow-x-auto border border-gray-200 dark:border-gray-700">
                {preview}
              </pre>
            </div>
          )}

          {parsedClasses && (
            <div className="mt-3 p-4 bg-success-50 dark:bg-success-950/20 border border-success-200 dark:border-success-800 rounded-xl animate-scale-in">
              <div className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-success-500 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <CheckCircle className="w-4 h-4 text-white" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-success-800 dark:text-success-200 mb-1">
                    已识别 {parsedClasses.numClasses} 个类别
                  </p>
                  <p className="text-xs text-success-700 dark:text-success-300 mb-2">
                    类别列表: {parsedClasses.names.slice(0, 5).join(', ')}
                    {parsedClasses.names.length > 5 && ' ...'}
                  </p>
                  <details className="text-xs text-success-700 dark:text-success-300">
                    <summary className="cursor-pointer hover:text-success-900 dark:hover:text-success-100">查看完整列表</summary>
                    <div className="mt-2 pl-4 border-l-2 border-success-300 dark:border-success-700">
                      {parsedClasses.names.map((name, idx) => (
                        <div key={idx}>
                          {idx + 1}. {name}
                        </div>
                      ))}
                    </div>
                  </details>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {error && (
        <div className="mt-3 border-l-4 border-error-500 bg-error-50 dark:bg-error-950/20 rounded-r-xl p-3 animate-slide-up">
          <div className="flex items-start gap-2">
            <div className="w-6 h-6 rounded-full bg-error-500 flex items-center justify-center flex-shrink-0 mt-0.5">
              <AlertCircle className="w-4 h-4 text-white" />
            </div>
            <p className="text-sm text-error-700 dark:text-error-300 flex-1">{error}</p>
          </div>
        </div>
      )}
    </div>
  );
}
