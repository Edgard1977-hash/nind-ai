import { useState, useRef, useEffect, useMemo } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { ArrowLeft, Image, Video, Send, X, Sparkles } from "lucide-react";
import { toast } from "sonner";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Generate random stars
const generateStars = (count) => {
  return Array.from({ length: count }).map((_, i) => ({
    id: i,
    left: Math.random() * 100,
    top: Math.random() * 100,
    size: Math.random() * 2 + 1,
    delay: Math.random() * 4,
    duration: Math.random() * 3 + 2,
  }));
};

export const CreatePage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const type = searchParams.get("type") || "video";
  
  const [prompt, setPrompt] = useState("");
  const [mediaFile, setMediaFile] = useState(null);
  const [mediaPreview, setMediaPreview] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  
  const fileInputRef = useRef(null);
  const stars = useMemo(() => generateStars(100), []);

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setMediaFile(file);
      const url = URL.createObjectURL(file);
      setMediaPreview({
        url,
        type: file.type.startsWith("video") ? "video" : "image"
      });
    }
  };

  const removeMedia = () => {
    setMediaFile(null);
    if (mediaPreview?.url) {
      URL.revokeObjectURL(mediaPreview.url);
    }
    setMediaPreview(null);
  };

  const handleSubmit = async () => {
    if (!prompt.trim()) {
      toast.error("Введите описание");
      return;
    }

    setIsLoading(true);
    try {
      const response = await axios.post(`${API}/video/generate`, {
        prompt: prompt.trim(),
        format_id: "auto",  // Smart auto-detection
        language: "auto"
      });
      
      toast.success("Генерация началась! AI анализирует ваш промт...");
      navigate(`/video/${response.data.id}`);
    } catch (error) {
      console.error("Failed to start generation:", error);
      toast.error("Ошибка при запуске генерации");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black relative overflow-hidden" data-testid="create-page">
      {/* Space Background with Stars */}
      <div className="space-bg">
        <div className="stars">
          {stars.map((star) => (
            <div
              key={star.id}
              className="star"
              style={{
                left: `${star.left}%`,
                top: `${star.top}%`,
                width: `${star.size}px`,
                height: `${star.size}px`,
                animationDelay: `${star.delay}s`,
                animationDuration: `${star.duration}s`,
              }}
            />
          ))}
        </div>
      </div>

      {/* Header */}
      <header className="relative z-10 flex items-center justify-between p-4">
        <button
          onClick={() => navigate("/")}
          className="p-2 rounded-full glass-ios"
          data-testid="back-button"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <h1 className="text-lg font-semibold">
          {type === "video" ? "Создать видео" : "Создать фото"}
        </h1>
        <div className="w-10" /> {/* Spacer */}
      </header>

      {/* Main Content Area */}
      <main className="relative z-10 flex-1 flex flex-col items-center justify-center min-h-[60vh] px-4">
        {/* Media Preview */}
        {mediaPreview ? (
          <div className="media-preview-container w-full">
            <div className="media-blur-edge" />
            {mediaPreview.type === "video" ? (
              <video
                src={mediaPreview.url}
                className="media-preview"
                controls
                playsInline
              />
            ) : (
              <img
                src={mediaPreview.url}
                alt="Preview"
                className="media-preview"
              />
            )}
            <button
              onClick={removeMedia}
              className="absolute top-4 right-4 p-2 rounded-full glass-ios"
              data-testid="remove-media"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        ) : (
          <div className="text-center animate-float">
            <Sparkles className="w-16 h-16 mx-auto mb-4 text-white/30" />
            <p className="text-white/50 text-lg">
              Опишите что хотите создать
            </p>
            <p className="text-white/30 text-sm mt-2">
              или добавьте фото/видео
            </p>
          </div>
        )}
      </main>

      {/* Bottom Input Area */}
      <div className="prompt-input-container">
        <div className="glass-ios rounded-[28px] p-2">
          <div className="flex items-center gap-2">
            {/* Add Media Buttons */}
            <button
              onClick={() => {
                fileInputRef.current.accept = "image/*";
                fileInputRef.current.click();
              }}
              className="p-3 rounded-full hover:bg-white/10 transition-colors"
              data-testid="add-image-btn"
            >
              <Image className="w-5 h-5 text-white/60" />
            </button>
            <button
              onClick={() => {
                fileInputRef.current.accept = "video/*";
                fileInputRef.current.click();
              }}
              className="p-3 rounded-full hover:bg-white/10 transition-colors"
              data-testid="add-video-btn"
            >
              <Video className="w-5 h-5 text-white/60" />
            </button>
            
            {/* Input Field */}
            <input
              type="text"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Опишите ваше видео..."
              className="flex-1 bg-transparent border-none outline-none text-white placeholder:text-white/40 py-2"
              onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
              data-testid="prompt-input"
            />
            
            {/* Send Button */}
            <button
              onClick={handleSubmit}
              disabled={isLoading || !prompt.trim()}
              className="p-3 rounded-full bg-white text-black disabled:opacity-50 disabled:cursor-not-allowed transition-all hover:scale-105 active:scale-95"
              data-testid="submit-btn"
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-black/30 border-t-black rounded-full animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>
        </div>
        
        {/* Hidden file input */}
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileSelect}
          className="hidden"
          data-testid="file-input"
        />
      </div>
    </div>
  );
};

export default CreatePage;
