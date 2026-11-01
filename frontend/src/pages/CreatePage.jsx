import { useState, useRef, useEffect, useMemo } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { ArrowLeft, Image, Video, Send, X, Sparkles, Plus, Package, Tag, Film, Music, Loader2, Check, Download } from "lucide-react";
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
  const [mediaFiles, setMediaFiles] = useState([]); // Product images
  const [videoFile, setVideoFile] = useState(null); // Video for montage
  const [videoUrl, setVideoUrl] = useState(null); // Uploaded video URL
  const [videoPreview, setVideoPreview] = useState(null);
  const [musicFile, setMusicFile] = useState(null);
  const [musicUrl, setMusicUrl] = useState(null);
  const [logoFile, setLogoFile] = useState(null); // Brand logo
  const [brandName, setBrandName] = useState(""); // Brand name
  const [isLoading, setIsLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadMessage, setUploadMessage] = useState("");
  const [showProductOptions, setShowProductOptions] = useState(false);
  const [montageResult, setMontageResult] = useState(null);
  const [montageProgress, setMontageProgress] = useState(0);
  const [montageMessage, setMontageMessage] = useState("");
  
  const fileInputRef = useRef(null);
  const videoInputRef = useRef(null);
  const musicInputRef = useRef(null);
  const logoInputRef = useRef(null);
  const stars = useMemo(() => generateStars(100), []);

  // Prevent leaving page during upload
  useEffect(() => {
    const handleBeforeUnload = (e) => {
      if (uploadProgress > 0 || isLoading) {
        e.preventDefault();
        e.returnValue = 'Загрузка в процессе! Если вы уйдёте, загрузка прервётся.';
        return e.returnValue;
      }
    };
    
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [uploadProgress, isLoading]);

  // Detect if prompt is about product advertisement
  const isProductAd = useMemo(() => {
    const productKeywords = ['реклам', 'товар', 'продукт', 'product', 'advertis', 'showcase', 'commercial', 'macbook', 'iphone'];
    return productKeywords.some(kw => prompt.toLowerCase().includes(kw));
  }, [prompt]);

  // Chunked upload for large files
  const uploadFileChunked = async (file, onProgress) => {
    const CHUNK_SIZE = 1 * 1024 * 1024; // 1MB chunks to bypass proxy limits
    const totalChunks = Math.ceil(file.size / CHUNK_SIZE);
    
    console.log(`Starting chunked upload: ${file.size} bytes, ${totalChunks} chunks`);
    
    const initResponse = await axios.post(`${API}/upload/init`, {
      filename: file.name,
      total_size: file.size,
      total_chunks: totalChunks
    });
    
    const uploadId = initResponse.data.upload_id;
    console.log(`Upload ID: ${uploadId}`);
    
    for (let i = 0; i < totalChunks; i++) {
      const start = i * CHUNK_SIZE;
      const end = Math.min(start + CHUNK_SIZE, file.size);
      const chunk = file.slice(start, end);
      
      const arrayBuffer = await chunk.arrayBuffer();
      const base64 = btoa(
        new Uint8Array(arrayBuffer).reduce((data, byte) => data + String.fromCharCode(byte), '')
      );
      
      await axios.post(`${API}/upload/chunk`, {
        upload_id: uploadId,
        chunk_index: i,
        data: base64
      }, { timeout: 60000 });
      
      if (onProgress) {
        onProgress(Math.round(((i + 1) / totalChunks) * 100), `Часть ${i + 1}/${totalChunks}`);
      }
      console.log(`Uploaded chunk ${i + 1}/${totalChunks}`);
    }
    
    const completeResponse = await axios.post(`${API}/upload/complete?upload_id=${uploadId}`);
    console.log(`Upload complete: ${completeResponse.data.url}`);
    return completeResponse.data.url;
  };

  // Handle video file selection for montage
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
    setUploadProgress(0);
    
    try {
      // ALWAYS use chunked upload for videos to bypass proxy size limits
      setUploadMessage(`Загружаем ${fileSizeMB.toFixed(1)} MB по частям...`);
      toast.info(`Загрузка ${fileSizeMB.toFixed(1)} MB видео...`);
      
      const url = await uploadFileChunked(file, (progress, msg) => {
        setUploadProgress(progress);
        setUploadMessage(msg);
      });
      setVideoUrl(url);
      
      setUploadProgress(0);
      setUploadMessage("");
      toast.success("Видео загружено!");
    } catch (error) {
      console.error("Video upload failed:", error);
      toast.error(`Ошибка загрузки: ${error.message || 'Попробуйте ещё раз'}`);
      setVideoFile(null);
      setVideoPreview(null);
    }
  };

  // Handle music file selection
  const handleMusicSelect = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    if (!file.type.startsWith("audio/")) {
      toast.error("Пожалуйста, выберите аудио файл");
      return;
    }
    
    setMusicFile(file);
    
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

  const removeVideo = () => {
    if (videoPreview) URL.revokeObjectURL(videoPreview);
    setVideoFile(null);
    setVideoPreview(null);
    setVideoUrl(null);
    setMontageResult(null);
  };

  const removeMusic = () => {
    setMusicFile(null);
    setMusicUrl(null);
  };
  const handleFileSelect = async (e) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;
    
    setUploadProgress(0);
    const uploadedUrls = [];
    
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const formData = new FormData();
      formData.append("file", file);
      
      try {
        const response = await axios.post(`${API}/upload`, formData, {
          headers: { "Content-Type": "multipart/form-data" },
          onUploadProgress: (progressEvent) => {
            const progress = Math.round(
              ((i + progressEvent.loaded / progressEvent.total) / files.length) * 100
            );
            setUploadProgress(progress);
          }
        });
        
        uploadedUrls.push({
          url: response.data.url,
          preview: URL.createObjectURL(file),
          type: file.type.startsWith("video") ? "video" : "image"
        });
      } catch (error) {
        console.error("Upload failed:", error);
        toast.error(`Ошибка загрузки: ${file.name}`);
      }
    }
    
    setMediaFiles(prev => [...prev, ...uploadedUrls]);
    setUploadProgress(0);
    toast.success(`Загружено ${uploadedUrls.length} файл(ов)`);
  };

  const handleLogoSelect = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append("file", file);
    
    try {
      const response = await axios.post(`${API}/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      
      setLogoFile({
        url: response.data.url,
        preview: URL.createObjectURL(file)
      });
      toast.success("Логотип загружен");
    } catch (error) {
      console.error("Logo upload failed:", error);
      toast.error("Ошибка загрузки логотипа");
    }
  };

  const removeMedia = (index) => {
    setMediaFiles(prev => {
      const newFiles = [...prev];
      if (newFiles[index]?.preview) {
        URL.revokeObjectURL(newFiles[index].preview);
      }
      newFiles.splice(index, 1);
      return newFiles;
    });
  };

  const removeLogo = () => {
    if (logoFile?.preview) {
      URL.revokeObjectURL(logoFile.preview);
    }
    setLogoFile(null);
  };

  const handleSubmit = async () => {
    // For device mockup, prompt is optional
    if (!videoUrl && !prompt.trim()) {
      toast.error("Введите описание");
      return;
    }

    setIsLoading(true);
    
    try {
      // If video is uploaded, create 3D device mockup animation
      if (videoUrl) {
        setMontageMessage("Создаём 3D анимацию устройства...");
        setMontageProgress(10);
        
        // Send to device mockup endpoint - phone FULLY VISIBLE
        const response = await axios.post(`${API}/device-mockup/create`, {
          video_url: videoUrl,
          device_type: "phone",
          rotation: 12,
          bg_color: [100, 20, 20],  // Dark red gradient
          animation_style: "camera",  // Camera movement (zoom + rotate)
          phone_position: "center",
          aspect_ratio: "9:16"  // Portrait format
        });
        
        const projectId = response.data.id;
        setMontageProgress(30);
        setMontageMessage("Рендерим cinematic анимацию...");
        
        // Poll for progress
        const pollInterval = setInterval(async () => {
          try {
            const statusRes = await axios.get(`${API}/video/${projectId}`);
            const data = statusRes.data;
            
            // Estimate progress based on status
            if (data.status === "processing") {
              setMontageProgress(prev => Math.min(prev + 5, 85));
              setMontageMessage("Создаём плавную 3D анимацию...");
            }
            
            if (data.status === "completed" && data.video_url) {
              clearInterval(pollInterval);
              setMontageResult(`${BACKEND_URL}${data.video_url}`);
              setMontageProgress(100);
              setMontageMessage("Готово!");
              setIsLoading(false);
              toast.success("Cinematic анимация готова!");
            } else if (data.status === "failed") {
              clearInterval(pollInterval);
              setIsLoading(false);
              toast.error(`Ошибка: ${data.error || "Не удалось создать"}`);
            }
          } catch (e) {
            console.error("Poll error:", e);
          }
        }, 2000);
        
        return;
      }
      
      // Standard video generation (no video uploaded)
      const requestData = {
        prompt: prompt.trim(),
        format_id: "auto",
        language: "auto"
      };
      
      if (mediaFiles.length > 0) {
        requestData.product_images = mediaFiles.map(f => f.url);
      }
      if (logoFile) {
        requestData.logo_url = logoFile.url;
      }
      if (brandName.trim()) {
        requestData.brand_name = brandName.trim();
      }
      
      const response = await axios.post(`${API}/video/generate`, requestData);
      
      toast.success("Генерация началась! AI анализирует ваш промт...");
      navigate(`/video/${response.data.id}`);
    } catch (error) {
      console.error("Failed to start generation:", error);
      toast.error("Ошибка при запуске генерации");
    } finally {
      if (!videoUrl) setIsLoading(false);
    }
  };

  const resetMontage = () => {
    setMontageResult(null);
    setMontageProgress(0);
    setMontageMessage("");
    removeVideo();
    setPrompt("");
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
          onClick={() => {
            if (uploadProgress > 0 || isLoading) {
              toast.warning("Дождитесь завершения загрузки!");
              return;
            }
            navigate("/");
          }}
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
        
        {/* Montage Result */}
        {montageResult ? (
          <div className="w-full max-w-md" data-testid="montage-result">
            <div className="flex items-center gap-2 mb-3">
              <Check className="w-5 h-5 text-green-400" />
              <span className="text-white font-medium">3D анимация готова!</span>
            </div>
            <div className="glass-ios rounded-2xl overflow-hidden">
              <video
                src={montageResult}
                className="w-full aspect-video"
                controls
                autoPlay
              />
            </div>
            <div className="flex gap-3 mt-4">
              <a
                href={montageResult}
                download
                className="flex-1 py-3 rounded-xl glass-ios hover:bg-white/10 transition-colors flex items-center justify-center gap-2 font-medium"
                data-testid="download-montage"
              >
                <Download className="w-5 h-5" />
                Скачать
              </a>
              <button
                onClick={resetMontage}
                className="flex-1 py-3 rounded-xl bg-purple-500/20 hover:bg-purple-500/30 transition-colors flex items-center justify-center gap-2 font-medium"
                data-testid="new-montage"
              >
                <Sparkles className="w-5 h-5" />
                Создать ещё
              </button>
            </div>
          </div>
        ) : montageProgress > 0 ? (
          /* Montage Progress */
          <div className="w-full max-w-md" data-testid="montage-progress">
            <div className="glass-ios rounded-2xl p-6">
              <div className="flex items-center gap-3 mb-4">
                <Loader2 className="w-6 h-6 animate-spin text-purple-400" />
                <span className="text-white">{montageMessage}</span>
              </div>
              <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-500"
                  style={{ width: `${montageProgress}%` }}
                />
              </div>
              <p className="text-center text-white/40 text-sm mt-2">{montageProgress}%</p>
            </div>
          </div>
        ) : videoPreview ? (
          /* Video Preview for 3D Device Mockup */
          <div className="w-full max-w-md" data-testid="video-preview">
            <div className="flex items-center gap-2 mb-3">
              <Film className="w-5 h-5 text-purple-400" />
              <span className="text-white/60 text-sm">Видео для 3D анимации</span>
            </div>
            <div className="relative glass-ios rounded-2xl overflow-hidden">
              <video
                src={videoPreview}
                className="w-full aspect-video object-cover"
                controls
              />
              <button
                onClick={removeVideo}
                className="absolute top-2 right-2 p-2 rounded-full bg-black/60 hover:bg-black/80 transition-colors"
                data-testid="remove-video"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            
            <p className="text-white/40 text-sm text-center mt-3">
              Видео будет показано на 3D телефоне с анимацией. Нажмите отправить.
            </p>
          </div>
        ) : mediaFiles.length > 0 ? (
          /* Product Images Preview */
          <div className="w-full max-w-md">
            <div className="flex items-center gap-2 mb-3">
              <Package className="w-5 h-5 text-white/60" />
              <span className="text-white/60 text-sm">Изображения продукта ({mediaFiles.length})</span>
            </div>
            <div className="grid grid-cols-3 gap-2">
              {mediaFiles.map((file, index) => (
                <div key={index} className="relative aspect-square rounded-xl overflow-hidden glass-ios">
                  <img
                    src={file.preview}
                    alt={`Product ${index + 1}`}
                    className="w-full h-full object-cover"
                  />
                  <button
                    onClick={() => removeMedia(index)}
                    className="absolute top-1 right-1 p-1 rounded-full bg-black/60 hover:bg-black/80 transition-colors"
                    data-testid={`remove-media-${index}`}
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))}
              <button
                onClick={() => {
                  fileInputRef.current.accept = "image/*";
                  fileInputRef.current.multiple = true;
                  fileInputRef.current.click();
                }}
                className="aspect-square rounded-xl glass-ios flex items-center justify-center hover:bg-white/10 transition-colors"
                data-testid="add-more-images"
              >
                <Plus className="w-6 h-6 text-white/40" />
              </button>
            </div>
            
            {/* Logo preview */}
            {logoFile && (
              <div className="mt-4 flex items-center gap-3">
                <div className="relative w-16 h-16 rounded-xl overflow-hidden glass-ios">
                  <img
                    src={logoFile.preview}
                    alt="Logo"
                    className="w-full h-full object-contain p-2"
                  />
                  <button
                    onClick={removeLogo}
                    className="absolute top-0 right-0 p-1 rounded-full bg-black/60"
                    data-testid="remove-logo"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
                <div className="flex-1">
                  <input
                    type="text"
                    value={brandName}
                    onChange={(e) => setBrandName(e.target.value)}
                    placeholder="Название бренда"
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white placeholder:text-white/40 outline-none focus:border-white/30"
                    data-testid="brand-name-input"
                  />
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center animate-float">
            <Sparkles className="w-16 h-16 mx-auto mb-4 text-white/30" />
            <p className="text-white/50 text-lg">
              Опишите что хотите создать
            </p>
            <p className="text-white/30 text-sm mt-2">
              или загрузите видео для 3D анимации на устройстве
            </p>
          </div>
        )}
        
        {/* Upload Progress */}
        {uploadProgress > 0 && (
          <div className="w-full max-w-md mt-4">
            <div className="h-1 bg-white/10 rounded-full overflow-hidden">
              <div 
                className="h-full bg-white transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
            <p className="text-center text-white/40 text-xs mt-1">{uploadMessage || `Загрузка ${uploadProgress}%`}</p>
          </div>
        )}
      </main>

      {/* Product Options Panel */}
      {(isProductAd || showProductOptions) && mediaFiles.length === 0 && (
        <div className="relative z-10 px-4 pb-4">
          <div className="glass-ios rounded-2xl p-4 max-w-md mx-auto">
            <div className="flex items-center gap-2 mb-3">
              <Package className="w-5 h-5 text-purple-400" />
              <span className="text-white font-medium">Реклама продукта</span>
            </div>
            <p className="text-white/50 text-sm mb-3">
              Добавьте изображения вашего продукта или AI создаст их по описанию
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => {
                  fileInputRef.current.accept = "image/*";
                  fileInputRef.current.multiple = true;
                  fileInputRef.current.click();
                }}
                className="flex-1 py-2 rounded-xl bg-white/10 text-white text-sm hover:bg-white/20 transition-colors flex items-center justify-center gap-2"
                data-testid="upload-product-images"
              >
                <Image className="w-4 h-4" />
                Загрузить фото
              </button>
              <button
                onClick={() => {
                  logoInputRef.current.click();
                }}
                className="flex-1 py-2 rounded-xl bg-white/10 text-white text-sm hover:bg-white/20 transition-colors flex items-center justify-center gap-2"
                data-testid="upload-logo"
              >
                <Tag className="w-4 h-4" />
                Загрузить лого
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Bottom Input Area */}
      <div className="prompt-input-container">
        <div className="glass-ios rounded-[28px] p-2">
          <div className="flex items-center gap-2">
            {/* Add Media Buttons */}
            <button
              onClick={() => {
                fileInputRef.current.accept = "image/*";
                fileInputRef.current.multiple = true;
                fileInputRef.current.click();
              }}
              className="p-3 rounded-full hover:bg-white/10 transition-colors"
              title="Добавить изображения"
              data-testid="add-image-btn"
            >
              <Image className="w-5 h-5 text-white/60" />
            </button>
            <button
              onClick={() => videoInputRef.current.click()}
              className={`p-3 rounded-full hover:bg-white/10 transition-colors ${videoFile ? 'bg-purple-500/20' : ''}`}
              title="Загрузить видео для монтажа"
              data-testid="add-video-btn"
            >
              <Video className="w-5 h-5 text-white/60" />
            </button>
            
            {/* Input Field */}
            <input
              type="text"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder={videoFile ? "Описание для 3D анимации (опционально)" : "Опишите ваше видео..."}
              className="flex-1 bg-transparent border-none outline-none text-white placeholder:text-white/40 py-2"
              onKeyDown={(e) => e.key === "Enter" && !isLoading && handleSubmit()}
              disabled={isLoading}
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
        
        {/* Hidden file inputs */}
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileSelect}
          className="hidden"
          data-testid="file-input"
        />
        <input
          type="file"
          ref={videoInputRef}
          onChange={handleVideoSelect}
          accept="video/*"
          className="hidden"
          data-testid="video-input"
        />
        <input
          type="file"
          ref={musicInputRef}
          onChange={handleMusicSelect}
          accept="audio/*"
          className="hidden"
          data-testid="music-input"
        />
        <input
          type="file"
          ref={logoInputRef}
          onChange={handleLogoSelect}
          accept="image/*"
          className="hidden"
          data-testid="logo-input"
        />
      </div>
    </div>
  );
};

export default CreatePage;
