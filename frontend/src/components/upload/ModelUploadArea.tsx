import { useState } from 'preact/hooks';
import { UploadCloud } from 'lucide-preact';

interface ModelUploadAreaProps {
  onFileSelect: (file: File) => void;
  selectedFile?: File;
}

export default function ModelUploadArea({ onFileSelect, selectedFile }: ModelUploadAreaProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string>('');

  const validateFile = (file: File): boolean => {
    // 检查文件格式
    const validExtensions = ['.pt', '.pth', '.onnx'];
    const fileName = file.name.toLowerCase();
    const hasValidExtension = validExtensions.some(ext => fileName.endsWith(ext));

    if (!hasValidExtension) {
      setError('文件格式不支持。请上传 .pt、.pth 或 .onnx 文件。');
      return false;
    }

    // 检查文件大小（500MB = 500 * 1024 * 1024 bytes）
    const maxSize = 500 * 1024 * 1024;
    if (file.size > maxSize) {
      setError('文件大小超过限制。最大支持 500MB。');
      return false;
    }

    setError('');
    return true;
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
      }
    }
  };

  const handleClick = () => {
    const input = document.getElementById('model-file-input') as HTMLInputElement;
    input?.click();
  };

  return (
    <div>
      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
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
          id="model-file-input"
          type="file"
          accept=".pt,.pth,.onnx"
          className="hidden"
          onChange={handleFileInput}
        />
        <UploadCloud className="mx-auto h-16 w-16 text-gray-400 mb-4" />
        <p className="text-lg font-medium text-gray-700 mb-2">
          {selectedFile ? selectedFile.name : '拖拽文件到此处或点击上传'}
        </p>
        <p className="text-sm text-gray-500">
          支持 .pt、.pth、.onnx 格式，最大 500MB
        </p>
        {selectedFile && (
          <div className="mt-3 text-sm text-green-600">
            ✓ 已选择: {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
          </div>
        )}
      </div>

      {error && (
        <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}
    </div>
  );
}
