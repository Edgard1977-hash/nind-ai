import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { API } from "@/lib/backend";
import { saveUser } from "@/lib/session";

export const AuthCallback = () => {
  const navigate = useNavigate();
  const hasProcessed = useRef(false);

  useEffect(() => {
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const hash = new URLSearchParams(window.location.hash.replace(/^#/, ""));
    const query = new URLSearchParams(window.location.search);
    const token = query.get("token") || hash.get("token");

    if (!token) {
      navigate("/auth", { replace: true });
      return;
    }

    const finish = async () => {
      try {
        const response = await fetch(`${API}/auth/me`, {
          headers: { Authorization: `Bearer ${token}` },
          credentials: "include",
        });
        if (!response.ok) throw new Error("Auth failed");
        const user = await response.json();
        user.token = token;
        saveUser(user);
        navigate("/", { replace: true, state: { user } });
      } catch (error) {
        console.error("Auth callback error:", error);
        navigate("/auth", { replace: true });
      }
    };

    finish();
  }, [navigate]);

  return (
    <div className="nind-auth">
      <p className="nind-auth-muted">Signing you in…</p>
    </div>
  );
};

export default AuthCallback;
