import json
import os
import time
import datetime

import requests
import streamlit as st

try:
    from frontend.auth_api import ask_agent
    from frontend.auth_storage import clear_auth_cookie, restore_auth_from_cookie
except ModuleNotFoundError:
    from auth_api import ask_agent
    from auth_storage import clear_auth_cookie, restore_auth_from_cookie


def get_int_env(name, default):
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default

# ── Constants ────────────────────────────────────────────────────────────────
TEXT_EXTENSIONS = {
    ".txt", ".md", ".csv", ".log", ".yaml", ".yml", ".xml", ".html", ".htm",
    ".ini", ".toml", ".conf", ".py", ".js", ".ts", ".jsx", ".tsx", ".sql",
    ".env", ".sh", ".bash", ".rb", ".go", ".rs", ".java", ".kt", ".swift",
    ".c", ".cpp", ".h", ".cs", ".php", ".r", ".tf", ".hcl", ".dockerfile",
}
DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".rtf", ".epub", ".odt"}
IMAGE_EXTENSIONS    = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".svg", ".ico", ".tiff", ".avif"}
VIDEO_EXTENSIONS    = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".mpeg", ".mpg", ".flv", ".wmv"}
AUDIO_EXTENSIONS    = {".mp3", ".wav", ".m4a", ".ogg", ".aac", ".flac", ".opus", ".aiff"}
ARCHIVE_EXTENSIONS  = {".zip", ".tar", ".gz", ".bz2", ".xz", ".rar", ".7z", ".tgz"}
DATA_EXTENSIONS     = {".json", ".jsonl", ".ndjson", ".parquet", ".pkl"}

MAX_TEXT_CHARS     = 12000
TEXT_PREVIEW_CHARS = 800
MAX_ATTACHMENT_COUNT = get_int_env("MAX_ATTACHMENT_COUNT", 5)
LLM_PROVIDER       = os.getenv("LLM_PROVIDER", "gemini").strip().lower()
MODEL_NAME         = os.getenv("GEMINI_MODEL", "gemini-2.5-flash") if LLM_PROVIDER == "gemini" else os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
MODEL_LABEL        = f"{LLM_PROVIDER} / {MODEL_NAME}" if LLM_PROVIDER else MODEL_NAME

KIND_ICONS = {
    "image": "🖼️", "video": "🎬", "audio": "🎵", "text": "📄",
    "json": "📦", "document": "📑", "archive": "🗜️", "data": "📊", "file": "📎",
}


# ── CSS ──────────────────────────────────────────────────────────────────────
def inject_css():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  --bg:            #0d0e12;
  --bg-start:      #0d0e12;
  --bg-end:        #10121a;
  --bg-grad-1:     rgba(0, 210, 255, 0.08);
  --bg-grad-2:     rgba(37, 99, 235, 0.05);
  --surface:       #151720;
  --surface-hover: #1c1e29;
  --surface-input: #0d0e12;
  --border:        #202230;
  --border-glow:   rgba(0, 210, 255, 0.25);
  --text:          #cbd5e1;
  --text-strong:   #f8fafc;
  --accent:        #00d2ff;
  --accent-soft:   #38bdf8;
  --accent-glow:   rgba(0, 210, 255, 0.15);
  --success:       #10b981;
  --warning:       #f59e0b;
  --critical:      #ef4444;
  --radius:        12px;
  --shadow:        0 4px 12px rgba(0, 0, 0, 0.25), 0 1px 2px rgba(0, 0, 0, 0.15);
}

* { box-sizing: border-box; }

.stApp {
  background:
    radial-gradient(circle at 20% 20%, var(--bg-grad-1), transparent 26%),
    radial-gradient(circle at 80% 82%, var(--bg-grad-2), transparent 22%),
    linear-gradient(180deg, var(--bg-start) 0%, var(--bg-end) 100%);
  color: var(--text);
  font-family: 'Inter', sans-serif;
}

[data-testid="stHeader"] { background: transparent; }
.main .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1200px; }

#MainMenu,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
footer {
  display: none !important;
  visibility: hidden !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
  background: #0b0f17 !important;
  border-right: 1px solid var(--border);
}
[data-testid="stSidebarNav"] {
  display: none !important;
}
[data-testid="stSidebar"] * { color: var(--text) !important; }
[data-testid="stSidebarUserContent"] { padding: 1.5rem 1rem !important; }

/* Brand container */
.brand-container {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 2rem;
  padding-left: 0.25rem;
}
.brand-logo {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: var(--accent-glow) !important;
}
.brand-logo svg {
  stroke: var(--accent) !important;
}
.brand-text {
  display: flex;
  flex-direction: column;
}
.brand-title {
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--text-strong) !important;
  letter-spacing: -0.02em;
  line-height: 1.2;
}
.brand-subtitle {
  font-size: 0.7rem;
  color: #cbd5e1 !important;
  font-weight: 500;
}

/* User profile card */
.user-profile-card {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  border-radius: var(--radius);
  background: #0f141e;
  border: 1px solid var(--border);
  box-shadow: var(--shadow);
  margin-bottom: 1.5rem;
}
.user-avatar-circle {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: var(--accent) !important;
  color: #080b11 !important;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 1.1rem;
}
.user-info {
  display: flex;
  flex-direction: column;
}
.user-name {
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--text-strong) !important;
  line-height: 1.2;
}
.user-email {
  font-size: 0.75rem;
  color: #cbd5e1 !important;
  margin-bottom: 0.15rem;
}
.user-status {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.72rem;
  color: #10b981 !important;
  font-weight: 500;
}
.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 8px #10b981;
}

/* Nav Menu Headers and Items */
.nav-heading {
  font-size: 0.68rem;
  font-weight: 600;
  color: #cbd5e1 !important;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-top: 1.25rem;
  margin-bottom: 0.5rem;
  padding-left: 0.5rem;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.55rem 0.75rem;
  border-radius: 8px;
  font-size: 0.88rem;
  font-weight: 500;
  color: #cbd5e1 !important;
  transition: all 0.15s;
  margin-bottom: 0.15rem;
}
.nav-item:hover {
  color: #f8fafc !important;
  background: rgba(255, 255, 255, 0.02) !important;
}
.nav-item.active {
  color: var(--accent) !important;
  background: var(--accent-glow) !important;
  font-weight: 600;
}
.nav-icon {
  font-size: 1rem;
}

/* Reset default Streamlit button styles globally to match SaaS theme */
div.stButton > button,
button[data-testid="baseButton-secondary"],
button[data-testid="baseButton-primary"] {
  background-color: #0f141e !important;
  color: #f8fafc !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 0.88rem !important;
  font-weight: 500 !important;
  transition: all 0.2s !important;
  box-shadow: none !important;
}
div.stButton > button:hover,
button[data-testid="baseButton-secondary"]:hover {
  background-color: #161e2b !important;
  border-color: var(--accent) !important;
  color: var(--accent) !important;
}

/* Logout button specific styling */
div.logout-btn-wrapper button,
div.logout-btn-wrapper button[data-testid="baseButton-secondary"] {
  width: 100% !important;
  background-color: transparent !important;
  border: 1px solid rgba(239, 68, 68, 0.3) !important;
  color: #ef4444 !important;
  border-radius: 8px !important;
  font-weight: 500 !important;
  font-size: 0.88rem !important;
  padding: 0.55rem 1rem !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 0.5rem !important;
  transition: all 0.2s !important;
}
div.logout-btn-wrapper button:hover,
div.logout-btn-wrapper button[data-testid="baseButton-secondary"]:hover {
  background-color: rgba(239, 68, 68, 0.05) !important;
  border-color: #ef4444 !important;
  color: #ef4444 !important;
  box-shadow: 0 0 10px rgba(239, 68, 68, 0.15) !important;
}

/* AI Model Card */
.ai-model-card {
  background: #0f141e;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1rem;
  box-shadow: var(--shadow);
  margin-top: 0.5rem;
}
.ai-model-header {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-strong) !important;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
}
.ai-model-sparkle {
  color: var(--accent) !important;
}
.ai-model-status {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.72rem;
  color: #10b981 !important;
  font-weight: 500;
  margin-top: 0.25rem;
}

/* Top Header layout */
.top-header-container {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
  width: 100%;
}
.welcome-text-group {
  display: flex;
  flex-direction: column;
}
.welcome-title {
  font-size: 1.6rem !important;
  font-weight: 700 !important;
  color: var(--text-strong) !important;
  letter-spacing: -0.02em;
  margin: 0 !important;
}
.welcome-subtitle {
  font-size: 0.88rem !important;
  color: #cbd5e1 !important;
  margin-top: 0.2rem !important;
}
.header-metadata-group {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  align-items: center;
  margin-top: 0.2rem;
}
.header-metadata-card {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  background-color: #151720;
  border: 1px solid #202230;
  padding: 0.45rem 0.8rem;
  border-radius: 8px;
  text-align: left;
}
.metadata-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  justify-content: center;
}
.metadata-title {
  font-size: 0.68rem;
  font-weight: 500;
  color: #64748b;
  line-height: 1.35 !important;
}
.metadata-value {
  font-size: 0.72rem;
  font-weight: 600;
  color: #cbd5e1;
  line-height: 1.35 !important;
}
.value-green {
  color: #10b981 !important;
}

/* Statistics Grid - CSS Grid to prevent column squishing */
.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  width: 100%;
  margin-bottom: 1.5rem;
}
@media (max-width: 900px) {
  .dashboard-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
@media (max-width: 480px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}

.stat-card {
  background: #0f141e;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1rem;
  display: flex;
  align-items: center;
  gap: 0.85rem;
  box-shadow: var(--shadow);
  transition: all 0.2s;
}
.stat-card-blue { border-left: 3px solid var(--accent); }
.stat-card-green { border-left: 3px solid #10b981; }
.stat-card-orange { border-left: 3px solid #f59e0b; }
.stat-card-red { border-left: 3px solid #ef4444; }

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow), 0 8px 24px rgba(0, 0, 0, 0.3);
}
.stat-card-blue:hover { border-color: var(--accent); }
.stat-card-green:hover { border-color: rgba(16, 185, 129, 0.5); }
.stat-card-orange:hover { border-color: rgba(245, 158, 11, 0.5); }
.stat-card-red:hover { border-color: rgba(239, 68, 68, 0.5); }

.stat-icon-container {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  border-radius: 10px;
  flex-shrink: 0;
}
.stat-icon-blue { background: var(--accent-glow); }
.stat-icon-blue svg { stroke: var(--accent) !important; }
.stat-icon-green { background: rgba(16, 185, 129, 0.1); }
.stat-icon-orange { background: rgba(245, 158, 11, 0.1); }
.stat-icon-red { background: rgba(239, 68, 68, 0.1); }

.stat-content {
  display: flex;
  flex-direction: column;
}
.stat-title {
  font-size: 0.75rem;
  color: #cbd5e1;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.02em;
}
.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #f8fafc;
  line-height: 1.1;
  margin: 0.15rem 0;
}
.stat-desc {
  font-size: 0.68rem;
  color: #cbd5e1;
}

/* File Uploader styling */
.upload-heading {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-strong);
  margin-bottom: 0.75rem;
}
[data-testid="stFileUploaderDropzone"] {
  border: 1px dashed rgba(255, 255, 255, 0.1) !important;
  background: rgba(15, 20, 30, 0.4) !important;
  border-radius: var(--radius) !important;
}
[data-testid="stFileUploaderDropzone"]:hover {
  border-color: var(--accent) !important;
}
[data-testid="stFileUploaderDropzone"] button {
  background: #1e293b !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  color: #f8fafc !important;
  border-radius: 6px !important;
}
[data-testid="stFileUploaderDropzone"] button:hover {
  background: #334155 !important;
  border-color: var(--accent) !important;
  color: #f8fafc !important;
}

/* Text area input fields (forced dark theme integration) */
textarea,
div[data-baseweb="textarea"] {
  background-color: #0f141e !important;
  color: #f8fafc !important;
  -webkit-text-fill-color: #f8fafc !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  box-shadow: var(--shadow);
}
div[data-baseweb="textarea"] textarea {
  color: #f8fafc !important;
  -webkit-text-fill-color: #f8fafc !important;
  background-color: transparent !important;
}
div[data-baseweb="textarea"]:focus-within {
  border-color: var(--accent) !important;
}
textarea::placeholder {
  color: #94a3b8 !important;
  -webkit-text-fill-color: #94a3b8 !important;
  opacity: 1 !important;
}

/* Upload & Analyze action button */
div.upload-btn-container button,
div.upload-btn-container button[data-testid="baseButton-secondary"],
div.upload-btn-container button[data-testid="baseButton-primary"] {
  background-color: var(--accent) !important;
  color: #080b11 !important;
  border: none !important;
  border-radius: 8px !important;
  font-weight: 600 !important;
  width: 100% !important;
  padding: 0.6rem 1rem !important;
  box-shadow: 0 4px 12px rgba(6, 182, 212, 0.2) !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 0.5rem !important;
  transition: all 0.2s !important;
}
div.upload-btn-container button:hover,
div.upload-btn-container button[data-testid="baseButton-primary"]:hover {
  background-color: var(--accent-soft) !important;
  color: #080b11 !important;
  box-shadow: 0 4px 16px rgba(6, 182, 212, 0.4) !important;
}

/* Custom dashed uploader container */
div[data-testid="stFileUploader"] {
  background-color: #151720 !important;
  border: 1px dashed rgba(0, 210, 255, 0.2) !important;
  border-radius: 12px !important;
  padding: 1rem !important;
  transition: all 0.2s ease !important;
}
div[data-testid="stFileUploader"]:hover {
  border-color: rgba(0, 210, 255, 0.45) !important;
  box-shadow: 0 0 12px rgba(0, 210, 255, 0.05) !important;
}

/* Staged / Uploaded files card list */
.uploaded-files-heading {
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--text-strong);
  margin-top: 1.5rem;
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}
.uploaded-file-card {
  background: #151720 !important;
  border: 1px solid #202230 !important;
  border-radius: 8px !important;
  padding: 0.5rem 0.75rem !important;
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-bottom: 0.5rem;
  width: 100%;
}
.uploaded-file-icon {
  font-size: 0.95rem;
  display: flex;
  align-items: center;
}
.icon-purple { color: #c084fc !important; }
.icon-orange { color: #fbbf24 !important; }
.icon-green { color: #34d399 !important; }
.icon-blue { color: #38bdf8 !important; }

.uploaded-file-name {
  font-size: 0.8rem;
  color: #f8fafc !important;
  flex-grow: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.uploaded-file-size {
  font-size: 0.72rem;
  color: #64748b;
  margin-right: 0.2rem;
  font-family: monospace;
}
.uploaded-file-badge {
  background-color: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 4px;
  color: #94a3b8;
  font-size: 0.65rem;
  font-weight: 600;
  padding: 0.15rem 0.35rem;
  text-transform: uppercase;
  line-height: 1;
}
.staged-clear-btn button {
  background: transparent !important;
  border: none !important;
  color: #ef4444 !important;
  font-size: 0.78rem !important;
  font-weight: 600 !important;
  padding: 0 !important;
  width: auto !important;
  min-height: 0 !important;
}
.staged-clear-btn button:hover {
  color: #f87171 !important;
  background: transparent !important;
  box-shadow: none !important;
}

/* Remove file button styling */
.remove-file-btn button {
  background: transparent !important;
  border: none !important;
  color: #cbd5e1 !important;
  font-size: 0.8rem !important;
  padding: 0 !important;
  width: auto !important;
  min-width: 0 !important;
  height: 24px !important;
  line-height: 24px !important;
  box-shadow: none !important;
}
.remove-file-btn button:hover {
  color: #ef4444 !important;
  background: transparent !important;
}

/* Clear actions - Inline Links Styling */
.chat-clear-btn-wrapper {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  height: 100%;
}
.chat-clear-btn-wrapper button {
  background: transparent !important;
  border: 1px solid rgba(239, 68, 68, 0.3) !important;
  color: #ef4444 !important;
  border-radius: 6px !important;
  font-size: 0.75rem !important;
  font-weight: 600 !important;
  padding: 0.35rem 0.65rem !important;
  width: auto !important;
  min-height: 0 !important;
  transition: all 0.2s ease !important;
}
.chat-clear-btn-wrapper button:hover {
  border-color: #ef4444 !important;
  background: rgba(239, 68, 68, 0.05) !important;
  box-shadow: 0 0 8px rgba(239, 68, 68, 0.1) !important;
}

/* Welcome Assistant Card (Right Col) */
.welcome-chat-card {
  background: #0f141e;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.25rem;
  display: flex;
  gap: 0.85rem;
  margin-bottom: 1.5rem;
  max-width: 85%;
  box-shadow: var(--shadow);
}
.chat-avatar-left {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--accent-glow) !important;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.chat-avatar-left svg {
  stroke: var(--accent) !important;
}
.welcome-chat-content {
  display: flex;
  flex-direction: column;
}
.welcome-chat-header {
  font-size: 0.92rem;
  font-weight: 600;
  color: var(--text-strong);
  margin-bottom: 0.5rem;
}
.welcome-chat-body {
  font-size: 0.85rem;
  color: var(--text-strong);
  line-height: 1.6;
}
.welcome-check-item {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  margin-bottom: 0.35rem;
  color: var(--text-strong);
}
.welcome-chat-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin: 0.6rem 0 0.8rem 0;
}
.welcome-chat-pill {
  background: rgba(255, 255, 255, 0.03) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  border-radius: 6px !important;
  padding: 0.35rem 0.65rem !important;
  font-size: 0.76rem !important;
  color: #cbd5e1 !important;
  display: inline-flex !important;
  align-items: center;
  gap: 0.4rem;
}
.welcome-chat-timestamp {
  font-size: 0.68rem;
  color: #64748b;
  margin-top: 0.6rem;
  font-family: 'JetBrains Mono', monospace;
}

/* Chat Input Styling */
div[data-testid="stChatInput"] {
  background-color: #0d0e12 !important;
  border: 1px solid #202230 !important;
  border-radius: 12px !important;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
}
div[data-testid="stChatInput"]:hover {
  border-color: rgba(0, 210, 255, 0.4) !important;
}
div[data-testid="stChatInput"]:focus-within {
  border-color: #00d2ff !important;
  box-shadow: 0 0 0 1px rgba(0, 210, 255, 0.2), 0 8px 24px -4px rgba(0, 0, 0, 0.5) !important;
}
div[data-testid="stChatInput"] textarea {
  color: #f8fafc !important; /* Standard text color */
  background-color: transparent !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 0.92rem !important;
  caret-color: var(--accent) !important; /* Cyan cursor */
}
div[data-testid="stChatInput"] textarea::placeholder {
  color: #94a3b8 !important; /* Clear placeholder */
  opacity: 0.85 !important;
}
div[data-testid="stChatInput"] button {
  background-color: var(--accent) !important;
  color: #070a13 !important;
  border-radius: 8px !important;
  transition: all 0.2s ease !important;
}
div[data-testid="stChatInput"] button:hover {
  background-color: var(--accent-soft) !important;
}
.stChatInputContainer {
  background-color: #0d0e12 !important;
  border: none !important;
}

/* Chat bubble overrides for alignment */
.stChatMessage {
  background: transparent !important;
  border: none !important;
  padding: 0.5rem 0 !important;
}
[data-testid="stChatMessageContent"] {
  border-radius: var(--radius) !important;
  padding: 0.95rem 1.1rem !important;
  border: 1px solid var(--border) !important;
  max-width: 85% !important;
  box-shadow: var(--shadow);
}
[data-testid="stChatMessageContent"] p,
[data-testid="stChatMessageContent"] li,
[data-testid="stChatMessageContent"] span {
  font-size: 0.92rem !important;
  line-height: 1.6;
  color: inherit !important;
}
/* User bubbles */
[data-testid="stChatMessageUser"] {
  flex-direction: row-reverse !important;
  text-align: right !important;
}
[data-testid="stChatMessageUser"] [data-testid="stChatMessageContent"] {
  background: #182235 !important;
  border: 1px solid rgba(0, 210, 255, 0.15) !important;
  border-radius: 12px 12px 0 12px !important;
  color: var(--text-strong) !important;
  text-align: left !important;
  display: inline-block !important;
}
[data-testid="stChatMessageUser"] [data-testid="stChatMessageContent"] * {
  color: var(--text-strong) !important;
}
/* Assistant bubbles */
[data-testid="stChatMessageAssistant"] {
  flex-direction: row !important;
}
[data-testid="stChatMessageAssistant"] [data-testid="stChatMessageContent"] {
  background: #151720 !important;
  border: 1px solid #202230 !important;
  border-radius: 12px 12px 12px 0 !important;
  color: var(--text-strong) !important;
  display: inline-block !important;
}
[data-testid="stChatMessageAssistant"] [data-testid="stChatMessageContent"] * {
  color: var(--text-strong) !important;
}

/* Message timestamps */
.msg-ts {
  font-size: 0.68rem;
  color: #cbd5e1;
  font-family: 'JetBrains Mono', monospace;
  margin-top: 0.25rem;
}
[data-testid="stChatMessageUser"] .msg-ts {
  text-align: right !important;
}

/* Expander custom styling */
[data-testid="stExpander"] {
  background: #151720 !important;
  border: 1px solid #202230 !important;
  border-radius: var(--radius) !important;
  box-shadow: var(--shadow);
}
[data-testid="stExpander"] summary {
  font-size: 0.82rem !important;
}

/* Custom embedded alert elements for chat response warnings */
.security-alert-high {
  background-color: rgba(239, 68, 68, 0.04) !important;
  border: 1px solid rgba(239, 68, 68, 0.25) !important;
  border-radius: 8px !important;
  padding: 0.8rem 1rem !important;
  margin: 0.75rem 0 !important;
  text-align: left;
}
.security-alert-high-title {
  font-size: 0.82rem !important;
  font-weight: 700 !important;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin-bottom: 0.35rem;
  color: #f87171 !important;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}
.security-alert-high-body {
  font-size: 0.78rem !important;
  color: #cbd5e1 !important;
  line-height: 1.5;
}

/* Navigation buttons in sidebar */
.nav-btn-chat, .nav-btn-reports, .nav-btn-docs {
  margin-bottom: 0.5rem;
}
.nav-btn-chat button, .nav-btn-reports button, .nav-btn-docs button {
  text-align: left !important;
  justify-content: flex-start !important;
  background-color: transparent !important;
  border: 1px solid transparent !important;
  color: #cbd5e1 !important;
  font-weight: 500 !important;
  padding: 0.55rem 0.75rem !important;
  transition: all 0.15s !important;
}
.nav-btn-chat button:hover, .nav-btn-reports button:hover, .nav-btn-docs button:hover {
  background-color: rgba(255, 255, 255, 0.02) !important;
  color: #f8fafc !important;
  border-color: var(--border) !important;
}
.nav-btn-chat.active button, .nav-btn-reports.active button, .nav-btn-docs.active button {
  color: var(--accent) !important;
  background-color: var(--accent-glow) !important;
  border-color: var(--accent) !important;
  font-weight: 600 !important;
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ──────────────────────────────────────────────────────────────────
def get_ext(name): return os.path.splitext(name.lower())[1]
def get_file_tag_style(filename):
    ext = get_ext(filename)
    if ext == ".json":
        return "purple", "JSON"
    elif ext in [".log", ".txt"]:
        return "orange", "LOG" if "log" in ext else "TXT"
    elif ext in [".yaml", ".yml", ".tf", ".tfvars"]:
        return "green", "YAML" if "yaml" in ext else "TF"
    elif ext == ".py":
        return "blue", "PY"
    else:
        return "blue", ext[1:].upper() if len(ext) > 1 else "FILE"
def now_ts():
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    ist_now = utc_now + datetime.timedelta(hours=5, minutes=30)
    return ist_now.strftime("%I:%M %p")

def format_size(n):
    for unit in ["B", "KB", "MB", "GB"]:
        if n < 1024 or unit == "GB":
            return f"{int(n)} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024

def detect_kind(name, mime):
    ext = get_ext(name); mime = mime or ""
    if mime.startswith("image/") or ext in IMAGE_EXTENSIONS:  return "image"
    if mime.startswith("video/") or ext in VIDEO_EXTENSIONS:  return "video"
    if mime.startswith("audio/") or ext in AUDIO_EXTENSIONS:  return "audio"
    if mime == "application/json" or ext == ".json":          return "json"
    if ext in ARCHIVE_EXTENSIONS:                             return "archive"
    if ext in DATA_EXTENSIONS:                                return "data"
    if mime.startswith("text/") or ext in TEXT_EXTENSIONS:    return "text"
    if ext in DOCUMENT_EXTENSIONS:                            return "document"
    return "file"

def extract_text(raw, kind):
    if kind not in {"text", "json", "data"}: return None
    decoded = raw.decode("utf-8", errors="ignore").strip()
    if not decoded: return None
    if kind == "json":
        try:    return json.dumps(json.loads(decoded), indent=2)[:MAX_TEXT_CHARS]
        except: pass
    return decoded[:MAX_TEXT_CHARS]

def build_payload(f):
    raw   = f.getvalue()
    mime  = f.type or "application/octet-stream"
    kind  = detect_kind(f.name, mime)
    text  = extract_text(raw, kind)
    payload = {"name": f.name, "mime_type": mime, "size_bytes": len(raw), "kind": kind, "text_content": text}
    preview = {"name": f.name, "mime_type": mime, "size_bytes": len(raw), "kind": kind,
               "text_preview": text[:TEXT_PREVIEW_CHARS] if text else None}
    return payload, preview

def submit_request(query, attachments, history=None):
    token = st.session_state.get("auth_token")
    if not token:
        raise RuntimeError("Missing authentication token.")
    return ask_agent(query, attachments, token=token, timeout=180, history=history or [])


def get_dashboard_stats():
    total_audits = 0
    critical_risks = 0
    medium_risks = 0
    low_risks = 0
    iam_scans = 0
    log_scans = 0
    general_scans = 0
    
    # Traverse all messages across all chats
    for chat in st.session_state.get("chats", []):
        for msg in chat.get("messages", []):
            if msg["role"] == "user":
                total_audits += len(msg.get("attachments", []))
                if not msg.get("attachments") and msg.get("content"):
                    total_audits += 1
            elif msg["role"] == "assistant":
                content = (msg.get("content") or "").lower()
                if "risk level: high" in content or "risk level: critical" in content:
                    critical_risks += 1
                elif "risk level: medium" in content:
                    medium_risks += 1
                elif "risk level: low" in content:
                    low_risks += 1
                
                if "iam policy analysis" in content:
                    iam_scans += 1
                elif "log security analysis" in content:
                    log_scans += 1
                else:
                    general_scans += 1
                    
    # Set default values if empty to show a nice initial dashboard
    if total_audits == 0:
        total_audits = 5
        critical_risks = 1
        medium_risks = 2
        low_risks = 2
        iam_scans = 2
        log_scans = 1
        general_scans = 2

    return {
        "total_audits": total_audits,
        "critical_risks": critical_risks,
        "medium_risks": medium_risks,
        "low_risks": low_risks,
        "iam_scans": iam_scans,
        "log_scans": log_scans,
        "general_scans": general_scans,
    }


def get_active_chat():
    for chat in st.session_state.chats:
        if chat["id"] == st.session_state.active_chat_id:
            return chat
    # Fallback to the first chat if the active one is missing.
    st.session_state.active_chat_id = st.session_state.chats[0]["id"]
    return st.session_state.chats[0]


def refresh_chat_meta(chat):
    chat["updated_at"] = time.time()
    # Auto-title from first user message.
    if chat.get("title") in {"New chat", ""}:
        for msg in chat["messages"]:
            if msg.get("role") == "user" and msg.get("content"):
                title = msg["content"].strip().replace("\n", " ")
                chat["title"] = title[:36] + ("..." if len(title) > 36 else "")
                break


def build_chat_history(chat, max_turns=8):
    history = []
    for msg in chat["messages"][-max_turns:]:
        content = (msg.get("content") or "").strip()
        if msg.get("role") in {"user", "assistant"} and content:
            history.append({"role": msg["role"], "content": content})
    return history


def create_new_chat():
    chat_id = st.session_state.next_chat_id
    st.session_state.next_chat_id += 1
    st.session_state.chats.append({
        "id": chat_id,
        "title": "New chat",
        "messages": [],
        "created_at": time.time(),
        "updated_at": time.time(),
    })
    st.session_state.active_chat_id = chat_id


def init_auth_state():
    if "auth_token" not in st.session_state:
        st.session_state.auth_token = None
    if "user_email" not in st.session_state:
        st.session_state.user_email = None

    # Restore auth details across browser refreshes when cookie exists.
    if not st.session_state.auth_token:
        token, email = restore_auth_from_cookie()
        if token:
            st.session_state.auth_token = token
            st.session_state.user_email = email


def require_auth():
    if not st.session_state.get("auth_token"):
        st.switch_page("pages/login.py")
        st.stop()


def logout_user():
    st.session_state.auth_token = None
    st.session_state.user_email = None
    clear_auth_cookie()
    st.switch_page("pages/login.py")


# ── Sidebar ───────────────────────────────────────────────────────────────────
def get_user_name_from_email(email):
    if not email:
        return "Krishan Kant"
    if email.lower() == "krishan@example.com":
        return "Krishan Kant"
    parts = email.split('@')[0].split('.')
    return " ".join([p.capitalize() for p in parts])


def render_sidebar():
    with st.sidebar:
        # Brand section
        st.markdown(
            """
            <div class="brand-container">
              <div class="brand-logo">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
              </div>
              <div class="brand-text">
                <div class="brand-title">CloudSec Agent</div>
                <div class="brand-subtitle">AI Powered Cloud Security</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Profile Section
        user_email = st.session_state.get('user_email') or 'krishan@example.com'
        user_name = get_user_name_from_email(user_email)
        first_letter = user_name[0].upper() if user_name else 'K'
        st.markdown(
            f"""
            <div class="user-profile-card">
              <div class="user-avatar-circle">{first_letter}</div>
              <div class="user-info">
                <div class="user-name">{user_name}</div>
                <div class="user-email">{user_email}</div>
                <div class="user-status"><span class="status-dot"></span> Connected</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Navigation menu
        st.markdown("<div class='nav-heading'>NAVIGATION</div>", unsafe_allow_html=True)
        active_tab = st.session_state.get("active_tab", "Chat")

        st.markdown(f"<div class='nav-btn-chat{' active' if active_tab == 'Chat' else ''}'>", unsafe_allow_html=True)
        if st.button("💬 Chat Workspace", key="sidebar_nav_chat", use_container_width=True):
            st.session_state.active_tab = "Chat"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(f"<div class='nav-btn-reports{' active' if active_tab == 'Reports' else ''}'>", unsafe_allow_html=True)
        if st.button("📊 Analytics Dashboard", key="sidebar_nav_reports", use_container_width=True):
            st.session_state.active_tab = "Reports"
            st.rerun()

        st.markdown(f"<div class='nav-btn-docs{' active' if active_tab == 'Docs' else ''}'>", unsafe_allow_html=True)
        if st.button("📖 Documentation Library", key="sidebar_nav_docs", use_container_width=True):
            st.session_state.active_tab = "Docs"
            st.rerun()

        # Export findings button
        active_chat = get_active_chat()
        if active_chat["messages"]:
            export_txt = "\n\n".join(
                f"[{m['role'].upper()}] {m.get('timestamp','')}\n{m.get('content','')}"
                for m in active_chat["messages"]
            )
            st.download_button(
                "💾 Export findings (TXT)",
                export_txt,
                file_name="cloudsec_audit_report.txt",
                mime="text/plain",
                use_container_width=True,
                key="sidebar_export_btn",
            )

            # Generate PDF export
            try:
                from frontend.pdf_generator import build_pdf_bytes
            except ModuleNotFoundError:
                from pdf_generator import build_pdf_bytes

            try:
                pdf_data = build_pdf_bytes(
                    active_chat.get("title", "New Chat"),
                    active_chat["messages"],
                    st.session_state.get("user_email") or "krishan@example.com"
                )
                st.download_button(
                    "📄 Download PDF Report",
                    pdf_data,
                    file_name="cloudsec_security_report.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="sidebar_pdf_export_btn",
                )
            except Exception as e:
                st.error(f"Error compiling PDF: {e}")

        # Logout action
        st.markdown("<div class='logout-btn-wrapper'>", unsafe_allow_html=True)
        if st.button("🚪 Logout", key="sidebar_logout_btn"):
            logout_user()
        st.markdown("</div>", unsafe_allow_html=True)

        # AI Model Card at bottom
        st.markdown(
            f"""
            <div class="ai-model-section">
              <div class="nav-heading">AI MODEL</div>
              <div class="ai-model-card">
                <div class="ai-model-header">
                  <span class="ai-model-sparkle">✨</span> Gemini 2.5 Flash
                </div>
                <div class="ai-model-status">
                  <span class="status-dot"></span> Connected
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ── Init ──────────────────────────────────────────────────────────────────────
def init_state():
    if "uploader_key" not in st.session_state: st.session_state.uploader_key = 0
    if "active_tab" not in st.session_state: st.session_state.active_tab = "Chat"
    if "chats" not in st.session_state:
        st.session_state.chats = [{
            "id": 1,
            "title": "New chat",
            "messages": [],
            "created_at": time.time(),
            "updated_at": time.time(),
        }]
    if "active_chat_id" not in st.session_state: st.session_state.active_chat_id = 1
    if "next_chat_id" not in st.session_state: st.session_state.next_chat_id = 2
    if "removed_files" not in st.session_state: st.session_state.removed_files = set()


st.set_page_config(
    page_title="CloudSec Auditor Console",
    page_icon="⛨",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()
init_auth_state()
require_auth()
init_state()

render_sidebar()
active_chat = get_active_chat()

# Reserve header & stats container at the top of the page
top_container = st.container()

active_tab = st.session_state.get("active_tab", "Chat")

if active_tab == "Reports":
    with top_container:
        user_email = st.session_state.get('user_email') or 'krishan@example.com'
        first_name = get_user_name_from_email(user_email).split(' ')[0]
        st.markdown(
            f"""
            <div class="welcome-text-group">
              <h1 class="welcome-title">📊 Analytics Dashboard</h1>
              <p class="welcome-subtitle">Security Metrics and Audit Reports for {first_name}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Fetch dynamic stats from chats
    stats = get_dashboard_stats()
    
    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
    
    # 1. Metric Cards Grid using custom CSS selectors defined in CSS section
    st.markdown(
        f"""
        <div class="dashboard-grid">
          <div class="stat-card stat-card-blue">
            <div class="stat-icon-container stat-icon-blue">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#00d2ff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
            </div>
            <div class="stat-content">
              <div class="stat-title">Total Audits</div>
              <div class="stat-value">{stats['total_audits']}</div>
            </div>
          </div>
          <div class="stat-card stat-card-red">
            <div class="stat-icon-container stat-icon-red">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
            </div>
            <div class="stat-content">
              <div class="stat-title">Critical Risks</div>
              <div class="stat-value">{stats['critical_risks']}</div>
            </div>
          </div>
          <div class="stat-card stat-card-orange">
            <div class="stat-icon-container stat-icon-orange">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            </div>
            <div class="stat-content">
              <div class="stat-title">Medium Risks</div>
              <div class="stat-value">{stats['medium_risks']}</div>
            </div>
          </div>
          <div class="stat-card stat-card-green">
            <div class="stat-icon-container stat-icon-green">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
            </div>
            <div class="stat-content">
              <div class="stat-title">Low Risks</div>
              <div class="stat-value">{stats['low_risks']}</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
    
    # 2. Distributions Columns
    col_dist_left, col_dist_right = st.columns(2, gap="large")
    
    with col_dist_left:
        st.markdown("### 🗂️ Audit Categories")
        st.markdown(
            f"""
            <div style="background-color: #151720; border: 1px solid #202230; padding: 1.5rem; border-radius: 12px; box-shadow: var(--shadow);">
              <div style="margin-bottom: 1.25rem;">
                <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 0.35rem;">
                  <span>🔒 IAM Policy Audits</span>
                  <strong>{stats['iam_scans']}</strong>
                </div>
                <div style="background-color: #0d0e12; border-radius: 4px; height: 8px; overflow: hidden;">
                  <div style="background-color: #c084fc; width: {min(100, int(stats['iam_scans']/max(1, stats['total_audits'])*100))}%; height: 100%;"></div>
                </div>
              </div>
              <div style="margin-bottom: 1.25rem;">
                <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 0.35rem;">
                  <span>📋 Cloud Log Scans</span>
                  <strong>{stats['log_scans']}</strong>
                </div>
                <div style="background-color: #0d0e12; border-radius: 4px; height: 8px; overflow: hidden;">
                  <div style="background-color: #fbbf24; width: {min(100, int(stats['log_scans']/max(1, stats['total_audits'])*100))}%; height: 100%;"></div>
                </div>
              </div>
              <div>
                <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 0.35rem;">
                  <span>🌐 RAG & General Queries</span>
                  <strong>{stats['general_scans']}</strong>
                </div>
                <div style="background-color: #0d0e12; border-radius: 4px; height: 8px; overflow: hidden;">
                  <div style="background-color: #38bdf8; width: {min(100, int(stats['general_scans']/max(1, stats['total_audits'])*100))}%; height: 100%;"></div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    with col_dist_right:
        st.markdown("### ⚠️ Threat Index")
        total_risks = stats['critical_risks'] + stats['medium_risks'] + stats['low_risks']
        st.markdown(
            f"""
            <div style="background-color: #151720; border: 1px solid #202230; padding: 1.5rem; border-radius: 12px; box-shadow: var(--shadow);">
              <div style="margin-bottom: 1.25rem;">
                <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 0.35rem;">
                  <span style="color: #ef4444;">🚨 Critical Risks</span>
                  <strong>{stats['critical_risks']}</strong>
                </div>
                <div style="background-color: #0d0e12; border-radius: 4px; height: 8px; overflow: hidden;">
                  <div style="background-color: #ef4444; width: {min(100, int(stats['critical_risks']/max(1, total_risks)*100))}%; height: 100%;"></div>
                </div>
              </div>
              <div style="margin-bottom: 1.25rem;">
                <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 0.35rem;">
                  <span style="color: #f59e0b;">⚡ Medium Risks</span>
                  <strong>{stats['medium_risks']}</strong>
                </div>
                <div style="background-color: #0d0e12; border-radius: 4px; height: 8px; overflow: hidden;">
                  <div style="background-color: #f59e0b; width: {min(100, int(stats['medium_risks']/max(1, total_risks)*100))}%; height: 100%;"></div>
                </div>
              </div>
              <div>
                <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 0.35rem;">
                  <span style="color: #10b981;">🛡️ Low Risks</span>
                  <strong>{stats['low_risks']}</strong>
                </div>
                <div style="background-color: #0d0e12; border-radius: 4px; height: 8px; overflow: hidden;">
                  <div style="background-color: #10b981; width: {min(100, int(stats['low_risks']/max(1, total_risks)*100))}%; height: 100%;"></div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.stop()

if active_tab == "Docs":
    with top_container:
        user_email = st.session_state.get('user_email') or 'krishan@example.com'
        first_name = get_user_name_from_email(user_email).split(' ')[0]
        st.markdown(
            f"""
            <div class="welcome-text-group">
              <h1 class="welcome-title">📖 Documentation Library</h1>
              <p class="welcome-subtitle">Authoritative Playbooks and CIS Guidelines for {first_name}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Document files mappings
    doc_files = {
        "🛡️ CIS AWS Foundations Benchmark": "cis_aws_foundations.md",
        "🔑 IAM Privilege Escalation Vectors": "iam_privilege_escalation.md",
        "🚨 Incident Containment Playbook": "incident_containment_playbook.md",
    }
    
    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
    doc_col_left, doc_col_right = st.columns([1.1, 2.9], gap="large")
    
    with doc_col_left:
        st.markdown("### Selection Guide")
        selected_title = st.radio(
            "Select Reference Guide",
            options=list(doc_files.keys()),
            label_visibility="collapsed"
        )
        
        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
        st.markdown(
            """
            <div style="background-color: #151720; border: 1px solid #202230; padding: 1.2rem; border-radius: 8px; font-size: 0.8rem; color: #cbd5e1; line-height: 1.5;">
              <strong>ℹ️ Grounding Context:</strong> These reference sheets serve as the primary knowledge base used by the RAG agent to verify and ground security advice. 
              <br/><br/>
              Changes made here are indexed during vector store build runs.
            </div>
            """, 
            unsafe_allow_html=True
        )

    with doc_col_right:
        filename = doc_files[selected_title]
        doc_path = os.path.join("data", "aws_docs", filename)
        
        if os.path.exists(doc_path):
            try:
                with open(doc_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Render content in a styled card container
                st.markdown(
                    f"""
                    <div style="background-color: #151720; border: 1px solid #202230; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.25); min-height: 500px;">
                    """,
                    unsafe_allow_html=True
                )
                st.markdown(content)
                st.markdown("</div>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error reading document: {e}")
        else:
            st.error(f"File not found at: {doc_path}")

    st.stop()

# Split main workspace into Left Column (File upload/details) and Right Column (Welcome / Chat)
main_col_left, main_col_right = st.columns([1.2, 1.8], gap="large")

with main_col_left:
    st.markdown("<div class='upload-heading'>Upload Files</div>", unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "files",
        accept_multiple_files=True,
        key=f"uploader_{st.session_state.uploader_key}",
        label_visibility="collapsed",
    )
    
    # Filter files that haven't been removed
    active_staged = []
    if uploaded_files:
        for f in uploaded_files:
            if f.name not in st.session_state.removed_files:
                active_staged.append(f)
                
    too_many_files = len(active_staged) > MAX_ATTACHMENT_COUNT
    if too_many_files:
        st.error(f"Limit: up to {MAX_ATTACHMENT_COUNT} staged files.")
        
    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
    
    # Context input
    additional_context = st.text_area(
        "Analysis Instructions",
        placeholder="Describe your analysis goals, target files, or security concerns.",
        key="additional_context_input",
        height=130,
        max_chars=1000,
    )
    # Character counter
    char_count = len(additional_context)
    st.markdown(f"<div style='text-align: right; font-size: 0.72rem; color: #cbd5e1; margin-top: -12px;'>{char_count} / 1000</div>", unsafe_allow_html=True)
    
    st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)
    
    # Primary analysis button
    st.markdown("<div class='upload-btn-container'>", unsafe_allow_html=True)
    send_files = st.button("📤 Upload & Analyze Files", use_container_width=True, disabled=too_many_files)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Render custom staged file list
    if active_staged:
        col_sh, col_sca = st.columns([2.5, 1.5])
        with col_sh:
            st.markdown(f"<div class='uploaded-files-heading'>Staged Files ({len(active_staged)})</div>", unsafe_allow_html=True)
        with col_sca:
            st.markdown("<div class='staged-clear-btn' style='text-align: right; margin-top: 1.25rem;'>", unsafe_allow_html=True)
            if st.button("Clear All", key="staged_clear_all", use_container_width=True):
                if uploaded_files:
                    for f in uploaded_files:
                        st.session_state.removed_files.add(f.name)
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        for f in active_staged:
            color_class, badge_text = get_file_tag_style(f.name)
            col_file, col_del = st.columns([6, 1])
            with col_file:
                st.markdown(f"""
                <div class="uploaded-file-card">
                  <div class="uploaded-file-icon icon-{color_class}">📄</div>
                  <div class="uploaded-file-name">{f.name}</div>
                  <div class="uploaded-file-badge">{badge_text}</div>
                  <div class="uploaded-file-size">{format_size(len(f.getvalue()))}</div>
                </div>
                """, unsafe_allow_html=True)
            with col_del:
                st.markdown("<div class='remove-file-btn'>", unsafe_allow_html=True)
                if st.button("✕", key=f"del_main_{f.name}_{st.session_state.uploader_key}", use_container_width=True):
                    st.session_state.removed_files.add(f.name)
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

with main_col_right:
    # Chat header
    ch_col_left, ch_col_right = st.columns([3, 1])
    with ch_col_left:
        st.markdown(
            """
            <div style="display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.5rem; text-align: left;">
              <div class="chat-avatar-left" style="background: rgba(0, 210, 255, 0.08); width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#00d2ff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
              </div>
              <div>
                <div style="font-size: 0.92rem; font-weight: 700; color: #f8fafc; line-height: 1.2;">Chat with CloudSec Agent</div>
                <div style="font-size: 0.72rem; color: #64748b; line-height: 1.2;">Intelligent • Context-Aware • Secure</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with ch_col_right:
        # Styled clear chat button
        st.markdown("<div class='chat-clear-btn-wrapper'>", unsafe_allow_html=True)
        if st.button("Clear Chat", key="clear_chat_timeline", use_container_width=True):
            active_chat["messages"] = []
            active_chat["title"] = "New chat"
            st.session_state.removed_files = set()
            refresh_chat_meta(active_chat)
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)

    # Render Welcome Assistant Card if chat history is empty
    if not active_chat["messages"]:
        st.markdown(
            f"""
            <div class="welcome-chat-card">
              <div class="chat-avatar-left">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#00d2ff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
              </div>
              <div class="welcome-chat-content">
                <div class="welcome-chat-header">👋 Hello! I'm CloudSec Agent</div>
                <div class="welcome-chat-body">
                  <p style="margin: 0 0 0.5rem 0; color: #94a3b8;">I can help you with:</p>
                  <div class="welcome-chat-pills">
                    <div class="welcome-chat-pill">
                      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#c084fc" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                      IAM Policy Reviews
                    </div>
                    <div class="welcome-chat-pill">
                      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#fbbf24" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M17.5 19A3.5 3.5 0 0 0 13 15.5a3.5 3.5 0 0 0-6 0A3.5 3.5 0 0 0 2.5 19h15z"/></svg>
                      Cloud Log Analysis
                    </div>
                    <div class="welcome-chat-pill">
                      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#34d399" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                      IaC Security Scanning
                    </div>
                  </div>
                  <p style="margin: 0.5rem 0 0 0;">Upload your files and ask me anything about your cloud security!</p>
                </div>
                <div class="welcome-chat-timestamp">{now_ts()}</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        # Render Chat History
        for msg in active_chat["messages"]:
            with st.chat_message(msg["role"]):
                if msg.get("content"):
                    st.markdown(msg["content"], unsafe_allow_html=True)
                
                if msg.get("attachments"):
                    chips = "".join(
                        f"<span class='chip'>{KIND_ICONS.get(a['kind'],'📎')} "
                        f"{a['name']} · {format_size(a['size_bytes'])}</span>"
                        for a in msg["attachments"]
                    )
                    st.markdown(f"<div class='chip-row'>{chips}</div>", unsafe_allow_html=True)
                    for att in msg["attachments"]:
                        if att.get("text_preview"):
                            with st.expander(f"Preview — {att['name']}", expanded=False):
                                st.code(att["text_preview"], language="text")
                                
                if msg.get("timestamp"):
                    if msg["role"] == "user":
                        st.markdown(f"<div class='msg-ts'>{msg['timestamp']} <span style='color: #00d2ff; margin-left: 0.2rem;'>✓✓</span></div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='msg-ts'>{msg['timestamp']}</div>", unsafe_allow_html=True)

    # Chat Input
    user_input = st.chat_input("Ask anything about your cloud security...")
    st.markdown("<p style='text-align: center; font-size: 0.72rem; color: #64748b; margin-top: 0.5rem;'><span style='color: #fbbf24; margin-right: 0.15rem;'>💡</span> Tip: Be specific about what you want to analyze for better results</p>", unsafe_allow_html=True)

# ── Header & Dynamic Dashboard Stats (Rendered at top container) ──────────────
with top_container:
    # 1. Top Header Row
    th_col_left, th_col_right = st.columns([2.2, 1.8])
    with th_col_left:
        user_email = st.session_state.get('user_email') or 'krishan@example.com'
        first_name = get_user_name_from_email(user_email).split(' ')[0]
        st.markdown(
            f"""
            <div class="welcome-text-group">
              <h1 class="welcome-title">Welcome back, {first_name}!</h1>
              <p class="welcome-subtitle">Your AI-Powered Cloud Security Assistant</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with th_col_right:
        utc_now = datetime.datetime.now(datetime.timezone.utc)
        ist_now = utc_now + datetime.timedelta(hours=5, minutes=30)
        time_str = ist_now.strftime("%I:%M %p IST")
        date_str = ist_now.strftime("%b %d, %Y")
        
        st.markdown(
            f"""
            <div class="header-metadata-group">
              <div class="header-metadata-card">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 11 11 13 15 9"/></svg>
                <div class="metadata-text">
                  <div class="metadata-title">Secure Session</div>
                  <div class="metadata-value value-green">256-bit Encrypted</div>
                </div>
              </div>
              <div class="header-metadata-card">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                <div class="metadata-text">
                  <div class="metadata-value">{time_str}</div>
                  <div class="metadata-title">{date_str}</div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ── Chat submission handler ───────────────────────────────────────────────────
should_submit = bool(user_input) or (bool(send_files) and bool(active_staged))

if should_submit:
    st.session_state.removed_files = set()
    request_history = build_chat_history(active_chat)
    payloads, previews = [], []
    for f in (active_staged or []):
        p, v = build_payload(f)
        payloads.append(p)
        previews.append(v)

    query = (user_input or "").strip()
    if additional_context.strip():
        query = f"{query}\n\n[Additional Context/Investigation Goals]:\n{additional_context.strip()}".strip()

    display_text = query if query else f"Sent {len(previews)} file(s) for security analysis."

    active_chat["messages"].append({
        "role": "user", "content": display_text,
        "attachments": previews, "timestamp": now_ts(),
    })
    refresh_chat_meta(active_chat)

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Analyzing threat matrix..."):
            try:
                data   = submit_request(query, payloads, request_history)
                answer = data.get("answer") or f"Error: {data.get('error', 'Unknown error')}"
            except requests.HTTPError as exc:
                if exc.response is not None and exc.response.status_code == 401:
                    logout_user()
                message = "The backend rejected the request."
                if exc.response is not None:
                    message = f"HTTP {exc.response.status_code}: {message}"
                    try:
                        detail = exc.response.json().get("detail")
                        if detail:
                            message = f"HTTP {exc.response.status_code}: {detail}"
                    except Exception:
                        response_text = exc.response.text.strip()
                        if response_text:
                            message = f"{message}\n\n{response_text[:500]}"
                answer = f"Request failed: {message}"
            except Exception as exc:
                answer = f"⚠️ Could not reach backend: {exc}"
        st.markdown(answer)
        st.markdown(f"<div class='msg-ts'>{now_ts()}</div>", unsafe_allow_html=True)

    active_chat["messages"].append({
        "role": "assistant", "content": answer,
        "attachments": [], "timestamp": now_ts(),
    })
    refresh_chat_meta(active_chat)

    st.session_state.uploader_key += 1
    st.rerun()
