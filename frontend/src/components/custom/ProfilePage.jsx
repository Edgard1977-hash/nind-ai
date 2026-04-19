import { useState, useEffect, useRef } from "react";
import { ChevronLeft, ChevronRight, X, Globe, Bell, HelpCircle, LogOut, Trash2 } from "lucide-react";
import { toast } from "sonner";
import axios from "axios";
import { translations, getTranslation } from "../../utils/translations";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CHECK_ICON = "/assets/check-icon.png";

// Credits icon SVG
const CreditsIcon = ({ className, color = "currentColor" }) => (
  <svg viewBox="0 0 1024 1024" fill={color} className={className}>
    <path d="M 498.04 902.32 C487.03,900.01 475.94,891.85 469.24,881.12 C466.30,876.39 464.43,871.45 454.27,841.50 C449.60,827.75 442.50,806.83 438.48,795.00 C434.46,783.17 424.65,754.60 416.68,731.50 C408.71,708.40 399.39,681.40 395.98,671.50 C388.62,650.16 385.22,643.34 378.45,636.41 C370.67,628.43 369.90,628.12 300.00,604.00 C285.98,599.16 263.25,591.29 249.50,586.52 C235.75,581.74 212.35,573.65 197.50,568.54 C161.94,556.30 145.49,550.28 139.99,547.49 C127.63,541.24 116.17,529.21 111.93,518.06 C104.36,498.12 110.23,477.38 127.50,463.09 C139.35,453.28 138.70,453.53 288.34,404.03 C330.05,390.24 366.01,378.02 368.23,376.88 C374.55,373.66 381.40,366.60 384.85,359.76 C386.58,356.32 398.77,321.33 411.93,282.00 C448.35,173.17 459.60,140.54 463.46,132.51 C472.77,113.15 492.48,102.78 514.11,105.84 C532.90,108.49 546.88,120.13 553.76,138.82 C555.11,142.49 572.11,192.83 591.54,250.67 C610.97,308.52 627.63,357.34 628.57,359.17 C631.46,364.83 636.05,369.98 641.39,373.58 C646.67,377.15 663.73,382.97 789.00,424.00 C873.18,451.56 877.75,453.41 890.17,464.84 C907.43,480.74 911.43,504.29 900.21,524.00 C891.35,539.58 880.18,546.86 848.50,557.74 C841.35,560.19 819.30,567.74 799.50,574.52 C691.95,611.32 651.67,625.51 645.98,628.61 C639.57,632.10 632.84,638.77 629.14,645.31 C626.23,650.46 617.93,673.51 600.98,723.50 C589.01,758.79 554.96,857.43 551.01,868.23 C545.18,884.21 537.37,893.59 525.12,899.32 C519.44,901.99 517.22,902.46 509.50,902.63 C504.55,902.74 499.39,902.60 498.04,902.32 Z"/>
  </svg>
);

// Upgrade icon SVG (new from user)
const UpgradeIcon = ({ className, color = "currentColor" }) => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 551 551" fill={color} className={className}>
    <path d="M 247.50 535.35 C237.41,534.26 217.51,530.67 206.95,528.03 C148.40,513.36 93.94,477.03 58.19,428.78 C46.79,413.40 43.43,407.94 35.20,391.50 C17.70,356.52 9.72,324.45 8.35,283.50 C6.90,240.36 15.11,201.93 33.97,163.50 C68.19,93.79 130.00,44.87 208.34,25.48 C227.53,20.73 241.29,18.96 264.00,18.32 C338.03,16.25 403.35,40.37 457.60,89.83 C480.32,110.54 499.64,136.79 514.04,166.50 C537.15,214.21 544.10,266.54 534.40,320.00 C525.80,367.48 505.11,410.49 473.56,446.50 C465.66,455.52 465.42,455.77 454.64,465.78 C422.76,495.42 382.37,517.15 338.00,528.53 C318.24,533.60 304.28,535.20 277.50,535.49 C263.20,535.65 249.70,535.58 247.50,535.35 ZM 297.04 478.57 C328.65,474.64 356.68,465.28 381.94,450.22 C411.74,432.44 437.43,406.76 455.89,376.28 C474.13,346.18 484.00,310.07 484.00,273.41 C484.00,240.17 477.24,212.88 461.30,181.69 C434.33,128.94 385.66,90.70 325.00,74.61 C308.91,70.34 298.26,68.90 278.50,68.33 C256.05,67.68 242.26,69.16 221.61,74.45 C182.38,84.51 151.23,101.90 123.89,129.00 C82.98,169.56 63.00,216.36 63.00,271.65 C63.00,298.67 65.70,316.07 73.61,340.00 C92.24,396.37 137.10,442.37 195.95,465.46 C212.94,472.12 236.88,477.79 254.50,479.32 C265.06,480.23 286.74,479.86 297.04,478.57 ZM 261.56 413.98 C255.62,411.66 248.77,405.19 245.73,399.02 L 243.50 394.50 L 243.22 312.66 L 242.94 230.83 L 217.75 255.57 C190.48,282.35 188.36,283.88 177.45,284.76 C168.31,285.49 162.03,283.08 154.91,276.11 C148.53,269.87 146.65,265.25 146.83,256.31 C147.02,246.73 149.08,244.07 177.31,216.74 C191.66,202.86 215.03,180.02 229.24,166.00 C258.98,136.65 261.86,134.56 272.50,134.56 C278.51,134.56 280.31,135.00 284.67,137.53 C287.67,139.27 304.44,154.60 325.12,174.50 C382.24,229.48 395.07,242.28 397.18,246.38 C403.61,258.90 398.29,274.09 384.86,281.53 C380.15,284.14 378.53,284.50 371.50,284.47 C364.67,284.45 362.76,284.03 358.44,281.67 C353.23,278.81 338.22,265.27 315.42,242.86 C308.23,235.79 302.04,230.00 301.67,230.00 C301.30,230.00 301.00,267.04 301.00,312.30 L 301.00 394.61 L 298.41 399.80 C291.86,412.94 275.27,419.33 261.56,413.98 Z"/>
  </svg>
);

// Pencil icon SVG
const PencilIcon = ({ className }) => (
  <svg viewBox="0 0 320 320" fill="currentColor" className={className}>
    <path d="M 34.50 306.07 C26.35,304.05 20.02,298.93 15.86,291.00 L 13.50 286.50 L 13.50 160.00 C13.50,44.49 13.64,33.18 15.15,29.86 C17.58,24.51 23.41,18.52 28.78,15.85 L 33.50 13.50 L 109.75 13.22 C151.69,13.07 186.00,13.30 186.00,13.73 C186.00,14.16 177.34,23.17 166.75,33.75 L 147.50 52.98 L 100.50 53.24 L 53.50 53.50 L 53.50 160.00 L 53.50 266.50 L 160.00 266.50 L 266.50 266.50 L 266.76 219.50 L 267.02 172.50 L 286.25 153.25 C296.83,142.66 305.84,134.00 306.27,134.00 C306.70,134.00 306.93,168.31 306.78,210.25 L 306.50 286.50 L 303.84 291.50 C300.70,297.42 297.14,300.92 291.00,304.14 L 286.50 306.50 L 162.00 306.66 C93.53,306.74 36.15,306.48 34.50,306.07 ZM 80.00 213.20 L 80.00 186.39 L 83.31 183.19 L 86.61 179.99 L 95.39 185.22 C112.19,195.23 124.77,207.81 134.78,224.61 L 140.01 233.39 L 136.81 236.69 L 133.61 240.00 L 106.80 240.00 L 80.00 240.00 L 80.00 213.20 ZM 150.68 211.39 C140.54,196.01 124.25,179.78 109.28,170.15 C105.31,167.59 102.05,165.27 102.03,165.00 C102.01,164.72 128.50,137.99 160.90,105.60 L 219.79 46.71 L 226.22 50.30 C244.50,60.53 259.47,75.50 269.70,93.79 L 273.29 100.21 L 214.26 159.24 L 155.22 218.27 L 150.68 211.39 ZM 283.04 76.68 C275.69,65.67 254.94,44.99 243.72,37.48 L 234.94 31.60 L 244.18 22.32 L 253.43 13.03 L 258.96 13.61 C273.27,15.10 285.53,19.68 292.57,26.17 C299.51,32.57 304.82,45.96 306.39,61.04 L 306.97 66.57 L 297.73 75.72 L 288.50 84.87 L 283.04 76.68 Z"/>
  </svg>
);

// Chevron icon (arrow without line)
const ChevronIcon = ({ className }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <polyline points="9 18 15 12 9 6"></polyline>
  </svg>
);

// Person icon SVG (новая иконка - такая же как в header)
const PersonIcon = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 659 659" fill="currentColor" className={className}>
    <path d="M 281.50 634.00 C215.38,629.79 149.86,617.82 86.82,598.42 C63.60,591.27 55.28,587.64 49.68,582.22 C43.75,576.48 43.00,574.34 43.00,563.16 C43.00,545.74 47.86,526.69 57.52,506.29 C81.62,455.37 130.93,416.06 200.50,392.29 C274.64,366.97 354.62,364.48 434.50,384.99 C482.26,397.26 527.95,420.28 558.79,447.64 C589.85,475.19 611.75,512.92 617.40,548.62 C620.57,568.64 619.13,576.28 610.89,583.39 C604.99,588.48 601.70,590.06 585.94,595.40 C537.18,611.92 469.83,625.11 396.00,632.60 C378.08,634.42 302.63,635.34 281.50,634.00 ZM 306.50 328.58 C268.24,322.16 235.34,303.84 213.04,276.55 C193.15,252.20 182.25,226.87 178.43,196.09 C171.82,142.83 187.71,96.31 224.53,61.16 C245.94,40.72 271.25,27.30 300.66,20.80 C314.93,17.64 343.05,17.66 357.77,20.83 C373.65,24.25 383.36,27.60 397.50,34.54 C439.98,55.36 470.78,93.68 480.45,137.73 C484.17,154.66 485.21,177.92 483.07,196.50 C476.67,252.18 436.52,301.82 382.00,321.47 C365.65,327.37 355.07,329.15 334.00,329.55 C320.68,329.81 311.96,329.50 306.50,328.58 Z"/>
  </svg>
);

// Languages
const LANGUAGES = [
  { code: 'en', name: 'English', flag: '🇬🇧' },
  { code: 'fr', name: 'Français', flag: '🇫🇷' },
  { code: 'de', name: 'Deutsch', flag: '🇩🇪' },
  { code: 'pt', name: 'Português', flag: '🇵🇹' },
  { code: 'es', name: 'Español', flag: '🇪🇸' },
  { code: 'ru', name: 'Русский', flag: '🇷🇺' },
];

// Get progress bar color based on percentage
const getProgressColor = (percentage) => {
  if (percentage === 0) return '#3A3B3F';
  if (percentage < 15) return '#FF4444';
  if (percentage < 30) return '#FFD700';
  return '#01E0FD';
};

// Show success toast
const showSuccessToast = (message) => {
  toast.success(message, {
    style: {
      background: '#1D1E20',
      color: '#fff',
      border: '1px solid rgba(255,255,255,0.1)',
    },
  });
};

export const ProfilePage = ({ user, onBack, onLogout, onUpdateUser, currentLang, onLanguageChange }) => {
  const [activeView, setActiveView] = useState('main');
  const [editName, setEditName] = useState(user?.name || '');
  const [editUsername, setEditUsername] = useState(user?.username || user?.name || '');
  const [isSaving, setIsSaving] = useState(false);
  const [usernameError, setUsernameError] = useState('');
  const [isCheckingUsername, setIsCheckingUsername] = useState(false);
  const [showLanguagePopup, setShowLanguagePopup] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState(currentLang || localStorage.getItem('slind_language') || 'en');
  const [showConfirmPopup, setShowConfirmPopup] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const fileInputRef = useRef(null);

  // Translation helper
  const t = (key) => getTranslation(selectedLanguage, key);

  // Plan labels with translations
  const getPlanLabel = (plan) => {
    const planKeys = {
      free: 'freePlan',
      start: 'startPlan',
      plus: 'plusPlan',
      creator: 'creatorPlan'
    };
    return t(planKeys[plan] || 'freePlan');
  };

  useEffect(() => {
    fetchNotifications();
  }, []);

  // Swipe to close popup states
  const [popupDragY, setPopupDragY] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const popupStartY = useRef(0);

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

  const handlePopupTouchEnd = (closePopup) => {
    if (popupDragY > 100) {
      closePopup();
    }
    setPopupDragY(0);
    setIsDragging(false);
  };

  const fetchNotifications = async () => {
    try {
      const response = await axios.get(`${API}/user/notifications`);
      setNotifications(response.data.notifications || []);
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
    if (!editUsername.trim() || !editName.trim()) return;
    
    const isAvailable = await checkUsernameAvailability(editUsername.trim());
    if (!isAvailable) return;
    
    setIsSaving(true);
    try {
      await axios.put(`${API}/users/${user.user_id}`, {
        username: editUsername.trim(),
        name: editName.trim()
      });
      
      const updatedUser = { 
        ...user, 
        username: editUsername.trim(), 
        name: editName.trim() 
      };
      localStorage.setItem("slind_user", JSON.stringify(updatedUser));
      if (onUpdateUser) onUpdateUser(updatedUser);
      
      showSuccessToast(t('savedChanges'));
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
      
      showSuccessToast(t('avatarUpdated'));
    } catch (error) {
      console.error("Failed to upload avatar:", error);
      toast.error("Failed to upload avatar");
    }
  };

  const handleLanguageSelect = (langCode) => {
    setSelectedLanguage(langCode);
    localStorage.setItem('slind_language', langCode);
    if (onLanguageChange) {
      onLanguageChange(langCode);
    }
    // Don't close popup automatically - user closes it manually
  };

  const handleConfirmAction = () => {
    if (showConfirmPopup === 'logout') {
      onLogout();
    } else if (showConfirmPopup === 'delete') {
      toast.error("Account deletion not implemented yet");
    }
    setShowConfirmPopup(null);
  };

  const userName = user?.username || user?.name || user?.email?.split('@')[0] || 'User';
  const userPlan = user?.plan || 'free';
  const userCredits = user?.credits || 0;
  const lastDeposit = user?.last_deposit || userCredits || 1;
  
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
          
          <h1 className="profile-v2-title">{t('account')}</h1>
          
          <div className="header-spacer" />
        </div>

        {/* User Card */}
        <button 
          className="profile-v2-user-card"
          onClick={() => {
            setEditName(user?.name || '');
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
            <p className="profile-v2-plan">{getPlanLabel(userPlan)}</p>
          </div>
          
          <ChevronIcon className="profile-v2-arrow" />
        </button>

        {/* Credits Progress Bar */}
        <div className="credits-progress-card">
          <div className="credits-balance-row">
            <CreditsIcon className="credits-icon-small" color="#FFFFFF" />
            <span className="credits-amount">{userCredits}</span>
            <span className="credits-label">{t('creditsLeft')}</span>
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
            <span className="get-more-text">{t('getMore')}</span>
          </div>
          <button 
            className="get-more-upgrade-btn"
            onClick={() => {/* TODO: Upgrade flow */}}
            data-testid="upgrade-btn"
          >
            {t('upgrade')}
          </button>
        </div>

        {/* Divider */}
        <div className="account-divider" />

        {/* Settings Menu */}
        <div className="settings-menu-card">
          <button 
            className="settings-menu-item"
            onClick={() => setShowLanguagePopup(true)}
            data-testid="language-btn"
          >
            <Globe className="settings-menu-icon" />
            <span className="settings-menu-text">{t('language')}</span>
            <ChevronIcon className="settings-menu-arrow" />
          </button>

          <button 
            className="settings-menu-item"
            onClick={() => setActiveView('notifications')}
            data-testid="notifications-btn"
          >
            <Bell className="settings-menu-icon" fill="currentColor" />
            <span className="settings-menu-text">{t('notifications')}</span>
            <ChevronIcon className="settings-menu-arrow" />
          </button>

          <button 
            className="settings-menu-item"
            onClick={() => {/* TODO: Help & Support */}}
            data-testid="help-btn"
          >
            <HelpCircle className="settings-menu-icon" />
            <span className="settings-menu-text">{t('helpSupport')}</span>
            <ChevronIcon className="settings-menu-arrow" />
          </button>

          <button 
            className="settings-menu-item logout"
            onClick={() => setShowConfirmPopup('logout')}
            data-testid="logout-btn"
          >
            <LogOut className="settings-menu-icon" />
            <span className="settings-menu-text">{t('logOut')}</span>
          </button>
        </div>

        {/* Delete Account */}
        <div className="delete-account-card">
          <button 
            className="settings-menu-item delete"
            onClick={() => setShowConfirmPopup('delete')}
            data-testid="delete-account-btn"
          >
            <Trash2 className="settings-menu-icon" />
            <span className="settings-menu-text">{t('deleteAccount')}</span>
          </button>
        </div>

        {/* Language Popup */}
        {showLanguagePopup && (
          <div className="popup-overlay" onClick={() => setShowLanguagePopup(false)}>
            <div 
              className="language-popup" 
              onClick={e => e.stopPropagation()}
              onTouchStart={handlePopupTouchStart}
              onTouchMove={handlePopupTouchMove}
              onTouchEnd={() => handlePopupTouchEnd(() => setShowLanguagePopup(false))}
              style={{ transform: `translateY(${popupDragY}px)` }}
            >
              <div className="popup-handle" />
              <h3 className="popup-title">{t('selectLanguage')}</h3>
              <div className="language-list">
                {LANGUAGES.map(lang => (
                  <button
                    key={lang.code}
                    className={`language-item ${selectedLanguage === lang.code ? 'selected' : ''}`}
                    onClick={() => handleLanguageSelect(lang.code)}
                  >
                    <span className="language-flag">{lang.flag}</span>
                    <span className="language-name">{lang.name}</span>
                    <div className={`language-radio ${selectedLanguage === lang.code ? 'selected' : ''}`}>
                      <div className="language-radio-inner" />
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Confirm Popup */}
        {showConfirmPopup && (
          <div className="popup-overlay" onClick={() => setShowConfirmPopup(null)}>
            <div 
              className="confirm-popup" 
              onClick={e => e.stopPropagation()}
              onTouchStart={handlePopupTouchStart}
              onTouchMove={handlePopupTouchMove}
              onTouchEnd={() => handlePopupTouchEnd(() => setShowConfirmPopup(null))}
              style={{ transform: `translateY(${popupDragY}px)` }}
            >
              <div className="popup-handle" />
              <h3 className="confirm-popup-title">{t('areYouSure')}</h3>
              <div className="confirm-popup-buttons">
                <button 
                  className="confirm-btn-back"
                  onClick={() => setShowConfirmPopup(null)}
                >
                  {t('noBack')}
                </button>
                <button 
                  className="confirm-btn-yes"
                  onClick={handleConfirmAction}
                >
                  {t('yes')}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  // ============ NOTIFICATIONS VIEW ============
  if (activeView === 'notifications') {
    return (
      <div className="profile-page-v2" data-testid="notifications-page">
        <div className="profile-v2-header">
          <button 
            className="profile-v2-back-btn"
            onClick={() => setActiveView('main')}
          >
            <ChevronLeft className="w-6 h-6" />
          </button>
          
          <h1 className="profile-v2-title">{t('notifications')}</h1>
          
          <div className="header-spacer" />
        </div>

        <div className="notifications-list">
          {notifications.length === 0 ? (
            <div className="notifications-empty">
              <Bell className="notifications-empty-icon" />
              <p>{t('noNotifications')}</p>
            </div>
          ) : (
            notifications.map((notif, index) => (
              <div key={index} className="notification-item">
                <div className="notification-dot" />
                <div className="notification-content">
                  <p className="notification-text">{notif.message}</p>
                  <span className="notification-time">{notif.time}</span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    );
  }

  // ============ PROFILE EDIT VIEW ============
  if (activeView === 'profile-edit') {
    return (
      <div className="profile-page-v2 edit-view" data-testid="profile-edit-page">
        <div className="profile-v2-header">
          <button 
            className="profile-v2-back-btn"
            onClick={() => setActiveView('main')}
            data-testid="profile-edit-back"
          >
            <ChevronLeft className="w-6 h-6" />
          </button>
          
          <h1 className="profile-v2-title">{t('profile')}</h1>
          
          <div className="header-spacer" />
        </div>

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

        <div className="profile-edit-form">
          <div className="profile-edit-field">
            <div className="profile-edit-input-vertical">
              <input
                type="text"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                className="profile-edit-input-top"
                placeholder="Name"
                data-testid="profile-name-input"
              />
              <div className="profile-input-divider-horizontal"></div>
              <input
                type="text"
                value={editUsername}
                onChange={(e) => {
                  setEditUsername(e.target.value);
                  setUsernameError('');
                }}
                onBlur={() => editUsername.length >= 3 && checkUsernameAvailability(editUsername)}
                className="profile-edit-input-bottom"
                placeholder="Username"
                data-testid="profile-username-input"
              />
            </div>
            {usernameError && (
              <p className="username-error">{usernameError}</p>
            )}
          </div>

          <button 
            className={`profile-save-btn ${(editUsername.trim() !== userName || editName.trim() !== (user?.name || '')) && !usernameError ? 'active' : ''}`}
            onClick={handleSaveProfile}
            disabled={isSaving || (editUsername.trim() === userName && editName.trim() === (user?.name || '')) || !!usernameError || isCheckingUsername}
            data-testid="profile-save-btn"
          >
            {isSaving ? t('saving') : isCheckingUsername ? t('checking') : t('save')}
          </button>
        </div>
      </div>
    );
  }

  return null;
};

export default ProfilePage;
