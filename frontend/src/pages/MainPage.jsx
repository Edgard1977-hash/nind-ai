import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { User, Paperclip, ArrowUp, X, Loader2 } from "lucide-react";
import { toast } from "sonner";
import axios from "axios";
import AuthPopup from "../components/custom/AuthPopup";
import ProfilePage from "../components/custom/ProfilePage";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Audio wave icon component - 5 bars (from user image)
const AudioWaveIcon = ({ className }) => (
  <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
    <rect x="2" y="9" width="3" height="6" rx="1.5"/>
    <rect x="6.5" y="6" width="3" height="12" rx="1.5"/>
    <rect x="11" y="3" width="3" height="18" rx="1.5"/>
    <rect x="15.5" y="6" width="3" height="12" rx="1.5"/>
    <rect x="20" y="9" width="3" height="6" rx="1.5"/>
  </svg>
);

// Microphone icon
const MicIcon = ({ className }) => (
  <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
    <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
    <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
  </svg>
);

// Credit icon - four pointed star with rounded petals
const CreditIcon = ({ className }) => (
  <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
    <path d="M12 2C12 2 13.5 8 14 10C15.5 10.5 22 12 22 12C22 12 15.5 13.5 14 14C13.5 16 12 22 12 22C12 22 10.5 16 10 14C8.5 13.5 2 12 2 12C2 12 8.5 10.5 10 10C10.5 8 12 2 12 2Z"/>
  </svg>
);

export const MainPage = () => {
  const navigate = useNavigate();
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);
  
  // State
  const [prompt, setPrompt] = useState("");
  const [user, setUser] = useState(null);
  const [showAuthPopup, setShowAuthPopup] = useState(false);
  const [showProfile, setShowProfile] = useState(false);
  const [attachments, setAttachments] = useState([]);
  const [uploadingFiles, setUploadingFiles] = useState({});
  const [isUploading, setIsUploading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

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

  // Check for user from auth callback
  useEffect(() => {
    if (window.location.hash?.includes('session_id=')) {
      // Auth callback will handle this
      return;
    }
  }, []);

  const handleProfileClick = () => {
    if (user) {
      setShowProfile(true);
    } else {
      setShowAuthPopup(true);
    }
  };

  const handleSubmit = async () => {
    if (!user) {
      setShowAuthPopup(true);
      return;
    }
    
    if (!prompt.trim() && attachments.length === 0) return;
    
    setIsGenerating(true);
    
    try {
      // Prepare request data
      const requestData = {
        prompt: prompt.trim(),
        format_id: "auto",
        language: "auto"
      };
      
      // Add attached files if any
      if (attachments.length > 0) {
        // Upload attachments first if they have files
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
        
        // Check if it's a video for device mockup
        const videoAttachment = attachments.find(a => a.type === "video");
        if (videoAttachment && uploadedUrls.length > 0) {
          // Create device mockup
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
        
        // Images for product ads
        requestData.product_images = uploadedUrls;
      }
      
      // Send to video generation API
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
      
      // Create preview
      const reader = new FileReader();
      reader.onload = (e) => {
        setAttachments(prev => [...prev, {
          id,
          file,
          preview: e.target.result,
          type: isVideo ? "video" : "image",
          uploading: isVideo,
          progress: 0
        }]);
        
        if (isVideo) {
          setIsUploading(true);
          // Simulate upload progress
          simulateUpload(id);
        }
      };
      reader.readAsDataURL(file);
    });
    
    e.target.value = "";
  };

  const simulateUpload = (id) => {
    let progress = 0;
    const interval = setInterval(() => {
      progress += Math.random() * 15;
      if (progress >= 100) {
        progress = 100;
        clearInterval(interval);
        setAttachments(prev => prev.map(a => 
          a.id === id ? { ...a, uploading: false, progress: 100 } : a
        ));
        setIsUploading(false);
      } else {
        setAttachments(prev => prev.map(a => 
          a.id === id ? { ...a, progress } : a
        ));
      }
    }, 200);
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
      {/* Animated liquid gradient background */}
      <div className="liquid-gradient-bg">
        <div className="gradient-blob blob-1" />
        <div className="gradient-blob blob-2" />
        <div className="gradient-blob blob-3" />
      </div>
      
      {/* Header */}
      <header className="main-header">
        {user && (
          <div className="credits-badge" data-testid="credits-badge">
            <CreditIcon className="w-4 h-4" />
            <span>{user.credits || 0}</span>
          </div>
        )}
        
        <button 
          className="avatar-button"
          onClick={handleProfileClick}
          data-testid="profile-button"
        >
          {user?.avatar ? (
            <img src={user.avatar} alt="Avatar" className="avatar-image" />
          ) : (
            <User className="w-5 h-5 text-white/70" />
          )}
        </button>
      </header>

      {/* Static heading */}
      <div className="static-heading">
        <h1 className="heading-main">Создавай лучше и легче</h1>
        <p className="heading-sub">Делай любой контент с ИИ</p>
      </div>

      {/* Input area */}
      <div className="input-area">
        {/* Outer container */}
        <div className={`input-outer ${isUploading ? "uploading" : ""}`}>
          {/* Attach button - outer left */}
          <button 
            className="input-icon-btn outer-left"
            onClick={() => fileInputRef.current?.click()}
            data-testid="attach-button"
          >
            <Paperclip className="w-5 h-5" />
          </button>

          {/* Inner container */}
          <div className="input-inner">
            {/* Attachments inside inner container */}
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

            {/* Textarea */}
            <textarea
              ref={textareaRef}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Создать контент…"
              className="prompt-textarea"
              rows={3}
              disabled={isGenerating}
              data-testid="prompt-input"
            />
          </div>

          {/* Right side buttons - outer */}
          <div className="outer-right-actions">
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
          
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*,video/*"
            multiple
            onChange={handleFileSelect}
            className="hidden"
          />
          
          {/* Uploading border animation */}
          {isUploading && <div className="uploading-border" />}
        </div>
      </div>

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
