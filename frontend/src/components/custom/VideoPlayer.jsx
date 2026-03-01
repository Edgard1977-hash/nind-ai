import { useState, useEffect, useRef } from "react";
import { Play, Pause, Volume2, VolumeX, RotateCcw } from "lucide-react";
import { cn } from "@/lib/utils";

export const VideoPlayer = ({ scenes, audioUrl, title, onReplay }) => {
  const [currentSceneIndex, setCurrentSceneIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [showSubtitle, setShowSubtitle] = useState(true);
  const audioRef = useRef(null);
  const timerRef = useRef(null);

  const currentScene = scenes[currentSceneIndex];
  const totalDuration = scenes.reduce((acc, s) => acc + (s.duration || 3), 0);

  useEffect(() => {
    if (isPlaying && scenes.length > 0) {
      const sceneDuration = (currentScene?.duration || 3) * 1000;
      
      timerRef.current = setTimeout(() => {
        if (currentSceneIndex < scenes.length - 1) {
          setCurrentSceneIndex(prev => prev + 1);
        } else {
          setIsPlaying(false);
          setCurrentSceneIndex(0);
          if (audioRef.current) {
            audioRef.current.pause();
            audioRef.current.currentTime = 0;
          }
        }
      }, sceneDuration);

      return () => clearTimeout(timerRef.current);
    }
  }, [isPlaying, currentSceneIndex, scenes, currentScene?.duration]);

  const handlePlayPause = () => {
    if (isPlaying) {
      setIsPlaying(false);
      if (audioRef.current) audioRef.current.pause();
    } else {
      setIsPlaying(true);
      if (audioRef.current) audioRef.current.play();
    }
  };

  const handleReplay = () => {
    setCurrentSceneIndex(0);
    setIsPlaying(true);
    if (audioRef.current) {
      audioRef.current.currentTime = 0;
      audioRef.current.play();
    }
    onReplay?.();
  };

  const toggleMute = () => {
    setIsMuted(!isMuted);
    if (audioRef.current) {
      audioRef.current.muted = !isMuted;
    }
  };

  const getAnimationClass = (animation) => {
    switch (animation) {
      case "zoom_in": return "animate-ken-burns-zoom-in";
      case "zoom_out": return "animate-ken-burns-zoom-out";
      case "pan_left": return "animate-ken-burns-pan-left";
      case "pan_right": return "animate-ken-burns-pan-right";
      default: return "animate-ken-burns-zoom-in";
    }
  };

  if (!scenes || scenes.length === 0) {
    return (
      <div className="video-container max-w-sm mx-auto bg-card rounded-3xl border border-white/10 flex items-center justify-center">
        <p className="text-muted-foreground">Нет сцен для отображения</p>
      </div>
    );
  }

  return (
    <div 
      className="video-container max-w-sm mx-auto bg-black rounded-3xl border border-white/10 overflow-hidden relative shadow-2xl"
      data-testid="video-player"
    >
      {/* Audio element */}
      {audioUrl && (
        <audio ref={audioRef} src={audioUrl} muted={isMuted} />
      )}

      {/* Scene Image with Ken Burns effect */}
      <div className="absolute inset-0 overflow-hidden">
        {currentScene?.image_url ? (
          <img
            key={`scene-${currentSceneIndex}`}
            src={currentScene.image_url}
            alt={`Scene ${currentSceneIndex + 1}`}
            className={cn(
              "w-full h-full object-cover",
              isPlaying && getAnimationClass(currentScene.animation)
            )}
          />
        ) : (
          <div className="w-full h-full bg-gradient-to-br from-violet-900/50 to-indigo-900/50 flex items-center justify-center">
            <p className="text-white/50">Изображение загружается...</p>
          </div>
        )}
      </div>

      {/* Bottom reflection blur */}
      <div className="absolute bottom-0 left-0 right-0 h-[30%] reflection-blur" />

      {/* News ticker (for news format) */}
      <div className="absolute bottom-[30%] left-0 right-0 news-ticker py-2 px-4">
        <p className="text-white text-xs font-bold tracking-wider uppercase truncate">
          {title || "BREAKING NEWS"}
        </p>
      </div>

      {/* Subtitle */}
      {showSubtitle && currentScene?.text && (
        <div className="absolute bottom-[8%] left-4 right-4 text-center">
          <p className="text-white text-lg md:text-xl font-bold subtitle-text leading-tight">
            {currentScene.text}
          </p>
        </div>
      )}

      {/* Scene indicator */}
      <div className="absolute top-4 left-4 right-4 flex gap-1">
        {scenes.map((_, idx) => (
          <div
            key={idx}
            className={cn(
              "h-1 flex-1 rounded-full transition-all duration-300",
              idx < currentSceneIndex
                ? "bg-primary"
                : idx === currentSceneIndex
                ? "bg-primary/50"
                : "bg-white/20"
            )}
          />
        ))}
      </div>

      {/* Controls overlay */}
      <div className="absolute inset-0 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity duration-300 bg-black/30">
        <div className="flex items-center gap-4">
          <button
            onClick={handleReplay}
            className="p-3 rounded-full bg-white/20 hover:bg-white/30 transition-colors"
            data-testid="replay-button"
          >
            <RotateCcw className="w-6 h-6 text-white" />
          </button>
          
          <button
            onClick={handlePlayPause}
            className="p-4 rounded-full bg-primary hover:bg-primary/80 transition-colors glow-primary"
            data-testid="play-pause-button"
          >
            {isPlaying ? (
              <Pause className="w-8 h-8 text-white" />
            ) : (
              <Play className="w-8 h-8 text-white ml-1" />
            )}
          </button>
          
          <button
            onClick={toggleMute}
            className="p-3 rounded-full bg-white/20 hover:bg-white/30 transition-colors"
            data-testid="mute-button"
          >
            {isMuted ? (
              <VolumeX className="w-6 h-6 text-white" />
            ) : (
              <Volume2 className="w-6 h-6 text-white" />
            )}
          </button>
        </div>
      </div>

      {/* Auto-play indicator */}
      {!isPlaying && currentSceneIndex === 0 && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/50">
          <button
            onClick={handlePlayPause}
            className="p-6 rounded-full bg-primary/90 hover:bg-primary transition-all duration-300 glow-primary animate-pulse-glow"
            data-testid="initial-play-button"
          >
            <Play className="w-12 h-12 text-white ml-1" />
          </button>
        </div>
      )}
    </div>
  );
};

export default VideoPlayer;
