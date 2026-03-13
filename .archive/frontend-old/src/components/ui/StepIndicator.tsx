import { cn } from "../../utils/cn";
import i18n from "../../i18n";

export interface StepIndicatorProps {
  currentStep: number;
}

export function StepIndicator({ currentStep }: StepIndicatorProps) {
  const steps = [
    { num: 1, label: i18n.t('steps.upload_data') },
    { num: 2, label: i18n.t('steps.configuration') },
    { num: 3, label: i18n.t('steps.execution') },
  ];

  return (
    <div className="mb-12 relative">
      <div className="flex items-center justify-center gap-2 sm:gap-6 max-w-lg mx-auto">
        {steps.map((step, index) => {
          const isActive = currentStep === step.num;
          const isPast = currentStep > step.num;
          
          return (
            <div key={step.num} className="flex items-center flex-1 last:flex-none">
              <div className="flex flex-col items-center relative z-10">
                <div 
                  className={cn(
                    "w-8 h-8 sm:w-10 sm:h-10 rounded-full flex items-center justify-center text-sm font-bold transition-all duration-300 border-2",
                    isActive 
                      ? "bg-[#ee5d35] text-white border-[#ee5d35] shadow-md shadow-orange-500/20" 
                      : isPast
                        ? "bg-slate-800 text-white border-slate-800"
                        : "bg-white text-slate-400 border-slate-200"
                  )}
                >
                  {isPast ? (
                    <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : (
                    step.num
                  )}
                </div>
                <span 
                  className={cn(
                    "absolute top-full mt-2 text-[10px] sm:text-xs font-medium whitespace-nowrap transition-colors",
                    isActive ? "text-[#ee5d35]" : isPast ? "text-slate-800" : "text-slate-400"
                  )}
                >
                  {step.label}
                </span>
              </div>
              
              {/* 连接线 */}
              {index < steps.length - 1 && (
                <div 
                  className={cn(
                    "flex-1 h-[2px] mx-2 sm:mx-4 transition-colors duration-300 relative -top-3 sm:-top-4",
                    isPast ? "bg-slate-800" : "bg-slate-200"
                  )} 
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
