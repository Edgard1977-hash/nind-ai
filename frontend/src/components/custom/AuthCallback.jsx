import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export const AuthCallback = () => {
  const navigate = useNavigate();
  const hasProcessed = useRef(false);

  useEffect(() => {
    // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    
    // Prevent double processing in StrictMode
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const processAuth = async () => {
      // Extract session_id from URL fragment
      const hash = window.location.hash;
      const params = new URLSearchParams(hash.replace("#", ""));
      const sessionId = params.get("session_id");

      if (!sessionId) {
        navigate("/", { replace: true });
        return;
      }

      try {
        // Exchange session_id for session_token
        const response = await fetch(`${BACKEND_URL}/api/auth/session`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          credentials: "include",
          body: JSON.stringify({ session_id: sessionId }),
        });

        if (!response.ok) {
          throw new Error("Auth failed");
        }

        const userData = await response.json();

        // Store user data
        localStorage.setItem("slind_user", JSON.stringify(userData));

        // Redirect to main page with user data
        navigate("/", { 
          replace: true,
          state: { user: userData }
        });
      } catch (error) {
        console.error("Auth callback error:", error);
        navigate("/", { replace: true });
      }
    };

    processAuth();
  }, [navigate]);

  return (
    <div className="auth-callback" style={{
      minHeight: "100vh",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      background: "#0C0C0E"
    }}>
      <div className="loading-spinner" style={{
        width: 40,
        height: 40,
        border: "3px solid rgba(255,255,255,0.1)",
        borderTopColor: "#00DDFF",
        borderRadius: "50%",
        animation: "spin 1s linear infinite"
      }} />
    </div>
  );
};

export default AuthCallback;
