import { useState, useRef, useEffect, useMemo } from "react";
import { Play, Pause, Volume2, VolumeX, Youtube, Gamepad2 } from "lucide-react";
import { cn } from "@/lib/utils";

// Placeholder gameplay videos for different types
const GAMEPLAY_PLACEHOLDERS = {
  minecraft_parkour: "https://images.unsplash.com/photo-1542751371-adc38448a05e?w=800",
  soap_cutting: "https://images.unsplash.com/photo-1583947215259-38e31be8751f?w=800",
  subway_surfers: "https://images.unsplash.com/photo-1511512578047-dfb367046420?w=800",
  satisfying: "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800",
  slime_asmr: "https://images.unsplash.com/photo-1604076913837-52ab5629fba9?w=800",
  cooking: "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=800",
};

export const GameplayClipPlayer = ({ project, audioUrl }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [currentSubtitleIndex, setCurrentSubtitleIndex] = useState(0);
  const audioRef = useRef(null);
  const timerRef = useRef(null);

  const scenes = useMemo(() => project?.scenes || [], [project?.scenes]);
  const youtubeUrl = project?.youtube_url || "";
  const gameplayType = project?.gameplay_type || "minecraft_parkour";
  const currentSubtitle = scenes[currentSubtitleIndex];

  // Extract YouTube video ID
  const getYoutubeEmbedUrl = (url) => {
    if (!url) return null;
    const match = url.match(/(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})/);
    return match ? `https://www.youtube.com/embed/${match[1]}?autoplay=0&controls=0&modestbranding=1` : null;
  };

  const youtubeEmbedUrl = getYoutubeEmbedUrl(youtubeUrl);

  useEffect(() => {
    if (isPlaying && scenes.length > 0) {
      const subtitleDuration = (currentSubtitle?.timestamp_end - currentSubtitle?.timestamp_start) * 1000 || 3000;
      
      timerRef.current = setTimeout(() => {
        if (currentSubtitleIndex < scenes.length - 1) {
          setCurrentSubtitleIndex(prev => prev + 1);
        } else {
          setIsPlaying(false);
          setCurrentSubtitleIndex(0);
          if (audioRef.current) {
            audioRef.current.pause();
            audioRef.current.currentTime = 0;
          }
        }
      }, subtitleDuration);

      return () => clearTimeout(timerRef.current);
    }
  }, [isPlaying, currentSubtitleIndex, scenes, currentSubtitle]);

  const handlePlayPause = () => {
    if (isPlaying) {
      setIsPlaying(false);
      if (audioRef.current) audioRef.current.pause();
    } else {
      setIsPlaying(true);
      if (audioRef.current) audioRef.current.play();
    }
  };

  const toggleMute = () => {
    setIsMuted(!isMuted);
    if (audioRef.current) {
      audioRef.current.muted = !isMuted;
    }
  };

  return (
    <div 
      className="video-container max-w-sm mx-auto bg-black rounded-3xl border border-white/10 overflow-hidden relative shadow-2xl"
      data-testid="gameplay-clip-player"
    >
      {/* Audio element */}
      {audioUrl && (
        <audio ref={audioRef} src={audioUrl} muted={isMuted} />
      )}

      {/* Split screen layout */}
      <div className="absolute inset-0 flex flex-col">
        {/* Top section - YouTube clip (60%) */}
        <div className="relative flex-[6] bg-gradient-to-br from-red-900/30 to-black overflow-hidden">
          {youtubeEmbedUrl ? (
            <iframe
              src={youtubeEmbedUrl}
              className="absolute inset-0 w-full h-full"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
              title="YouTube video"
            />
          ) : (
            <div className="absolute inset-0 flex flex-col items-center justify-center bg-gradient-to-br from-red-900/50 to-black">
              <Youtube className="w-16 h-16 text-red-500 mb-4" />
              <p className="text-white/70 text-sm text-center px-4">
                YouTube клип будет здесь
              </p>
              {youtubeUrl && (
                <p className="text-white/50 text-xs mt-2 px-4 truncate max-w-full">
                  {youtubeUrl}
                </p>
              )}
            </div>
          )}
          
          {/* YouTube badge */}
          <div className="absolute top-3 left-3 flex items-center gap-2 bg-red-600 px-2 py-1 rounded-full">
            <Youtube className="w-3 h-3 text-white" />
            <span className="text-xs text-white font-medium">Клип</span>
          </div>
        </div>

        {/* Divider line */}
        <div className="h-1 bg-gradient-to-r from-primary via-accent to-primary" />

        {/* Bottom section - Gameplay (40%) */}
        <div className="relative flex-[4] overflow-hidden">
          <div 
            className="absolute inset-0 bg-cover bg-center"
            style={{ backgroundImage: `url(${GAMEPLAY_PLACEHOLDERS[gameplayType]})` }}
          />
          <div className="absolute inset-0 bg-black/30" />
          
          {/* Gameplay badge */}
          <div className="absolute top-2 left-3 flex items-center gap-2 bg-accent/90 px-2 py-1 rounded-full">
            <Gamepad2 className="w-3 h-3 text-black" />
            <span className="text-xs text-black font-medium">
              {gameplayType === "minecraft_parkour" && "Minecraft"}
              {gameplayType === "soap_cutting" && "ASMR"}
              {gameplayType === "subway_surfers" && "Subway"}
              {gameplayType === "satisfying" && "Satisfying"}
              {gameplayType === "slime_asmr" && "Slime"}
              {gameplayType === "cooking" && "Cooking"}
            </span>
          </div>
        </div>
      </div>

      {/* Subtitles overlay */}
      {currentSubtitle?.text && (
        <div className="absolute bottom-[42%] left-4 right-4 text-center z-10">
          <div className={cn(
            "inline-block px-4 py-2 rounded-xl",
            currentSubtitle.highlight 
              ? "bg-accent text-black font-bold" 
              : "bg-black/80 text-white"
          )}>
            <p className="text-base md:text-lg font-medium subtitle-text">
              {currentSubtitle.text}
            </p>
          </div>
        </div>
      )}

      {/* Progress indicator */}
      <div className="absolute top-3 left-3 right-3 flex gap-1 z-20">
        {scenes.map((_, idx) => (
          <div
            key={idx}
            className={cn(
              "h-1 flex-1 rounded-full transition-all duration-300",
              idx < currentSubtitleIndex
                ? "bg-primary"
                : idx === currentSubtitleIndex
                ? "bg-primary/50"
                : "bg-white/20"
            )}
          />
        ))}
      </div>

      {/* Controls overlay */}
      <div className="absolute inset-0 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity duration-300 bg-black/30 z-30">
        <div className="flex items-center gap-4">
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

      {/* Initial play button */}
      {!isPlaying && currentSubtitleIndex === 0 && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/50 z-30">
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

export default GameplayClipPlayer;
