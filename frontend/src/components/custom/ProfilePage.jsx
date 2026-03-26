import { useState, useEffect, useRef } from "react";
import { ChevronLeft, ChevronRight, X } from "lucide-react";
import { toast } from "sonner";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Plan labels
const PLAN_LABELS = {
  free: "Free Plan",
  start: "Start Plan",
  plus: "Plus Plan",
  creator: "Creator Plan"
};

// Credits star icon (8-pointed star)
const CreditsIcon = ({ className }) => (
  <svg viewBox="0 0 512 512" fill="currentColor" className={className}>
    <path d="M256 8C119 8 8 119 8 256s111 248 248 248 248-111 248-248S393 8 256 8zm0 448c-110.5 0-200-89.5-200-200S145.5 56 256 56s200 89.5 200 200-89.5 200-200 200zm61.8-104.4l-84.9-61.7c-3.1-2.3-4.9-5.9-4.9-9.7V116c0-6.6 5.4-12 12-12h32c6.6 0 12 5.4 12 12v141.7l66.8 48.6c5.4 3.9 6.5 11.4 2.6 16.8L334.6 349c-3.9 5.3-11.4 6.5-16.8 2.6z"/>
  </svg>
);

// Edit/Pencil icon
const EditIcon = ({ className }) => (
  <svg viewBox="0 0 512 512" fill="currentColor" className={className}>
    <path d="M471.6 21.7c-21.9-21.9-57.3-21.9-79.2 0L362.3 51.7l97.9 97.9 30.1-30.1c21.9-21.9 21.9-57.3 0-79.2l-18.7-18.6zm-299.2 220c-6.1 6.1-10.8 13.6-13.5 21.9l-29.6 88.8c-2.9 8.6-.6 18.1 5.8 24.6s15.9 8.7 24.6 5.8l88.8-29.6c8.2-2.7 15.7-7.4 21.9-13.5L680 phases.3 97.9-97.9L searching.4 241.7zM64 336V80c0-26.5 21.5-48 48-48h80c17.7 0 32 14.3 32 32s-14.3 32-32 32H120v256h256v-72c0-17.7 14.3-32 32-32s32 14.3 32 32v80c0 26.5-21.5 48-48 48H112c-26.5 0-48-21.5-48-48z"/>
  </svg>
);

// Simple pencil icon
const PencilIcon = ({ className }) => (
  <svg viewBox="0 0 512 512" fill="currentColor" className={className}>
    <path d="M362.7 19.3L314.3 67.7 444.3 197.7l48.4-48.4c25-25 25-65.5 0-90.5L453.3 19.3c-25-25-65.5-25-90.5 0zm-71 89.4L58.6 341.6c-11.4 11.4-19.7 25.4-24.2 40.8L.7 491.5c-1.7 8.4 2.8 16.7 10.2 20.2 3.4 1.6 7.3 2 11.1 1.1l109.1-33.7c15.4-4.8 29.4-13.1 40.8-24.5L405 220.7 291.7 108.7z"/>
  </svg>
);

// Profile/Person icon
const PersonIcon = ({ className }) => (
  <svg viewBox="0 0 512 512" fill="currentColor" className={className}>
    <path d="M256 288c79.5 0 144-64.5 144-144S335.5 0 256 0 112 64.5 112 144s64.5 144 144 144zm-94.7 32C72.2 320 0 392.2 0 481.3c0 17 13.8 30.7 30.7 30.7h450.6c17 0 30.7-13.8 30.7-30.7 0-89.1-72.2-161.3-161.3-161.3H161.3z"/>
  </svg>
);

// Checkmark in circle icon
const CheckCircleIcon = ({ className }) => (
  <svg viewBox="0 0 512 512" fill="currentColor" className={className}>
    <path d="M256 512c141.4 0 256-114.6 256-256S397.4 0 256 0 0 114.6 0 256s114.6 256 256 256zm113-303L241 337c-9.4 9.4-24.6 9.4-33.9 0l-64-64c-9.4-9.4-9.4-24.6 0-33.9s24.6-9.4 33.9 0l47 47L335 175c9.4-9.4 24.6-9.4 33.9 0s9.4 24.6 0 33.9z"/>
  </svg>
);

// Star icon for credits (8-pointed star from user's image)
const StarIcon = ({ className }) => (
  <svg viewBox="0 0 512 512" fill="currentColor" className={className}>
    <path d="M256 0c-13.9 0-26.1 8.9-30.5 22.1l-42.1 124.7-124.7 42.1C45.5 193.4 36.6 205.5 36.6 219.4s8.9 26.1 22.1 30.5l124.7 42.1 42.1 124.7c4.4 13.2 16.6 22.1 30.5 22.1s26.1-8.9 30.5-22.1l42.1-124.7 124.7-42.1c13.2-4.4 22.1-16.6 22.1-30.5s-8.9-26.1-22.1-30.5l-124.7-42.1-42.1-124.7C282.1 8.9 269.9 0 256 0z"/>
  </svg>
);

export const ProfilePage = ({ user, onBack, onLogout, onUpdateUser }) => {
  const [activeView, setActiveView] = useState('main'); // main, settings, profile-edit
  const [userVideos, setUserVideos] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [editName, setEditName] = useState(user?.name || '');
  const [isSaving, setIsSaving] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetchUserVideos();
  }, [user]);

  const fetchUserVideos = async () => {
    if (!user?.user_id) {
      setIsLoading(false);
      return;
    }
    
    try {
      const response = await axios.get(`${API}/videos/user/${user.user_id}`);
      setUserVideos(response.data.projects || []);
    } catch (error) {
      console.error("Failed to fetch user videos:", error);
      setUserVideos([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveProfile = async () => {
    if (!editName.trim()) return;
    
    setIsSaving(true);
    try {
      const response = await axios.put(`${API}/users/${user.user_id}`, {
        name: editName.trim()
      });
      
      // Update local user
      const updatedUser = { ...user, name: editName.trim() };
      localStorage.setItem("slind_user", JSON.stringify(updatedUser));
      if (onUpdateUser) onUpdateUser(updatedUser);
      
      // Show success toast
      toast.custom(() => (
        <div className="custom-toast-success">
          <CheckCircleIcon className="w-5 h-5" />
          <span>Saved changes!</span>
        </div>
      ), { duration: 2000 });
      
      setActiveView('settings');
    } catch (error) {
      console.error("Failed to save profile:", error);
      toast.error("Failed to save changes");
    } finally {
      setIsSaving(false);
    }
  };

  const handleAvatarUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    // TODO: Implement avatar upload
    toast.info("Avatar upload coming soon!");
  };

  const completedVideos = userVideos.filter(v => v.status === 'completed');
  const userName = user?.name || user?.email?.split('@')[0] || 'User';
  const userPlan = user?.plan || 'free';
  const userCredits = user?.credits || 0;

  // Main Profile View
  if (activeView === 'main') {
    return (
      <div className="profile-page-new" data-testid="profile-page">
        {/* Gradient Banner */}
        <div className="profile-banner">
          <div className="profile-banner-gradient" />
          
          {/* Header on banner */}
          <div className="profile-banner-header">
            <button 
              className="profile-back-btn"
              onClick={onBack}
              data-testid="profile-back-btn"
            >
              <ChevronLeft className="w-6 h-6" />
            </button>
            
            <div className="profile-credits-badge">
              <StarIcon className="w-4 h-4" />
              <span>{userCredits}</span>
            </div>
          </div>
        </div>

        {/* User Info below banner */}
        <div className="profile-user-section">
          <div className="profile-user-info">
            <div className="profile-avatar-large">
              {user?.picture ? (
                <img src={user.picture} alt={userName} />
              ) : (
                <span>{userName[0]?.toUpperCase()}</span>
              )}
            </div>
            
            <div className="profile-user-details">
              <h2 className="profile-username">{userName}</h2>
              <p className="profile-plan">{PLAN_LABELS[userPlan]}</p>
            </div>
          </div>
          
          <button 
            className="profile-edit-btn"
            onClick={() => setActiveView('settings')}
            data-testid="edit-profile-btn"
          >
            <PencilIcon className="w-4 h-4" />
            <span>Edit</span>
          </button>
        </div>

        {/* Library Section */}
        <div className="profile-library">
          <h3 className="profile-library-title">Library</h3>
          
          {isLoading ? (
            <div className="profile-loading">Loading...</div>
          ) : completedVideos.length > 0 ? (
            <div className="profile-videos-grid">
              {completedVideos.map((video, index) => (
                <div 
                  key={video.id} 
                  className={`profile-video-item ${index % 3 === 0 ? 'portrait' : index % 3 === 1 ? 'landscape' : 'portrait'}`}
                  data-testid={`video-${video.id}`}
                >
                  {video.poster_url ? (
                    <img 
                      src={`${BACKEND_URL}${video.poster_url}`} 
                      alt={video.title || 'Video'}
                      className="profile-video-thumb"
                    />
                  ) : video.video_url ? (
                    <video 
                      src={`${BACKEND_URL}${video.video_url}`}
                      className="profile-video-thumb"
                      muted
                      playsInline
                    />
                  ) : (
                    <div className="profile-video-placeholder" />
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="profile-empty">
              <button 
                className="profile-start-create-btn"
                onClick={onBack}
                data-testid="start-create-btn"
              >
                Start create
              </button>
            </div>
          )}
        </div>
      </div>
    );
  }

  // Settings View
  if (activeView === 'settings') {
    return (
      <div className="profile-page-new settings-view" data-testid="settings-page">
        <div className="settings-header">
          <button 
            className="settings-close-btn"
            onClick={() => setActiveView('main')}
            data-testid="settings-close-btn"
          >
            <X className="w-6 h-6" />
          </button>
          <h2 className="settings-title">Settings</h2>
          <div className="settings-spacer" />
        </div>

        <div className="settings-menu">
          {/* Profile option */}
          <button 
            className="settings-menu-item"
            onClick={() => {
              setEditName(userName);
              setActiveView('profile-edit');
            }}
            data-testid="settings-profile-btn"
          >
            <PersonIcon className="w-5 h-5" />
            <span>Profile</span>
            <ChevronRight className="w-5 h-5 settings-arrow" />
          </button>

          <div className="settings-divider" />

          {/* Subscription option */}
          <div className="settings-menu-item subscription">
            <StarIcon className="w-5 h-5" />
            <span>My subscription</span>
            <button className="settings-upgrade-btn">Upgrade</button>
          </div>
          
          <div className="settings-divider" />
          
          {/* Logout option */}
          <button 
            className="settings-menu-item logout"
            onClick={onLogout}
            data-testid="settings-logout-btn"
          >
            <span>Log out</span>
          </button>
        </div>
      </div>
    );
  }

  // Profile Edit View
  if (activeView === 'profile-edit') {
    return (
      <div className="profile-page-new edit-view" data-testid="profile-edit-page">
        <div className="settings-header">
          <button 
            className="profile-back-btn"
            onClick={() => setActiveView('settings')}
            data-testid="profile-edit-back-btn"
          >
            <ChevronLeft className="w-6 h-6" />
          </button>
          <h2 className="settings-title">Profile</h2>
          <div className="settings-spacer" />
        </div>

        <div className="profile-edit-content">
          {/* Avatar with edit button */}
          <div className="profile-edit-avatar-container">
            <div className="profile-avatar-edit">
              {user?.picture ? (
                <img src={user.picture} alt={userName} />
              ) : (
                <span>{userName[0]?.toUpperCase()}</span>
              )}
            </div>
            <button 
              className="avatar-edit-btn"
              onClick={() => fileInputRef.current?.click()}
              data-testid="avatar-edit-btn"
            >
              <PencilIcon className="w-4 h-4" />
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleAvatarUpload}
              className="hidden"
            />
          </div>

          {/* Name input */}
          <div className="profile-edit-field">
            <label className="profile-edit-label">Name</label>
            <input
              type="text"
              value={editName}
              onChange={(e) => setEditName(e.target.value)}
              className="profile-edit-input"
              placeholder="Your name"
              data-testid="profile-name-input"
            />
          </div>

          {/* Save button */}
          <button 
            className={`profile-save-btn ${editName.trim() !== userName ? 'active' : ''}`}
            onClick={handleSaveProfile}
            disabled={isSaving || editName.trim() === userName}
            data-testid="profile-save-btn"
          >
            {isSaving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>
    );
  }

  return null;
};

export default ProfilePage;
