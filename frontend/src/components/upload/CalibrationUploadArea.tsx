import { useCallback, useState } from 'preact/hooks';
import { FileArchive, AlertCircle, CheckCircle } from 'lucide-preact';
import { useI18nStore } from '../../store/i18n';

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
  const { t } = useI18nStore();
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string>('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleDrop = useCallback((e: DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) {
      validateAndSelect(file);
    }
  }, []);

  const handleDragOver = useCallback((e: DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleFileInput = useCallback((e: Event) => {
    const target = e.target as HTMLInputElement;
    const file = target.files?.[0];
    if (file) {
      validateAndSelect(file);
    }
  }, []);

  const validateAndSelect = (file: File) => {
    setError('');

    // 验证文件格式
    if (!file.name.endsWith('.zip')) {
      setError(t('errorInvalidZipFormat') || 'Only .zip supported');
      return;
    }

    // 验证文件大小
    if (file.size > maxSize) {
      setError(t('errorModelTooLarge'));
      return;
    }

    setSelectedFile(file);
    onFileSelect(file);
  };

  const handleClick = () => {
    const input = document.getElementById('calibration-file-input') as HTMLInputElement;
    input?.click();
  };

  const handleRemove = () => {
    setSelectedFile(null);
    setError('');
    const input = document.getElementById('calibration-file-input') as HTMLInputElement;
    if (input) {
      input.value = '';
    }
  };

  return (
    <div className="animate-fade-in">
      {!selectedFile ? (
        <div
          className={`upload-zone hover:scale-[1.02] transition-transform duration-200 ${
            isDragging
              ? 'border-primary-500 bg-primary-50 dark:bg-primary-950/20'
              : 'border-gray-300 dark:border-gray-600'
          }`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={handleClick}
        >
          <input
            id="calibration-file-input"
            type="file"
            accept={accept}
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
            <FileArchive
              className={`${
                isDragging ? 'text-white' : 'text-primary-600 dark:text-primary-400'
              }`}
              size={32}
            />
          </div>
          <p className="text-lg font-medium text-gray-700 dark:text-gray-300 mb-2">
            {t('dragDropZip')}
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">
            {t('supportFormatZip')}
          </p>
          <div className="text-xs text-gray-400 dark:text-gray-500 space-y-1">
            <div>• Format: .zip</div>
            <div>• Size: Max 1GB</div>
            <div>• Rec: 32-100 images</div>
          </div>
        </div>
      ) : (
        <div className="border border-gray-300 dark:border-gray-600 rounded-xl p-4 bg-white dark:bg-gray-800 shadow-card animate-scale-in">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-100 to-accent-100 dark:from-primary-900/30 dark:to-accent-900/30 flex items-center justify-center">
                <FileArchive className="w-6 h-6 text-primary-600 dark:text-primary-400" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-700 dark:text-gray-300">{selectedFile.name}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={handleRemove}
              className="text-sm text-error-600 hover:text-error-700 dark:text-error-400 dark:hover:text-error-300 font-medium px-3 py-1 rounded-lg hover:bg-error-50 dark:hover:bg-error-950/20 transition-colors"
            >
              {t('changeFile')}
            </button>
          </div>
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
