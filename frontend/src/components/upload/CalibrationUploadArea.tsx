import { useCallback } from 'preact/hooks';
import { Upload, FileArchive } from 'lucide-preact';

interface Props {
  onFileSelect: (file: File) => void;
  accept?: string;
  maxSize?: number; // bytes
}

export default function CalibrationUploadArea({
  onFileSelect,
  accept = '.zip',
  maxSize = 1024 * 1024 * 1024, // 1GB
}: Props) {
  const handleDrop = useCallback((e: DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file) {
      validateAndSelect(file);
    }
  }, []);

  const handleDragOver = useCallback((e: DragEvent) => {
    e.preventDefault();
  }, []);

  const handleFileInput = useCallback((e: Event) => {
    const target = e.target as HTMLInputElement;
    const file = target.files?.[0];
    if (file) {
      validateAndSelect(file);
    }
  }, []);

  const validateAndSelect = (file: File) => {
    // 验证文件格式
    if (!file.name.endsWith('.zip')) {
      alert('校准数据集必须是 ZIP 格式');
      return;
    }

    // 验证文件大小
    if (file.size > maxSize) {
      alert(`文件过大 (${(file.size / 1024 / 1024).toFixed(2)}MB)，最大支持 ${maxSize / 1024 / 1024}MB`);
      return;
    }

    onFileSelect(file);
  };

  return (
    <div
      class="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-6 text-center cursor-pointer hover:border-primary transition-colors bg-white dark:bg-gray-800"
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onClick={() => {
        const input = document.getElementById('calibration-file-input') as HTMLInputElement;
        input?.click();
      }}
    >
      <input
        id="calibration-file-input"
        type="file"
        accept={accept}
        class="hidden"
        onChange={handleFileInput}
      />
      <div class="flex flex-col items-center gap-3">
        <div class="w-12 h-12 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center">
          <FileArchive class="w-6 h-6 text-blue-600 dark:text-blue-400" />
        </div>
        <div>
          <p class="text-sm font-medium text-gray-700 dark:text-gray-300">
            上传校准数据集（可选）
          </p>
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
            拖拽 ZIP 文件到此处或点击选择
          </p>
        </div>
        <div class="text-xs text-gray-400 dark:text-gray-500">
          <div>• 格式: .zip</div>
          <div>• 大小: 最大 1GB</div>
          <div>• 推荐: 32-100 张图片</div>
        </div>
      </div>
    </div>
  );
}
