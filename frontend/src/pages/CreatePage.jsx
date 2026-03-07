import { useState, useRef, useEffect, useMemo } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { ArrowLeft, Image, Video, Send, X, Sparkles, Plus, Package, Tag } from "lucide-react";
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
  const [logoFile, setLogoFile] = useState(null); // Brand logo
  const [brandName, setBrandName] = useState(""); // Brand name
  const [isLoading, setIsLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [showProductOptions, setShowProductOptions] = useState(false);
  
  const fileInputRef = useRef(null);
  const logoInputRef = useRef(null);
  const stars = useMemo(() => generateStars(100), []);

  // Detect if prompt is about product advertisement
  const isProductAd = useMemo(() => {
    const productKeywords = ['реклам', 'товар', 'продукт', 'product', 'advertis', 'showcase', 'commercial', 'macbook', 'iphone'];
    return productKeywords.some(kw => prompt.toLowerCase().includes(kw));
  }, [prompt]);

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
    if (!prompt.trim()) {
      toast.error("Введите описание");
      return;
    }

    setIsLoading(true);
    try {
      const requestData = {
        prompt: prompt.trim(),
        format_id: "auto",  // Smart auto-detection
        language: "auto"
      };
      
      // Add product advertisement data if available
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
        {/* Product Images Preview */}
        {mediaFiles.length > 0 ? (
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
              или добавьте фото/видео продукта
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
            <p className="text-center text-white/40 text-xs mt-1">Загрузка {uploadProgress}%</p>
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
              data-testid="add-image-btn"
            >
              <Image className="w-5 h-5 text-white/60" />
            </button>
            <button
              onClick={() => {
                fileInputRef.current.accept = "video/*";
                fileInputRef.current.multiple = false;
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
