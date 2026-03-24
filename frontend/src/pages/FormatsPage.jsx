import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Search } from "lucide-react";

const FORMATS = [
  { id: 1, name: "Format", color: "#3A3A3A" },
  { id: 2, name: "Format", color: "#3A3A3A" },
  { id: 3, name: "Format", color: "#3A3A3A" },
  { id: 4, name: "Format", color: "#3A3A3A" },
  { id: 5, name: "Format", color: "#3A3A3A" },
  { id: 6, name: "Format", color: "#3A3A3A" },
  { id: 7, name: "Format", color: "#3A3A3A" },
  { id: 8, name: "Format", color: "#3A3A3A" },
  { id: 9, name: "Format", color: "#3A3A3A" },
  { id: 10, name: "Format", color: "#3A3A3A" },
  { id: 11, name: "Format", color: "#3A3A3A" },
  { id: 12, name: "Format", color: "#3A3A3A" },
];

const TABS = ["Все", "Популярные", "Новые", "Тренды"];

const FormatsPage = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("Все");
  const [searchQuery, setSearchQuery] = useState("");

  return (
    <div className="formats-page">
      {/* Header */}
      <header className="formats-page-header">
        <button 
          className="back-button"
          onClick={() => navigate(-1)}
          data-testid="back-button"
        >
          <ArrowLeft className="w-6 h-6" />
        </button>
        <h1 className="formats-page-title">Formats</h1>
        <div className="header-spacer" />
      </header>

      {/* Search */}
      <div className="formats-search-container">
        <div className="formats-search">
          <Search className="w-5 h-5 search-icon" />
          <input
            type="text"
            placeholder="Search formats..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="formats-search-input"
            data-testid="formats-search-input"
          />
        </div>
      </div>

      {/* Tabs */}
      <div className="formats-tabs-container">
        <div className="formats-tabs">
          {TABS.map((tab) => (
            <button
              key={tab}
              className={`format-tab ${activeTab === tab ? 'active' : ''}`}
              onClick={() => setActiveTab(tab)}
              data-testid={`tab-${tab}`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Formats Grid */}
      <div className="formats-page-content">
        <div className="formats-page-grid">
          {FORMATS.filter(f => 
            f.name.toLowerCase().includes(searchQuery.toLowerCase())
          ).map((format) => (
            <div 
              key={format.id} 
              className="format-card-page"
              onClick={() => navigate('/')}
              data-testid={`format-${format.id}`}
            >
              <div 
                className="format-preview-page"
                style={{ backgroundColor: format.color }}
              />
              <span className="format-name-page">{format.name}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default FormatsPage;
