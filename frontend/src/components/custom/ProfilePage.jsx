import { useState, useEffect, useRef } from "react";
import { ChevronLeft, ChevronRight, X, Sparkles, User, Pencil, CheckCircle } from "lucide-react";
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
          <CheckCircle className="w-5 h-5" />
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
              <Sparkles className="w-4 h-4" />
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
            <Pencil className="w-4 h-4" />
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
            <User className="w-5 h-5" />
            <span>Profile</span>
            <ChevronRight className="w-5 h-5 settings-arrow" />
          </button>

          <div className="settings-divider" />

          {/* Subscription option */}
          <div className="settings-menu-item subscription">
            <Sparkles className="w-5 h-5" />
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
              <Pencil className="w-4 h-4" />
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
