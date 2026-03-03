import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, Download, Share2, RotateCcw, Home } from "lucide-react";
import { Button } from "@/components/ui/button";
import { VideoPlayer } from "@/components/custom/VideoPlayer";
import { GameplayClipPlayer } from "@/components/custom/GameplayClipPlayer";
import { GenerationProgress } from "@/components/custom/GenerationProgress";
import { toast } from "sonner";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const VideoPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchProject = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/video/${id}`);
      setProject(response.data);
      setIsLoading(false);

      // Continue polling if still processing
      if (response.data.status === "pending" || response.data.status === "processing") {
        setTimeout(fetchProject, 2000);
      }
    } catch (err) {
      console.error("Failed to fetch project:", err);
      setError("Проект не найден");
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchProject();
  }, [fetchProject]);

  const handleShare = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      toast.success("Ссылка скопирована!");
    } catch {
      toast.error("Не удалось скопировать ссылку");
    }
  };

  const handleNewVideo = () => {
    navigate("/");
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center" data-testid="video-page">
        <div className="animate-spin w-8 h-8 border-4 border-primary border-t-transparent rounded-full" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4" data-testid="video-page-error">
        <p className="text-destructive text-lg">{error}</p>
        <Button onClick={() => navigate("/")} variant="outline">
          <Home className="w-4 h-4 mr-2" />
          На главную
        </Button>
      </div>
    );
  }

  const isProcessing = project?.status === "pending" || project?.status === "processing";
  const isCompleted = project?.status === "completed";
  const hasError = project?.status === "error";

  return (
    <div className="min-h-screen flex flex-col" data-testid="video-page">
      {/* Background */}
      <div className="fixed inset-0 hero-gradient pointer-events-none" />
      <div className="noise-overlay" />

      {/* Header */}
      <header className="relative z-10 p-4 md:p-6 flex items-center justify-between">
        <button
          onClick={() => navigate("/")}
          className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
          data-testid="back-button"
        >
          <ArrowLeft className="w-5 h-5" />
          <span className="hidden sm:inline">Назад</span>
        </button>

        {isCompleted && (
          <div className="flex items-center gap-2">
            <Button
              onClick={handleShare}
              variant="outline"
              size="sm"
              className="rounded-full"
              data-testid="share-button"
            >
              <Share2 className="w-4 h-4 mr-2" />
              Поделиться
            </Button>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main className="flex-1 flex flex-col items-center justify-center px-4 md:px-8 pb-8">
        {/* Title */}
        <h1 className="text-2xl md:text-3xl font-bold font-['Chivo'] text-center mb-6 max-w-lg">
          {project?.title || "Генерация видео..."}
        </h1>

        {/* Processing State */}
        {isProcessing && (
          <div className="w-full max-w-md">
            <GenerationProgress
              progress={project?.progress || 0}
              message={project?.progress_message || "Обработка..."}
            />
          </div>
        )}

        {/* Error State */}
        {hasError && (
          <div className="text-center space-y-4" data-testid="video-error-state">
            <div className="p-6 rounded-2xl bg-destructive/10 border border-destructive/20 max-w-md">
              <p className="text-destructive font-medium mb-2">Произошла ошибка</p>
              <p className="text-sm text-muted-foreground">{project?.error}</p>
            </div>
            <Button onClick={handleNewVideo} variant="outline" className="rounded-full">
              <RotateCcw className="w-4 h-4 mr-2" />
              Попробовать снова
            </Button>
          </div>
        )}

        {/* Completed State - Video Player */}
        {isCompleted && project?.scenes && (
          <div className="w-full max-w-md mx-auto space-y-6">
            {/* Use GameplayClipPlayer for gameplay_clip format */}
            {project.format_id === "gameplay_clip" ? (
              <GameplayClipPlayer
                project={project}
                audioUrl={project.audio_url ? `${BACKEND_URL}${project.audio_url}` : null}
              />
            ) : (
              <VideoPlayer
                scenes={project.scenes.map(s => ({
                  ...s,
                  image_url: s.image_url ? `${BACKEND_URL}${s.image_url}` : null
                }))}
                audioUrl={project.audio_url ? `${BACKEND_URL}${project.audio_url}` : null}
                title={project.title}
              />
            )}

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-3">
              <Button
                onClick={handleNewVideo}
                className="flex-1 bg-primary hover:bg-primary/90 rounded-full"
                data-testid="new-video-button"
              >
                <Home className="w-4 h-4 mr-2" />
                Создать новое
              </Button>
            </div>

            {/* YouTube URL for gameplay_clip */}
            {project.format_id === "gameplay_clip" && project.youtube_url && (
              <div className="glass-card rounded-2xl p-4">
                <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-wider mb-2">
                  YouTube видео
                </h3>
                <a 
                  href={project.youtube_url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-sm text-primary hover:underline break-all"
                >
                  {project.youtube_url}
                </a>
              </div>
            )}

            {/* Script Preview */}
            {project.script && (
              <div className="glass-card rounded-2xl p-4 mt-6">
                <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-wider mb-2">
                  {project.format_id === "gameplay_clip" ? "Субтитры" : "Скрипт"}
                </h3>
                <p className="text-sm text-foreground/80 leading-relaxed">
                  {project.script}
                </p>
              </div>
            )}
          </div>
        )}

        {/* Original Prompt */}
        <div className="mt-8 text-center">
          <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Промт</p>
          <p className="text-sm text-foreground/60 max-w-md">{project?.prompt}</p>
        </div>
      </main>
    </div>
  );
};

export default VideoPage;
