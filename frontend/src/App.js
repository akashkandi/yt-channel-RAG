import { useState, useEffect } from "react";
import axios from "axios";
import ReactMarkdown from "react-markdown";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

const DEFAULT_QUESTIONS = [
  "What is the main topic covered?",
  "Summarize the key concepts explained",
  "What examples are used to explain things?",
  "What are the most important points?",
  "How does this topic work in practice?",
];

function App() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [videos, setVideos] = useState([]);
  const [stats, setStats] = useState(null);
  const [activeTab, setActiveTab] = useState("ask");
  const [channelInput, setChannelInput] = useState("");
  const [ingesting, setIngesting] = useState(false);
  const [ingestStatus, setIngestStatus] = useState(null);
  const [ingestError, setIngestError] = useState(null);

  useEffect(() => {
    axios.get(`${API_URL}/stats`).then((res) => setStats(res.data)).catch(() => {});
  }, []);

  const fetchVideos = async () => {
    try {
      const res = await axios.get(`${API_URL}/videos`);
      setVideos(res.data.videos);
      setActiveTab("videos");
    } catch (e) {
      console.error("Failed to fetch videos");
    }
  };

  const ingestChannel = async () => {
    if (!channelInput.trim()) return;
    setIngesting(true);
    setIngestStatus(null);
    setIngestError(null);
    setAnswer(null);
    try {
      const res = await axios.post(`${API_URL}/ingest`, {
        channel_id: channelInput.trim(),
      }, { timeout: 600000 });
      setIngestStatus(res.data);
      const statsRes = await axios.get(`${API_URL}/stats`);
      setStats(statsRes.data);
      setChannelInput("");
    } catch (e) {
      const msg = e.response?.data?.detail || "Failed to ingest. Check the URL and try again.";
      setIngestError(msg);
    } finally {
      setIngesting(false);
    }
  };

  const askQuestion = async () => {
    if (!question.trim()) return;
    setLoading(true);
    setError(null);
    setAnswer(null);
    try {
      const res = await axios.post(`${API_URL}/ask`, {
        question: question,
        n_results: 5,
      });
      setAnswer(res.data);
      setActiveTab("ask");
    } catch (e) {
      setError("Something went wrong. Make sure the backend is running.");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      askQuestion();
    }
  };

  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}m ${s}s`;
  };

  const scoreColor = (score) => {
    if (score >= 7) return "#4ade80";
    if (score >= 4) return "#facc15";
    return "#f87171";
  };

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <div className="logo">
            <div className="logo-icon">
              <svg viewBox="0 0 24 24" fill="white" width="20" height="20">
                <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
              </svg>
            </div>
            <div>
              <h1>YouTube Knowledge Base</h1>
              <p>Chat with any YouTube channel or playlist</p>
            </div>
          </div>
          {stats && stats.total_chunks > 0 && (
            <div className="stats-bar">
              <div className="stat">
                <span className="stat-num">{stats.total_videos}</span>
                <span className="stat-label">Videos</span>
              </div>
              <div className="stat">
                <span className="stat-num">{stats.total_chunks.toLocaleString()}</span>
                <span className="stat-label">Chunks</span>
              </div>
              <div className="stat">
                <span className="stat-num">GPT-4o</span>
                <span className="stat-label">Model</span>
              </div>
            </div>
          )}
        </div>
      </header>

      {/* Channel Ingest Bar */}
      <div className="ingest-bar">
        <div className="ingest-row">
          <input
            className="channel-input"
            placeholder="Paste any YouTube channel, playlist, or video URL..."
            value={channelInput}
            onChange={(e) => setChannelInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && ingestChannel()}
            disabled={ingesting}
          />
          <button
            className="ingest-btn"
            onClick={ingestChannel}
            disabled={ingesting || !channelInput.trim()}
          >
            {ingesting ? (
              <span className="ingest-loading">
                <span className="loading-spinner small"></span>
                Loading...
              </span>
            ) : "Load Channel"}
          </button>
        </div>

        {ingesting && (
          <div className="ingest-progress">
            <div className="progress-bar">
              <div className="progress-fill"></div>
            </div>
            <span>Fetching transcripts and building knowledge base... this takes 2-5 minutes</span>
          </div>
        )}

        {ingestStatus && (
          <div className="ingest-success">
            ✅ Loaded <strong>{ingestStatus.videos_processed} videos</strong> and <strong>{ingestStatus.chunks_created.toLocaleString()} chunks</strong> from <strong>{ingestStatus.channel_name}</strong>
          </div>
        )}

        {ingestError && (
          <div className="ingest-error">❌ {ingestError}</div>
        )}
      </div>

      <nav className="nav">
        <button
          className={activeTab === "ask" ? "nav-btn active" : "nav-btn"}
          onClick={() => setActiveTab("ask")}
        >
          Ask a Question
        </button>
        <button
          className={activeTab === "videos" ? "nav-btn active" : "nav-btn"}
          onClick={fetchVideos}
        >
          Browse Videos
        </button>
      </nav>

      <main className="main">
        {activeTab === "ask" && (
          <div className="ask-section">

            {stats && stats.total_chunks === 0 && (
              <div className="empty-state">
                <div className="empty-icon">▶</div>
                <h2>Load a YouTube channel to get started</h2>
                <p>Paste any YouTube channel URL, playlist URL, or video URL above and click "Load Channel". Then ask any question about the content.</p>
                <div className="example-urls">
                  <p>Examples:</p>
                  <code>https://www.youtube.com/@AndrejKarpathy</code>
                  <code>https://www.youtube.com/playlist?list=PLZHQObOWTQDNU6R1_67000Dx_ZCJB-3pi</code>
                </div>
              </div>
            )}

            {stats && stats.total_chunks > 0 && (
              <>
                <div className="examples">
                  <p className="examples-label">Try asking:</p>
                  <div className="example-chips">
                    {DEFAULT_QUESTIONS.map((q) => (
                      <button
                        key={q}
                        className="example-chip"
                        onClick={() => setQuestion(q)}
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="input-area">
                  <textarea
                    className="question-input"
                    placeholder="Ask anything about the loaded videos..."
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    onKeyDown={handleKeyDown}
                    rows={3}
                  />
                  <button
                    className="ask-btn"
                    onClick={askQuestion}
                    disabled={loading || !question.trim()}
                  >
                    {loading ? (
                      <span className="ingest-loading">
                        <span className="loading-spinner small white"></span>
                        Thinking...
                      </span>
                    ) : "Ask →"}
                  </button>
                </div>
              </>
            )}

            {error && <div className="error">{error}</div>}

            {loading && (
              <div className="loading">
                <div className="loading-spinner"></div>
                <p>Searching through {stats ? stats.total_chunks.toLocaleString() : 0} transcript chunks...</p>
              </div>
            )}

            {answer && (
              <div className="answer-section">
                <div className="score-row">
                  <div className="score-badge" style={{borderColor: scoreColor(answer.retrieval_score), color: scoreColor(answer.retrieval_score)}}>
                    Relevance: {answer.retrieval_score}/10
                  </div>
                  {answer.unique_videos_count >= 2 && (
                    <div className="score-badge green-badge">
                      ✦ {answer.unique_videos_count} videos synthesized
                    </div>
                  )}
                </div>

                {answer.cross_video_synthesis && (
                  <div className="synthesis-box">
                    <p className="synthesis-label">✦ Cross-Video Synthesis</p>
                    <p>{answer.cross_video_synthesis}</p>
                  </div>
                )}

                <div className="answer-box">
                  <ReactMarkdown>{answer.answer}</ReactMarkdown>
                </div>

                <div className="citations">
                  <h3>Sources — click to watch at exact timestamp</h3>
                  <div className="citation-grid">
                    {answer.citations.map((c, i) => (
                      <a
                        key={i}
                        href={c.youtube_link}
                        target="_blank"
                        rel="noreferrer"
                        className="citation-card"
                      >
                        <div className="citation-num">{c.source_num}</div>
                        <div className="citation-info">
                          <p className="citation-title">{c.video_title}</p>
                          <p className="citation-time">▶ Jump to {formatTime(c.start_time)}</p>
                        </div>
                        <span className="citation-arrow">→</span>
                      </a>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === "videos" && (
          <div className="videos-section">
            <h2>Loaded Videos ({videos.length})</h2>
            <div className="video-grid">
              {videos.map((v) => (
                <a
                  key={v.video_id}
                  href={v.url}
                  target="_blank"
                  rel="noreferrer"
                  className="video-card"
                >
                  <img
                    src={`https://img.youtube.com/vi/${v.video_id}/mqdefault.jpg`}
                    alt={v.title}
                    className="video-thumb"
                  />
                  <p className="video-title">{v.title}</p>
                </a>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;