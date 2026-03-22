import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Plus, ArrowUp, X, Loader2, Search, ChevronRight, ArrowRight } from "lucide-react";
import { toast } from "sonner";
import axios from "axios";
import AuthPopup from "../components/custom/AuthPopup";
import ProfilePage from "../components/custom/ProfilePage";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Logo image URL
const LOGO_URL = "https://customer-assets.emergentagent.com/job_ai-format-studio/artifacts/x0akmc4x_A7746620-B806-4A1B-B685-CC4290123288.png";

// Microphone icon
const MicIcon = ({ className }) => (
  <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
    <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
    <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
  </svg>
);

// Format categories
const FORMAT_TABS = ["Все", "Новые", "Видео", "Фото", "Монтаж", "Анимации"];

// Placeholder formats
const FORMATS = [
  { id: 1, name: "Формат", color: "#3A3A3A" },
  { id: 2, name: "Формат", color: "#3A3A3A" },
  { id: 3, name: "Формат", color: "#3A3A3A" },
  { id: 4, name: "Формат", color: "#3A3A3A" },
  { id: 5, name: "Формат", color: "#3A3A3A" },
  { id: 6, name: "Формат", color: "#3A3A3A" },
];

export const MainPage = () => {
  const navigate = useNavigate();
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);
  
  // State
  const [prompt, setPrompt] = useState("");
  const [user, setUser] = useState(null);
  const [showAuthPopup, setShowAuthPopup] = useState(false);
  const [showProfile, setShowProfile] = useState(false);
  const [showFormatsPopup, setShowFormatsPopup] = useState(false);
  const [isPopupClosing, setIsPopupClosing] = useState(false);
  const [attachments, setAttachments] = useState([]);
  const [uploadingFiles, setUploadingFiles] = useState({});
  const [isUploading, setIsUploading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [activeTab, setActiveTab] = useState("Все");
  const [searchQuery, setSearchQuery] = useState("");

  // Check auth status
  useEffect(() => {
    const savedUser = localStorage.getItem("slind_user");
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (e) {
        localStorage.removeItem("slind_user");
      }
    }
  }, []);

  const handleSubmit = async () => {
    if (!user) {
      setShowAuthPopup(true);
      return;
    }
    
    if (!prompt.trim() && attachments.length === 0) return;
    
    setIsGenerating(true);
    
    try {
      const requestData = {
        prompt: prompt.trim(),
        format_id: "auto",
        language: "auto"
      };
      
      if (attachments.length > 0) {
        const uploadedUrls = [];
        for (const att of attachments) {
          if (att.file && !att.uploadedUrl) {
            const formData = new FormData();
            formData.append("file", att.file);
            const uploadRes = await axios.post(`${API}/upload`, formData, {
              headers: { "Content-Type": "multipart/form-data" }
            });
            uploadedUrls.push(uploadRes.data.url);
          } else if (att.uploadedUrl) {
            uploadedUrls.push(att.uploadedUrl);
          }
        }
        
        const videoAttachment = attachments.find(a => a.type === "video");
        if (videoAttachment && uploadedUrls.length > 0) {
          const response = await axios.post(`${API}/device-mockup/create`, {
            video_url: uploadedUrls[0],
            device_type: "phone",
            rotation: 12,
            bg_color: [15, 15, 20],
            animation_style: "camera",
            phone_position: "center",
            aspect_ratio: "9:16"
          });
          
          toast.success("Создаём 3D анимацию...");
          navigate(`/video/${response.data.id}`);
          return;
        }
        
        requestData.product_images = uploadedUrls;
      }
      
      const response = await axios.post(`${API}/video/generate`, requestData);
      toast.success("Генерация началась!");
      navigate(`/video/${response.data.id}`);
    } catch (error) {
      console.error("Failed to start generation:", error);
      toast.error("Ошибка при запуске генерации");
      setIsGenerating(false);
    }
  };

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    
    files.forEach(file => {
      const id = Date.now() + Math.random();
      const isVideo = file.type.startsWith("video/");
      
      const reader = new FileReader();
      reader.onload = (event) => {
        setAttachments(prev => [...prev, {
          id,
          type: isVideo ? "video" : "image",
          preview: event.target.result,
          file,
          uploading: false,
          progress: 0
        }]);
      };
      reader.readAsDataURL(file);
    });
    
    e.target.value = "";
  };

  const removeAttachment = (id) => {
    setAttachments(prev => prev.filter(a => a.id !== id));
  };

  const handleAuthSuccess = (userData) => {
    setUser(userData);
    localStorage.setItem("slind_user", JSON.stringify(userData));
    setShowAuthPopup(false);
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem("slind_user");
    setShowProfile(false);
  };

  const handleGetStarted = () => {
    if (user) {
      setShowProfile(true);
    } else {
      setShowAuthPopup(true);
    }
  };

  const handleClosePopup = () => {
    setIsPopupClosing(true);
    setTimeout(() => {
      setShowFormatsPopup(false);
      setIsPopupClosing(false);
    }, 300);
  };

  if (showProfile && user) {
    return (
      <ProfilePage 
        user={user} 
        onBack={() => setShowProfile(false)}
        onLogout={handleLogout}
      />
    );
  }

  return (
    <div className="main-page" data-testid="main-page">
      {/* Background */}
      <div className="liquid-gradient-bg" />
      
      {/* Perspective Grid */}
      <div className="perspective-grid">
        <svg viewBox="0 0 400 300" preserveAspectRatio="none" className="grid-svg">
          {/* Vertical lines - fewer for bigger squares */}
          <line x1="0" y1="0" x2="0" y2="300" stroke="rgba(255,255,255,0.08)" strokeWidth="1"/>
          <line x1="80" y1="0" x2="80" y2="300" stroke="rgba(255,255,255,0.08)" strokeWidth="1"/>
          <line x1="160" y1="0" x2="160" y2="300" stroke="rgba(255,255,255,0.08)" strokeWidth="1"/>
          <line x1="240" y1="0" x2="240" y2="300" stroke="rgba(255,255,255,0.08)" strokeWidth="1"/>
          <line x1="320" y1="0" x2="320" y2="300" stroke="rgba(255,255,255,0.08)" strokeWidth="1"/>
          <line x1="400" y1="0" x2="400" y2="300" stroke="rgba(255,255,255,0.08)" strokeWidth="1"/>
          
          {/* Horizontal curved lines - fewer for bigger squares */}
          <path d="M0,0 Q200,0 400,0" stroke="rgba(255,255,255,0.06)" strokeWidth="1" fill="none"/>
          <path d="M0,75 Q200,65 400,75" stroke="rgba(255,255,255,0.07)" strokeWidth="1" fill="none"/>
          <path d="M0,150 Q200,130 400,150" stroke="rgba(255,255,255,0.08)" strokeWidth="1" fill="none"/>
          <path d="M0,225 Q200,195 400,225" stroke="rgba(255,255,255,0.09)" strokeWidth="1" fill="none"/>
          <path d="M0,300 Q200,260 400,300" stroke="rgba(255,255,255,0.1)" strokeWidth="1" fill="none"/>
        </svg>
      </div>
      
      {/* Fixed Header with blur */}
      <header className="fixed-header">
        <div className="header-blur" />
        <div className="header-content">
          <div className="logo-container">
            <img src={LOGO_URL} alt="Slind" className="logo-image" />
          </div>
          
          <button 
            className="get-started-btn"
            onClick={handleGetStarted}
            data-testid="get-started-btn"
          >
            Get started
          </button>
        </div>
      </header>

      {/* Main content - scrollable */}
      <div className="main-content">
        {/* Heading section */}
        <div className="heading-section">
          <h1 className="heading-main">Create more better</h1>
          <p className="heading-sub">Make content entirely with AI</p>
        </div>

        {/* Input area - centered */}
        <div className="input-area">
          <div className={`input-outer ${isUploading ? "uploading" : ""}`}>
            {attachments.length > 0 && (
              <div className="attachments-row">
                {attachments.map((attachment) => (
                  <div key={attachment.id} className="attachment-item">
                    {attachment.type === "video" && attachment.uploading ? (
                      <div className="attachment-uploading">
                        <div 
                          className="attachment-preview-blur"
                          style={{ backgroundImage: `url(${attachment.preview})` }}
                        />
                        <span className="upload-progress">{Math.round(attachment.progress)}%</span>
                      </div>
                    ) : (
                      <img 
                        src={attachment.preview} 
                        alt="Attachment" 
                        className="attachment-preview"
                      />
                    )}
                    <button 
                      className="attachment-remove"
                      onClick={() => removeAttachment(attachment.id)}
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
            )}

            <div className="input-inner">
              <textarea
                ref={textareaRef}
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Создать контент…"
                className="prompt-textarea"
                rows={2}
                disabled={isGenerating}
                data-testid="prompt-input"
              />
            </div>

            <div className="input-bottom-row">
              <button 
                className="input-icon-btn"
                onClick={() => fileInputRef.current?.click()}
                data-testid="attach-button"
              >
                <Plus className="w-5 h-5" />
              </button>

              <div className="input-bottom-right">
                <button className="input-icon-btn" data-testid="mic-button">
                  <MicIcon className="w-5 h-5" />
                </button>
                
                <button 
                  className={`send-button ${prompt.trim() || attachments.length > 0 ? "active" : ""}`}
                  onClick={handleSubmit}
                  disabled={isGenerating || (!prompt.trim() && attachments.length === 0)}
                  data-testid="send-button"
                >
                  {isGenerating ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <ArrowUp className="w-5 h-5" />
                  )}
                </button>
              </div>
            </div>
            
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*,video/*"
              multiple
              onChange={handleFileSelect}
              className="hidden"
            />
            
            {isUploading && <div className="uploading-border" />}
          </div>
        </div>

        {/* Formats section */}
        <div className="formats-section">
          <h2 className="formats-title">Форматы</h2>
          
          <div className="formats-container">
            <div className="formats-scroll">
              {FORMATS.map((format) => (
                <div key={format.id} className="format-card">
                  <div 
                    className="format-preview"
                    style={{ backgroundColor: format.color }}
                  />
                  <span className="format-name">{format.name}</span>
                </div>
              ))}
              
              {/* Circle button at the end */}
              <button 
                className="formats-scroll-btn"
                onClick={() => setShowFormatsPopup(true)}
                data-testid="formats-scroll-btn"
              >
                <ArrowRight className="w-5 h-5" />
              </button>
            </div>
            
            <button 
              className="view-all-btn"
              onClick={() => setShowFormatsPopup(true)}
              data-testid="view-all-btn"
            >
              <span>Смотреть всё</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Examples section */}
        <div className="examples-section">
          <div className="examples-header">
            <h2 className="examples-title">Examples of generation</h2>
            <p className="examples-subtitle">with Slind AI</p>
          </div>
          
          <div className="examples-container">
            <div className="examples-scroll">
              {[1, 2, 3, 4, 5].map((num) => (
                <div key={num} className="example-card">
                  <div className="example-video-placeholder" />
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Formats Popup */}
      {showFormatsPopup && (
        <div className={`formats-popup-overlay ${isPopupClosing ? "closing" : ""}`} onClick={handleClosePopup}>
          <div className={`formats-popup ${isPopupClosing ? "closing" : ""}`} onClick={(e) => e.stopPropagation()}>
            <div className="popup-handle" />
            
            {/* Search */}
            <div className="popup-search">
              <Search className="search-icon" />
              <input 
                type="text"
                placeholder="Найти формат контента"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="search-input"
              />
            </div>
            
            {/* Tabs */}
            <div className="popup-tabs">
              {FORMAT_TABS.map((tab) => (
                <button
                  key={tab}
                  className={`popup-tab ${activeTab === tab ? "active" : ""}`}
                  onClick={() => setActiveTab(tab)}
                >
                  {tab}
                </button>
              ))}
            </div>
            
            {/* Grid */}
            <div className="popup-grid">
              {FORMATS.map((format) => (
                <div key={format.id} className="popup-format-card">
                  <div 
                    className="popup-format-preview"
                    style={{ backgroundColor: format.color }}
                  />
                  <span className="popup-format-name">{format.name}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Auth Popup */}
      <AuthPopup 
        isOpen={showAuthPopup}
        onClose={() => setShowAuthPopup(false)}
        onSuccess={handleAuthSuccess}
      />
    </div>
  );
};

export default MainPage;
