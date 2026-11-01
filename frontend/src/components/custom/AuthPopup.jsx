import { useState, useEffect } from "react";
import { BACKEND_URL } from "@/lib/backend";

// Google icon
const GoogleIcon = ({ className }) => (
  <svg viewBox="0 0 24 24" className={className}>
    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
  </svg>
);

export const AuthPopup = ({ isOpen, onClose, onSuccess }) => {
  const [isClosing, setIsClosing] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setIsClosing(false);
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  const handleClose = () => {
    setIsClosing(true);
    setTimeout(() => {
      onClose();
      setIsClosing(false);
    }, 300);
  };

  const handleGoogleLogin = () => {
    const next = encodeURIComponent(window.location.origin);
    window.location.href = `${BACKEND_URL}/api/auth/google?next=${next}`;
  };

  if (!isOpen && !isClosing) return null;

  return (
    <div className={`auth-popup-overlay ${isClosing ? "closing" : ""}`} onClick={handleClose}>
      <div 
        className={`auth-popup ${isClosing ? "closing" : ""}`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Drag indicator */}
        <div className="drag-indicator" />
        
        {/* Title */}
        <h2 className="auth-title">Sign in</h2>
        
        {/* Auth buttons */}
        <div className="auth-buttons">
          <button 
            className="auth-btn google primary"
            onClick={handleGoogleLogin}
            data-testid="google-login-btn"
          >
            <GoogleIcon className="w-5 h-5" />
            <span>Continue with Google</span>
          </button>
        </div>

        <p className="auth-service-name">nind</p>
      </div>
    </div>
  );
};

export default AuthPopup;
