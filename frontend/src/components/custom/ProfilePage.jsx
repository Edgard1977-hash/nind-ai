import { useState, useEffect, useRef } from "react";
import { ChevronLeft, ChevronRight, X } from "lucide-react";
import { toast } from "sonner";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// User's custom icons
const CHECK_ICON = "/assets/check-icon.png";

// Star icon SVG (user's custom)
const StarIcon = ({ className, color = "currentColor" }) => (
  <svg viewBox="0 0 1024 1024" fill={color} className={className}>
    <path d="M 258.67 993.43 C241.26,990.72 225.95,985.25 211.01,976.40 C204.99,972.83 200.31,968.92 193.81,962.01 C169.14,935.77 156.00,904.97 156.00,873.36 C156.00,865.24 159.17,845.22 176.47,744.00 C178.96,729.42 183.50,702.88 186.54,685.00 L 192.08 652.50 L 188.29 649.07 C184.55,645.69 149.24,611.40 84.18,547.98 C65.85,530.12 48.33,513.26 45.25,510.51 C34.38,500.84 22.94,484.47 17.61,470.97 C11.40,455.23 10.50,449.96 10.53,429.50 C10.55,408.82 11.24,404.82 18.12,385.32 C28.99,354.50 50.47,330.48 79.19,317.03 C90.04,311.95 99.36,309.44 116.50,306.97 C183.06,297.38 312.90,277.77 314.50,277.07 C315.86,276.47 324.36,260.01 340.96,225.84 C389.84,125.27 408.97,86.81 413.58,79.88 C419.67,70.72 433.22,56.51 442.62,49.44 C462.85,34.22 487.17,26.00 512.00,26.00 C542.23,26.00 569.71,37.28 592.36,59.00 C607.63,73.64 611.35,79.50 632.05,121.50 C651.85,161.68 686.98,233.54 700.12,260.73 C706.28,273.47 708.45,277.07 710.23,277.48 C711.48,277.77 756.60,284.54 810.50,292.53 C864.40,300.51 912.79,308.10 918.04,309.40 C949.67,317.24 975.07,335.24 993.46,362.87 C1005.49,380.93 1010.30,394.88 1011.90,416.28 C1014.01,444.53 1007.47,470.29 992.41,493.09 C984.86,504.53 986.96,502.38 904.99,581.99 C851.21,634.21 833.56,651.31 832.73,652.00 C832.05,652.56 835.92,676.40 849.49,755.50 C865.85,850.81 868.00,864.83 868.00,876.30 C868.00,909.65 856.35,936.89 831.56,961.51 C821.36,971.64 819.55,972.98 808.99,978.22 C785.59,989.81 770.01,993.52 745.00,993.45 C726.14,993.40 718.29,992.09 703.45,986.53 C697.61,984.34 666.44,968.52 627.50,947.96 C622.55,945.35 604.78,936.03 588.00,927.24 C571.22,918.46 547.52,906.04 535.32,899.64 C523.12,893.24 512.66,888.00 512.08,888.00 C511.49,888.00 469.50,909.73 418.76,936.30 C368.02,962.86 324.25,985.54 321.50,986.69 C303.85,994.06 279.50,996.67 258.67,993.43 Z"/>
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

// Plan labels
const PLAN_CONFIG = {
  free: { label: "Free Plan" },
  start: { label: "Start Plan" },
  plus: { label: "Plus Plan" },
  creator: { label: "Creator Plan" }
};

// Get progress bar color based on percentage
const getProgressColor = (percentage) => {
  if (percentage === 0) return '#3A3B3F'; // gray
  if (percentage < 15) return '#FF4444'; // red
  if (percentage < 30) return '#FFD700'; // yellow
  return '#01E0FD'; // cyan
};

export const ProfilePage = ({ user, onBack, onLogout, onUpdateUser }) => {
  const [activeView, setActiveView] = useState('main');
  const [editUsername, setEditUsername] = useState(user?.username || user?.name || '');
  const [isSaving, setIsSaving] = useState(false);
  const [usernameError, setUsernameError] = useState('');
  const [isCheckingUsername, setIsCheckingUsername] = useState(false);
  const fileInputRef = useRef(null);

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

  const userName = user?.username || user?.name || user?.email?.split('@')[0] || 'User';
  const userPlan = user?.plan || 'free';
  const userCredits = user?.credits || 0;
  const lastDeposit = user?.last_deposit || userCredits || 1; // Prevent division by zero
  const planConfig = PLAN_CONFIG[userPlan];
  
  // Calculate progress percentage based on last deposit
  const progressPercentage = lastDeposit > 0 ? Math.round((userCredits / lastDeposit) * 100) : 0;
  const progressColor = getProgressColor(progressPercentage);

  // ============ MAIN ACCOUNT VIEW ============
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
          
          <h1 className="profile-v2-title">Account</h1>
          
          <div className="header-spacer" />
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

        {/* Credits Progress Bar */}
        <div className="credits-progress-container">
          <div 
            className="credits-progress-inner"
            style={{ 
              borderColor: progressColor,
              borderWidth: '5px',
              borderStyle: 'solid'
            }}
          >
            <StarIcon className="credits-star-icon" color="#01E0FD" />
            <span className="credits-amount">{userCredits}</span>
            <span className="credits-label">credits left</span>
          </div>
        </div>

        {/* Get More Card */}
        <div className="get-more-card">
          <div className="get-more-left">
            <StarIcon className="get-more-star" color="#01E0FD" />
            <span className="get-more-text">Get more</span>
          </div>
          <button 
            className="get-more-upgrade-btn"
            onClick={() => {/* TODO: Upgrade flow */}}
            data-testid="upgrade-btn"
          >
            Upgrade
          </button>
        </div>
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
