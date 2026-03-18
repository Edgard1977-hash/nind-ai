import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { User, Paperclip, ArrowUp, X } from "lucide-react";
import AuthPopup from "../components/custom/AuthPopup";
import ProfilePage from "../components/custom/ProfilePage";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Animated words for the heading
const ANIMATED_WORDS = [
  "любой контент",
  "видео-монтаж",
  "моушн-дизайн",
  "логотип",
  "Промо-видео",
  "карточку товара"
];

// Audio wave icon component - three vertical bars
const AudioWaveIcon = ({ className }) => (
  <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
    <rect x="6" y="8" width="3" height="8" rx="1.5"/>
    <rect x="10.5" y="4" width="3" height="16" rx="1.5"/>
    <rect x="15" y="8" width="3" height="8" rx="1.5"/>
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
  const [currentWordIndex, setCurrentWordIndex] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);
  const [animationPhase, setAnimationPhase] = useState("visible"); // visible, strikethrough, fadeout, fadein
  const [user, setUser] = useState(null);
  const [showAuthPopup, setShowAuthPopup] = useState(false);
  const [showProfile, setShowProfile] = useState(false);
  const [attachments, setAttachments] = useState([]);
  const [uploadingFiles, setUploadingFiles] = useState({});
  const [isUploading, setIsUploading] = useState(false);

  // Word rotation animation
  useEffect(() => {
    const wordDuration = 4000;
    
    const interval = setInterval(() => {
      setAnimationPhase("strikethrough");
      
      setTimeout(() => {
        setAnimationPhase("fadeout");
      }, 400);
      
      setTimeout(() => {
        setCurrentWordIndex((prev) => (prev + 1) % ANIMATED_WORDS.length);
        setAnimationPhase("fadein");
      }, 800);
      
      setTimeout(() => {
        setAnimationPhase("visible");
      }, 1200);
    }, wordDuration);

    return () => clearInterval(interval);
  }, []);

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

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      const scrollHeight = textareaRef.current.scrollHeight;
      const maxHeight = 240; // ~10 lines
      textareaRef.current.style.height = Math.min(scrollHeight, maxHeight) + "px";
    }
  }, [prompt]);

  const handleProfileClick = () => {
    if (user) {
      setShowProfile(true);
    } else {
      setShowAuthPopup(true);
    }
  };

  const handleSubmit = () => {
    if (!user) {
      setShowAuthPopup(true);
      return;
    }
    
    if (!prompt.trim() && attachments.length === 0) return;
    
    // Navigate to profile with loading state
    setShowProfile(true);
    // TODO: Start generation
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
      {/* Cyan glow at bottom */}
      <div className="cyan-glow" />
      
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

      {/* Animated heading */}
      <div className="animated-heading">
        <span className="heading-static">Сделаю </span>
        <span className={`heading-animated ${animationPhase}`}>
          {ANIMATED_WORDS[currentWordIndex]}
          <span className="strikethrough-line" />
        </span>
      </div>

      {/* Input area */}
      <div className="input-area">
        {/* Attachments */}
        {attachments.length > 0 && (
          <div className="attachments-container">
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

        {/* Input field */}
        <div className={`input-container ${isUploading ? "uploading" : ""}`}>
          <button 
            className="input-icon-btn left"
            onClick={() => fileInputRef.current?.click()}
            data-testid="attach-button"
          >
            <Paperclip className="w-5 h-5" />
          </button>
          
          <textarea
            ref={textareaRef}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Создать контент…"
            className="prompt-textarea"
            rows={1}
            data-testid="prompt-input"
          />
          
          <div className="input-actions">
            <button className="input-icon-btn" data-testid="audio-button">
              <AudioWaveIcon className="w-5 h-5" />
            </button>
            
            <button 
              className={`send-button ${prompt.trim() || attachments.length > 0 ? "active" : ""}`}
              onClick={handleSubmit}
              disabled={!prompt.trim() && attachments.length === 0}
              data-testid="send-button"
            >
              <ArrowUp className="w-5 h-5" />
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
