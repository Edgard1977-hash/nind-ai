import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Eye, EyeOff } from "lucide-react";
import { toast } from "sonner";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const FRONTEND_URL = window.location.origin;
const API = `${BACKEND_URL}/api`;

// Logo URL
const LOGO_URL = "https://customer-assets.emergentagent.com/job_ai-format-studio/artifacts/x0akmc4x_A7746620-B806-4A1B-B685-CC4290123288.png";

// Google icon
const GoogleIcon = ({ className }) => (
  <svg viewBox="0 0 24 24" className={className}>
    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
  </svg>
);

// Email icon (white version of uploaded icon)
const EmailIcon = ({ className }) => (
  <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
    <path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 2l-8 5-8-5h16zm0 12H4V8l8 5 8-5v10z"/>
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

  return (
    <div className="auth-page" data-testid="auth-page">
      {/* Logo - only on initial view */}
      {view === 'initial' && (
        <div className="auth-logo-container">
          <img src={LOGO_URL} alt="Slind" className="auth-logo" />
        </div>
      )}

      {/* Content */}
      <div className={`auth-page-content ${view !== 'initial' ? 'no-logo' : ''}`}>
        {/* Title for initial view */}
        {view === 'initial' && (
          <div className="auth-header-text">
            <h1 className="auth-page-title">Get started</h1>
            <p className="auth-page-subtitle">Log in or Sign up</p>
          </div>
        )}
        
        {/* Title for login/signup */}
        {view !== 'initial' && (
          <h1 className="auth-page-title" data-testid="auth-title">
            {view === 'login' ? 'Log in' : 'Sign up'}
          </h1>
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
              <EmailIcon className="w-5 h-5" />
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

            {view === 'login' && (
              <div className="auth-forgot-row">
                <button 
                  type="button"
                  className="auth-link"
                  onClick={() => toast.info("Функция восстановления пароля скоро будет доступна")}
                  data-testid="forgot-password-btn"
                >
                  Lost password?
                </button>
              </div>
            )}

            <button
              type="submit"
              className={`auth-submit-btn ${isFormValid ? 'active' : ''}`}
              disabled={!isFormValid || isLoading}
              data-testid="submit-btn"
            >
              {isLoading ? 'Loading...' : (view === 'login' ? 'Log in' : 'Sign up')}
            </button>
          </form>
        )}
      </div>

      {/* Footer */}
      {(view === 'login' || view === 'signup') && (
        <div className="auth-page-footer">
          {view === 'login' ? (
            <p className="auth-switch-text">
              No account?{' '}
              <button 
                className="auth-link"
                onClick={switchToSignup}
                data-testid="switch-to-signup"
              >
                Sign up
              </button>
            </p>
          ) : (
            <p className="auth-switch-text">
              Have account?{' '}
              <button 
                className="auth-link"
                onClick={switchToLogin}
                data-testid="switch-to-login"
              >
                Log in
              </button>
            </p>
          )}
        </div>
      )}
    </div>
  );
};

export default AuthPage;
