import "@/index.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import MainPage from "@/pages/MainPage";
import CreatePage from "@/pages/CreatePage";
import VideoPage from "@/pages/VideoPage";
import AuthCallback from "@/components/custom/AuthCallback";

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<MainPage />} />
          <Route path="/auth/callback" element={<AuthCallback />} />
          <Route path="/create" element={<CreatePage />} />
          <Route path="/video/:id" element={<VideoPage />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-center" richColors />
    </div>
  );
}

export default App;
