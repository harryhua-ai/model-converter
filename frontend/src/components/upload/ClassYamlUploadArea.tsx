import { useState } from 'preact/hooks';
import { FileText, Upload, CheckCircle } from 'lucide-preact';
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
    <div>
      <div className="mb-3">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          类别定义文件（可选）
        </label>
        <p className="text-xs text-gray-500 mb-3">
          上传 .yaml/.yml 文件定义模型输出的类别（用于目标检测模型）。如不需要可跳过。
        </p>
      </div>

      {!selectedFile ? (
        <div
          className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
            isDragging
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
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
          <FileText className="mx-auto h-12 w-12 text-gray-400 mb-3" />
          <p className="text-base font-medium text-gray-700 mb-1">
            上传类别定义文件
          </p>
          <p className="text-sm text-gray-500">支持 .yaml、.yml 格式</p>
        </div>
      ) : (
        <div className="border border-gray-300 rounded-lg p-4 bg-white">
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center">
              <FileText className="h-5 w-5 text-blue-500 mr-2" />
              <div>
                <p className="text-sm font-medium text-gray-700">{selectedFile.name}</p>
                <p className="text-xs text-gray-500">
                  {(selectedFile.size / 1024).toFixed(2)} KB
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={handleRemove}
              className="text-sm text-red-600 hover:text-red-700 font-medium"
            >
              移除
            </button>
          </div>

          {preview && (
            <div className="mt-3">
              <p className="text-xs font-medium text-gray-600 mb-2">文件预览：</p>
              <pre className="bg-gray-50 p-3 rounded text-xs text-gray-700 overflow-x-auto border border-gray-200">
                {preview}
              </pre>
            </div>
          )}

          {parsedClasses && (
            <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-md">
              <div className="flex items-start">
                <CheckCircle className="h-5 w-5 text-green-600 mr-2 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-semibold text-green-800 mb-1">
                    已识别 {parsedClasses.numClasses} 个类别
                  </p>
                  <p className="text-xs text-green-700 mb-2">
                    类别列表: {parsedClasses.names.slice(0, 5).join(', ')}
                    {parsedClasses.names.length > 5 && ' ...'}
                  </p>
                  <details className="text-xs text-green-700">
                    <summary className="cursor-pointer hover:text-green-900">查看完整列表</summary>
                    <div className="mt-2 pl-4 border-l-2 border-green-300">
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
        <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}
    </div>
  );
}
