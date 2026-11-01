import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import axios from "axios";
import Logo from "@/components/custom/Logo";
import { API, BACKEND_URL } from "@/lib/backend";
import { saveUser } from "@/lib/session";

const GoogleIcon = () => (
  <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
  </svg>
);

const AuthPage = () => {
  const navigate = useNavigate();
  const [intent, setIntent] = useState("login");
  const [step, setStep] = useState("email");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const emailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());

  const continueWithGoogle = () => {
    const next = encodeURIComponent(window.location.origin);
    window.location.href = `${BACKEND_URL}/api/auth/google?next=${next}`;
  };

  const continueFromEmail = (event) => {
    event.preventDefault();
    if (!emailValid) {
      toast.error("Enter a valid email");
      return;
    }
    setStep("password");
  };

  const submitPassword = async (event) => {
    event.preventDefault();
    if (password.length < 8) {
      toast.error("Password must be at least 8 characters");
      return;
    }
    setIsLoading(true);
    try {
      const path = intent === "login" ? "login" : "register";
      const response = await axios.post(`${API}/auth/${path}`, {
        email: email.trim(),
        password,
      });
      saveUser(response.data);
      toast.success(intent === "login" ? "Welcome back" : "Account created");
      navigate("/");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Could not continue");
    } finally {
      setIsLoading(false);
    }
  };

  const switchIntent = () => {
    setIntent((current) => (current === "login" ? "signup" : "login"));
    setStep("email");
    setPassword("");
  };

  return (
    <div className="nind-auth" data-testid="auth-page">
      <div className="nind-auth-card">
        <Logo className="nind-auth-logo" />
        <h1 className="nind-auth-title" data-testid="auth-title">
          {intent === "login" ? "Welcome back" : "Create an account"}
        </h1>

        {step === "email" ? (
          <form className="nind-auth-form" onSubmit={continueFromEmail}>
            <input
              type="email"
              className="nind-auth-input"
              placeholder="Email address"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              autoComplete="email"
              autoFocus
              data-testid="email-input"
            />
            <button type="submit" className="nind-auth-primary" data-testid="submit-btn">
              Continue
            </button>
          </form>
        ) : (
          <form className="nind-auth-form" onSubmit={submitPassword}>
            <button
              type="button"
              className="nind-auth-back"
              onClick={() => setStep("email")}
              data-testid="auth-back-btn"
            >
              {email}
            </button>
            <input
              type={intent === "signup" ? "password" : "password"}
              className="nind-auth-input"
              placeholder="Password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete={intent === "signup" ? "new-password" : "current-password"}
              autoFocus
              data-testid="password-input"
            />
            <button
              type="submit"
              className="nind-auth-primary"
              disabled={isLoading}
              data-testid="submit-btn"
            >
              {isLoading ? "Please wait…" : "Continue"}
            </button>
          </form>
        )}

        <div className="nind-auth-or" aria-hidden="true"><span>OR</span></div>

        <button
          type="button"
          className="nind-auth-google"
          onClick={continueWithGoogle}
          data-testid="google-login-btn"
        >
          <GoogleIcon />
          Continue with Google
        </button>

        <button type="button" className="nind-auth-switch" onClick={switchIntent} data-testid="switch-intent">
          {intent === "login" ? "Need an account? Sign up" : "Already have an account? Log in"}
        </button>
      </div>

      <p className="nind-auth-legal">
        By continuing you agree to the Terms and the Privacy Policy.
      </p>
    </div>
  );
};

export default AuthPage;
