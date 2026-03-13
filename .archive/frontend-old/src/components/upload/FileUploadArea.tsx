import { useState, useRef } from 'preact/hooks';
import { cn } from '../../utils/cn';
import i18n from '../../i18n';
import { Upload, FileDigit, CheckCircle2 } from 'lucide-preact';

interface FileUploadAreaProps {
  onFileSelect: (file: File) => void;
  selectedFile: File | null;
  onRemove: () => void;
}

export function FileUploadArea({ onFileSelect, selectedFile, onRemove }: FileUploadAreaProps) {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer?.files[0];
    if (file) {
      onFileSelect(file);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 md:p-6 h-full flex flex-col">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-slate-900 flex items-center justify-center">
          <Upload className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className="text-lg font-bold text-slate-900">{i18n.t('upload.model_title')}</h3>
          <p className="text-sm text-slate-500">{i18n.t('upload.model_desc')}</p>
        </div>
      </div>

      <div
        className={cn(
          "relative border-2 border-dashed rounded-xl p-8 text-center transition-all cursor-pointer bg-slate-50 flex-1 flex flex-col items-center justify-center",
          isDragging
            ? "border-[#ee5d35] bg-orange-50/50"
            : "border-slate-300 hover:border-slate-400 hover:bg-slate-100"
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pt,.pth,.onnx"
          className="hidden"
          onChange={(e) => {
            const file = (e.target as HTMLInputElement).files?.[0];
            if (file) onFileSelect(file);
          }}
        />

        {selectedFile ? (
          <div className="flex flex-col items-center gap-3">
            <div className="w-12 h-12 rounded-full bg-green-100 text-green-600 flex items-center justify-center">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <div>
              <p className="font-semibold text-slate-800">{selectedFile.name}</p>
              <p className="text-xs text-slate-500 mt-1">
                {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                if (fileInputRef.current) fileInputRef.current.value = '';
                onRemove();
              }}
              className="mt-2 text-sm text-slate-500 hover:text-red-500 underline underline-offset-4"
            >
              {i18n.t('upload.remove_file')}
            </button>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3 text-slate-500">
            <FileDigit className="w-10 h-10 text-slate-400" />
            <div>
              <span className="font-medium text-slate-800">{i18n.t('upload.click_to_upload')}</span> {i18n.t('upload.or_drag')}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
