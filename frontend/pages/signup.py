import requests
import streamlit as st

try:
    from frontend.auth_api import login_user, signup_user
    from frontend.auth_storage import persist_auth_to_cookie, restore_auth_from_cookie
except ModuleNotFoundError:
    from auth_api import login_user, signup_user
    from auth_storage import persist_auth_to_cookie, restore_auth_from_cookie


st.set_page_config(
    page_title="Sign Up | CloudSec Agent",
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
          --bg-grad-1: rgba(63,185,80,0.10);
          --bg-grad-2: rgba(47,129,247,0.08);
          --bg-start: #f8fafc;
          --bg-end: #f1f5f9;
          --text: #1e293b;
          --title: #0f172a;
          --muted: #64748b;
          --panel-bg: rgba(248,250,252,0.92);
          --panel-border: rgba(15,23,42,0.10);
          --panel-shadow: 0 10px 32px rgba(0,0,0,0.08);
          --panel-glow: rgba(63,185,80,0.10);
          --eyebrow-border: rgba(63,185,80,0.25);
          --eyebrow-bg: rgba(63,185,80,0.08);
          --eyebrow-text: #16a34a;
          --bullet-bg: rgba(15,23,42,0.03);
          --bullet-border: rgba(15,23,42,0.09);
          --bullet-text: #475569;
          --input-bg: #f8fafc;
          --input-text: #0f172a;
          --input-border: rgba(15,23,42,0.15);
          --placeholder: #94a3b8;
          --label: #334155;
          --button-start: #16a34a;
          --button-end: #15803d;
          --button-shadow: 0 8px 20px rgba(22,163,74,0.28);
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
          min-height: 520px;
          padding: 1.5rem;
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
          padding: 1.5rem;
          margin-bottom: 0.75rem;
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
          font-family: 'Inter', sans-serif !important;
        }

        .stTextInput div[data-baseweb="input"] {
          background: var(--input-bg) !important;
          border: 1px solid rgba(15, 23, 42, 0.12) !important;
          border-radius: 14px !important;
          transition: all 0.2s ease !important;
        }

        .stTextInput div[data-baseweb="input"]:hover {
          border-color: rgba(15, 23, 42, 0.25) !important;
        }

        .stTextInput div[data-baseweb="input"]:focus-within {
          border-color: var(--button-start) !important;
          box-shadow: 0 0 0 3px rgba(22, 163, 74, 0.15) !important;
        }

        .stTextInput div[data-baseweb="input"]:has(button) input {
          padding: 0.78rem 0.5rem 0.78rem 0.92rem !important;
        }

        .stTextInput input {
          background: transparent !important;
          color: var(--input-text) !important;
          border: none !important;
          border-radius: 0 !important;
          padding: 0.78rem 0.92rem !important;
          font-family: 'Inter', sans-serif !important;
          box-shadow: none !important;
          outline: none !important;
        }

        .stTextInput input::placeholder {
          color: var(--placeholder) !important;
          opacity: 1 !important;
        }
        .stTextInput input::-webkit-input-placeholder {
          color: var(--placeholder) !important;
          opacity: 1 !important;
        }
        .stTextInput input::-moz-placeholder {
          color: var(--placeholder) !important;
          opacity: 1 !important;
        }
        .stTextInput input:-ms-input-placeholder {
          color: var(--placeholder) !important;
          opacity: 1 !important;
        }

        /* Password visibility toggle button styling */
        .stTextInput div[data-baseweb="input"] button {
          color: var(--muted) !important;
          background: transparent !important;
          border: none !important;
          padding: 0 0.92rem 0 0.25rem !important;
          margin: 0 !important;
          height: 100% !important;
          align-self: center !important;
          transition: color 0.15s ease !important;
          box-shadow: none !important;
          outline: none !important;
        }
        .stTextInput div[data-baseweb="input"] button:hover {
          color: var(--text) !important;
          background: transparent !important;
        }
        .stTextInput div[data-baseweb="input"] button:focus,
        .stTextInput div[data-baseweb="input"] button:active {
          outline: none !important;
          color: var(--button-start) !important;
          background: transparent !important;
        }
        .stTextInput div[data-baseweb="input"] button svg {
          fill: currentColor !important;
        }

        div[data-testid="InputInstructions"] {
          display: none !important;
        }

        /* Secondary button styling (redirect/switch link buttons) */
        .stButton > button {
          width: 100%;
          background: #ffffff !important;
          color: var(--button-start) !important;
          border: 1px solid rgba(15, 23, 42, 0.12) !important;
          border-radius: 14px !important;
          font-weight: 600 !important;
          padding: 0.72rem 1rem !important;
          box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
          font-family: 'Inter', sans-serif !important;
          transition: all 0.2s ease !important;
        }

        .stButton > button,
        .stButton > button * {
          color: var(--button-start) !important;
        }

        .stButton > button:hover {
          background: #f8fafc !important;
          border-color: rgba(15, 23, 42, 0.2) !important;
          color: var(--button-start) !important;
          box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05) !important;
        }
        .stButton > button:hover * {
          color: var(--button-start) !important;
        }

        .stButton > button:focus,
        .stButton > button:focus-visible {
          background: #ffffff !important;
          border-color: var(--button-start) !important;
          color: var(--button-start) !important;
          box-shadow: 0 0 0 3px rgba(22, 163, 74, 0.15) !important;
          outline: none !important;
        }
        .stButton > button:focus *,
        .stButton > button:focus-visible * {
          color: var(--button-start) !important;
        }

        .stButton > button:active {
          background: #f1f5f9 !important;
          border-color: rgba(15, 23, 42, 0.25) !important;
          color: var(--button-start) !important;
          box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.05) !important;
        }
        .stButton > button:active * {
          color: var(--button-start) !important;
        }

        /* Primary Form Submit Button styling */
        div[data-testid="stFormSubmitButton"] button {
          width: 100%;
          background: linear-gradient(135deg, var(--button-start), var(--button-end)) !important;
          color: white !important;
          border: 1px solid var(--button-end) !important;
          border-radius: 14px !important;
          font-size: 0.95rem !important;
          font-weight: 700 !important;
          padding: 0.85rem 1.5rem !important;
          letter-spacing: 0.02em !important;
          box-shadow: 0 10px 25px -5px rgba(22, 163, 74, 0.4), 0 8px 20px -6px rgba(22, 163, 74, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
          transition: all 0.2s ease !important;
        }

        div[data-testid="stFormSubmitButton"] button,
        div[data-testid="stFormSubmitButton"] button * {
          color: white !important;
        }

        div[data-testid="stFormSubmitButton"] button:hover {
          background: linear-gradient(135deg, var(--button-start), var(--button-start)) !important;
          filter: brightness(1.08) !important;
          border-color: var(--button-end) !important;
          color: white !important;
          box-shadow: 0 12px 28px -4px rgba(22, 163, 74, 0.5), 0 8px 20px -6px rgba(22, 163, 74, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.25) !important;
        }
        div[data-testid="stFormSubmitButton"] button:hover * {
          color: white !important;
        }

        div[data-testid="stFormSubmitButton"] button:focus,
        div[data-testid="stFormSubmitButton"] button:focus-visible {
          background: linear-gradient(135deg, var(--button-start), var(--button-end)) !important;
          border-color: var(--button-end) !important;
          color: white !important;
          box-shadow: 0 0 0 3px rgba(22, 163, 74, 0.35), 0 10px 25px -5px rgba(22, 163, 74, 0.4) !important;
          outline: none !important;
        }
        div[data-testid="stFormSubmitButton"] button:focus *,
        div[data-testid="stFormSubmitButton"] button:focus-visible * {
          color: white !important;
        }

        div[data-testid="stFormSubmitButton"] button:active {
          background: linear-gradient(135deg, var(--button-end), var(--button-end)) !important;
          filter: brightness(0.95) !important;
          border-color: var(--button-end) !important;
          color: white !important;
          box-shadow: 0 2px 6px rgba(22, 163, 74, 0.2), inset 0 2px 4px rgba(0, 0, 0, 0.15) !important;
        }
        div[data-testid="stFormSubmitButton"] button:active * {
          color: white !important;
        }

        .switch-link {
          text-align: center;
          margin-top: 0.95rem;
          color: var(--muted);
          font-size: 0.92rem;
          font-family: 'Inter', sans-serif !important;
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

def init_auth_state():
    if "auth_token" not in st.session_state:
        st.session_state.auth_token = None
    if "user_email" not in st.session_state:
        st.session_state.user_email = None

    if not st.session_state.auth_token:
        token, email = restore_auth_from_cookie()
        if token:
            st.session_state.auth_token = token
            st.session_state.user_email = email

init_auth_state()
inject_css()

if st.session_state.get("auth_token"):
    st.switch_page("streamlit_app.py")

try:
    from frontend.auth_api import check_backend_health
except ImportError:
    from auth_api import check_backend_health

backend_awake = False
with st.spinner("Connecting to secure backend..."):
    backend_awake = check_backend_health()

if not backend_awake:
    st.warning("Backend is waking up from sleep (Render free tier cold start). Please wait...")
    import time
    time.sleep(3)
    st.rerun()

left, right = st.columns([1.1, 0.9], gap="large")

with left:
    st.markdown(
        """
        <div class="panel">
          <div>
            <div class="eyebrow">⛨ Cloud Security Workspace</div>
            <div class="hero-title">Create a secure workspace account.</div>
            <p class="hero-copy">Sign up to keep your cloud security investigations in one authenticated place with a clean audit trail.</p>
          </div>
          <div class="bullets">
            <div class="bullet"><strong>Fast setup:</strong> Email/password auth with hashed credentials and JWT session tokens.</div>
            <div class="bullet"><strong>Safer workflow:</strong> Keep your RAG assistant behind a login gate before access.</div>
            <div class="bullet"><strong>Simple access:</strong> One account, one workspace, no extra complexity.</div>
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
          <h1 class="card-title">Create account</h1>
          <p class="card-subtitle">Set up access to your cloud security RAG workspace.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("signup_form", clear_on_submit=False):
        email = st.text_input("Email", placeholder="you@example.com", key="signup_email")
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Create a strong password",
            key="signup_password",
            help="Supports letters, numbers, and special characters.",
        )
        confirm_password = st.text_input(
            "Confirm password",
            type="password",
            placeholder="Repeat your password",
            key="signup_confirm_password",
            help="Supports letters, numbers, and special characters.",
        )
        submitted = st.form_submit_button("Sign up")

    if submitted:
        normalized_email = email.strip().lower()
        if not normalized_email or not password or not confirm_password:
            st.error("Fill in all fields.")
        elif "@" not in normalized_email or "." not in normalized_email:
            st.error("Enter a valid email address.")
        elif len(password) < 8:
            st.error("Password must be at least 8 characters.")
        elif password != confirm_password:
            st.error("Passwords do not match.")
        else:
            try:
                with st.spinner("Connecting to the backend..."):
                    result = signup_user(normalized_email, password)
                    login_data = login_user(normalized_email, password)
            except requests.HTTPError as exc:
                message = "Signup failed."
                if exc.response is not None:
                    try:
                        message = exc.response.json().get("detail", message)
                    except Exception:
                        pass
                if "already registered" in message.lower():
                    st.session_state.login_email = normalized_email
                    st.switch_page("pages/login.py")
                else:
                    st.error(message)
            except requests.RequestException as exc:
                st.error(f"Could not reach the backend: {exc}")
            else:
                st.session_state.auth_token = login_data.get("access_token")
                st.session_state.user_email = login_data.get("user_email", normalized_email)

                if st.session_state.auth_token and st.session_state.user_email:
                    try:
                        persist_auth_to_cookie(st.session_state.auth_token, st.session_state.user_email)
                    except Exception:
                        pass

                st.success(result.get("message", "Account created successfully. Redirecting..."))
                import time
                time.sleep(0.5)
                st.rerun()

    st.markdown('<div class="switch-link">Already have an account?</div>', unsafe_allow_html=True)
    if st.button("Log in", use_container_width=True):
      st.switch_page("pages/login.py")
