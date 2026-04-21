import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, ArrowUp, ArrowLeft } from 'lucide-react';

const VoiceAssistantPage = () => {
  const navigate = useNavigate();
  const [prompt, setPrompt] = useState('');
  const [isRecording] = useState(false);
  const [isAISpeaking] = useState(false);

  const handleSend = () => {
    if (!prompt.trim()) return;
    // TODO: wire up voice assistant send
    console.log('Send:', prompt);
    setPrompt('');
  };

  return (
    <div className="voice-assistant-page" data-testid="voice-assistant-page">
      <button
        className="voice-assistant-back"
        onClick={() => navigate('/')}
        data-testid="voice-assistant-back"
        aria-label="Back"
      >
        <ArrowLeft className="w-5 h-5" />
      </button>

      <div className="voice-assistant-main">
        <div
          className={`voice-eyes ${isAISpeaking ? 'speaking' : ''} ${isRecording ? 'listening' : ''}`}
          data-testid="voice-eyes"
        >
          <div className="voice-eye left"></div>
          <div className="voice-eye right"></div>
        </div>
      </div>

      <div className="voice-assistant-bottom">
        <div className="voice-input-container">
          <button
            className="voice-plus-btn"
            data-testid="voice-plus-btn"
            aria-label="Attach"
          >
            <Plus className="w-5 h-5" />
          </button>

          <div className="voice-input-wrap">
            <input
              type="text"
              className="voice-input-field"
              placeholder="Ask anything"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleSend();
              }}
              data-testid="voice-input-field"
            />
            <button
              className="voice-send-btn"
              onClick={handleSend}
              disabled={!prompt.trim()}
              data-testid="voice-send-btn"
              aria-label="Send"
            >
              <ArrowUp className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VoiceAssistantPage;
