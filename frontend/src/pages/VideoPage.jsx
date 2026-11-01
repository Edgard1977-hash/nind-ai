import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, Download, Share2, Home, RotateCcw } from "lucide-react";
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

  const handleDownload = () => {
    if (project?.video_url) {
      const link = document.createElement("a");
      link.href = `${BACKEND_URL}${project.video_url}`;
      link.download = `${project.title || "video"}.mp4`;
      link.click();
      toast.success("Скачивание началось!");
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center" data-testid="video-page">
        <div className="w-10 h-10 border-2 border-white/30 border-t-white rounded-full animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-black flex flex-col items-center justify-center gap-4" data-testid="video-page">
        <p className="text-red-400 text-lg">{error}</p>
        <button 
          onClick={() => navigate("/")} 
          className="glass-button px-6 py-3 rounded-full flex items-center gap-2"
        >
          <Home className="w-4 h-4" />
          На главную
        </button>
      </div>
    );
  }

  const isProcessing = project?.status === "pending" || project?.status === "processing";
  const isCompleted = project?.status === "completed";
  const hasError = project?.status === "error";
  const hasVideo = project?.video_url;

  return (
    <div className="min-h-screen bg-black" data-testid="video-page">
      {/* Header */}
      <header className="flex items-center justify-between p-4">
        <button
          onClick={() => navigate("/")}
          className="p-2 rounded-full glass-ios"
          data-testid="back-button"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        
        <div className="flex gap-2">
          {hasVideo && (
            <button
              onClick={handleDownload}
              className="p-2 rounded-full glass-ios"
              data-testid="download-button"
            >
              <Download className="w-5 h-5" />
            </button>
          )}
          <button
            onClick={handleShare}
            className="p-2 rounded-full glass-ios"
            data-testid="share-button"
          >
            <Share2 className="w-5 h-5" />
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="px-4 pb-8">
        {/* Title */}
        <h1 className="text-xl font-bold text-center mb-6 px-4">
          {project?.title || "Генерация..."}
        </h1>

        {/* Processing State */}
        {isProcessing && (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="relative w-24 h-24 mb-6">
              <div className="absolute inset-0 border-4 border-white/10 rounded-full" />
              <div 
                className="absolute inset-0 border-4 border-transparent border-t-white rounded-full animate-spin"
                style={{ animationDuration: "1s" }}
              />
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-2xl font-bold">{project?.progress || 0}%</span>
              </div>
            </div>
            <p className="text-white/60 text-center">
              {project?.progress_message || "Обработка..."}
            </p>
          </div>
        )}

        {/* Error State */}
        {hasError && (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="glass-ios rounded-2xl p-6 mb-4 max-w-sm text-center">
              <p className="text-red-400 font-medium mb-2">Ошибка</p>
              <p className="text-white/60 text-sm">{project?.error}</p>
            </div>
            <button
              onClick={() => navigate("/create")}
              className="glass-button px-6 py-3 rounded-full flex items-center gap-2"
            >
              <RotateCcw className="w-4 h-4" />
              Попробовать снова
            </button>
          </div>
        )}

        {/* Completed State */}
        {isCompleted && (
          <div className="space-y-6">
            {/* Video Player */}
            {hasVideo ? (
              <div className="aspect-[9/16] max-w-sm mx-auto bg-black rounded-3xl overflow-hidden border border-white/10">
                <video
                  src={`${BACKEND_URL}${project.video_url}`}
                  poster={project.poster_url ? `${BACKEND_URL}${project.poster_url}` : undefined}
                  controls
                  playsInline
                  preload="auto"
                  className="w-full h-full object-contain"
                  data-testid="video-element"
                />
              </div>
            ) : (
              <div className="aspect-[9/16] max-w-sm mx-auto bg-white/5 rounded-3xl flex items-center justify-center">
                <p className="text-white/40">Видео недоступно</p>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-3 max-w-sm mx-auto">
              {hasVideo && (
                <button
                  onClick={handleDownload}
                  className="flex-1 glass-button py-4 rounded-[40px] font-semibold flex items-center justify-center gap-2"
                  data-testid="download-btn-main"
                >
                  <Download className="w-5 h-5" />
                  Скачать
                </button>
              )}
              <button
                onClick={() => navigate("/create")}
                className="flex-1 glass-button py-4 rounded-[40px] font-semibold flex items-center justify-center gap-2"
                data-testid="new-video-btn"
              >
                Создать ещё
              </button>
            </div>

            {/* Info */}
            {project?.script && (
              <div className="glass-ios rounded-2xl p-4 max-w-sm mx-auto">
                <p className="text-xs text-white/40 uppercase tracking-wider mb-2">Скрипт</p>
                <p className="text-white/80 text-sm line-clamp-4">{project.script}</p>
              </div>
            )}
          </div>
        )}

        {/* Prompt */}
        <div className="mt-8 text-center">
          <p className="text-xs text-white/30 uppercase tracking-wider mb-1">Промт</p>
          <p className="text-white/50 text-sm max-w-md mx-auto">{project?.prompt}</p>
        </div>
      </main>
    </div>
  );
};

export default VideoPage;
