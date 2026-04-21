import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { Plus, ArrowUp, ArrowLeft, X } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const VoiceAssistantPage = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const [user, setUser] = useState(null);
  const [prompt, setPrompt] = useState('');
  const [attachments, setAttachments] = useState([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isAISpeaking, setIsAISpeaking] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem('slind_user');
    if (saved) {
      try {
        setUser(JSON.parse(saved));
      } catch {
        localStorage.removeItem('slind_user');
      }
    }
  }, []);

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files || []);
    files.forEach((file) => {
      const preview = URL.createObjectURL(file);
      setAttachments((prev) => [
        ...prev,
        {
          id: `${Date.now()}-${Math.random()}`,
          file,
          preview,
          type: file.type?.startsWith('video/') ? 'video' : 'image',
        },
      ]);
    });
    e.target.value = '';
  };

  const removeAttachment = (id) => {
    setAttachments((prev) => prev.filter((a) => a.id !== id));
  };

  const handleSend = async () => {
    if (!user) {
      navigate('/auth');
      return;
    }
    if ((!prompt.trim() && attachments.length === 0) || isSubmitting) return;

    const currentPrompt = prompt.trim();
    const currentAttachments = [...attachments];

    setIsSubmitting(true);
    setIsAISpeaking(true);
    setPrompt('');
    setAttachments([]);

    try {
      const requestData = {
        prompt: currentPrompt,
        format_id: 'auto',
        language: 'auto',
        user_id: user.id || user.user_id,
      };

      if (currentAttachments.length > 0) {
        const uploadedUrls = [];
        for (const att of currentAttachments) {
          if (att.file) {
            const formData = new FormData();
            formData.append('file', att.file);
            const uploadRes = await axios.post(`${API}/upload`, formData, {
              headers: { 'Content-Type': 'multipart/form-data' },
            });
            uploadedUrls.push(uploadRes.data.url);
          }
        }

        const videoAttachment = currentAttachments.find((a) => a.type === 'video');
        if (videoAttachment && uploadedUrls.length > 0) {
          const response = await axios.post(`${API}/device-mockup/create`, {
            video_url: uploadedUrls[0],
            device_type: 'phone',
            rotation: 12,
            bg_color: [15, 15, 20],
            animation_style: 'camera',
            phone_position: 'center',
            aspect_ratio: '9:16',
            user_id: user.user_id || user.id,
          });
          toast.success('Создаём 3D анимацию...');
          navigate(`/video/${response.data.id}`);
          return;
        }

        requestData.product_images = uploadedUrls;
      }

      const response = await axios.post(`${API}/video/generate`, requestData, {
        headers: { Authorization: `Bearer ${user.token}` },
      });
      toast.success('Генерация началась!');
      navigate(`/video/${response.data.id}`);
    } catch (err) {
      console.error('Voice assistant submit failed:', err);
      toast.error('Ошибка при запуске генерации');
      setIsAISpeaking(false);
      setIsSubmitting(false);
    }
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
          className={`voice-eyes ${isAISpeaking ? 'speaking' : ''}`}
          data-testid="voice-eyes"
        >
          <div className="voice-eye left"></div>
          <div className="voice-eye right"></div>
        </div>
      </div>

      <div className="voice-assistant-bottom">
        {attachments.length > 0 && (
          <div className="voice-attachments-row" data-testid="voice-attachments-row">
            {attachments.map((att) => (
              <div key={att.id} className="voice-attachment-chip">
                {att.type === 'video' ? (
                  <video src={att.preview} muted />
                ) : (
                  <img src={att.preview} alt="" />
                )}
                <button
                  className="voice-attachment-remove"
                  onClick={() => removeAttachment(att.id)}
                  aria-label="Remove"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        )}

        <div className="voice-input-container">
          <button
            className="voice-plus-btn"
            onClick={() => fileInputRef.current?.click()}
            data-testid="voice-plus-btn"
            aria-label="Attach"
            type="button"
          >
            <Plus className="w-5 h-5" />
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*,video/*"
            multiple
            style={{ display: 'none' }}
            onChange={handleFileSelect}
          />

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
              disabled={isSubmitting}
              data-testid="voice-input-field"
            />
            <button
              className="voice-send-btn"
              onClick={handleSend}
              disabled={(!prompt.trim() && attachments.length === 0) || isSubmitting}
              data-testid="voice-send-btn"
              aria-label="Send"
              type="button"
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
