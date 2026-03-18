import { useState, useEffect } from "react";
import { ArrowLeft, Plus, X, LogOut } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Plan labels
const PLAN_LABELS = {
  free: "Free Plan",
  basic: "Basic Plan",
  plus: "Plus Plan",
  creator: "Creator Plan"
};

export const ProfilePage = ({ user, onBack, onLogout }) => {
  const [showAddMember, setShowAddMember] = useState(false);
  const [memberUsername, setMemberUsername] = useState("");
  const [teamMembers, setTeamMembers] = useState([]);
  const [generatingVideos, setGeneratingVideos] = useState([]);
  const [completedVideos, setCompletedVideos] = useState([]);

  useEffect(() => {
    // Fetch user's videos
    fetchVideos();
  }, []);

  const fetchVideos = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/videos`);
      const data = await response.json();
      
      const generating = (data.projects || []).filter(v => v.status === "processing");
      const completed = (data.projects || []).filter(v => v.status === "completed");
      
      setGeneratingVideos(generating);
      setCompletedVideos(completed);
    } catch (error) {
      console.error("Failed to fetch videos:", error);
    }
  };

  const handleAddMember = () => {
    if (!memberUsername.trim()) return;
    
    // Add member to team
    setTeamMembers(prev => [...prev, {
      id: Date.now(),
      username: memberUsername.startsWith("@") ? memberUsername : `@${memberUsername}`,
      avatar: null
    }]);
    setMemberUsername("");
    setShowAddMember(false);
  };

  const removeMember = (id) => {
    setTeamMembers(prev => prev.filter(m => m.id !== id));
  };

  return (
    <div className="profile-page" data-testid="profile-page">
      {/* Header */}
      <header className="profile-header">
        <button className="back-button" onClick={onBack} data-testid="back-button">
          <ArrowLeft className="w-6 h-6" />
        </button>
        <button className="logout-button" onClick={onLogout} data-testid="logout-button">
          <LogOut className="w-5 h-5" />
        </button>
      </header>

      {/* Team section */}
      <section className="profile-section">
        <h2 className="section-title">Команда</h2>
        <div className="team-row">
          <button 
            className="add-member-btn"
            onClick={() => setShowAddMember(true)}
            data-testid="add-member-btn"
          >
            <Plus className="w-5 h-5" />
          </button>
          
          {teamMembers.map((member) => (
            <div key={member.id} className="team-member">
              <div className="member-avatar">
                {member.avatar ? (
                  <img src={member.avatar} alt={member.username} />
                ) : (
                  <span>{member.username[1]?.toUpperCase()}</span>
                )}
              </div>
              <button 
                className="remove-member"
                onClick={() => removeMember(member.id)}
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* User info */}
      <section className="user-info-card">
        <div className="user-avatar-large">
          {user.avatar ? (
            <img src={user.avatar} alt={user.name} />
          ) : (
            <span>{user.name?.[0]?.toUpperCase() || user.username?.[1]?.toUpperCase()}</span>
          )}
        </div>
        <div className="user-details">
          <h3 className="user-name">{user.username || `@${user.name?.toLowerCase().replace(/\s/g, "")}`}</h3>
          <p className="user-plan">{PLAN_LABELS[user.plan || "free"]}</p>
        </div>
      </section>

      {/* Generating videos */}
      {generatingVideos.length > 0 && (
        <section className="profile-section">
          <h2 className="section-title">Генерируется</h2>
          <div className="videos-grid">
            {generatingVideos.map((video) => (
              <div key={video.id} className="video-generating" data-testid={`generating-${video.id}`}>
                <div className="video-loading-animation">
                  <div className="loading-spinner" />
                  <span className="loading-progress">{video.progress || 0}%</span>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Completed videos */}
      {completedVideos.length > 0 && (
        <section className="profile-section">
          <h2 className="section-title">Мои видео</h2>
          <div className="videos-grid">
            {completedVideos.map((video) => (
              <div key={video.id} className="video-card-profile" data-testid={`video-${video.id}`}>
                {video.poster_url ? (
                  <img 
                    src={`${BACKEND_URL}${video.poster_url}`} 
                    alt={video.title}
                    className="video-thumbnail"
                  />
                ) : (
                  <video 
                    src={`${BACKEND_URL}${video.video_url}`}
                    className="video-thumbnail"
                    muted
                    playsInline
                  />
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Add member popup */}
      {showAddMember && (
        <div className="popup-overlay" onClick={() => setShowAddMember(false)}>
          <div className="add-member-popup" onClick={e => e.stopPropagation()}>
            <div className="drag-indicator" />
            <h3>Добавить участника команды</h3>
            <input
              type="text"
              value={memberUsername}
              onChange={(e) => setMemberUsername(e.target.value)}
              placeholder="@username"
              className="member-input"
              data-testid="member-username-input"
            />
            <button 
              className="add-member-submit"
              onClick={handleAddMember}
              data-testid="add-member-submit"
            >
              Добавить в команду
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProfilePage;
