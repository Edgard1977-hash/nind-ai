import { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { Plus, ArrowUp, ArrowLeft, X, Mic, Square, Loader2 } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const VoiceAssistantPage = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const canvasRef = useRef(null);
  const audioCtxRef = useRef(null);
  const analyserRef = useRef(null);
  const rafRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const audioChunksRef = useRef([]);

  const [user, setUser] = useState(null);
  const [prompt, setPrompt] = useState('');
  const [attachments, setAttachments] = useState([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [isInIframe, setIsInIframe] = useState(false);

  useEffect(() => {
    try {
      setIsInIframe(window.self !== window.top);
    } catch {
      setIsInIframe(true);
    }
    const saved = localStorage.getItem('slind_user');
    if (saved) {
      try {
        setUser(JSON.parse(saved));
      } catch {
        localStorage.removeItem('slind_user');
      }
    }
  }, []);

  // --- Waveform drawing ---
  const drawWaveform = useCallback(() => {
    const canvas = canvasRef.current;
    const analyser = analyserRef.current;
    if (!canvas || !analyser) return;

    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const render = () => {
      rafRef.current = requestAnimationFrame(render);
      analyser.getByteTimeDomainData(dataArray);

      const w = rect.width;
      const h = rect.height;
      ctx.clearRect(0, 0, w, h);

      // Bar-style visualizer for a cleaner look
      const bars = 42;
      const step = Math.floor(bufferLength / bars);
      const barWidth = (w / bars) * 0.55;
      const gap = (w / bars) * 0.45;

      for (let i = 0; i < bars; i++) {
        // Sample center of each bucket
        const v = (dataArray[i * step] - 128) / 128; // -1..1
        const amp = Math.min(1, Math.abs(v) * 2.2);
        const barH = Math.max(3, amp * h * 0.9);
        const x = i * (barWidth + gap) + gap / 2;
        const y = (h - barH) / 2;

        ctx.fillStyle = '#0096FE';
        ctx.beginPath();
        const r = Math.min(barWidth / 2, 4);
        ctx.moveTo(x + r, y);
        ctx.lineTo(x + barWidth - r, y);
        ctx.quadraticCurveTo(x + barWidth, y, x + barWidth, y + r);
        ctx.lineTo(x + barWidth, y + barH - r);
        ctx.quadraticCurveTo(x + barWidth, y + barH, x + barWidth - r, y + barH);
        ctx.lineTo(x + r, y + barH);
        ctx.quadraticCurveTo(x, y + barH, x, y + barH - r);
        ctx.lineTo(x, y + r);
        ctx.quadraticCurveTo(x, y, x + r, y);
        ctx.fill();
      }
    };
    render();
  }, []);

  const drawIdleWaveform = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const w = rect.width;
    const h = rect.height;
    ctx.clearRect(0, 0, w, h);
    const bars = 42;
    const barWidth = (w / bars) * 0.55;
    const gap = (w / bars) * 0.45;
    ctx.fillStyle = 'rgba(0, 150, 254, 0.28)';
    for (let i = 0; i < bars; i++) {
      const x = i * (barWidth + gap) + gap / 2;
      const barH = 3;
      const y = (h - barH) / 2;
      const r = Math.min(barWidth / 2, 1.5);
      ctx.beginPath();
      ctx.moveTo(x + r, y);
      ctx.lineTo(x + barWidth - r, y);
      ctx.quadraticCurveTo(x + barWidth, y, x + barWidth, y + r);
      ctx.lineTo(x + barWidth, y + barH - r);
      ctx.quadraticCurveTo(x + barWidth, y + barH, x + barWidth - r, y + barH);
      ctx.lineTo(x + r, y + barH);
      ctx.quadraticCurveTo(x, y + barH, x, y + barH - r);
      ctx.lineTo(x, y + r);
      ctx.quadraticCurveTo(x, y, x + r, y);
      ctx.fill();
    }
  }, []);

  useEffect(() => {
    drawIdleWaveform();
    const onResize = () => {
      if (!isRecording) drawIdleWaveform();
    };
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, [drawIdleWaveform, isRecording]);

  // --- File attachments ---
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

  // --- Submit flow (text + attachments) ---
  const submitPrompt = async (textOverride) => {
    if (!user) {
      navigate('/auth');
      return;
    }
    const currentPrompt = (textOverride ?? prompt).trim();
    const currentAttachments = [...attachments];
    if (!currentPrompt && currentAttachments.length === 0) return;
    if (isSubmitting) return;

    setIsSubmitting(true);
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
      setIsSubmitting(false);
    }
  };

  // --- Recording ---
  const startRecording = async () => {
    if (!user) {
      navigate('/auth');
      return;
    }
    if (isRecording || isTranscribing || isSubmitting) return;

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      toast.error('Ваш браузер не поддерживает запись. Откройте на HTTPS в новой вкладке.');
      return;
    }

    if (!window.isSecureContext) {
      toast.error('Запись возможна только на HTTPS');
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      const audioCtx = new AudioCtx();
      audioCtxRef.current = audioCtx;
      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 2048;
      source.connect(analyser);
      analyserRef.current = analyser;

      const mime = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : 'audio/webm';
      const recorder = new MediaRecorder(stream, { mimeType: mime });
      mediaRecorderRef.current = recorder;
      audioChunksRef.current = [];

      recorder.ondataavailable = (ev) => {
        if (ev.data && ev.data.size > 0) audioChunksRef.current.push(ev.data);
      };
      recorder.onstop = async () => {
        if (rafRef.current) cancelAnimationFrame(rafRef.current);
        rafRef.current = null;
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((t) => t.stop());
          streamRef.current = null;
        }
        if (audioCtxRef.current) {
          try { await audioCtxRef.current.close(); } catch (err) { /* noop */ }
          audioCtxRef.current = null;
        }
        analyserRef.current = null;
        drawIdleWaveform();

        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        if (!blob.size) {
          toast.error('Пустая запись');
          return;
        }
        await transcribeAndSubmit(blob);
      };

      recorder.start();
      setIsRecording(true);
      drawWaveform();
    } catch (err) {
      console.error('Mic access failed:', err);
      const name = err?.name || '';
      // In an iframe without allow="microphone" the browser rejects silently.
      // Fall back to opening a fresh tab where the page is top-level and mic works.
      if (isInIframe) {
        const link = document.createElement('a');
        link.href = window.location.href;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        toast.info('Откройте страницу в новой вкладке, там микрофон будет работать');
        return;
      }
      if (name === 'NotAllowedError' || name === 'PermissionDeniedError') {
        toast.error('Доступ к микрофону запрещён. Разрешите его в настройках браузера.');
      } else if (name === 'NotFoundError' || name === 'DevicesNotFoundError') {
        toast.error('Микрофон не найден');
      } else if (name === 'NotReadableError') {
        toast.error('Микрофон уже занят другим приложением');
      } else if (name === 'SecurityError') {
        toast.error('Запись возможна только на HTTPS. Откройте страницу в отдельной вкладке.');
      } else {
        toast.error('Не удалось получить доступ к микрофону: ' + (err?.message || name));
      }
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    setIsRecording(false);
  };

  const transcribeAndSubmit = async (blob) => {
    setIsTranscribing(true);
    try {
      const lang = localStorage.getItem('slind_language') || 'ru';
      const formData = new FormData();
      formData.append('file', blob, 'voice.webm');
      formData.append('language', lang);

      const res = await axios.post(`${API}/voice/transcribe`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      const text = (res.data?.text || '').trim();
      setIsTranscribing(false);

      if (!text) {
        toast.error('Не удалось распознать речь');
        return;
      }
      toast.success(`Распознано: "${text.slice(0, 60)}${text.length > 60 ? '…' : ''}"`);
      await submitPrompt(text);
    } catch (err) {
      console.error('Transcribe failed:', err);
      setIsTranscribing(false);
      toast.error('Ошибка транскрипции');
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        try { mediaRecorderRef.current.stop(); } catch (e) { /* noop */ }
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
      }
      if (audioCtxRef.current) {
        try { audioCtxRef.current.close(); } catch (e) { /* noop */ }
      }
    };
  }, []);

  const busy = isSubmitting || isTranscribing;

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
        <div className="voice-assistant-center">
          <div
            className={`voice-eyes ${isRecording ? 'listening' : ''} ${isTranscribing ? 'speaking' : ''}`}
            data-testid="voice-eyes"
          >
            <div className="voice-eye left"></div>
            <div className="voice-eye right"></div>
          </div>

          <div className="voice-waveform" data-testid="voice-waveform">
            <canvas ref={canvasRef} className="voice-waveform-canvas" />
          </div>

          <div className="voice-status-label" data-testid="voice-status-label">
            {isRecording && 'Слушаю...'}
            {isTranscribing && 'Распознаю речь...'}
            {isSubmitting && !isTranscribing && 'Отправляю запрос...'}
            {!isRecording && !isTranscribing && !isSubmitting && (
              isInIframe ? (
                <a
                  href={window.location.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="voice-open-newtab"
                  data-testid="voice-open-newtab"
                >
                  Открыть в новой вкладке
                  <span className="voice-open-newtab-hint">для работы микрофона</span>
                </a>
              ) : (
                <>Нажмите <Mic className="w-3.5 h-3.5 inline-block -mt-0.5" /> чтобы говорить</>
              )
            )}
          </div>
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
              placeholder={isRecording ? 'Запись...' : 'Ask anything'}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') submitPrompt();
              }}
              disabled={busy || isRecording}
              data-testid="voice-input-field"
            />
            {prompt.trim() || attachments.length > 0 ? (
              <button
                className="voice-send-btn"
                onClick={() => submitPrompt()}
                disabled={busy}
                data-testid="voice-send-btn"
                aria-label="Send"
                type="button"
              >
                <ArrowUp className="w-5 h-5" />
              </button>
            ) : (
              <button
                className={`voice-mic-btn ${isRecording ? 'recording' : ''}`}
                onClick={isRecording ? stopRecording : startRecording}
                disabled={busy}
                data-testid="voice-mic-btn"
                aria-label={isRecording ? 'Stop recording' : 'Start recording'}
                type="button"
              >
                {busy ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : isRecording ? (
                  <Square className="w-5 h-5" />
                ) : (
                  <Mic className="w-5 h-5" />
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default VoiceAssistantPage;
