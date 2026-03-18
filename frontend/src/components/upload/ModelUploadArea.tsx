import { useState } from 'preact/hooks';
import { UploadCloud, CheckCircle, AlertCircle } from 'lucide-preact';
import { useI18nStore } from '../../store/i18n';

interface ModelUploadAreaProps {
  onFileSelect: (file: File) => void;
  selectedFile?: File;
}

export default function ModelUploadArea({ onFileSelect, selectedFile }: ModelUploadAreaProps) {
  const { t } = useI18nStore();
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string>('');

  const validateFile = (file: File): boolean => {
    // 检查文件格式
    const validExtensions = ['.pt', '.pth', '.onnx'];
    const fileName = file.name.toLowerCase();
    const hasValidExtension = validExtensions.some(ext => fileName.endsWith(ext));

    if (!hasValidExtension) {
      setError(t('errorInvalidModelFormat'));
      return false;
    }

    // 检查文件大小（500MB = 500 * 1024 * 1024 bytes）
    const maxSize = 500 * 1024 * 1024;
    if (file.size > maxSize) {
      setError(t('errorModelTooLarge'));
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
    <div className="animate-fade-in">
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
          id="model-file-input"
          type="file"
          accept=".pt,.pth,.onnx"
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
          <UploadCloud
            className={`${
              isDragging ? 'text-white' : 'text-primary-600 dark:text-primary-400'
            }`}
            size={32}
          />
        </div>
        <p className="text-lg font-medium text-gray-700 dark:text-gray-300 mb-2">
          {selectedFile ? `${t('fileSelected')} ${selectedFile.name}` : t('dragDropModel')}
          {!selectedFile && <span className="text-primary-600 dark:text-primary-400 ml-1 hover:underline cursor-pointer">{t('browseFile')}</span>}
        </p>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          {t('supportFormatModel')}
        </p>
        {selectedFile && (
          <div className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-success-50 dark:bg-success-950/20 rounded-xl animate-scale-in">
            <div className="w-5 h-5 rounded-full bg-success-500 flex items-center justify-center">
              <CheckCircle className="w-3 h-3 text-white" />
            </div>
            <div className="text-sm text-success-700 dark:text-success-300">
              <div className="font-medium">{selectedFile.name}</div>
              <div className="text-xs text-success-600 dark:text-success-400">
                {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
              </div>
            </div>
          </div>
        )}
      </div>

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
