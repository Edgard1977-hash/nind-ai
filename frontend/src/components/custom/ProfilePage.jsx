import { useState, useEffect, useRef } from "react";
import { ChevronLeft, ChevronRight, X, Bell } from "lucide-react";
import { toast } from "sonner";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// User's custom icons
const CHECK_ICON = "/assets/check-icon.png";

// Credits icon SVG
const CreditsIcon = ({ className }) => (
  <svg viewBox="0 0 1024 1024" fill="currentColor" className={className}>
    <path d="M 498.04 902.32 C487.03,900.01 475.94,891.85 469.24,881.12 C466.30,876.39 464.43,871.45 454.27,841.50 C449.60,827.75 442.50,806.83 438.48,795.00 C434.46,783.17 424.65,754.60 416.68,731.50 C408.71,708.40 399.39,681.40 395.98,671.50 C388.62,650.16 385.22,643.34 378.45,636.41 C370.67,628.43 369.90,628.12 300.00,604.00 C285.98,599.16 263.25,591.29 249.50,586.52 C235.75,581.74 212.35,573.65 197.50,568.54 C161.94,556.30 145.49,550.28 139.99,547.49 C127.63,541.24 116.17,529.21 111.93,518.06 C104.36,498.12 110.23,477.38 127.50,463.09 C139.35,453.28 138.70,453.53 288.34,404.03 C330.05,390.24 366.01,378.02 368.23,376.88 C374.55,373.66 381.40,366.60 384.85,359.76 C386.58,356.32 398.77,321.33 411.93,282.00 C448.35,173.17 459.60,140.54 463.46,132.51 C472.77,113.15 492.48,102.78 514.11,105.84 C532.90,108.49 546.88,120.13 553.76,138.82 C555.11,142.49 572.11,192.83 591.54,250.67 C610.97,308.52 627.63,357.34 628.57,359.17 C631.46,364.83 636.05,369.98 641.39,373.58 C646.67,377.15 663.73,382.97 789.00,424.00 C873.18,451.56 877.75,453.41 890.17,464.84 C907.43,480.74 911.43,504.29 900.21,524.00 C891.35,539.58 880.18,546.86 848.50,557.74 C841.35,560.19 819.30,567.74 799.50,574.52 C691.95,611.32 651.67,625.51 645.98,628.61 C639.57,632.10 632.84,638.77 629.14,645.31 C626.23,650.46 617.93,673.51 600.98,723.50 C589.01,758.79 554.96,857.43 551.01,868.23 C545.18,884.21 537.37,893.59 525.12,899.32 C519.44,901.99 517.22,902.46 509.50,902.63 C504.55,902.74 499.39,902.60 498.04,902.32 Z"/>
  </svg>
);

// Person icon SVG
const PersonIcon = ({ className }) => (
  <svg viewBox="0 0 1024 1024" fill="currentColor" className={className}>
    <path d="M 472.50 907.92 C399.79,903.47 339.60,894.58 279.93,879.46 C199.83,859.17 171.51,841.57 164.58,807.79 C160.48,787.78 164.88,739.16 174.11,702.56 C193.23,626.76 238.62,581.38 324.50,552.17 C343.87,545.58 372.91,539.00 382.61,539.00 C386.12,539.00 388.26,539.88 393.73,543.58 C413.47,556.94 443.76,567.65 476.00,572.66 C490.33,574.89 528.58,575.18 543.00,573.16 C577.95,568.29 607.96,557.82 630.43,542.68 L 636.37 538.68 L 646.06 539.81 C665.43,542.08 703.65,553.48 727.57,564.12 C788.29,591.11 823.84,627.19 843.22,681.50 C856.66,719.16 864.59,779.85 859.54,806.52 C853.77,837.05 831.12,853.72 770.58,871.98 C708.99,890.55 632.18,903.33 554.29,907.97 C534.80,909.14 491.96,909.10 472.50,907.92 ZM 491.00 493.36 C422.58,484.88 365.71,437.02 344.05,369.72 C338.60,352.77 336.94,342.22 336.31,320.50 C335.48,291.89 338.48,271.23 346.61,249.61 C361.87,208.97 393.61,173.73 432.51,154.20 C474.35,133.20 527.65,130.25 571.51,146.49 C629.04,167.79 671.99,217.51 684.59,277.39 C688.07,293.95 688.98,322.12 686.57,339.27 C679.49,389.87 653.55,433.03 612.50,462.55 C601.94,470.14 579.28,481.64 566.50,485.89 C548.85,491.76 539.55,493.16 516.00,493.49 C504.17,493.66 492.92,493.60 491.00,493.36 Z"/>
  </svg>
);

// Pencil icon SVG
const PencilIcon = ({ className }) => (
  <svg viewBox="0 0 320 320" fill="currentColor" className={className}>
    <path d="M 34.50 306.07 C26.35,304.05 20.02,298.93 15.86,291.00 L 13.50 286.50 L 13.50 160.00 C13.50,44.49 13.64,33.18 15.15,29.86 C17.58,24.51 23.41,18.52 28.78,15.85 L 33.50 13.50 L 109.75 13.22 C151.69,13.07 186.00,13.30 186.00,13.73 C186.00,14.16 177.34,23.17 166.75,33.75 L 147.50 52.98 L 100.50 53.24 L 53.50 53.50 L 53.50 160.00 L 53.50 266.50 L 160.00 266.50 L 266.50 266.50 L 266.76 219.50 L 267.02 172.50 L 286.25 153.25 C296.83,142.66 305.84,134.00 306.27,134.00 C306.70,134.00 306.93,168.31 306.78,210.25 L 306.50 286.50 L 303.84 291.50 C300.70,297.42 297.14,300.92 291.00,304.14 L 286.50 306.50 L 162.00 306.66 C93.53,306.74 36.15,306.48 34.50,306.07 ZM 80.00 213.20 L 80.00 186.39 L 83.31 183.19 L 86.61 179.99 L 95.39 185.22 C112.19,195.23 124.77,207.81 134.78,224.61 L 140.01 233.39 L 136.81 236.69 L 133.61 240.00 L 106.80 240.00 L 80.00 240.00 L 80.00 213.20 ZM 150.68 211.39 C140.54,196.01 124.25,179.78 109.28,170.15 C105.31,167.59 102.05,165.27 102.03,165.00 C102.01,164.72 128.50,137.99 160.90,105.60 L 219.79 46.71 L 226.22 50.30 C244.50,60.53 259.47,75.50 269.70,93.79 L 273.29 100.21 L 214.26 159.24 L 155.22 218.27 L 150.68 211.39 ZM 283.04 76.68 C275.69,65.67 254.94,44.99 243.72,37.48 L 234.94 31.60 L 244.18 22.32 L 253.43 13.03 L 258.96 13.61 C273.27,15.10 285.53,19.68 292.57,26.17 C299.51,32.57 304.82,45.96 306.39,61.04 L 306.97 66.57 L 297.73 75.72 L 288.50 84.87 L 283.04 76.68 Z"/>
  </svg>
);

// Plus icon SVG
const PlusIcon = ({ className }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <line x1="12" y1="5" x2="12" y2="19"></line>
    <line x1="5" y1="12" x2="19" y2="12"></line>
  </svg>
);

// Plan labels and credits
const PLAN_CONFIG = {
  free: { label: "Free Plan", maxCredits: 30 },
  start: { label: "Start Plan", maxCredits: 100 },
  plus: { label: "Plus Plan", maxCredits: 500 },
  creator: { label: "Creator Plan", maxCredits: 2000 }
};

export const ProfilePage = ({ user, onBack, onLogout, onUpdateUser }) => {
  const [activeView, setActiveView] = useState('main');
  const [userVideos, setUserVideos] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [editUsername, setEditUsername] = useState(user?.username || user?.name || '');
  const [isSaving, setIsSaving] = useState(false);
  const [usernameError, setUsernameError] = useState('');
  const [isCheckingUsername, setIsCheckingUsername] = useState(false);
  const fileInputRef = useRef(null);
  
  // Team state
  const [teamMembers, setTeamMembers] = useState([]);
  const [showInvitePopup, setShowInvitePopup] = useState(false);
  const [inviteUsername, setInviteUsername] = useState('');
  const [inviteError, setInviteError] = useState('');
  const [isSendingInvite, setIsSendingInvite] = useState(false);
  
  // Notifications state
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  
  // Swipe popup state
  const [popupDragY, setPopupDragY] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const popupStartY = useRef(0);

  useEffect(() => {
    fetchUserVideos();
    fetchTeam();
    fetchNotifications();
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

  const fetchTeam = async () => {
    if (!user?.user_id) return;
    
    try {
      const response = await axios.get(`${API}/users/${user.user_id}/team`);
      setTeamMembers(response.data.team || []);
    } catch (error) {
      console.error("Failed to fetch team:", error);
    }
  };

  const fetchNotifications = async () => {
    if (!user?.user_id) return;
    
    try {
      const response = await axios.get(`${API}/users/${user.user_id}/notifications`);
      setNotifications(response.data.notifications || []);
      setUnreadCount(response.data.unread_count || 0);
    } catch (error) {
      console.error("Failed to fetch notifications:", error);
    }
  };

  const checkUsernameAvailability = async (username) => {
    if (username.length < 3) {
      setUsernameError('At least 3 characters');
      return false;
    }
    
    setIsCheckingUsername(true);
    try {
      const response = await axios.get(`${API}/users/check-username/${username}?exclude_user_id=${user.user_id}`);
      if (!response.data.available) {
        setUsernameError('Username taken');
        return false;
      }
      setUsernameError('');
      return true;
    } catch (error) {
      console.error("Failed to check username:", error);
      return true;
    } finally {
      setIsCheckingUsername(false);
    }
  };

  const handleSaveProfile = async () => {
    if (!editUsername.trim()) return;
    
    const isAvailable = await checkUsernameAvailability(editUsername.trim());
    if (!isAvailable) return;
    
    setIsSaving(true);
    try {
      await axios.put(`${API}/users/${user.user_id}`, {
        username: editUsername.trim(),
        name: editUsername.trim()
      });
      
      const updatedUser = { ...user, username: editUsername.trim(), name: editUsername.trim() };
      localStorage.setItem("slind_user", JSON.stringify(updatedUser));
      if (onUpdateUser) onUpdateUser(updatedUser);
      
      toast.custom(() => (
        <div className="custom-toast-success">
          <img src={CHECK_ICON} alt="" className="toast-icon" />
          <span>Saved changes!</span>
        </div>
      ), { duration: 2000 });
      
      setActiveView('main');
    } catch (error) {
      console.error("Failed to save profile:", error);
      if (error.response?.data?.detail) {
        setUsernameError(error.response.data.detail);
      } else {
        toast.error("Failed to save changes");
      }
    } finally {
      setIsSaving(false);
    }
  };

  const handleAvatarUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    try {
      const formData = new FormData();
      formData.append("file", file);
      
      const uploadRes = await axios.post(`${API}/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      
      const avatarUrl = `${BACKEND_URL}${uploadRes.data.url}`;
      
      await axios.put(`${API}/users/${user.user_id}`, {
        picture: avatarUrl
      });
      
      const updatedUser = { ...user, picture: avatarUrl };
      localStorage.setItem("slind_user", JSON.stringify(updatedUser));
      if (onUpdateUser) onUpdateUser(updatedUser);
      
      toast.custom(() => (
        <div className="custom-toast-success">
          <img src={CHECK_ICON} alt="" className="toast-icon" />
          <span>Avatar updated!</span>
        </div>
      ), { duration: 2000 });
      
    } catch (error) {
      console.error("Failed to upload avatar:", error);
      toast.error("Failed to upload avatar");
    }
  };

  const handleSendInvite = async () => {
    if (inviteUsername.length < 3) return;
    
    setIsSendingInvite(true);
    setInviteError('');
    
    try {
      await axios.post(`${API}/users/${user.user_id}/team/invite`, {
        username: inviteUsername.trim()
      });
      
      toast.custom(() => (
        <div className="custom-toast-success">
          <img src={CHECK_ICON} alt="" className="toast-icon" />
          <span>Invite sent!</span>
        </div>
      ), { duration: 2000 });
      
      setShowInvitePopup(false);
      setInviteUsername('');
    } catch (error) {
      console.error("Failed to send invite:", error);
      setInviteError(error.response?.data?.detail || 'Failed to send invite');
    } finally {
      setIsSendingInvite(false);
    }
  };

  const handleAcceptInvite = async (inviteId) => {
    try {
      await axios.post(`${API}/team/invites/${inviteId}/accept`);
      fetchNotifications();
      fetchTeam();
      toast.custom(() => (
        <div className="custom-toast-success">
          <img src={CHECK_ICON} alt="" className="toast-icon" />
          <span>Joined team!</span>
        </div>
      ), { duration: 2000 });
    } catch (error) {
      console.error("Failed to accept invite:", error);
      toast.error("Failed to accept invite");
    }
  };

  const handleDeclineInvite = async (inviteId) => {
    try {
      await axios.post(`${API}/team/invites/${inviteId}/decline`);
      fetchNotifications();
    } catch (error) {
      console.error("Failed to decline invite:", error);
    }
  };

  // Swipe handlers for popup
  const handlePopupTouchStart = (e) => {
    popupStartY.current = e.touches[0].clientY;
    setIsDragging(true);
  };

  const handlePopupTouchMove = (e) => {
    if (!isDragging) return;
    const currentY = e.touches[0].clientY;
    const diff = currentY - popupStartY.current;
    if (diff > 0) {
      setPopupDragY(diff);
    }
  };

  const handlePopupTouchEnd = () => {
    setIsDragging(false);
    if (popupDragY > 100) {
      setShowInvitePopup(false);
    }
    setPopupDragY(0);
  };

  const completedVideos = userVideos.filter(v => v.status === 'completed');
  const userName = user?.username || user?.name || user?.email?.split('@')[0] || 'User';
  const userPlan = user?.plan || 'free';
  const userCredits = user?.credits || 0;
  const planConfig = PLAN_CONFIG[userPlan];

  // ============ NOTIFICATIONS VIEW ============
  if (activeView === 'notifications') {
    return (
      <div className="profile-page-v2" data-testid="notifications-page">
        <div className="profile-v2-header">
          <button 
            className="profile-v2-back-btn"
            onClick={() => setActiveView('main')}
            data-testid="notifications-back-btn"
          >
            <ChevronLeft className="w-6 h-6" />
          </button>
          
          <h1 className="profile-v2-title">Notifications</h1>
          
          <div className="header-spacer" />
        </div>

        <div className="notifications-list">
          {notifications.length === 0 ? (
            <div className="notifications-empty">
              <p>No notifications yet</p>
            </div>
          ) : (
            notifications.map((notif) => (
              <div 
                key={notif.id} 
                className={`notification-item ${!notif.read ? 'unread' : ''}`}
                data-testid={`notification-${notif.id}`}
              >
                <div className="notification-content">
                  <p className="notification-title">{notif.title}</p>
                  <p className="notification-message">{notif.message}</p>
                </div>
                
                {notif.type === 'team_invite' && notif.data?.invite_id && (
                  <div className="notification-actions">
                    <button 
                      className="notif-accept-btn"
                      onClick={() => handleAcceptInvite(notif.data.invite_id)}
                    >
                      Accept
                    </button>
                    <button 
                      className="notif-decline-btn"
                      onClick={() => handleDeclineInvite(notif.data.invite_id)}
                    >
                      Decline
                    </button>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    );
  }

  // ============ MAIN PROFILE VIEW ============
  if (activeView === 'main') {
    return (
      <div className="profile-page-v2" data-testid="profile-page">
        {/* Header */}
        <div className="profile-v2-header">
          <button 
            className="profile-v2-close-btn"
            onClick={onBack}
            data-testid="profile-close-btn"
          >
            <X className="w-5 h-5" />
          </button>
          
          <h1 className="profile-v2-title">Профиль</h1>
          
          <div className="profile-v2-header-right">
            <button 
              className="profile-v2-notif-btn"
              onClick={() => setActiveView('notifications')}
              data-testid="notifications-btn"
            >
              <Bell className="w-5 h-5" />
              {unreadCount > 0 && (
                <span className="notif-badge">{unreadCount}</span>
              )}
            </button>
            
            <div className="profile-v2-credits">
              <CreditsIcon className="credits-icon-svg" />
              <span>{userCredits}</span>
            </div>
          </div>
        </div>

        {/* User Card */}
        <button 
          className="profile-v2-user-card"
          onClick={() => {
            setEditUsername(userName);
            setActiveView('profile-edit');
          }}
          data-testid="profile-card"
        >
          <div className="profile-v2-avatar">
            {user?.picture ? (
              <img src={user.picture} alt={userName} />
            ) : (
              <PersonIcon className="default-avatar-icon" />
            )}
          </div>
          
          <div className="profile-v2-user-info">
            <h2 className="profile-v2-username">{userName}</h2>
            <p className="profile-v2-plan">{planConfig.label}</p>
          </div>
          
          <ChevronRight className="profile-v2-arrow" />
        </button>

        {/* Team Section */}
        <div className="profile-section">
          <h3 className="profile-section-title">Team</h3>
          <p className="profile-section-subtitle">Create together</p>
          
          <div className="team-cards-row">
            {/* Invite Member Card */}
            <button 
              className="team-invite-card"
              onClick={() => setShowInvitePopup(true)}
              data-testid="invite-member-btn"
            >
              <div className="team-invite-circle">
                <PlusIcon className="team-plus-icon" />
              </div>
              <span className="team-invite-text">Invite member</span>
            </button>
            
            {/* Team Members */}
            {teamMembers.map((member) => (
              <div 
                key={member.id} 
                className="team-member-card"
                data-testid={`team-member-${member.member_id}`}
              >
                <div className="team-member-avatar">
                  {member.member_info?.picture ? (
                    <img src={member.member_info.picture} alt="" />
                  ) : (
                    <PersonIcon className="team-member-icon" />
                  )}
                </div>
                <span className="team-member-name">
                  {member.member_info?.username || member.member_info?.name || 'User'}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* My Creations Section */}
        <div className="profile-section">
          <h3 className="profile-section-title">My creations</h3>
          
          {isLoading ? (
            <div className="profile-loading">Loading...</div>
          ) : completedVideos.length > 0 ? (
            <div className="creations-grid">
              {completedVideos.map((video) => (
                <div 
                  key={video.id} 
                  className="creation-item"
                  data-testid={`video-${video.id}`}
                >
                  {video.poster_url ? (
                    <img 
                      src={`${BACKEND_URL}${video.poster_url}`} 
                      alt={video.title || 'Video'}
                      className="creation-thumb"
                    />
                  ) : video.video_url ? (
                    <video 
                      src={`${BACKEND_URL}${video.video_url}`}
                      className="creation-thumb"
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
            <div className="creations-empty">
              <div className="creations-empty-grid">
                <div className="creation-item-empty top-left" />
                <div className="creation-item-empty top-right" />
                <div className="creation-item-empty bottom-left" />
                <div className="creation-item-empty bottom-right" />
              </div>
              <div className="creations-empty-overlay">
                <p className="creations-empty-text">No videos yet</p>
                <button 
                  className="creations-start-btn"
                  onClick={onBack}
                  data-testid="start-create-btn"
                >
                  Start create!
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Invite Popup */}
        {showInvitePopup && (
          <div 
            className="invite-popup-overlay"
            onClick={(e) => e.target === e.currentTarget && setShowInvitePopup(false)}
          >
            <div 
              className="invite-popup"
              style={{ transform: `translateY(${popupDragY}px)` }}
              onTouchStart={handlePopupTouchStart}
              onTouchMove={handlePopupTouchMove}
              onTouchEnd={handlePopupTouchEnd}
            >
              <div className="popup-drag-handle" />
              
              <h2 className="invite-popup-title">Invite member</h2>
              
              <input
                type="text"
                value={inviteUsername}
                onChange={(e) => {
                  setInviteUsername(e.target.value);
                  setInviteError('');
                }}
                placeholder="username"
                className="invite-input"
                data-testid="invite-username-input"
              />
              
              {inviteError && (
                <p className="invite-error">{inviteError}</p>
              )}
              
              <button 
                className={`invite-send-btn ${inviteUsername.length >= 3 ? 'active' : ''}`}
                onClick={handleSendInvite}
                disabled={inviteUsername.length < 3 || isSendingInvite}
                data-testid="send-invite-btn"
              >
                {isSendingInvite ? 'Sending...' : 'Send invite'}
              </button>
              
              <p className="invite-hint">
                Invitations will be sent to users via notifications.
              </p>
            </div>
          </div>
        )}
      </div>
    );
  }

  // ============ PROFILE EDIT VIEW ============
  if (activeView === 'profile-edit') {
    return (
      <div className="profile-page-v2 edit-view" data-testid="profile-edit-page">
        {/* Header */}
        <div className="profile-v2-header">
          <button 
            className="profile-v2-back-btn"
            onClick={() => setActiveView('main')}
            data-testid="profile-edit-back"
          >
            <ChevronLeft className="w-6 h-6" />
          </button>
          
          <h1 className="profile-v2-title">Profile</h1>
          
          <div className="header-spacer" />
        </div>

        {/* Avatar with edit */}
        <div className="profile-edit-avatar-section">
          <div className="profile-edit-avatar-wrapper">
            <div className="profile-edit-avatar-large">
              {user?.picture ? (
                <img src={user.picture} alt={userName} />
              ) : (
                <PersonIcon className="default-avatar-icon-large" />
              )}
            </div>
            <button 
              className="avatar-edit-btn-v2"
              onClick={() => fileInputRef.current?.click()}
              data-testid="avatar-edit-btn"
            >
              <PencilIcon className="pencil-icon" />
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleAvatarUpload}
              className="hidden"
            />
          </div>
        </div>

        {/* Username input */}
        <div className="profile-edit-form">
          <div className="profile-edit-field">
            <label className="profile-edit-label">Username</label>
            <input
              type="text"
              value={editUsername}
              onChange={(e) => {
                setEditUsername(e.target.value);
                setUsernameError('');
              }}
              onBlur={() => editUsername.length >= 3 && checkUsernameAvailability(editUsername)}
              className={`profile-edit-input ${usernameError ? 'error' : ''}`}
              placeholder="Your username"
              data-testid="profile-username-input"
            />
            {usernameError && (
              <p className="username-error">{usernameError}</p>
            )}
          </div>

          <button 
            className={`profile-save-btn ${editUsername.trim() !== userName && !usernameError ? 'active' : ''}`}
            onClick={handleSaveProfile}
            disabled={isSaving || editUsername.trim() === userName || !!usernameError || isCheckingUsername}
            data-testid="profile-save-btn"
          >
            {isSaving ? 'Saving...' : isCheckingUsername ? 'Checking...' : 'Save'}
          </button>
        </div>

        {/* Logout */}
        <div className="profile-logout-section">
          <button 
            className="profile-logout-btn"
            onClick={onLogout}
            data-testid="logout-btn"
          >
            Log out
          </button>
        </div>
      </div>
    );
  }

  return null;
};

export default ProfilePage;
