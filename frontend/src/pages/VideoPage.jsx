import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Download, Link2, RefreshCw, Trash2 } from "lucide-react";
import { toast } from "sonner";
import axios from "axios";
import { API, BACKEND_URL } from "@/lib/backend";

const mediaUrl = (path) => {
  if (!path) return "";
  if (path.startsWith("http")) return path;
  return `${BACKEND_URL}${path}`;
};

const formatWhen = (value) => {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
};

const formatDuration = (project) => {
  const seconds = (project?.scenes || []).reduce(
    (sum, scene) => sum + (Number(scene?.duration) || 0),
    0
  );
  if (!seconds) return null;
  const whole = Math.round(seconds);
  const minutes = Math.floor(whole / 60);
  const rest = whole % 60;
  return minutes ? `${minutes}m ${rest}s` : `${rest}s`;
};

const modeLabel = (mode) => (mode === "enhanced" ? "Улучшенная" : "Базовая");

export const VideoPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  const fetchProject = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/video/${id}`);
      setProject(response.data);
      setError(null);
      setIsLoading(false);
      if (response.data.status === "pending" || response.data.status === "processing") {
        setTimeout(fetchProject, 2000);
      }
    } catch (err) {
      setError(err.response?.status === 401 ? "Sign in to view this video" : "This video could not be found");
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchProject();
  }, [fetchProject]);

  const copyLink = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      toast.success("Link copied");
    } catch {
      toast.error("Could not copy the link");
    }
  };

  const download = () => {
    if (!project?.video_url) return;
    const link = document.createElement("a");
    link.href = mediaUrl(project.video_url);
    link.download = `${project.title || "nind"}.mp4`;
    link.click();
  };

  const remove = async () => {
    if (!window.confirm("Delete this video?")) return;
    setBusy(true);
    try {
      await axios.delete(`${API}/videos/${id}`);
      toast.success("Deleted");
      navigate("/");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Could not delete");
      setBusy(false);
    }
  };

  const regenerate = async () => {
    if (!project?.prompt) {
      navigate("/create");
      return;
    }
    setBusy(true);
    try {
      const response = await axios.post(`${API}/video/generate`, {
        prompt: project.prompt,
        format_id: project.format_id || "auto",
        language: project.language || "auto",
        mode: project.mode || "basic",
      });
      toast.success("Generating a new version");
      navigate(`/video/${response.data.id}`);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Could not regenerate");
      setBusy(false);
    }
  };

  if (isLoading) {
    return (
      <div className="nind-video" data-testid="video-page">
        <div className="nind-video-status">Loading…</div>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="nind-video" data-testid="video-page">
        <header className="nind-video-top">
          <button type="button" className="nind-video-icon" onClick={() => navigate("/")} data-testid="back-button">
            <ArrowLeft size={18} />
          </button>
        </header>
        <div className="nind-video-status">
          <h1>Video unavailable</h1>
          <p>{error}</p>
          <button type="button" className="nind-video-primary" onClick={() => navigate("/")}>
            Back home
          </button>
        </div>
      </div>
    );
  }

  const processing = project.status === "pending" || project.status === "processing";
  const failed = project.status === "error" || project.status === "failed";
  const ready = project.status === "completed" && project.video_url;
  const when = formatWhen(project.created_at || project.completed_at);
  const duration = formatDuration(project);
  const formatName = (project.format_id || "auto").split("_").join(" ");

  return (
    <div className="nind-video" data-testid="video-page">
      <header className="nind-video-top">
        <button type="button" className="nind-video-icon" onClick={() => navigate("/")} data-testid="back-button" aria-label="Back">
          <ArrowLeft size={18} />
        </button>
        <span className="nind-video-brand">nind</span>
        <span className="nind-video-top-spacer" />
      </header>

      <main className="nind-video-layout">
        <section className="nind-video-stage">
          {processing && (
            <div className="nind-video-progress" data-testid="video-progress">
              <div className="nind-video-progress-track">
                <div style={{ width: `${Math.min(100, project.progress || 4)}%` }} />
              </div>
              <strong>{project.progress || 0}%</strong>
              <p>{project.progress_message || "Rendering…"}</p>
            </div>
          )}

          {failed && (
            <div className="nind-video-progress nind-video-error" data-testid="video-error">
              <strong>Could not finish this video</strong>
              <p>{project.error || "The generation failed."}</p>
            </div>
          )}

          {ready && (
            <video
              className="nind-video-player"
              src={mediaUrl(project.video_url)}
              poster={project.poster_url ? mediaUrl(project.poster_url) : undefined}
              controls
              playsInline
              preload="metadata"
              data-testid="video-element"
            />
          )}

          {!processing && !failed && !ready && (
            <div className="nind-video-progress">
              <p>The file is not ready yet.</p>
            </div>
          )}
        </section>

        <section className="nind-video-meta">
          <p className="nind-video-kicker">{modeLabel(project.mode)}</p>
          <h1>{project.title || project.prompt || "Untitled"}</h1>
          {project.prompt && project.title && project.prompt !== project.title && (
            <p className="nind-video-prompt">{project.prompt}</p>
          )}

          <dl className="nind-video-facts">
            <div>
              <dt>Mode</dt>
              <dd>{project.mode === "enhanced" ? "Enhanced" : "Basic"}</dd>
            </div>
            <div>
              <dt>Format</dt>
              <dd>{formatName}</dd>
            </div>
            <div>
              <dt>Duration</dt>
              <dd>{duration || "—"}</dd>
            </div>
            <div>
              <dt>Created</dt>
              <dd>{when || "—"}</dd>
            </div>
          </dl>

          <div className="nind-video-actions">
            <button type="button" className="nind-video-primary" onClick={download} disabled={!ready} data-testid="download-button">
              <Download size={16} /> Download
            </button>
            <button type="button" className="nind-video-secondary" onClick={regenerate} disabled={busy} data-testid="regenerate-button">
              <RefreshCw size={16} /> Regenerate
            </button>
            <button type="button" className="nind-video-secondary" onClick={copyLink} data-testid="share-button">
              <Link2 size={16} /> Copy link
            </button>
            <button type="button" className="nind-video-danger" onClick={remove} disabled={busy} data-testid="delete-button">
              <Trash2 size={16} /> Delete
            </button>
          </div>
        </section>
      </main>
    </div>
  );
};

export default VideoPage;
