import { useState, useCallback } from "react";
import { Search, X, Newspaper, BookOpen, HelpCircle, Smile, GraduationCap, ShoppingBag, Gamepad2, Sparkles, Cat } from "lucide-react";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

const ICON_MAP = {
  Newspaper: Newspaper,
  BookOpen: BookOpen,
  HelpCircle: HelpCircle,
  Smile: Smile,
  GraduationCap: GraduationCap,
  ShoppingBag: ShoppingBag,
  Gamepad2: Gamepad2,
  Sparkles: Sparkles,
  Cat: Cat,
};

export const FormatSelector = ({ formats, categories, isOpen, onClose, onSelect, selectedFormat }) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [activeCategory, setActiveCategory] = useState("all");

  const filteredFormats = formats.filter((format) => {
    const matchesSearch = 
      format.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      format.name_ru.toLowerCase().includes(searchQuery.toLowerCase()) ||
      format.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      format.description_ru.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesCategory = activeCategory === "all" || format.category === activeCategory;
    
    return matchesSearch && matchesCategory;
  });

  const handleSelect = useCallback((format) => {
    onSelect(format);
    onClose();
  }, [onSelect, onClose]);

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 z-50 flex flex-col"
      data-testid="format-selector-modal"
    >
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/90 backdrop-blur-2xl"
        onClick={onClose}
      />
      
      {/* Content */}
      <div className="relative z-10 flex flex-col h-full max-h-[95vh] mt-auto mx-4 mb-4 md:mx-8 md:mb-8 animate-fade-in-up">
        {/* Header */}
        <div className="flex items-center justify-between p-4 md:p-6 glass rounded-t-3xl">
          <h2 className="text-2xl md:text-3xl font-bold font-['Chivo']">
            Выберите формат
          </h2>
          <button
            onClick={onClose}
            className="p-2 rounded-full hover:bg-white/10 transition-colors"
            data-testid="close-format-selector"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Search */}
        <div className="p-4 md:px-6 glass-card border-t-0 rounded-none">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Поиск форматов..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-12 bg-black/50 border-white/10 h-12 text-base"
              data-testid="format-search-input"
            />
          </div>
        </div>

        {/* Category Tabs */}
        <div className="flex gap-2 p-4 md:px-6 glass-card border-t-0 rounded-none overflow-x-auto">
          {Object.entries(categories).map(([key, cat]) => (
            <button
              key={key}
              onClick={() => setActiveCategory(key)}
              className={cn(
                "px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all duration-200",
                activeCategory === key
                  ? "bg-primary text-primary-foreground"
                  : "bg-secondary/50 text-secondary-foreground hover:bg-secondary"
              )}
              data-testid={`category-tab-${key}`}
            >
              {cat.name}
            </button>
          ))}
        </div>

        {/* Format Grid */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6 glass-card border-t-0 rounded-b-3xl">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 md:gap-6">
            {filteredFormats.map((format, index) => {
              const IconComponent = ICON_MAP[format.icon] || Newspaper;
              const isSelected = selectedFormat?.id === format.id;
              
              return (
                <button
                  key={format.id}
                  onClick={() => handleSelect(format)}
                  className={cn(
                    "group relative overflow-hidden rounded-3xl border transition-all duration-300 cursor-pointer h-48 md:h-64 flex flex-col justify-end text-left",
                    `stagger-${(index % 6) + 1} animate-fade-in-up opacity-0`,
                    isSelected
                      ? "border-primary glow-primary"
                      : "border-white/10 hover:border-primary/50 hover:scale-[1.02]"
                  )}
                  style={{ animationFillMode: 'forwards' }}
                  data-testid={`format-card-${format.id}`}
                >
                  {/* Background Image */}
                  <div 
                    className="absolute inset-0 bg-cover bg-center transition-transform duration-500 group-hover:scale-110"
                    style={{ backgroundImage: `url(${format.image_url})` }}
                  />
                  
                  {/* Overlay */}
                  <div className="absolute inset-0 format-card-overlay" />
                  
                  {/* Content */}
                  <div className="relative z-10 p-4 md:p-6">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="p-2 rounded-xl bg-primary/20 backdrop-blur-sm">
                        <IconComponent className="w-4 h-4 md:w-5 md:h-5 text-primary" />
                      </div>
                      {isSelected && (
                        <span className="px-2 py-1 text-xs bg-primary rounded-full">
                          Выбрано
                        </span>
                      )}
                    </div>
                    <h3 className="text-lg md:text-xl font-bold text-white mb-1">
                      {format.name_ru}
                    </h3>
                    <p className="text-xs md:text-sm text-gray-300 line-clamp-2">
                      {format.description_ru}
                    </p>
                  </div>
                </button>
              );
            })}
          </div>
          
          {filteredFormats.length === 0 && (
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
              <Search className="w-12 h-12 mb-4 opacity-50" />
              <p className="text-lg">Форматы не найдены</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default FormatSelector;
