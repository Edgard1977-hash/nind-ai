import "@/index.css";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import MainPage from "@/pages/MainPage";
import CreatePage from "@/pages/CreatePage";
import VideoPage from "@/pages/VideoPage";
import FormatsPage from "@/pages/FormatsPage";
import AuthPage from "@/pages/AuthPage";
import AuthCallback from "@/components/custom/AuthCallback";
import UpgradePage from "@/pages/UpgradePage";

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
    </Routes>
  );
}

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <AppRouter />
      </BrowserRouter>
      <Toaster position="top-center" richColors />
    </div>
  );
}

export default App;
