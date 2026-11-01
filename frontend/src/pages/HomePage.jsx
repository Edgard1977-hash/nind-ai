import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Video, Image, Home, Compass, User, HelpCircle, Crown, Film } from "lucide-react";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Hero images for rotation
const HERO_IMAGES = [
  "https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=800&q=80",
  "https://images.unsplash.com/photo-1478720568477-152d9b164e26?w=800&q=80",
  "https://images.unsplash.com/photo-1485846234645-a62644f84728?w=800&q=80",
  "https://images.unsplash.com/photo-1492691527719-9d1e07e534b4?w=800&q=80",
];

export const HomePage = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("all");
  const [videos, setVideos] = useState([]);
  const [heroIndex, setHeroIndex] = useState(0);

  useEffect(() => {
    fetchVideos();
    // Rotate hero image
    const interval = setInterval(() => {
      setHeroIndex((prev) => (prev + 1) % HERO_IMAGES.length);
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchVideos = async () => {
    try {
      const response = await axios.get(`${API}/videos`);
      setVideos(response.data.projects || []);
    } catch (error) {
      console.error("Failed to fetch videos:", error);
    }
  };

  const tabs = [
    { id: "all", label: "Все" },
    { id: "video", label: "Видео" },
    { id: "photo", label: "Фото" },
    { id: "recent", label: "Недавние" },
  ];

  const completedVideos = videos.filter(v => v.status === "completed" && v.video_url);

  return (
    <div className="min-h-screen bg-black pb-24" data-testid="home-page">
      {/* Hero Image Section */}
      <div className="hero-image-container">
        <img
          src={HERO_IMAGES[heroIndex]}
          alt="Hero"
          className="hero-image"
          style={{ transition: "opacity 1s ease" }}
        />
        <div className="hero-overlay-top" />
        <div className="hero-overlay-bottom" />
        
        {/* Action Buttons */}
        <div className="absolute bottom-8 left-0 right-0 px-6">
          <div className="flex gap-3">
            <button
              onClick={() => navigate("/create?type=video")}
              className="flex-1 glass-button py-4 rounded-[40px] flex items-center justify-center gap-2"
              data-testid="create-video-btn"
            >
              <Video className="w-5 h-5" />
              <span className="font-semibold text-sm">Видео</span>
            </button>
            <button
              onClick={() => navigate("/montage")}
              className="flex-1 glass-button py-4 rounded-[40px] flex items-center justify-center gap-2 bg-gradient-to-r from-purple-500/30 to-pink-500/30"
              data-testid="montage-btn"
            >
              <Film className="w-5 h-5" />
              <span className="font-semibold text-sm">Монтаж</span>
            </button>
            <button
              onClick={() => navigate("/create?type=photo")}
              className="flex-1 glass-button py-4 rounded-[40px] flex items-center justify-center gap-2"
              data-testid="create-photo-btn"
            >
              <Image className="w-5 h-5" />
              <span className="font-semibold text-sm">Фото</span>
            </button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 px-4 py-4 overflow-x-auto">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`tab-button whitespace-nowrap ${activeTab === tab.id ? "active" : ""}`}
            data-testid={`tab-${tab.id}`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Video Grid */}
      <div className="video-grid">
        {completedVideos.length > 0 ? (
          completedVideos.map((video) => (
            <button
              key={video.id}
              onClick={() => navigate(`/video/${video.id}`)}
              className="video-card"
              data-testid={`video-card-${video.id}`}
            >
              {video.poster_url ? (
                <img
                  src={`${BACKEND_URL}${video.poster_url}`}
                  alt={video.title || "Video"}
                  className="w-full h-full object-cover"
                />
              ) : (
                <video
                  src={`${BACKEND_URL}${video.video_url}`}
                  className="w-full h-full object-cover"
                  muted
                  playsInline
                  preload="metadata"
                />
              )}
              {/* Video title overlay */}
              <div className="absolute bottom-0 left-0 right-0 p-2 bg-gradient-to-t from-black/80 to-transparent">
                <p className="text-xs text-white truncate">{video.title || "Видео"}</p>
              </div>
            </button>
          ))
        ) : (
          // Empty state placeholders with "?"
          Array.from({ length: 6 }).map((_, i) => (
            <div 
              key={i} 
              className="video-card" 
              data-testid={`empty-card-${i}`}
            >
              <span style={{ fontSize: '4rem', fontWeight: 200, color: 'rgba(255,255,255,0.3)' }}>?</span>
            </div>
          ))
        )}
      </div>

      {/* Bottom Navigation */}
      <nav className="bottom-nav">
        <div className="flex justify-around items-center">
          <button className="flex flex-col items-center gap-1 text-white" data-testid="nav-home">
            <Home className="w-6 h-6" />
            <span className="text-xs">Главная</span>
          </button>
          <button 
            onClick={() => navigate("/create")}
            className="flex flex-col items-center gap-1 text-white/50"
            data-testid="nav-create"
          >
            <Compass className="w-6 h-6" />
            <span className="text-xs">Создать</span>
          </button>
          <button 
            onClick={() => navigate("/pricing")}
            className="flex flex-col items-center gap-1 text-white/50"
            data-testid="nav-pricing"
          >
            <Crown className="w-6 h-6" />
            <span className="text-xs">Тарифы</span>
          </button>
          <button className="flex flex-col items-center gap-1 text-white/50" data-testid="nav-profile">
            <User className="w-6 h-6" />
            <span className="text-xs">Профиль</span>
          </button>
        </div>
      </nav>
    </div>
  );
};

export default HomePage;
