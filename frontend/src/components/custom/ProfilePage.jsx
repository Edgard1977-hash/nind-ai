import { useState, useEffect, useRef } from "react";
import { ChevronLeft, ChevronRight, X } from "lucide-react";
import { toast } from "sonner";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// User's custom icons
const CHECK_ICON = "/assets/check-icon.png";

// Credits icon SVG (user's custom sparkle)
const CreditsIcon = ({ className, color = "currentColor" }) => (
  <svg viewBox="0 0 1024 1024" fill={color} className={className}>
    <path d="M 498.04 902.32 C487.03,900.01 475.94,891.85 469.24,881.12 C466.30,876.39 464.43,871.45 454.27,841.50 C449.60,827.75 442.50,806.83 438.48,795.00 C434.46,783.17 424.65,754.60 416.68,731.50 C408.71,708.40 399.39,681.40 395.98,671.50 C388.62,650.16 385.22,643.34 378.45,636.41 C370.67,628.43 369.90,628.12 300.00,604.00 C285.98,599.16 263.25,591.29 249.50,586.52 C235.75,581.74 212.35,573.65 197.50,568.54 C161.94,556.30 145.49,550.28 139.99,547.49 C127.63,541.24 116.17,529.21 111.93,518.06 C104.36,498.12 110.23,477.38 127.50,463.09 C139.35,453.28 138.70,453.53 288.34,404.03 C330.05,390.24 366.01,378.02 368.23,376.88 C374.55,373.66 381.40,366.60 384.85,359.76 C386.58,356.32 398.77,321.33 411.93,282.00 C448.35,173.17 459.60,140.54 463.46,132.51 C472.77,113.15 492.48,102.78 514.11,105.84 C532.90,108.49 546.88,120.13 553.76,138.82 C555.11,142.49 572.11,192.83 591.54,250.67 C610.97,308.52 627.63,357.34 628.57,359.17 C631.46,364.83 636.05,369.98 641.39,373.58 C646.67,377.15 663.73,382.97 789.00,424.00 C873.18,451.56 877.75,453.41 890.17,464.84 C907.43,480.74 911.43,504.29 900.21,524.00 C891.35,539.58 880.18,546.86 848.50,557.74 C841.35,560.19 819.30,567.74 799.50,574.52 C691.95,611.32 651.67,625.51 645.98,628.61 C639.57,632.10 632.84,638.77 629.14,645.31 C626.23,650.46 617.93,673.51 600.98,723.50 C589.01,758.79 554.96,857.43 551.01,868.23 C545.18,884.21 537.37,893.59 525.12,899.32 C519.44,901.99 517.22,902.46 509.50,902.63 C504.55,902.74 499.39,902.60 498.04,902.32 Z"/>
  </svg>
);

// Upgrade icon SVG
const UpgradeIcon = ({ className, color = "currentColor" }) => (
  <svg viewBox="0 0 1024 1024" fill={color} className={className}>
    <path d="M 501.40 832.12 C495.40,830.07 491.71,827.38 487.25,821.78 C480.59,813.45 481.00,826.00 481.00,628.53 L 481.00 449.43 L 448.25 482.29 C430.24,500.36 413.70,516.20 411.50,517.50 C392.69,528.57 367.00,513.54 367.00,491.45 C367.00,479.08 364.80,481.69 432.92,413.30 C472.84,373.23 496.42,350.29 499.19,348.82 C502.64,346.99 505.11,346.53 511.57,346.52 C525.33,346.49 523.04,344.59 591.85,413.15 C638.28,459.41 653.29,474.95 655.11,478.65 C658.63,485.80 658.49,497.50 654.79,504.59 C651.56,510.78 646.39,515.48 639.18,518.77 C634.57,520.88 632.73,521.18 626.64,520.78 C621.98,520.48 617.94,519.53 615.00,518.05 C611.95,516.51 599.66,504.92 576.76,481.96 L 543.02 448.14 L 542.76 630.32 L 542.50 812.50 L 539.50 817.92 C532.18,831.15 516.11,837.14 501.40,832.12 ZM 369.92 791.05 C355.32,786.62 321.88,764.79 296.50,743.10 C263.75,715.13 235.47,679.27 214.70,639.41 C206.68,624.01 195.13,589.00 190.49,566.06 C177.49,501.67 184.77,430.58 210.09,374.75 C238.28,312.60 285.53,261.59 348.28,225.56 C357.94,220.02 389.61,205.00 391.65,205.00 C392.03,205.00 395.09,203.90 398.45,202.56 C416.80,195.21 450.44,187.54 478.00,184.41 C495.62,182.41 536.90,182.97 554.75,185.46 C586.26,189.85 614.69,197.50 640.52,208.53 C713.98,239.91 772.39,293.18 807.14,360.50 C825.70,396.47 836.01,432.75 838.95,472.50 C844.99,553.96 824.08,628.59 778.15,689.50 C748.26,729.13 704.08,766.72 662.50,787.92 C655.93,791.26 654.91,791.48 646.00,791.49 C637.48,791.49 635.94,791.19 631.07,788.63 C624.16,785.01 618.90,779.53 615.32,772.24 C612.94,767.40 612.50,765.25 612.50,758.50 C612.50,751.70 612.93,749.62 615.39,744.61 C619.40,736.46 624.02,732.22 635.04,726.59 C691.95,697.52 735.68,650.52 757.91,594.52 C777.38,545.48 781.26,487.89 768.43,438.26 C756.09,390.55 734.83,353.13 699.00,316.03 C684.40,300.92 659.69,283.55 635.03,271.07 C605.30,256.02 581.43,248.54 545.00,242.83 C531.73,240.75 488.50,241.10 474.00,243.40 C427.61,250.75 387.91,267.38 351.00,294.91 C285.81,343.52 246.43,425.85 249.32,507.50 C251.68,574.48 277.83,634.66 324.40,680.37 C343.04,698.66 361.77,712.17 386.18,724.94 C402.00,733.22 407.41,738.15 410.95,747.55 C413.79,755.06 413.42,764.92 410.02,772.77 C407.07,779.59 398.88,787.15 391.46,789.93 C385.74,792.07 375.11,792.62 369.92,791.05 Z"/>
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
        <div className="credits-progress-card">
          <div className="credits-balance-row">
            <CreditsIcon className="credits-icon-small" color="#FFFFFF" />
            <span className="credits-amount">{userCredits}</span>
            <span className="credits-label">credits left</span>
          </div>
          <div className="credits-progress-track">
            <div 
              className="credits-progress-fill"
              style={{ 
                width: `${progressPercentage}%`,
                backgroundColor: progressColor
              }}
            />
          </div>
        </div>

        {/* Get More Card */}
        <div className="get-more-card">
          <div className="get-more-left">
            <UpgradeIcon className="get-more-icon" color="#01E0FD" />
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
