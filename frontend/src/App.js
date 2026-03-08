import "@/index.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import HomePage from "@/pages/HomePage";
import CreatePage from "@/pages/CreatePage";
import VideoPage from "@/pages/VideoPage";
import PricingPage from "@/pages/PricingPage";
import SubscriptionSuccessPage from "@/pages/SubscriptionSuccessPage";
import MontagePage from "@/pages/MontagePage";

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/create" element={<CreatePage />} />
          <Route path="/video/:id" element={<VideoPage />} />
          <Route path="/pricing" element={<PricingPage />} />
          <Route path="/subscription/success" element={<SubscriptionSuccessPage />} />
          <Route path="/montage" element={<MontagePage />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-center" richColors />
    </div>
  );
}

export default App;
