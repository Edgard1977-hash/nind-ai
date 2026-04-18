import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ChevronLeft, Eye, EyeOff } from "lucide-react";
import { toast } from "sonner";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const FRONTEND_URL = window.location.origin;
const API = `${BACKEND_URL}/api`;

// Google icon
const GoogleIcon = ({ className }) => (
  <svg viewBox="0 0 24 24" className={className}>
    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
  </svg>
);

// Email envelope icon (from user's uploaded image, white version)
const EnvelopeIcon = ({ className }) => (
  <svg viewBox="0 0 512 512" fill="currentColor" className={className}>
    <path d="M48 128C48 100.5 70.5 78 98 78H414C441.5 78 464 100.5 464 128V130.2L256 263.5L48 130.2V128ZM48 178.3V384C48 411.5 70.5 434 98 434H414C441.5 434 464 411.5 464 384V178.3L275.6 299.8C264.5 307.1 249.5 307.1 238.4 299.8L48 178.3Z"/>
  </svg>
);

const AuthPage = () => {
  const navigate = useNavigate();
  
  // Views: 'initial', 'login', 'signup'
  const [view, setView] = useState('initial');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const isFormValid = email.trim() !== '' && password.trim() !== '';

  const handleGoogleLogin = () => {
    const redirectUri = `${FRONTEND_URL}/auth/callback`;
    const authUrl = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUri)}`;
    window.location.href = authUrl;
  };

  const handleEmailLogin = async () => {
    if (!isFormValid) return;
    
    setIsLoading(true);
    try {
      const response = await axios.post(`${API}/auth/login`, {
        email: email.trim(),
        password: password
      });
      
      const userData = response.data;
      localStorage.setItem("slind_user", JSON.stringify(userData));
      toast.success("Вход выполнен!");
      navigate('/');
    } catch (error) {
      console.error("Login error:", error);
      toast.error(error.response?.data?.detail || "Ошибка входа");
    } finally {
      setIsLoading(false);
    }
  };

  const handleEmailSignup = async () => {
    if (!isFormValid) return;
    
    setIsLoading(true);
    try {
      const response = await axios.post(`${API}/auth/register`, {
        email: email.trim(),
        password: password
      });
      
      const userData = response.data;
      localStorage.setItem("slind_user", JSON.stringify(userData));
      toast.success("Регистрация успешна!");
      navigate('/');
    } catch (error) {
      console.error("Signup error:", error);
      toast.error(error.response?.data?.detail || "Ошибка регистрации");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (view === 'login') {
      handleEmailLogin();
    } else if (view === 'signup') {
      handleEmailSignup();
    }
  };

  const resetForm = () => {
    setEmail('');
    setPassword('');
  };

  const switchToLogin = () => {
    resetForm();
    setView('login');
  };

  const switchToSignup = () => {
    resetForm();
    setView('signup');
  };

  const goBack = () => {
    setView('initial');
    resetForm();
  };

  return (
    <div className="auth-page" data-testid="auth-page">
      {/* Back button for login/signup forms */}
      {view !== 'initial' && (
        <button 
          className="auth-back-btn"
          onClick={goBack}
          data-testid="auth-back-btn"
        >
          <ChevronLeft className="w-7 h-7" />
        </button>
      )}

      {/* Content */}
      <div className={`auth-page-content ${view !== 'initial' ? 'form-view' : ''}`}>
        {/* Title for initial view */}
        {view === 'initial' && (
          <div className="auth-header-text">
            <h1 className="auth-page-title-large">Get started</h1>
            <p className="auth-page-subtitle">Log in or Sign up</p>
          </div>
        )}
        
        {/* Title for login/signup */}
        {view !== 'initial' && (
          <div className="auth-form-header">
            <h1 className="auth-page-title" data-testid="auth-title">
              {view === 'login' ? 'Log in' : 'Sign up'}
            </h1>
            <p className="auth-page-subtitle-form">
              {view === 'login' ? 'to nind ai' : 'create an account'}
            </p>
          </div>
        )}

        {/* Initial view - social buttons */}
        {view === 'initial' && (
          <div className="auth-buttons-container">
            <button 
              className="auth-social-btn google"
              onClick={handleGoogleLogin}
              data-testid="google-login-btn"
            >
              <GoogleIcon className="w-5 h-5" />
              <span>Continue with Google</span>
            </button>

            <button 
              className="auth-social-btn email"
              onClick={() => setView('login')}
              data-testid="email-login-btn"
            >
              <EnvelopeIcon className="w-5 h-5" />
              <span>Continue with Email</span>
            </button>
          </div>
        )}

        {/* Login/Signup form */}
        {(view === 'login' || view === 'signup') && (
          <form className="auth-form" onSubmit={handleSubmit}>
            <div className="auth-input-group">
              <input
                type="email"
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="auth-input"
                data-testid="email-input"
                autoComplete="email"
              />
            </div>

            <div className="auth-input-group">
              <input
                type={showPassword ? "text" : "password"}
                placeholder={view === 'signup' ? "Create password" : "Password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="auth-input"
                data-testid="password-input"
                autoComplete={view === 'signup' ? "new-password" : "current-password"}
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword(!showPassword)}
                data-testid="password-toggle"
              >
                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>

            <button
              type="submit"
              className={`auth-submit-btn ${isFormValid ? 'active' : ''}`}
              disabled={!isFormValid || isLoading}
              data-testid="submit-btn"
            >
              {isLoading ? 'Loading...' : (view === 'login' ? 'Log in' : 'Sign up')}
            </button>

            {/* Footer under button - Lost password on left, Sign up/Log in on right */}
            <div className="auth-form-footer">
              {view === 'login' ? (
                <>
                  <button 
                    type="button"
                    className="auth-link auth-link-gray"
                    onClick={() => toast.info("Функция восстановления пароля скоро будет доступна")}
                    data-testid="forgot-password-btn"
                  >
                    Lost password?
                  </button>
                  <p className="auth-switch-text">
                    No account?{' '}
                    <button 
                      type="button"
                      className="auth-link auth-link-white"
                      onClick={switchToSignup}
                      data-testid="switch-to-signup"
                    >
                      Sign up
                    </button>
                  </p>
                </>
              ) : (
                <>
                  <div></div>
                  <p className="auth-switch-text">
                    Have account?{' '}
                    <button 
                      type="button"
                      className="auth-link auth-link-white"
                      onClick={switchToLogin}
                      data-testid="switch-to-login"
                    >
                      Log in
                    </button>
                  </p>
                </>
              )}
            </div>
          </form>
        )}
      </div>

      {/* Gradient overlay for initial view */}
      {view === 'initial' && (
        <div className="auth-gradient-overlay"></div>
      )}

      {/* Grid background for initial view */}
      {view === 'initial' && (
        <div className="auth-grid">
          <svg viewBox="0 0 400 200" preserveAspectRatio="none" className="auth-grid-svg">
            <line x1="0" y1="0" x2="0" y2="200" stroke="rgba(255,255,255,0.04)" strokeWidth="1"/>
            <line x1="80" y1="0" x2="80" y2="200" stroke="rgba(255,255,255,0.04)" strokeWidth="1"/>
            <line x1="160" y1="0" x2="160" y2="200" stroke="rgba(255,255,255,0.04)" strokeWidth="1"/>
            <line x1="240" y1="0" x2="240" y2="200" stroke="rgba(255,255,255,0.04)" strokeWidth="1"/>
            <line x1="320" y1="0" x2="320" y2="200" stroke="rgba(255,255,255,0.04)" strokeWidth="1"/>
            <line x1="400" y1="0" x2="400" y2="200" stroke="rgba(255,255,255,0.04)" strokeWidth="1"/>
            <path d="M0,0 Q200,0 400,0" stroke="rgba(255,255,255,0.03)" strokeWidth="1" fill="none"/>
            <path d="M0,50 Q200,40 400,50" stroke="rgba(255,255,255,0.04)" strokeWidth="1" fill="none"/>
            <path d="M0,100 Q200,80 400,100" stroke="rgba(255,255,255,0.04)" strokeWidth="1" fill="none"/>
            <path d="M0,150 Q200,120 400,150" stroke="rgba(255,255,255,0.05)" strokeWidth="1" fill="none"/>
            <path d="M0,200 Q200,160 400,200" stroke="rgba(255,255,255,0.05)" strokeWidth="1" fill="none"/>
          </svg>
        </div>
      )}

      {/* Privacy Policy text at bottom */}
      <p className="auth-privacy-text">
        By continuing, I acknowledge the{' '}
        <a href="#" className="auth-privacy-link">Privacy Policy</a>
        {' '}and agree to the{' '}
        <a href="#" className="auth-privacy-link">Terms of Use</a>
        . I also confirm that I am at least 18 years old
      </p>
    </div>
  );
};

export default AuthPage;
