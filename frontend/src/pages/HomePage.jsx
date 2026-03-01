import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Sparkles, ChevronDown, Wand2, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { FormatSelector } from "@/components/custom/FormatSelector";
import { toast } from "sonner";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const HomePage = () => {
  const navigate = useNavigate();
  const [prompt, setPrompt] = useState("");
  const [selectedFormat, setSelectedFormat] = useState(null);
  const [isFormatSelectorOpen, setIsFormatSelectorOpen] = useState(false);
  const [formats, setFormats] = useState([]);
  const [categories, setCategories] = useState({});
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    fetchFormats();
  }, []);

  const fetchFormats = async () => {
    try {
      const response = await axios.get(`${API}/formats`);
      setFormats(response.data.formats);
      setCategories(response.data.categories);
      // Set default format
      if (response.data.formats.length > 0) {
        setSelectedFormat(response.data.formats[0]);
      }
    } catch (error) {
      console.error("Failed to fetch formats:", error);
      toast.error("Не удалось загрузить форматы");
    }
  };

  const handleGenerate = useCallback(async () => {
    if (!prompt.trim()) {
      toast.error("Введите описание видео");
      return;
    }
    if (!selectedFormat) {
      toast.error("Выберите формат видео");
      return;
    }

    setIsLoading(true);
    try {
      const response = await axios.post(`${API}/video/generate`, {
        prompt: prompt.trim(),
        format_id: selectedFormat.id,
        language: "auto"
      });
      
      toast.success("Генерация началась!");
      navigate(`/video/${response.data.id}`);
    } catch (error) {
      console.error("Failed to start generation:", error);
      toast.error("Ошибка при запуске генерации");
    } finally {
      setIsLoading(false);
    }
  }, [prompt, selectedFormat, navigate]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleGenerate();
    }
  };

  return (
    <div className="min-h-screen flex flex-col" data-testid="home-page">
      {/* Background gradient */}
      <div className="fixed inset-0 hero-gradient pointer-events-none" />
      
      {/* Noise overlay */}
      <div className="noise-overlay" />

      {/* Header */}
      <header className="relative z-10 p-4 md:p-6">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-primary/20">
            <Zap className="w-6 h-6 text-primary" />
          </div>
          <h1 className="text-xl md:text-2xl font-bold font-['Chivo'] tracking-tight">
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-primary to-accent">
              VidFlux
            </span>
            <span className="text-white/80"> AI</span>
          </h1>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex flex-col items-center justify-center px-4 md:px-8 pb-8">
        {/* Hero Section */}
        <div className="text-center mb-8 md:mb-12 max-w-3xl mx-auto">
          <h2 className="text-4xl sm:text-5xl lg:text-6xl font-black font-['Chivo'] tracking-tight leading-none mb-4">
            Создавайте{" "}
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-primary to-accent">
              вирусные видео
            </span>
            <br />
            за секунды
          </h2>
          <p className="text-base md:text-lg text-muted-foreground max-w-xl mx-auto">
            AI генерирует контент, изображения и озвучку по вашему промту
          </p>
        </div>

        {/* Input Section */}
        <div className="w-full max-w-2xl mx-auto space-y-4">
          {/* Main Input */}
          <div className="relative input-glow rounded-2xl transition-shadow duration-300">
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Опишите ваше видео... Например: Топ-5 самых дорогих машин 2024 года"
              className="w-full bg-black/50 border-2 border-white/10 focus:border-primary/50 text-lg md:text-xl p-5 md:p-6 pr-32 rounded-2xl resize-none h-32 md:h-36 placeholder:text-muted-foreground/50 focus:outline-none transition-colors"
              data-testid="prompt-input"
            />
            
            {/* Format selector button inside input */}
            <button
              onClick={() => setIsFormatSelectorOpen(true)}
              className="absolute right-3 bottom-3 flex items-center gap-2 px-3 py-2 rounded-xl bg-secondary/80 hover:bg-secondary border border-white/10 transition-colors text-sm font-medium"
              data-testid="format-selector-button"
            >
              {selectedFormat ? (
                <>
                  <span className="text-primary">{selectedFormat.name_ru}</span>
                  <ChevronDown className="w-4 h-4 text-muted-foreground" />
                </>
              ) : (
                <>
                  <span>Формат</span>
                  <ChevronDown className="w-4 h-4" />
                </>
              )}
            </button>
          </div>

          {/* Generate Button */}
          <Button
            onClick={handleGenerate}
            disabled={isLoading || !prompt.trim()}
            className="w-full bg-primary text-primary-foreground hover:bg-primary/90 shadow-[0_0_30px_-5px_var(--primary)] hover:shadow-[0_0_40px_-5px_var(--primary)] transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] font-bold uppercase tracking-wider text-sm py-6 rounded-full"
            data-testid="generate-button"
          >
            {isLoading ? (
              <>
                <Wand2 className="w-5 h-5 mr-2 animate-spin" />
                Генерация...
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5 mr-2" />
                Создать видео
              </>
            )}
          </Button>

          {/* Quick hints */}
          <div className="flex flex-wrap justify-center gap-2 pt-4">
            {["Новости технологий", "Топ-5 фактов", "Обзор продукта", "Интересная история"].map((hint) => (
              <button
                key={hint}
                onClick={() => setPrompt(hint)}
                className="px-3 py-1.5 rounded-full text-xs font-medium bg-secondary/50 hover:bg-secondary border border-white/5 hover:border-white/20 transition-colors text-muted-foreground hover:text-foreground"
                data-testid={`hint-${hint}`}
              >
                {hint}
              </button>
            ))}
          </div>
        </div>
      </main>

      {/* Format Selector Modal */}
      <FormatSelector
        formats={formats}
        categories={categories}
        isOpen={isFormatSelectorOpen}
        onClose={() => setIsFormatSelectorOpen(false)}
        onSelect={setSelectedFormat}
        selectedFormat={selectedFormat}
      />
    </div>
  );
};

export default HomePage;
