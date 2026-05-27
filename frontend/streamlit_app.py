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

QUICK_ACTIONS = [
    {"icon": "🔍", "label": "Audit IAM Policy",    "prompt": "Analyze this IAM policy for privilege escalation risks and least-privilege violations."},
    {"icon": "📋", "label": "Review Cloud Logs",   "prompt": "Review this cloud log and flag anything suspicious — unusual IPs, privilege changes, or data exfiltration patterns."},
    {"icon": "⚙️",  "label": "Scan IaC File",      "prompt": "Scan this Terraform / CloudFormation file for infrastructure-as-code security misconfigurations."},
    {"icon": "🛡️", "label": "IAM Best Practices", "prompt": "Summarize AWS IAM best practices with actionable hardening steps."},
]

KIND_ICONS = {
    "image": "🖼️", "video": "🎬", "audio": "🎵", "text": "📄",
    "json": "📦", "document": "📑", "archive": "🗜️", "data": "📊", "file": "📎",
}


# ── CSS ──────────────────────────────────────────────────────────────────────
def inject_css():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  --bg:        #f8fafc;
  --surface:   #f1f5f9;
  --surface2:  #e2e8f0;
  --border:    rgba(15,23,42,0.10);
  --border2:   rgba(15,23,42,0.15);
  --text:      #1e293b;
  --text-strong:#0f172a;
  --muted:     #64748b;
  --accent:    #1e61f7;
  --accent-soft:#1e61f7;
  --accent-dim:rgba(30,97,247,0.12);
  --code-bg:   rgba(15,23,42,0.06);
  --chat-input-bg: rgba(248,250,252,0.96);
  --success:   #16a34a;
  --radius:    12px;
}

* { box-sizing: border-box; }

.stApp {
  background: var(--bg);
  color: var(--text);
  font-family: 'Inter', sans-serif;
}

[data-testid="stHeader"]   { background: transparent; }
.main .block-container     { padding-top: 2rem; padding-bottom: 4rem; max-width: 820px; }

#MainMenu,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
footer {
  display: none !important;
  visibility: hidden !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
  background: var(--surface);
  border-right: 1px solid var(--border);
}
[data-testid="stSidebarNav"] {
  display: none !important;
}
[data-testid="stSidebar"] *           { color: var(--text) !important; }
[data-testid="stSidebarUserContent"]  { padding-top: 0.25rem; }

/* ── Hero (shown only on empty state) ── */
.hero {
  text-align: center;
  padding: 3.5rem 1rem 2.2rem;
  animation: fadeUp 0.4s ease-out;
}
.hero-icon  { font-size: 2.2rem; display: block; margin-bottom: 0.8rem; }
.hero-title {
  font-size: 1.75rem; font-weight: 600;
  color: var(--text); letter-spacing: -0.03em;
  margin: 0 0 0.5rem;
}
.hero-sub {
  font-size: 0.92rem; color: var(--muted);
  line-height: 1.65; max-width: 720px;
  margin: 0 auto 0.5rem; font-weight: 400;
  text-align: center;
}
.live-badge {
  display: inline-flex; align-items: center; gap: 0.4rem;
  padding: 0.26rem 0.65rem; border-radius: 999px;
  background: rgba(63,185,80,0.08);
  border: 1px solid rgba(63,185,80,0.18);
  color: var(--success); font-size: 0.7rem;
  font-family: 'JetBrains Mono', monospace;
  margin-bottom: 1.4rem;
}
.live-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--success);
  animation: pulse 2s ease-in-out infinite;
}

/* ── Quick actions grid ── */
.qa-wrap {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.5rem;
  max-width: 500px;
  margin: 0 auto;
  animation: fadeUp 0.45s ease-out 0.07s both;
}

/* ── Divider label ── */
.or-divider {
  display: flex; align-items: center; gap: 0.7rem;
  margin: 1.5rem 0 0.6rem;
  color: var(--muted); font-size: 0.71rem;
  font-family: 'JetBrains Mono', monospace;
  text-transform: uppercase; letter-spacing: 0.08em;
}
.or-divider::before, .or-divider::after {
  content: ''; flex: 1; height: 1px; background: var(--border);
}

/* ── Chat messages ── */
.stChatMessage {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0.15rem 0 !important;
}
[data-testid="stChatMessageContent"] p,
[data-testid="stChatMessageContent"] li,
[data-testid="stChatMessageContent"] span { color: var(--text) !important; font-size: 0.95rem; line-height: 1.7; }
[data-testid="stChatMessageContent"] code {
  font-family: 'JetBrains Mono', monospace !important;
  background: var(--code-bg) !important;
  color: var(--accent-soft) !important;
  padding: 0.15em 0.38em; border-radius: 5px;
}
[data-testid="stChatMessageContent"] pre {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
}

/* ── Chat input ── */
.stChatInputContainer {
  background: var(--chat-input-bg) !important;
  border-top: 1px solid var(--border) !important;
  backdrop-filter: blur(10px);
}
.stChatInput > div {
  background: var(--surface) !important;
  border: 1px solid var(--border2) !important;
  border-radius: 14px !important;
  box-shadow: 0 0 0 3px rgba(47,129,247,0.05) !important;
}
.stChatInput textarea { color: var(--text) !important; font-size: 0.94rem !important; }
.stChatInput button   { background: var(--accent) !important; border: none !important; border-radius: 10px !important; }

/* ── Buttons ── */
.stButton > button {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  color: var(--text) !important;
  font-size: 0.83rem !important;
  font-weight: 500 !important;
  transition: all 0.18s !important;
}
.stButton > button:hover {
  border-color: var(--border2) !important;
  background: var(--surface2) !important;
}

/* ── File chips ── */
.chip-row { display: flex; flex-wrap: wrap; gap: 0.35rem; margin-top: 0.4rem; }
.chip {
  display: inline-flex; align-items: center; gap: 0.3rem;
  padding: 0.26rem 0.58rem; border-radius: 999px;
  background: var(--accent-dim);
  border: 1px solid color-mix(in srgb, var(--accent) 28%, transparent);
  color: var(--accent-soft); font-size: 0.74rem;
  font-family: 'JetBrains Mono', monospace;
}

/* ── Timestamp ── */
.msg-ts { font-size: 0.68rem; color: var(--muted); font-family: 'JetBrains Mono', monospace; margin-top: 0.2rem; }

/* ── Sidebar model badge ── */
.model-badge {
  display: flex; align-items: center; gap: 0.5rem;
  padding: 0.5rem 0.75rem; border-radius: var(--radius);
  background: var(--accent-dim);
  border: 1px solid color-mix(in srgb, var(--accent) 24%, transparent);
  font-size: 0.78rem; font-family: 'JetBrains Mono', monospace;
  color: var(--accent-soft); margin-bottom: 0.7rem;
}

.signed-card {
  padding: 0.75rem 0.85rem;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: color-mix(in srgb, var(--surface) 80%, transparent);
  margin-bottom: 0.9rem;
}

.signed-label {
  font-size: 0.72rem;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.signed-value {
  font-size: 0.9rem;
  color: var(--text-strong);
  margin-top: 0.25rem;
  word-break: break-word;
}

.brand-title {
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--text-strong);
}

.brand-subtitle {
  font-size: 0.7rem;
  color: var(--muted);
  margin-top: 0.1rem;
  font-family: 'JetBrains Mono', monospace;
}

.upload-title {
  font-size: 0.77rem;
  color: var(--muted);
  margin-bottom: 0.4rem;
}

/* ── Expander ── */
[data-testid="stExpander"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
}
[data-testid="stExpander"] summary { font-size: 0.82rem !important; }

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.3; }
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ──────────────────────────────────────────────────────────────────
def get_ext(name): return os.path.splitext(name.lower())[1]
def now_ts():      return datetime.datetime.now().strftime("%H:%M")

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
def render_sidebar():
    with st.sidebar:
        st.markdown(
            f"""
            <div class='signed-card'>
              <div class='signed-label'>Signed in as</div>
              <div class='signed-value'>{st.session_state.get('user_email') or 'Unknown'}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("Logout", use_container_width=True):
            logout_user()

        # Brand
        st.markdown("""
        <div style="margin-bottom:1.1rem;">
          <div class="brand-title">⛨ CloudSec Agent</div>
          <div class="brand-subtitle">RAG-Powered · Cloud Security</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f'<div class="model-badge">🤖 &nbsp;{MODEL_LABEL}</div>', unsafe_allow_html=True)
        st.divider()

        # Upload
        st.markdown(
            "<div class='upload-title'>📎 Attach Files</div>",
            unsafe_allow_html=True,
        )

        uploaded_files = st.file_uploader(
            "files",
            accept_multiple_files=True,
            key=f"uploader_{st.session_state.uploader_key}",
            label_visibility="collapsed",
        )
        too_many_files = bool(uploaded_files) and len(uploaded_files) > MAX_ATTACHMENT_COUNT
        if too_many_files:
            st.error(f"Attach up to {MAX_ATTACHMENT_COUNT} files per request.")

    # Previews for staged files
        if uploaded_files:
            for f in uploaded_files:
                raw = f.getvalue()
                kind = detect_kind(f.name, f.type or "")
                icon = KIND_ICONS.get(kind, "📎")
                label = f"{icon} {f.name[:24]}{'…' if len(f.name) > 24 else ''}"
                with st.expander(label, expanded=False):
                    if kind == "image":
                        st.image(raw, use_container_width=True)
                    elif kind == "video":
                        st.video(raw)
                    elif kind == "audio":
                        st.audio(raw)
                    elif kind in {"text", "json", "data"}:
                        txt = extract_text(raw, kind) or ""
                        if txt:
                            st.code(txt[:400], language="text")
                    else:
                        st.caption(f.type or "Binary file")

        c1, c2 = st.columns(2)
        with c1:
            send_files = st.button("Send Files", use_container_width=True, disabled=not uploaded_files or too_many_files)
        with c2:
            clear_chat = st.button("Clear Chat", use_container_width=True)

    # Export (only when there's history)
        active_chat = get_active_chat()
        if active_chat["messages"]:
            st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)
            export_txt = "\n\n".join(
                f"[{m['role'].upper()}] {m.get('timestamp','')}\n{m.get('content','')}"
                for m in active_chat["messages"]
            )
            st.download_button(
                "💾 Export Chat",
                export_txt,
                file_name="cloudsec_chat.txt",
                mime="text/plain",
                use_container_width=True,
            )

        st.divider()

        return uploaded_files, send_files, clear_chat


# ── Init ──────────────────────────────────────────────────────────────────────
def init_state():
    if "uploader_key" not in st.session_state: st.session_state.uploader_key = 0
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


st.set_page_config(
    page_title="CloudSec Agent",
    page_icon="⛨",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()
init_auth_state()
require_auth()
init_state()

uploaded_files, send_files, clear_chat = render_sidebar()
active_chat = get_active_chat()

if clear_chat:
    active_chat["messages"] = []
    active_chat["title"] = "New chat"
    refresh_chat_meta(active_chat)
    st.rerun()

# ── Empty state: hero + quick actions ────────────────────────────────────────
quick_prompt = None

if not active_chat["messages"]:
    st.markdown(f"""
    <div class="hero">
      <span class="hero-icon">⛨</span>
      <div class="live-badge"><span class="live-dot"></span>&nbsp; Connected · {MODEL_LABEL}</div>
      <h1 class="hero-title">What can I help you secure?</h1>
    </div>
    """, unsafe_allow_html=True)

    # 2-column quick action buttons, centered
    _, left, right, _ = st.columns([1, 2, 2, 1])
    for i, qa in enumerate(QUICK_ACTIONS):
        col = left if i % 2 == 0 else right
        with col:
            if st.button(f"{qa['icon']}  {qa['label']}", key=f"qa_{i}", use_container_width=True):
                quick_prompt = qa["prompt"]

    st.markdown('<div class="or-divider">or type a message below</div>', unsafe_allow_html=True)

# ── Active chat ───────────────────────────────────────────────────────────────
else:
    for msg in active_chat["messages"]:
        avatar = "🧑‍💻" if msg["role"] == "user" else "🤖"
        with st.chat_message(msg["role"], avatar=avatar):
            if msg.get("content"):
                st.markdown(msg["content"])

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
                st.markdown(f"<div class='msg-ts'>{msg['timestamp']}</div>", unsafe_allow_html=True)

# ── Input & submission ────────────────────────────────────────────────────────
user_input    = st.chat_input("Message CloudSec Agent…")
should_submit = bool(user_input) or bool(quick_prompt) or (bool(send_files) and bool(uploaded_files))

if should_submit:
    request_history = build_chat_history(active_chat)
    payloads, previews = [], []
    for f in (uploaded_files or []):
        p, v = build_payload(f)
        payloads.append(p)
        previews.append(v)

    query        = user_input or quick_prompt or ""
    display_text = query if query else f"Sent {len(previews)} file(s) for analysis."

    active_chat["messages"].append({
        "role": "user", "content": display_text,
        "attachments": previews, "timestamp": now_ts(),
    })
    refresh_chat_meta(active_chat)

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Thinking…"):
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
