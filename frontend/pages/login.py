import requests
import streamlit as st

try:
    from frontend.auth_api import login_user
    from frontend.auth_storage import persist_auth_to_cookie
except ModuleNotFoundError:
    from auth_api import login_user
    from auth_storage import persist_auth_to_cookie


st.set_page_config(
    page_title="Login | CloudSec Agent",
    page_icon="⛨",
    layout="wide",
    initial_sidebar_state="collapsed",
)
def inject_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        :root {
          --bg-grad-1: rgba(47,129,247,0.12);
          --bg-grad-2: rgba(63,185,80,0.08);
          --bg-start: #f8fafc;
          --bg-end: #f1f5f9;
          --text: #1e293b;
          --title: #0f172a;
          --muted: #64748b;
          --panel-bg: rgba(248,250,252,0.92);
          --panel-border: rgba(15,23,42,0.10);
          --panel-shadow: 0 10px 32px rgba(0,0,0,0.08);
          --panel-glow: rgba(47,129,247,0.10);
          --eyebrow-border: rgba(47,129,247,0.25);
          --eyebrow-bg: rgba(47,129,247,0.08);
          --eyebrow-text: #1e61f7;
          --bullet-bg: rgba(15,23,42,0.03);
          --bullet-border: rgba(15,23,42,0.09);
          --bullet-text: #475569;
          --input-bg: #f8fafc;
          --input-text: #0f172a;
          --input-border: rgba(15,23,42,0.15);
          --placeholder: #94a3b8;
          --label: #334155;
          --button-start: #1e61f7;
          --button-end: #0d47a1;
          --button-shadow: 0 8px 20px rgba(30,97,247,0.28);
        }

        .stApp {
          background:
            radial-gradient(circle at 20% 20%, var(--bg-grad-1), transparent 26%),
            radial-gradient(circle at 80% 82%, var(--bg-grad-2), transparent 22%),
            linear-gradient(180deg, var(--bg-start) 0%, var(--bg-end) 100%);
          color: var(--text);
          font-family: 'Inter', sans-serif;
        }

        [data-testid="stSidebar"],
        [data-testid="stSidebarNav"] {
          display: none !important;
        }

        #MainMenu,
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        footer {
          display: none !important;
          visibility: hidden !important;
        }

        [data-testid="stAppViewContainer"] > .main {
          display: grid;
          align-items: center;
          min-height: calc(100vh - 2.25rem);
        }

        .main .block-container {
          width: min(980px, 100%);
          max-width: 980px;
          padding-top: 0.6rem;
          padding-bottom: 0.6rem;
        }

        .panel,
        .card {
          border-radius: 24px;
          border: 1px solid var(--panel-border);
          background: var(--panel-bg);
          backdrop-filter: blur(16px);
          box-shadow: var(--panel-shadow);
        }

        .panel {
          min-height: 360px;
          padding: 1.35rem;
          display: flex;
          flex-direction: column;
          justify-content: space-between;
          position: relative;
          overflow: hidden;
        }

        .panel::after {
          content: '';
          position: absolute;
          inset: auto -80px -90px auto;
          width: 220px;
          height: 220px;
          border-radius: 50%;
          background: radial-gradient(circle, var(--panel-glow), transparent 70%);
          pointer-events: none;
        }

        .card {
          min-height: 0;
          padding: 1.2rem;
          margin-bottom: 0.55rem;
        }

        .eyebrow {
          display: inline-flex;
          align-items: center;
          gap: 0.4rem;
          width: fit-content;
          padding: 0.3rem 0.7rem;
          border-radius: 999px;
          border: 1px solid var(--eyebrow-border);
          background: var(--eyebrow-bg);
          color: var(--eyebrow-text);
          font-size: 0.72rem;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          font-family: monospace;
        }

        .hero-title {
          margin: 0.95rem 0 0.6rem;
          font-size: clamp(2.2rem, 4vw, 3.8rem);
          line-height: 0.98;
          letter-spacing: -0.06em;
          color: var(--title);
          max-width: 10ch;
        }

        .hero-copy {
          margin: 0 0 1.2rem;
          color: var(--muted);
          line-height: 1.7;
          max-width: 48ch;
        }

        .bullets {
          display: grid;
          gap: 0.8rem;
        }

        .bullet {
          padding: 0.85rem 0.95rem;
          border-radius: 16px;
          background: var(--bullet-bg);
          border: 1px solid var(--bullet-border);
          color: var(--bullet-text);
          line-height: 1.5;
          font-size: 0.93rem;
        }

        .card-title {
          margin: 0 0 0.3rem;
          font-size: 1.8rem;
          letter-spacing: -0.04em;
          color: var(--title);
        }

        .card-subtitle {
          margin: 0 0 1.1rem;
          color: var(--muted);
          line-height: 1.6;
          font-size: 0.94rem;
        }

        .stTextInput label {
          color: var(--label) !important;
          font-weight: 500 !important;
        }

        .stTextInput input {
          background: var(--input-bg) !important;
          color: var(--input-text) !important;
          border: 1px solid var(--input-border) !important;
          border-radius: 14px !important;
          padding: 0.78rem 0.92rem !important;
        }

        .stTextInput input::placeholder {
          color: var(--placeholder) !important;
        }

        div[data-testid="InputInstructions"] {
          display: none !important;
        }

        .stButton > button {
          width: 100%;
          background: linear-gradient(135deg, var(--button-start), var(--button-end)) !important;
          color: white !important;
          border: none !important;
          border-radius: 14px !important;
          font-weight: 700 !important;
          padding: 0.72rem 1rem !important;
          box-shadow: var(--button-shadow) !important;
        }

        .stButton > button:hover { filter: brightness(1.06); }

        .switch-link {
          text-align: center;
          margin-top: 0.95rem;
          color: var(--muted);
          font-size: 0.92rem;
        }

        @media (max-width: 900px) {
          .card-wrap {
            grid-template-columns: 1fr;
          }

          .panel,
          .card {
            min-height: auto;
          }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


inject_css()

if st.session_state.get("auth_token"):
    st.switch_page("streamlit_app.py")

if st.session_state.get("login_email") and "login_email_input" not in st.session_state:
    st.session_state.login_email_input = st.session_state.login_email

left, right = st.columns([1.1, 0.9], gap="large")

with left:
    st.markdown(
        """
        <div class="panel">
          <div>
            <div class="eyebrow">⛨ Cloud Security Workspace</div>
            <div class="hero-title">Secure access starts here.</div>
            <p class="hero-copy">Sign in to review IAM policies, inspect cloud logs, and analyze IaC in a focused, authenticated workspace.</p>
          </div>
          <div class="bullets">
            <div class="bullet"><strong>Policy review:</strong> Surface privilege escalation and least-privilege gaps fast.</div>
            <div class="bullet"><strong>Log analysis:</strong> Catch suspicious IPs, credential misuse, and risky changes.</div>
            <div class="bullet"><strong>Team-ready:</strong> One workspace, one account, better auditability.</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with right:
    st.markdown(
        """
        <div class="card">
          <div class="eyebrow">⛨ CloudSec Agent</div>
          <h1 class="card-title">Welcome back</h1>
          <p class="card-subtitle">Use your account to open the CloudSec RAG workspace.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("login_form", clear_on_submit=False):
      email = st.text_input("Email", placeholder="you@example.com", key="login_email_input")
      password = st.text_input(
        "Password",
        type="password",
        placeholder="Enter your password",
        key="login_password",
        help="Supports letters, numbers, and special characters.",
      )
      submitted = st.form_submit_button("Log in")

    if submitted:
        if not email or not password:
            st.error("Enter both email and password.")
        else:
            try:
                data = login_user(email.strip().lower(), password)
            except requests.HTTPError as exc:
                message = "Login failed."
                if exc.response is not None:
                    try:
                        message = exc.response.json().get("detail", message)
                    except Exception:
                        pass
                st.error(message)
            except requests.RequestException as exc:
                st.error(f"Could not reach the backend: {exc}")
            else:
                st.session_state.auth_token = data.get("access_token")
                st.session_state.user_email = data.get("user_email", email.strip().lower())

                # Cookie persistence should not block successful login.
                if st.session_state.auth_token and st.session_state.user_email:
                    try:
                        persist_auth_to_cookie(st.session_state.auth_token, st.session_state.user_email)
                    except Exception:
                        pass

                st.success("Logged in successfully.")
                st.switch_page("streamlit_app.py")

    st.markdown('<div class="switch-link">No account yet?</div>', unsafe_allow_html=True)
    if st.button("Create one", use_container_width=True):
      st.switch_page("pages/signup.py")
