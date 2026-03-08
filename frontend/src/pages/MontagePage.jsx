import { useState, useEffect, useRef, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { 
  ArrowLeft, Upload, Music, Play, Loader2, Sparkles, 
  Film, Zap, Youtube, Laugh, Clapperboard, Check
} from "lucide-react";
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

const STYLE_ICONS = {
  tiktok: <Zap className="w-6 h-6" />,
  youtube: <Youtube className="w-6 h-6" />,
  meme: <Laugh className="w-6 h-6" />,
  cinematic: <Clapperboard className="w-6 h-6" />
};

const STYLE_COLORS = {
  tiktok: "from-pink-500/20 to-cyan-500/20",
  youtube: "from-red-500/20 to-orange-500/20",
  meme: "from-yellow-500/20 to-green-500/20",
  cinematic: "from-purple-500/20 to-blue-500/20"
};

export const MontagePage = () => {
  const navigate = useNavigate();
  const [styles, setStyles] = useState([]);
  const [selectedStyle, setSelectedStyle] = useState("tiktok");
  const [videoFile, setVideoFile] = useState(null);
  const [videoUrl, setVideoUrl] = useState(null);
  const [videoPreview, setVideoPreview] = useState(null);
  const [musicFile, setMusicFile] = useState(null);
  const [musicUrl, setMusicUrl] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [progressMessage, setProgressMessage] = useState("");
  const [montageId, setMontageId] = useState(null);
  const [resultVideoUrl, setResultVideoUrl] = useState(null);
  
  const videoInputRef = useRef(null);
  const musicInputRef = useRef(null);
  const stars = useMemo(() => generateStars(100), []);

  useEffect(() => {
    fetchStyles();
  }, []);

  useEffect(() => {
    if (montageId) {
      const interval = setInterval(checkProgress, 2000);
      return () => clearInterval(interval);
    }
  }, [montageId]);

  const fetchStyles = async () => {
    try {
      const response = await axios.get(`${API}/montage/styles`);
      setStyles(response.data.styles);
    } catch (error) {
      console.error("Failed to fetch styles:", error);
      // Fallback styles
      setStyles([
        { id: "tiktok", name: "TikTok/Reels", name_ru: "TikTok/Reels" },
        { id: "youtube", name: "YouTube", name_ru: "YouTube" },
        { id: "meme", name: "Meme/Comedy", name_ru: "Мемы/Комедия" },
        { id: "cinematic", name: "Cinematic", name_ru: "Кинематографичный" }
      ]);
    }
  };

  const handleVideoSelect = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    if (!file.type.startsWith("video/")) {
      toast.error("Пожалуйста, выберите видео файл");
      return;
    }
    
    const fileSizeMB = file.size / (1024 * 1024);
    setVideoFile(file);
    setVideoPreview(URL.createObjectURL(file));
    
    setIsUploading(true);
    setProgress(0);
    
    try {
      // Use chunked upload for files > 5MB
      if (fileSizeMB > 5) {
        setProgressMessage(`Загружаем ${fileSizeMB.toFixed(0)} MB по частям...`);
        const url = await uploadFileChunked(file);
        setVideoUrl(url);
      } else {
        // Small files - direct upload
        setProgressMessage("Загружаем видео...");
        const formData = new FormData();
        formData.append("file", file);
        
        const response = await axios.post(`${API}/upload`, formData, {
          headers: { "Content-Type": "multipart/form-data" },
          timeout: 300000,
          onUploadProgress: (progressEvent) => {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setProgress(percentCompleted);
            setProgressMessage(`Загружаем видео... ${percentCompleted}%`);
          }
        });
        setVideoUrl(response.data.url);
      }
      
      setProgress(0);
      setProgressMessage("");
      toast.success("Видео загружено!");
    } catch (error) {
      console.error("Video upload failed:", error);
      toast.error(error.message || "Ошибка загрузки видео");
      setVideoFile(null);
      setVideoPreview(null);
    } finally {
      setIsUploading(false);
    }
  };
  
  // Chunked upload for large files
  const uploadFileChunked = async (file) => {
    const CHUNK_SIZE = 2 * 1024 * 1024; // 2MB chunks
    const totalChunks = Math.ceil(file.size / CHUNK_SIZE);
    
    // Initialize upload
    const initResponse = await axios.post(`${API}/upload/init`, {
      filename: file.name,
      total_size: file.size,
      total_chunks: totalChunks
    });
    
    const uploadId = initResponse.data.upload_id;
    
    // Upload chunks
    for (let i = 0; i < totalChunks; i++) {
      const start = i * CHUNK_SIZE;
      const end = Math.min(start + CHUNK_SIZE, file.size);
      const chunk = file.slice(start, end);
      
      // Convert to base64
      const arrayBuffer = await chunk.arrayBuffer();
      const base64 = btoa(
        new Uint8Array(arrayBuffer).reduce((data, byte) => data + String.fromCharCode(byte), '')
      );
      
      await axios.post(`${API}/upload/chunk`, {
        upload_id: uploadId,
        chunk_index: i,
        data: base64
      });
      
      const percentCompleted = Math.round(((i + 1) / totalChunks) * 100);
      setProgress(percentCompleted);
      setProgressMessage(`Загружаем часть ${i + 1}/${totalChunks}... ${percentCompleted}%`);
    }
    
    // Complete upload
    const completeResponse = await axios.post(`${API}/upload/complete?upload_id=${uploadId}`);
    return completeResponse.data.url;
  };

  const handleMusicSelect = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    if (!file.type.startsWith("audio/")) {
      toast.error("Пожалуйста, выберите аудио файл");
      return;
    }
    
    setMusicFile(file);
    
    // Upload music
    const formData = new FormData();
    formData.append("file", file);
    
    try {
      const response = await axios.post(`${API}/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      setMusicUrl(response.data.url);
      toast.success("Музыка загружена");
    } catch (error) {
      console.error("Music upload failed:", error);
      toast.error("Ошибка загрузки музыки");
      setMusicFile(null);
    }
  };

  const startMontage = async () => {
    if (!videoUrl) {
      toast.error("Сначала загрузите видео");
      return;
    }
    
    setIsProcessing(true);
    setProgress(0);
    setProgressMessage("Запускаем AI монтаж...");
    
    try {
      const response = await axios.post(`${API}/montage/create`, {
        video_url: videoUrl,
        style: selectedStyle,
        music_url: musicUrl
      });
      
      setMontageId(response.data.id);
      toast.success("Монтаж запущен! AI анализирует видео...");
    } catch (error) {
      console.error("Failed to start montage:", error);
      toast.error("Ошибка запуска монтажа");
      setIsProcessing(false);
    }
  };

  const checkProgress = async () => {
    if (!montageId) return;
    
    try {
      const response = await axios.get(`${API}/montage/${montageId}`);
      const data = response.data;
      
      setProgress(data.progress || 0);
      setProgressMessage(data.progress_message || "");
      
      if (data.status === "completed") {
        setIsProcessing(false);
        setMontageId(null);
        toast.success("Монтаж готов!");
        // Save result URL for display
        if (data.video_url) {
          setResultVideoUrl(`${BACKEND_URL}${data.video_url}`);
        }
      } else if (data.status === "error") {
        setIsProcessing(false);
        setMontageId(null);
        toast.error(`Ошибка: ${data.error}`);
      }
    } catch (error) {
      console.error("Failed to check progress:", error);
    }
  };

  return (
    <div className="min-h-screen bg-black relative overflow-hidden" data-testid="montage-page">
      {/* Space Background */}
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
        <div className="flex items-center gap-2">
          <Film className="w-5 h-5 text-purple-400" />
          <span className="font-semibold">AI Монтаж</span>
        </div>
        <div className="w-10" />
      </header>

      {/* Main Content */}
      <main className="relative z-10 px-4 pb-24 max-w-2xl mx-auto">
        {/* Title */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold mb-2">AI Видеомонтаж</h1>
          <p className="text-white/60">
            Загрузите видео — AI найдёт лучшие моменты и создаст монтаж
          </p>
        </div>

        {/* Video Upload */}
        <div className="mb-6">
          <label className="block text-white/80 mb-2 font-medium">
            1. Загрузите видео
          </label>
          
          {videoPreview ? (
            <div className="relative rounded-2xl overflow-hidden glass-ios">
              <video
                src={videoPreview}
                className="w-full aspect-video object-cover"
                controls
              />
              <button
                onClick={() => {
                  setVideoFile(null);
                  setVideoPreview(null);
                  setVideoUrl(null);
                }}
                className="absolute top-2 right-2 p-2 rounded-full bg-black/60 hover:bg-black/80"
              >
                ✕
              </button>
            </div>
          ) : (
            <button
              onClick={() => videoInputRef.current.click()}
              disabled={isUploading}
              className="w-full py-12 rounded-2xl glass-ios border-2 border-dashed border-white/20 hover:border-white/40 transition-colors flex flex-col items-center gap-3"
              data-testid="upload-video-btn"
            >
              {isUploading ? (
                <Loader2 className="w-10 h-10 animate-spin text-white/60" />
              ) : (
                <>
                  <Upload className="w-10 h-10 text-white/60" />
                  <span className="text-white/60">Нажмите чтобы загрузить видео</span>
                </>
              )}
            </button>
          )}
          
          <input
            type="file"
            ref={videoInputRef}
            onChange={handleVideoSelect}
            accept="video/*"
            className="hidden"
          />
        </div>

        {/* Style Selection */}
        <div className="mb-6">
          <label className="block text-white/80 mb-2 font-medium">
            2. Выберите стиль монтажа
          </label>
          
          <div className="grid grid-cols-2 gap-3">
            {styles.map((style) => (
              <button
                key={style.id}
                onClick={() => setSelectedStyle(style.id)}
                className={`p-4 rounded-xl glass-ios bg-gradient-to-br ${STYLE_COLORS[style.id]} transition-all ${
                  selectedStyle === style.id ? 'ring-2 ring-white' : ''
                }`}
                data-testid={`style-${style.id}`}
              >
                <div className="flex items-center gap-3">
                  {STYLE_ICONS[style.id]}
                  <div className="text-left">
                    <p className="font-medium">{style.name_ru}</p>
                    <p className="text-xs text-white/50">{style.name}</p>
                  </div>
                  {selectedStyle === style.id && (
                    <Check className="w-5 h-5 ml-auto text-green-400" />
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Music Upload (Optional) */}
        <div className="mb-8">
          <label className="block text-white/80 mb-2 font-medium">
            3. Добавьте музыку (опционально)
          </label>
          
          <button
            onClick={() => musicInputRef.current.click()}
            className={`w-full py-4 rounded-xl glass-ios flex items-center justify-center gap-3 transition-colors ${
              musicFile ? 'bg-green-500/20' : 'hover:bg-white/5'
            }`}
            data-testid="upload-music-btn"
          >
            <Music className="w-5 h-5" />
            <span>{musicFile ? musicFile.name : "Выбрать музыку"}</span>
            {musicFile && <Check className="w-5 h-5 text-green-400" />}
          </button>
          
          <input
            type="file"
            ref={musicInputRef}
            onChange={handleMusicSelect}
            accept="audio/*"
            className="hidden"
          />
        </div>

        {/* Progress */}
        {isProcessing && (
          <div className="mb-6 glass-ios rounded-2xl p-4">
            <div className="flex items-center gap-3 mb-3">
              <Loader2 className="w-5 h-5 animate-spin text-purple-400" />
              <span className="text-white/80">{progressMessage}</span>
            </div>
            <div className="h-2 bg-white/10 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="text-center text-white/40 text-xs mt-2">{progress}%</p>
          </div>
        )}

        {/* Start Button */}
        <button
          onClick={startMontage}
          disabled={!videoUrl || isProcessing}
          className="w-full py-4 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 text-white font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-all hover:from-purple-600 hover:to-pink-600 flex items-center justify-center gap-2"
          data-testid="start-montage-btn"
        >
          {isProcessing ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Создаём монтаж...
            </>
          ) : (
            <>
              <Sparkles className="w-5 h-5" />
              Создать AI монтаж
            </>
          )}
        </button>

        {/* Result Video */}
        {resultVideoUrl && (
          <div className="mt-6 glass-ios rounded-2xl p-4" data-testid="result-section">
            <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
              <Check className="w-5 h-5 text-green-400" />
              Ваш монтаж готов!
            </h3>
            <video
              src={resultVideoUrl}
              className="w-full rounded-xl mb-4"
              controls
              autoPlay
            />
            <div className="flex gap-3">
              <a
                href={resultVideoUrl}
                download
                className="flex-1 py-3 rounded-xl bg-white/10 hover:bg-white/20 transition-colors flex items-center justify-center gap-2 font-medium"
                data-testid="download-btn"
              >
                <Film className="w-5 h-5" />
                Скачать
              </a>
              <button
                onClick={() => {
                  setResultVideoUrl(null);
                  setVideoFile(null);
                  setVideoPreview(null);
                  setVideoUrl(null);
                }}
                className="flex-1 py-3 rounded-xl bg-purple-500/20 hover:bg-purple-500/30 transition-colors flex items-center justify-center gap-2 font-medium"
                data-testid="new-montage-btn"
              >
                <Sparkles className="w-5 h-5" />
                Новый монтаж
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default MontagePage;
