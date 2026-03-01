import { Progress } from "@/components/ui/progress";
import { Loader2 } from "lucide-react";

export const GenerationProgress = ({ progress, message }) => {
  return (
    <div 
      className="w-full max-w-md mx-auto space-y-6"
      data-testid="generation-progress"
    >
      {/* Animated loader */}
      <div className="flex justify-center">
        <div className="relative">
          <div className="w-24 h-24 rounded-full border-4 border-primary/20" />
          <div 
            className="absolute inset-0 w-24 h-24 rounded-full border-4 border-transparent border-t-primary animate-spin"
            style={{ animationDuration: '1s' }}
          />
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-2xl font-bold text-primary">{progress}%</span>
          </div>
        </div>
      </div>

      {/* Progress bar */}
      <div className="space-y-2">
        <Progress value={progress} className="h-2 bg-secondary" />
        <div className="relative h-2 -mt-2 rounded-full overflow-hidden">
          <div 
            className="absolute inset-0 progress-shine"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Status message */}
      <div className="flex items-center justify-center gap-2 text-muted-foreground">
        <Loader2 className="w-4 h-4 animate-spin" />
        <p className="text-sm font-medium">{message}</p>
      </div>

      {/* Step indicators */}
      <div className="flex justify-center gap-8 text-xs text-muted-foreground">
        <div className={`flex flex-col items-center ${progress >= 10 ? 'text-primary' : ''}`}>
          <div className={`w-3 h-3 rounded-full mb-1 ${progress >= 10 ? 'bg-primary' : 'bg-secondary'}`} />
          <span>Анализ</span>
        </div>
        <div className={`flex flex-col items-center ${progress >= 30 ? 'text-primary' : ''}`}>
          <div className={`w-3 h-3 rounded-full mb-1 ${progress >= 30 ? 'bg-primary' : 'bg-secondary'}`} />
          <span>Изображения</span>
        </div>
        <div className={`flex flex-col items-center ${progress >= 80 ? 'text-primary' : ''}`}>
          <div className={`w-3 h-3 rounded-full mb-1 ${progress >= 80 ? 'bg-primary' : 'bg-secondary'}`} />
          <span>Озвучка</span>
        </div>
        <div className={`flex flex-col items-center ${progress >= 100 ? 'text-primary' : ''}`}>
          <div className={`w-3 h-3 rounded-full mb-1 ${progress >= 100 ? 'bg-primary' : 'bg-secondary'}`} />
          <span>Готово</span>
        </div>
      </div>
    </div>
  );
};

export default GenerationProgress;
