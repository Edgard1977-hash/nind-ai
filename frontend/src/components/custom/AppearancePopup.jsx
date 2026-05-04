import { useState, useEffect } from "react";

// Appearance popup: System / Light / Dark theme picker
const SunIcon = () => (
  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="4" />
    <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" />
  </svg>
);

const MoonIcon = () => (
  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
  </svg>
);

const SystemIcon = () => (
  // Half-white sphere icon
  <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
    <circle cx="16" cy="16" r="11" stroke="currentColor" strokeWidth="2" />
    <path d="M16 5 A11 11 0 0 1 16 27 Z" fill="currentColor" />
  </svg>
);

const APPEARANCE_KEY = "slind_theme";

export const applyTheme = (mode) => {
  const html = document.documentElement;
  let theme = mode;
  if (mode === "system") {
    // Respect OS preference — default to dark if no preference
    theme = window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
  }
  if (theme === "dark") {
    html.removeAttribute("data-theme");
  } else {
    html.setAttribute("data-theme", theme);
  }
};

export const initThemeFromStorage = () => {
  const saved = localStorage.getItem(APPEARANCE_KEY) || "system";
  applyTheme(saved);
  if (saved === "system") {
    const mq = window.matchMedia("(prefers-color-scheme: light)");
    const onChange = () => applyTheme("system");
    mq.addEventListener?.("change", onChange);
  }
  return saved;
};

const TITLES = {
  ru: { title: "Внешний вид", system: "System", light: "Light", dark: "Dark" },
  en: { title: "Appearance", system: "System", light: "Light", dark: "Dark" },
};

const AppearancePopup = ({ onClose, lang = "ru" }) => {
  const [closing, setClosing] = useState(false);
  const [selected, setSelected] = useState(
    localStorage.getItem(APPEARANCE_KEY) || "system"
  );
  const t = TITLES[lang] || TITLES.en;

  useEffect(() => {
    const onKey = (e) => { if (e.key === "Escape") doClose(); };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const doClose = () => {
    setClosing(true);
    setTimeout(() => onClose && onClose(), 280);
  };

  const pick = (mode) => {
    setSelected(mode);
    localStorage.setItem(APPEARANCE_KEY, mode);
    applyTheme(mode);
  };

  const options = [
    { id: "system", label: t.system, Icon: SystemIcon },
    { id: "light", label: t.light, Icon: SunIcon },
    { id: "dark", label: t.dark, Icon: MoonIcon },
  ];

  return (
    <div
      className={`popup-overlay appearance-popup-overlay ${closing ? "closing" : ""}`}
      onClick={doClose}
      data-testid="appearance-popup"
    >
      <div className="appearance-popup" onClick={(e) => e.stopPropagation()}>
        <div className="popup-handle" />
        <h2 className="popup-title">{t.title}</h2>
        <div className="appearance-grid">
          {options.map(({ id, label, Icon }) => (
            <div key={id} className="appearance-option-wrap">
              <button
                className={`appearance-card ${selected === id ? "selected" : ""}`}
                onClick={() => pick(id)}
                data-testid={`appearance-${id}`}
                aria-label={label}
              >
                <Icon />
              </button>
              <div className="appearance-label">{label}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default AppearancePopup;
