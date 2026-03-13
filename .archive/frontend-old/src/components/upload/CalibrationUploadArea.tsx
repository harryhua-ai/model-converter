import { useState, useRef } from 'preact/hooks';
import { cn } from '../../utils/cn';
import i18n from '../../i18n';
import { Archive, HelpCircle, CheckCircle2, FileDigit } from 'lucide-preact';

interface CalibrationUploadAreaProps {
  onFileSelect: (file: File) => void;
  selectedFile: File | null;
  onRemove: () => void;
}

export function CalibrationUploadArea({
  onFileSelect,
  selectedFile,
  onRemove
}: CalibrationUploadAreaProps) {
  const [isCalibDragging, setIsCalibDragging] = useState(false);
  const calibInputRef = useRef<HTMLInputElement>(null);

  const handleCalibDragOver = (e: DragEvent) => {
    e.preventDefault();
    setIsCalibDragging(true);
  };

  const handleCalibDragLeave = () => {
    setIsCalibDragging(false);
  };

  const handleCalibDrop = (e: DragEvent) => {
    e.preventDefault();
    setIsCalibDragging(false);
    const file = e.dataTransfer?.files[0];
    if (file) {
      onFileSelect(file);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 md:p-6 h-full flex flex-col">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-slate-900 flex items-center justify-center">
            <Archive className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-bold text-slate-900">{i18n.t('upload.calib_title')}</h3>
              
              <div className="relative group flex items-center">
                <HelpCircle className="w-4 h-4 text-slate-400 cursor-help hover:text-[#ee5d35] transition-colors" />
                
                {/* Tooltip */}
                <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 w-64 p-3 bg-slate-800 text-white text-xs rounded-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 shadow-xl z-50 text-center pointer-events-none">
                  {i18n.t('upload.calib_hint')}
                  <div className="absolute left-1/2 -bottom-1 -translate-x-1/2 border-4 border-transparent border-t-slate-800" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div
        className={cn(
          "relative border-2 border-dashed rounded-xl p-8 text-center transition-all cursor-pointer bg-slate-50 flex-1 flex flex-col items-center justify-center min-h-[160px]",
          isCalibDragging
            ? "border-[#ee5d35] bg-orange-50/50"
            : "border-slate-300 hover:border-slate-400 hover:bg-slate-100"
        )}
        onDragOver={handleCalibDragOver}
        onDragLeave={handleCalibDragLeave}
        onDrop={handleCalibDrop}
        onClick={() => calibInputRef.current?.click()}
      >
        <input
          ref={calibInputRef}
          type="file"
          accept=".zip"
          className="hidden"
          onChange={(e) => {
            const file = (e.target as HTMLInputElement).files?.[0];
            if (file) {
              onFileSelect(file);
            }
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
                if (calibInputRef.current) calibInputRef.current.value = '';
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
              <span className="font-medium text-slate-800">{i18n.t('upload.click_zip')}</span> {i18n.t('upload.or_drag_zip')}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
