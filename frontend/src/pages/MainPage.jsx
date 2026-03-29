import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Plus, ArrowUp, X, Loader2, Search, ChevronRight, Check } from "lucide-react";
import { toast } from "sonner";
import axios from "axios";
import ProfilePage from "../components/custom/ProfilePage";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Logo image URL
const LOGO_URL = "https://customer-assets.emergentagent.com/job_ai-format-studio/artifacts/x0akmc4x_A7746620-B806-4A1B-B685-CC4290123288.png";

// Search icon SVG (user's custom)
const SearchIconCustom = ({ className }) => (
  <svg viewBox="0 0 1024 1024" fill="currentColor" className={className}>
    <path d="M 836.00 852.40 C820.81,849.66 814.26,845.70 792.75,826.24 C766.95,802.89 756.60,793.45 729.95,768.93 C717.05,757.06 698.17,739.78 688.00,730.52 C677.83,721.26 663.88,708.44 657.00,702.03 C650.12,695.63 634.71,681.27 622.74,670.12 L 600.98 649.85 L 590.24 656.62 C575.76,665.74 553.24,676.81 537.85,682.37 C492.55,698.73 443.36,703.39 393.36,696.05 C337.77,687.89 283.52,662.02 240.20,623.00 C190.47,578.20 156.55,511.80 150.08,446.58 C148.54,430.96 148.74,399.68 150.50,384.70 C158.02,320.39 186.33,263.35 232.83,218.83 C303.86,150.83 400.77,124.09 498.00,145.66 C535.80,154.04 574.87,172.12 607.00,196.07 C703.17,267.78 743.77,389.25 709.43,502.53 C701.93,527.28 691.32,549.57 676.18,572.42 L 667.62 585.33 L 672.06 589.32 C674.50,591.51 699.45,613.42 727.50,638.02 C755.55,662.63 787.50,690.75 798.50,700.53 C809.50,710.30 829.75,728.28 843.50,740.49 C879.34,772.30 883.32,776.36 887.73,785.65 C890.87,792.27 891.46,794.63 891.82,802.04 C892.04,806.80 891.73,813.05 891.11,815.92 C886.65,836.71 868.98,851.25 846.74,852.42 C842.21,852.66 837.38,852.65 836.00,852.40 ZM 465.81 646.48 C504.58,641.05 539.25,627.76 571.50,605.97 C593.33,591.22 615.67,568.78 631.19,546.00 C646.87,523.01 657.12,500.31 664.50,472.28 C675.64,429.96 673.42,381.68 658.36,338.74 C632.56,265.18 568.15,208.68 489.50,190.61 C471.78,186.54 456.39,184.94 435.00,184.93 C399.60,184.91 369.44,191.01 337.00,204.74 C296.83,221.74 260.26,252.12 236.07,288.57 C209.70,328.32 196.61,374.59 198.32,421.94 C199.55,456.16 206.94,485.09 222.46,516.50 C234.46,540.78 249.40,561.29 269.16,580.65 C309.19,619.84 363.85,644.16 421.50,648.41 C430.25,649.06 455.14,647.97 465.81,646.48 Z"/>
  </svg>
);

// Microphone icon
const MicIcon = ({ className }) => (
  <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
    <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
    <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
  </svg>
);

// Sparkles icon
const SparklesIcon = ({ className }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z"/>
  </svg>
);

// Person icon SVG
const PersonIcon = ({ className }) => (
  <svg viewBox="0 0 1024 1024" fill="currentColor" className={className}>
    <path d="M 472.50 907.92 C399.79,903.47 339.60,894.58 279.93,879.46 C199.83,859.17 171.51,841.57 164.58,807.79 C160.48,787.78 164.88,739.16 174.11,702.56 C193.23,626.76 238.62,581.38 324.50,552.17 C343.87,545.58 372.91,539.00 382.61,539.00 C386.12,539.00 388.26,539.88 393.73,543.58 C413.47,556.94 443.76,567.65 476.00,572.66 C490.33,574.89 528.58,575.18 543.00,573.16 C577.95,568.29 607.96,557.82 630.43,542.68 L 636.37 538.68 L 646.06 539.81 C665.43,542.08 703.65,553.48 727.57,564.12 C788.29,591.11 823.84,627.19 843.22,681.50 C856.66,719.16 864.59,779.85 859.54,806.52 C853.77,837.05 831.12,853.72 770.58,871.98 C708.99,890.55 632.18,903.33 554.29,907.97 C534.80,909.14 491.96,909.10 472.50,907.92 ZM 491.00 493.36 C422.58,484.88 365.71,437.02 344.05,369.72 C338.60,352.77 336.94,342.22 336.31,320.50 C335.48,291.89 338.48,271.23 346.61,249.61 C361.87,208.97 393.61,173.73 432.51,154.20 C474.35,133.20 527.65,130.25 571.51,146.49 C629.04,167.79 671.99,217.51 684.59,277.39 C688.07,293.95 688.98,322.12 686.57,339.27 C679.49,389.87 653.55,433.03 612.50,462.55 C601.94,470.14 579.28,481.64 566.50,485.89 C548.85,491.76 539.55,493.16 516.00,493.49 C504.17,493.66 492.92,493.60 491.00,493.36 Z"/>
  </svg>
);

// Format categories
const FORMAT_TABS = ["Все", "Новые", "Видео", "Фото", "Монтаж", "Анимации"];

// Animated placeholder phrases
const PLACEHOLDER_PHRASES = [
  "Cut my video and…",
  "create logo animation for…",
  "make video story about…",
  "create motion design for…",
  "make promo video for…",
  "create short-form video for…",
  "make highlights from…",
  "create fan edit about…",
  "add visual effects in…",
  "make colour grading for…",
  "create sound effects for…",
  "Make motion graphics for…"
];

// Placeholder formats with videos
const FORMATS = [
  { id: 1, name: "Reels Story", color: "#3A3A3A", videos: [] },
  { id: 2, name: "TikTok Trend", color: "#4A3A5A", videos: [] },
  { id: 3, name: "Product Showcase", color: "#3A4A5A", videos: [] },
  { id: 4, name: "Meme Format", color: "#5A4A3A", videos: [] },
  { id: 5, name: "Before/After", color: "#3A5A4A", videos: [] },
  { id: 6, name: "Tutorial", color: "#4A4A4A", videos: [] },
  { id: 7, name: "Promo Video", color: "#5A3A4A", videos: [] },
  { id: 8, name: "Story Time", color: "#3A4A4A", videos: [] },
];

export const MainPage = () => {
  const navigate = useNavigate();
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);
  
  // State
  const [prompt, setPrompt] = useState("");
  const [user, setUser] = useState(null);
  const [showProfile, setShowProfile] = useState(false);
  const [showFormatsPopup, setShowFormatsPopup] = useState(false);
  const [isPopupClosing, setIsPopupClosing] = useState(false);
  const [attachments, setAttachments] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [activeTab, setActiveTab] = useState("Все");
  const [searchQuery, setSearchQuery] = useState("");
  const [headerScrolled, setHeaderScrolled] = useState(false);
  
  // New states for logged-in view
  const [activeMainTab, setActiveMainTab] = useState("Formats");
  const [selectedFormat, setSelectedFormat] = useState(null);
  const [showFormatPopup, setShowFormatPopup] = useState(false);
  const [showFormatsListPopup, setShowFormatsListPopup] = useState(false);
  const [generatePrompt, setGeneratePrompt] = useState(true);
  const [userVideos, setUserVideos] = useState([]);
  const [isLoadingVideos, setIsLoadingVideos] = useState(false);
  
  // Popup swipe state
  const [popupDragY, setPopupDragY] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const popupStartY = useRef(0);

  // Animated placeholder state
  const [placeholderText, setPlaceholderText] = useState("");
  const [phraseIndex, setPhraseIndex] = useState(0);
  const [isTyping, setIsTyping] = useState(true);

  // Check auth status and setup scroll listener
  useEffect(() => {
    const savedUser = localStorage.getItem("slind_user");
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (e) {
        localStorage.removeItem("slind_user");
      }
    }
    
    // Scroll listener for header animation (only for non-logged in)
    const handleScroll = () => {
      const scrollY = window.scrollY;
      const threshold = 350;
      setHeaderScrolled(scrollY > threshold);
    };
    
    window.addEventListener('scroll', handleScroll);
    
    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  // Fetch user videos when switching to Library tab
  useEffect(() => {
    if (activeMainTab === "Library" && user) {
      fetchUserVideos();
    }
  }, [activeMainTab, user]);

  // Animated placeholder typing effect
  useEffect(() => {
    const currentPhrase = PLACEHOLDER_PHRASES[phraseIndex];
    let timeout;

    if (isTyping) {
      // Typing animation
      if (placeholderText.length < currentPhrase.length) {
        timeout = setTimeout(() => {
          setPlaceholderText(currentPhrase.slice(0, placeholderText.length + 1));
        }, 50);
      } else {
        // Finished typing, wait then start erasing
        timeout = setTimeout(() => {
          setIsTyping(false);
        }, 2000);
      }
    } else {
      // Erasing animation
      if (placeholderText.length > 0) {
        timeout = setTimeout(() => {
          setPlaceholderText(placeholderText.slice(0, -1));
        }, 30);
      } else {
        // Finished erasing, move to next phrase
        setPhraseIndex((prev) => (prev + 1) % PLACEHOLDER_PHRASES.length);
        setIsTyping(true);
      }
    }

    return () => clearTimeout(timeout);
  }, [placeholderText, phraseIndex, isTyping]);

  // Intersection Observer for section animations
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
          }
        });
      },
      { threshold: 0.1 }
    );

    const titles = document.querySelectorAll('.section-title, .section-subtitle');
    titles.forEach((el) => observer.observe(el));

    return () => {
      titles.forEach((el) => observer.unobserve(el));
    };
  }, [user]);

  const fetchUserVideos = async () => {
    if (!user?.user_id) return;
    setIsLoadingVideos(true);
    try {
      const response = await axios.get(`${API}/videos/user/${user.user_id}`);
      setUserVideos(response.data.projects || []);
    } catch (error) {
      console.error("Failed to fetch videos:", error);
    } finally {
      setIsLoadingVideos(false);
    }
  };

  const handleSubmit = async () => {
    if (!user) {
      navigate('/auth');
      return;
    }
    
    if (!prompt.trim() && attachments.length === 0) return;
    
    setIsGenerating(true);
    
    try {
      const requestData = {
        prompt: prompt.trim(),
        format_id: selectedFormat?.id || "auto",
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

  const handleUpdateUser = (updatedUser) => {
    setUser(updatedUser);
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem("slind_user");
    setShowProfile(false);
  };

  const handleGetStarted = () => {
    navigate('/auth');
  };

  const handleAvatarClick = () => {
    if (user) {
      setShowProfile(true);
    } else {
      navigate('/auth');
    }
  };

  const handleClosePopup = () => {
    setIsPopupClosing(true);
    setTimeout(() => {
      setShowFormatsPopup(false);
      setIsPopupClosing(false);
    }, 300);
  };

  const handleSelectFormat = (format) => {
    setShowFormatPopup(true);
    setSelectedFormat(format);
  };

  const handleUseFormat = () => {
    setShowFormatPopup(false);
  };

  // Swipe handlers for popups
  const handlePopupTouchStart = (e) => {
    popupStartY.current = e.touches[0].clientY;
    setIsDragging(true);
  };

  const handlePopupTouchMove = (e) => {
    if (!isDragging) return;
    const diff = e.touches[0].clientY - popupStartY.current;
    if (diff > 0) setPopupDragY(diff);
  };

  const handlePopupTouchEnd = (closePopup) => {
    setIsDragging(false);
    if (popupDragY > 100) {
      closePopup();
    }
    setPopupDragY(0);
  };

  // Show profile page
  if (showProfile && user) {
    return (
      <ProfilePage 
        user={user} 
        onBack={() => setShowProfile(false)}
        onLogout={handleLogout}
        onUpdateUser={handleUpdateUser}
      />
    );
  }

  const completedVideos = userVideos.filter(v => v.status === 'completed');

  // ============ LOGGED IN VIEW ============
  if (user) {
    return (
      <div className="main-page-fixed" data-testid="main-page-logged">
        {/* Background Grid */}
        <div className="perspective-grid">
          <svg viewBox="0 0 400 300" preserveAspectRatio="none" className="grid-svg">
            <line x1="0" y1="0" x2="0" y2="300" stroke="rgba(255,255,255,0.08)" strokeWidth="1"/>
            <line x1="80" y1="0" x2="80" y2="300" stroke="rgba(255,255,255,0.08)" strokeWidth="1"/>
            <line x1="160" y1="0" x2="160" y2="300" stroke="rgba(255,255,255,0.08)" strokeWidth="1"/>
            <line x1="240" y1="0" x2="240" y2="300" stroke="rgba(255,255,255,0.08)" strokeWidth="1"/>
            <line x1="320" y1="0" x2="320" y2="300" stroke="rgba(255,255,255,0.08)" strokeWidth="1"/>
            <line x1="400" y1="0" x2="400" y2="300" stroke="rgba(255,255,255,0.08)" strokeWidth="1"/>
            
            <path d="M0,0 Q200,0 400,0" stroke="rgba(255,255,255,0.06)" strokeWidth="1" fill="none"/>
            <path d="M0,75 Q200,65 400,75" stroke="rgba(255,255,255,0.07)" strokeWidth="1" fill="none"/>
            <path d="M0,150 Q200,130 400,150" stroke="rgba(255,255,255,0.08)" strokeWidth="1" fill="none"/>
            <path d="M0,225 Q200,195 400,225" stroke="rgba(255,255,255,0.09)" strokeWidth="1" fill="none"/>
            <path d="M0,300 Q200,260 400,300" stroke="rgba(255,255,255,0.1)" strokeWidth="1" fill="none"/>
          </svg>
        </div>
        
        {/* Fixed Header */}
        <header className="main-fixed-header">
          <div className="header-left-logo">
            <img src={LOGO_URL} alt="Slind" className="header-logo-large" />
          </div>
          
          <div className="header-right-actions">
            <button 
              className="header-upgrade-btn"
              onClick={() => {/* TODO: Upgrade flow */}}
              data-testid="upgrade-btn"
            >
              Upgrade
            </button>
            
            <button 
              className="header-avatar-btn"
              onClick={handleAvatarClick}
              data-testid="header-avatar-btn"
            >
              {user.picture ? (
                <img src={user.picture} alt={user.name} />
              ) : (
                <span>{(user.name || user.email)?.[0]?.toUpperCase()}</span>
              )}
            </button>
          </div>
        </header>

        {/* Content - always Create view */}
        <div className="create-content-v2">
            {/* Center section - heading and input */}
            <div className="create-center-section">
              {/* Heading */}
              <div className="create-heading">
                <h1 className="create-title">
                  Ready to create?
                </h1>
              </div>

              {/* Input area */}
              <div className="create-input-area">
                <div className={`input-outer ${isUploading ? "uploading" : ""}`}>
                  {attachments.length > 0 && (
                    <div className="attachments-row">
                      {attachments.map((attachment) => (
                        <div key={attachment.id} className="attachment-item">
                          <img 
                            src={attachment.preview} 
                            alt="Attachment" 
                            className="attachment-preview"
                          />
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
                      placeholder={`Slind AI, ${placeholderText}`}
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
              </div>
            </div>
            </div>

            {/* Bottom Panel with Tabs */}
            <div className="bottom-panel">
              {/* Tabs */}
              <div className="bottom-tabs-container">
                <div 
                  className="bottom-tabs-indicator"
                  style={{
                    left: activeMainTab === 'Creations' ? '4px' : '50%',
                    width: 'calc(50% - 4px)'
                  }}
                />
                <button 
                  className={`bottom-tab ${activeMainTab === 'Creations' ? 'active' : ''}`}
                  onClick={() => setActiveMainTab('Creations')}
                  data-testid="creations-tab"
                >
                  My creations
                </button>
                <button 
                  className={`bottom-tab ${activeMainTab === 'Formats' ? 'active' : ''}`}
                  onClick={() => setActiveMainTab('Formats')}
                  data-testid="formats-tab"
                >
                  Formats
                </button>
              </div>

              {/* Content */}
              <div className="bottom-panel-content">
                {activeMainTab === 'Formats' ? (
                  <>
                    <div className="create-formats-grid">
                      {FORMATS.slice(0, 8).map((format) => (
                        <button 
                          key={format.id}
                          className={`create-format-card ${selectedFormat?.id === format.id ? 'selected' : ''}`}
                          onClick={() => handleSelectFormat(format)}
                          data-testid={`create-format-${format.id}`}
                        >
                          <div 
                            className="create-format-video"
                            style={{ backgroundColor: format.color }}
                          />
                        </button>
                      ))}
                    </div>
                    
                    <button 
                      className="create-see-all-btn"
                      onClick={() => navigate('/formats')}
                      data-testid="create-see-all-btn"
                    >
                      See all
                    </button>
                  </>
                ) : (
                  /* My Creations */
                  <>
                    {isLoadingVideos ? (
                      <div className="library-loading">Loading...</div>
                    ) : completedVideos.length > 0 ? (
                      <div className="creations-grid-real">
                        {completedVideos.map((video) => (
                          <div 
                            key={video.id} 
                            className="creation-card"
                            onClick={() => navigate(`/video/${video.id}`)}
                            data-testid={`library-video-${video.id}`}
                          >
                            {video.poster_url ? (
                              <img 
                                src={`${BACKEND_URL}${video.poster_url}`} 
                                alt={video.title || 'Video'}
                              />
                            ) : video.video_url ? (
                              <video 
                                src={`${BACKEND_URL}${video.video_url}`}
                                muted
                                playsInline
                              />
                            ) : (
                              <div className="creation-placeholder" />
                            )}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="creations-empty-pattern">
                        <div className="creations-pattern-grid">
                          {/* Left column */}
                          <div className="pattern-column">
                            <div className="pattern-item ratio-9-16" />
                            <div className="pattern-item ratio-1-1" />
                            <div className="pattern-item ratio-16-9" />
                            <div className="pattern-item ratio-9-16" />
                          </div>
                          {/* Right column */}
                          <div className="pattern-column">
                            <div className="pattern-item ratio-16-9" />
                            <div className="pattern-item ratio-9-16" />
                            <div className="pattern-item ratio-1-1" />
                            <div className="pattern-item ratio-16-9" />
                          </div>
                        </div>
                        <div className="creations-empty-fade" />
                        <div className="creations-empty-overlay">
                          <p className="creations-empty-text">No videos yet</p>
                          <button 
                            className="creations-start-btn"
                            onClick={() => {
                              window.scrollTo({ top: 0, behavior: 'smooth' });
                              setTimeout(() => textareaRef.current?.focus(), 500);
                            }}
                            data-testid="start-create-btn"
                          >
                            Start create
                          </button>
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>

        {/* Format Detail Popup */}
        {showFormatPopup && selectedFormat && (
          <div 
            className="format-popup-overlay"
            onClick={() => setShowFormatPopup(false)}
          >
            <div 
              className="format-detail-popup"
              style={{ transform: `translateY(${popupDragY}px)` }}
              onClick={(e) => e.stopPropagation()}
              onTouchStart={handlePopupTouchStart}
              onTouchMove={handlePopupTouchMove}
              onTouchEnd={() => handlePopupTouchEnd(() => setShowFormatPopup(false))}
            >
              <div className="popup-drag-handle" />
              
              {/* Videos carousel */}
              <div className="format-videos-row">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="format-video-item">
                    <div 
                      className="format-video-placeholder"
                      style={{ backgroundColor: selectedFormat.color }}
                    />
                  </div>
                ))}
              </div>
              
              {/* Format name */}
              <h3 className="format-detail-name">{selectedFormat.name}</h3>
              
              {/* Generate prompt checkbox */}
              <label className="generate-prompt-row" onClick={() => setGeneratePrompt(!generatePrompt)}>
                <div className={`custom-checkbox ${generatePrompt ? 'checked' : ''}`}>
                  {generatePrompt && <Check className="check-icon" />}
                </div>
                <span>Generate prompt</span>
              </label>
              
              {/* Use button */}
              <button 
                className="format-use-btn"
                onClick={handleUseFormat}
                data-testid="format-use-btn"
              >
                <SparklesIcon className="sparkles-icon" />
                <span>Use</span>
              </button>
            </div>
          </div>
        )}

        {/* Formats List Popup (search) */}
        {showFormatsListPopup && (
          <div 
            className="format-popup-overlay"
            onClick={() => setShowFormatsListPopup(false)}
          >
            <div 
              className="formats-list-popup"
              style={{ transform: `translateY(${popupDragY}px)` }}
              onClick={(e) => e.stopPropagation()}
              onTouchStart={handlePopupTouchStart}
              onTouchMove={handlePopupTouchMove}
              onTouchEnd={() => handlePopupTouchEnd(() => setShowFormatsListPopup(false))}
            >
              <div className="popup-drag-handle" />
              
              <h2 className="formats-list-title">Formats</h2>
              
              <div className="formats-list-grid">
                {FORMATS.map((format) => (
                  <button 
                    key={format.id}
                    className="formats-list-item"
                    onClick={() => {
                      handleSelectFormat(format);
                      setShowFormatsListPopup(false);
                    }}
                    data-testid={`formats-list-${format.id}`}
                  >
                    <div 
                      className="formats-list-thumb"
                      style={{ backgroundColor: format.color }}
                    />
                    <span className="formats-list-name">{format.name}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  // ============ NOT LOGGED IN VIEW (ORIGINAL) ============
  return (
    <div className="main-page" data-testid="main-page">
      {/* Background */}
      <div className="liquid-gradient-bg" />
      
      {/* Perspective Grid */}
      <div className="perspective-grid">
        <svg viewBox="0 0 400 300" preserveAspectRatio="none" className="grid-svg">
          <line x1="0" y1="0" x2="0" y2="300" stroke="rgba(255,255,255,0.08)" strokeWidth="1"/>
          <line x1="80" y1="0" x2="80" y2="300" stroke="rgba(255,255,255,0.08)" strokeWidth="1"/>
          <line x1="160" y1="0" x2="160" y2="300" stroke="rgba(255,255,255,0.08)" strokeWidth="1"/>
          <line x1="240" y1="0" x2="240" y2="300" stroke="rgba(255,255,255,0.08)" strokeWidth="1"/>
          <line x1="320" y1="0" x2="320" y2="300" stroke="rgba(255,255,255,0.08)" strokeWidth="1"/>
          <line x1="400" y1="0" x2="400" y2="300" stroke="rgba(255,255,255,0.08)" strokeWidth="1"/>
          
          <path d="M0,0 Q200,0 400,0" stroke="rgba(255,255,255,0.06)" strokeWidth="1" fill="none"/>
          <path d="M0,75 Q200,65 400,75" stroke="rgba(255,255,255,0.07)" strokeWidth="1" fill="none"/>
          <path d="M0,150 Q200,130 400,150" stroke="rgba(255,255,255,0.08)" strokeWidth="1" fill="none"/>
          <path d="M0,225 Q200,195 400,225" stroke="rgba(255,255,255,0.09)" strokeWidth="1" fill="none"/>
          <path d="M0,300 Q200,260 400,300" stroke="rgba(255,255,255,0.1)" strokeWidth="1" fill="none"/>
        </svg>
      </div>
      
      {/* Fixed Header with blur */}
      <header className={`fixed-header ${headerScrolled ? 'scrolled' : ''}`}>
        <div className="header-blur" />
        <div className="header-content">
          <div className={`logo-container ${headerScrolled ? 'hidden' : ''}`}>
            <img src={LOGO_URL} alt="Slind" className="logo-image" />
          </div>
          
          <span className={`header-overview-text ${headerScrolled ? 'visible' : ''}`}>Overview</span>
          
          <button 
            className={`get-started-btn ${headerScrolled ? 'hidden' : ''}`}
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
          <h1 className="heading-main">Create better</h1>
          <p className="heading-sub">Make video editing entirely with AI</p>
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
                placeholder={`Slind AI, ${placeholderText}`}
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

        {/* How it works section */}
        <div className="how-section">
          <h2 className="section-title">How Slind AI works?</h2>
          <div className="how-video-wrapper">
            <div className="how-video-placeholder" />
          </div>
        </div>

        {/* Formats section - grid */}
        <div className="formats-section-new">
          <h2 className="section-title">Formats</h2>
          <p className="section-subtitle">Find an idea faster</p>
          
          <div className="formats-grid">
            {FORMATS.slice(0, 8).map((format) => (
              <div key={format.id} className="format-card-new">
                <div 
                  className="format-preview-new"
                  style={{ backgroundColor: format.color }}
                />
                <span className="format-name-new">{format.name}</span>
              </div>
            ))}
          </div>
          
          <button 
            className="see-all-btn"
            onClick={() => navigate('/formats')}
            data-testid="see-all-btn"
          >
            See all
          </button>
        </div>

        {/* Examples section - masonry grid */}
        <div className="examples-section-new">
          <h2 className="section-title">Examples of generation</h2>
          <p className="section-subtitle">with Slind AI</p>
          
          <div className="examples-grid">
            <div className="examples-column">
              <div className="example-item portrait">
                <div className="example-placeholder" />
              </div>
              <div className="example-item landscape">
                <div className="example-placeholder" />
              </div>
              <div className="example-item portrait">
                <div className="example-placeholder" />
              </div>
              <div className="example-item landscape">
                <div className="example-placeholder" />
              </div>
            </div>
            <div className="examples-column">
              <div className="example-item landscape">
                <div className="example-placeholder" />
              </div>
              <div className="example-item portrait">
                <div className="example-placeholder" />
              </div>
              <div className="example-item landscape">
                <div className="example-placeholder" />
              </div>
              <div className="example-item portrait">
                <div className="example-placeholder" />
              </div>
            </div>
          </div>
          
          <div className="examples-fade" />
          
          <button 
            className="start-create-btn"
            onClick={() => {
              window.scrollTo({ top: 0, behavior: 'smooth' });
              setTimeout(() => textareaRef.current?.focus(), 500);
            }}
            data-testid="start-create-btn"
          >
            Start create
          </button>
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
    </div>
  );
};

export default MainPage;
