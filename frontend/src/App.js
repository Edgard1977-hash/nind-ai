import "@/index.css";
import { useEffect } from "react";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { Toaster, toast } from "@/components/ui/sonner";
import MainPage from "@/pages/MainPage";
import CreatePage from "@/pages/CreatePage";
import VideoPage from "@/pages/VideoPage";
import FormatsPage from "@/pages/FormatsPage";
import AuthPage from "@/pages/AuthPage";
import AuthCallback from "@/components/custom/AuthCallback";
import UpgradePage from "@/pages/UpgradePage";
import VoiceAssistantPage from "@/pages/VoiceAssistantPage";
import { initThemeFromStorage } from "@/components/custom/AppearancePopup";

// Initialize theme from localStorage before any render
initThemeFromStorage();

// Check for session_id in URL before rendering normal routes
function AppRouter() {
  const location = useLocation();
  
  // CRITICAL: Check URL fragment for session_id synchronously during render
  // This prevents race conditions with auth state
  if (location.hash?.includes('session_id=')) {
    return <AuthCallback />;
  }
  
  return (
    <Routes>
      <Route path="/" element={<MainPage />} />
      <Route path="/auth" element={<AuthPage />} />
      <Route path="/auth/callback" element={<AuthCallback />} />
      <Route path="/create" element={<CreatePage />} />
      <Route path="/video/:id" element={<VideoPage />} />
      <Route path="/formats" element={<FormatsPage />} />
      <Route path="/upgrade" element={<UpgradePage />} />
      <Route path="/voice" element={<VoiceAssistantPage />} />
    </Routes>
  );
}

// Manual swipe-to-dismiss for sonner toasts (works on mouse + touch)
function useToastSwipeToDismiss() {
  useEffect(() => {
    const TRIGGER = 60; // px to consider as a swipe
    const dragState = new WeakMap();

    const onDown = (e) => {
      const toastEl = e.target.closest('[data-sonner-toast]');
      if (!toastEl) return;
      const id = toastEl.getAttribute('data-id') || toastEl.dataset.id;
      dragState.set(toastEl, {
        id,
        startX: e.clientX,
        startY: e.clientY,
        active: true,
      });
      toastEl.style.transition = 'none';
      toastEl.setPointerCapture && toastEl.setPointerCapture(e.pointerId);
    };

    const onMove = (e) => {
      const toastEl = e.target.closest('[data-sonner-toast]');
      if (!toastEl) return;
      const s = dragState.get(toastEl);
      if (!s || !s.active) return;
      const dx = e.clientX - s.startX;
      const dy = e.clientY - s.startY;
      // Only allow up / left / right (not down)
      const ay = Math.min(0, dy);
      toastEl.style.transform = `translate(${dx}px, ${ay}px)`;
      const dist = Math.max(Math.abs(dx), Math.abs(ay));
      toastEl.style.opacity = String(Math.max(0.2, 1 - dist / 200));
    };

    const onUp = (e) => {
      const toastEl = e.target.closest('[data-sonner-toast]');
      if (!toastEl) return;
      const s = dragState.get(toastEl);
      if (!s || !s.active) return;
      s.active = false;
      const dx = e.clientX - s.startX;
      const dy = e.clientY - s.startY;
      const swipedUp = -dy > TRIGGER;
      const swipedSide = Math.abs(dx) > TRIGGER;
      toastEl.style.transition = 'transform 0.22s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.22s ease';
      if (swipedUp || swipedSide) {
        // Animate UP and OUT (consistent feel even when swiping sideways)
        const outX = swipedSide ? Math.sign(dx) * 600 : 0;
        const outY = swipedUp ? -260 : -120;
        toastEl.style.transform = `translate(${outX}px, ${outY}px)`;
        toastEl.style.opacity = '0';
        if (s.id) {
          setTimeout(() => toast.dismiss(s.id), 200);
        } else {
          setTimeout(() => toast.dismiss(), 200);
        }
      } else {
        toastEl.style.transform = '';
        toastEl.style.opacity = '';
      }
    };

    document.addEventListener('pointerdown', onDown);
    document.addEventListener('pointermove', onMove);
    document.addEventListener('pointerup', onUp);
    document.addEventListener('pointercancel', onUp);
    return () => {
      document.removeEventListener('pointerdown', onDown);
      document.removeEventListener('pointermove', onMove);
      document.removeEventListener('pointerup', onUp);
      document.removeEventListener('pointercancel', onUp);
    };
  }, []);
}

function App() {
  useToastSwipeToDismiss();
  return (
    <div className="App">
      <BrowserRouter>
        <AppRouter />
      </BrowserRouter>
      <Toaster 
        position="top-center" 
        duration={3000}
        toastOptions={{
          style: {
            background: '#FFFFFF',
            border: 'none',
            borderRadius: '24px',
            color: '#000',
          },
        }}
      />
    </div>
  );
}

export default App;
