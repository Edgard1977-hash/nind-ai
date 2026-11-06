import { useEffect, useRef, useState } from "react";
import axios from "axios";
import { BACKEND_URL } from "@/lib/backend";

const API = `${BACKEND_URL}/api`;

const FALLBACK_VOICES = [
  { id: "marin", label: "Marin", gender: "female" },
  { id: "cedar", label: "Cedar", gender: "male" },
  { id: "alloy", label: "Alloy", gender: "neutral" },
  { id: "nova", label: "Nova", gender: "female" },
  { id: "shimmer", label: "Shimmer", gender: "female" },
  { id: "coral", label: "Coral", gender: "female" },
  { id: "ash", label: "Ash", gender: "male" },
  { id: "echo", label: "Echo", gender: "male" },
  { id: "onyx", label: "Onyx", gender: "male" },
];

const VoicePicker = ({ voice, onChange }) => {
  const [voices, setVoices] = useState(FALLBACK_VOICES);
  const appliedDefault = useRef(false);

  useEffect(() => {
    let cancel = false;
    axios
      .get(`${API}/voices`)
      .then((response) => {
        if (cancel) return;
        const next = response.data?.voices;
        if (Array.isArray(next) && next.length) setVoices(next);
        if (!appliedDefault.current && response.data?.default) {
          appliedDefault.current = true;
          onChange(response.data.default);
        }
      })
      .catch(() => {});
    return () => {
      cancel = true;
    };
  }, [onChange]);

  return (
    <div className="voice-picker" role="listbox" aria-label="Voice" data-testid="voice-picker">
      <span className="voice-picker-label">Voice</span>
      {voices.map((item) => (
        <button
          key={item.id}
          type="button"
          role="option"
          aria-selected={voice === item.id}
          className={voice === item.id ? "active" : ""}
          onClick={() => onChange(item.id)}
          data-testid={`voice-${item.id}`}
        >
          {item.label}
          <span className="voice-picker-gender">{item.gender}</span>
        </button>
      ))}
    </div>
  );
};

export default VoicePicker;
