# CloudSec RAG Agent

## Overview

CloudSec RAG Agent is an authenticated AI assistant for cloud security analysis. It combines a FastAPI backend, a Streamlit chat interface, local retrieval-augmented generation (RAG), and security-focused analyzers for common cloud review workflows.

The system helps users:

- Review IAM policies for wildcard permissions and overly broad access.
- Inspect cloud log snippets for suspicious actions.
- Flag simple cloud misconfiguration patterns.
- Ask cloud-security questions grounded in local knowledge-base documents.
- Use Gemini by default for generated responses, with optional OpenAI fallback.

At a high level, the RAG flow loads local security documents from `data/`, chunks them with metadata, retrieves relevant context, builds a structured prompt, and returns a concise assistant response.

## Features

- **Authenticated API access**
  - Email/password signup and login.
  - Bcrypt password hashing.
  - JWT bearer tokens for protected routes.
  - Lightweight in-memory rate limiting for login and signup attempts.

- **Cloud security assistant**
  - Dedicated IAM policy analyzer.
  - Basic cloud log analyzer.
  - Misconfiguration detector for common risky patterns.
  - General assistant fallback for non-cloud-security prompts.

- **RAG pipeline**
  - Loads supported text-like files from `data/`.
  - Splits documents into overlapping chunks.
  - Adds metadata such as source path, filename, and chunk id.
  - Uses FAISS when available.
  - Falls back to local hash embeddings and keyword search when needed.
  - Detects stale vectorstore document schemas and rebuilds safely.
  - Includes source references in cloud-security RAG answers.

- **Prompt and response reliability**
  - Separates system instructions, retrieved context, sources, and user query.
  - Treats user content and uploaded files as untrusted data.
  - Makes model/API failures visible instead of silently returning fallback text.
  - Includes clearer fallback responses when the selected model provider is not configured.

- **Deployment-ready configuration**
  - `Procfile`, `render.yaml`, and `Dockerfile` included.
  - Safe environment variable parsing with defaults.
  - Production guard for missing `SECRET_KEY`.
  - Production CORS wildcard protection.
  - Configurable request, attachment, and concurrency limits.

- **Streamlit frontend**
  - Signup and login pages.
  - Auth-gated chat workspace.
  - File upload support with frontend-side attachment count validation.
  - Chat history in session state.
  - Chat export.

## Architecture

```text
User
  |
  v
Streamlit Frontend
  |
  v
FastAPI Backend
  |
  +--> Auth Layer
  |      - Signup
  |      - Login
  |      - JWT validation
  |
  +--> Agent Router
  |      - IAM policy analyzer
  |      - Log analyzer
  |      - Misconfiguration detector
  |      - RAG/general assistant path
  |
  +--> Retriever
  |      - Load local docs
  |      - Chunk documents
  |      - Embed/query vectorstore
  |      - Rerank retrieved context
  |
  +--> LLM Call
         - Gemini API by default
         - Optional OpenAI Responses API fallback
         - Honest fallback when unavailable
```

### Request Flow

1. The user signs up or logs in through Streamlit.
2. The frontend stores the JWT session and sends authenticated requests to `/ask`.
3. The backend validates the token and classifies the request.
4. Structured analyzers handle IAM, log, and misconfiguration inputs.
5. Cloud-security questions use the retriever to fetch relevant local context from `data/`.
6. The agent builds a structured prompt with retrieved chunks, source labels, and retrieval quality hints.
7. The response is returned to the frontend in the existing `{"answer": ...}` format.

General non-cloud questions are answered directly by the configured model provider. Cloud/security questions use RAG first so answers are grounded in local documents.

## Tech Stack

| Area | Technology |
| --- | --- |
| Backend | FastAPI, Uvicorn, Pydantic |
| Frontend | Streamlit, Requests |
| Authentication | JWT, bcrypt, SQLAlchemy |
| Storage | SQLite by default, configurable `DATABASE_URL` |
| RAG / Retrieval | FAISS, NumPy, local hash embeddings, optional SentenceTransformer |
| LLM | Gemini API by default, optional OpenAI Responses API |
| Deployment | Render, Docker, Streamlit Community Cloud |
| Configuration | `.env`, `python-dotenv`, environment variables |

## Project Structure

```text
app.py                    Backend entrypoint
app/
  main.py                 FastAPI routes, auth dependencies, request models
  agent.py                Agent routing, prompt construction, model calls
  auth.py                 Password hashing and JWT helpers
  config.py               Environment configuration and production guards
  database.py             SQLAlchemy user model and DB session handling
  embeddings.py           Embedding helpers and hash fallback
  ingest.py               Vectorstore build entrypoint
  retriever.py            RAG retrieval, reranking, vectorstore persistence
  security/               IAM, log, and misconfiguration analyzers
frontend/
  streamlit_app.py        Auth-gated chat workspace
  auth_api.py             Frontend API client
  auth_storage.py         Cookie persistence helpers
  pages/login.py          Login page
  pages/signup.py         Signup page
data/                     Local knowledge-base and sample security inputs
  aws_docs/               Curated cloud security knowledge-base files
vectorstore/              Generated vector index and document cache
```

## Getting Started

### 1. Clone Repo

```bash
git clone <your-repo-url>
cd cloudsec-rag-agent
```

### 2. Create A Virtual Environment

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup Environment Variables

Copy the example file:

```bash
copy .env.example .env
```

On macOS/Linux:

```bash
cp .env.example .env
```

Set at least:

```text
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.5-flash
SECRET_KEY=replace-with-a-long-random-secret
CLOUDSEC_API_URL=http://127.0.0.1:8000
ENVIRONMENT=development
```

Gemini is used by default for live generated model responses. Without a configured model API key, the app still returns clear fallback messages for supported flows.

### 5. Build Or Refresh The Vectorstore

```bash
python -m app.ingest
```

Run this when you add or update files under `data/`.

The RAG index is generated from local files. If you add a file such as `data/aws_docs/s3_security.txt`, rebuild the vectorstore before testing questions about that topic.

### 6. Run Backend

```bash
python app.py
```

The backend starts on:

```text
http://127.0.0.1:8000
```

Health check:

```text
http://127.0.0.1:8000/health
```

### 7. Run Frontend

In a second terminal:

```bash
streamlit run frontend/streamlit_app.py
```

Open the Streamlit URL, create an account, log in, and start using the chat workspace.

## Environment Variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `LLM_PROVIDER` | `gemini` | Model provider to use: `gemini` or `openai`. |
| `GEMINI_API_KEY` | Empty | API key for Gemini API calls. |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model used by the backend. |
| `GEMINI_BASE_URL` | `https://generativelanguage.googleapis.com/v1beta` | Base URL for Gemini API calls. |
| `GEMINI_MAX_OUTPUT_TOKENS` | `800` | Maximum Gemini output tokens. |
| `OPENAI_API_KEY` | Empty | Optional API key for OpenAI Responses API calls when `LLM_PROVIDER=openai`. |
| `OPENAI_MODEL` | `gpt-4.1-mini` | Optional OpenAI model used when `LLM_PROVIDER=openai`. |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | Base URL for OpenAI-compatible Responses API. |
| `OPENAI_MAX_OUTPUT_TOKENS` | `400` | Maximum model output tokens. |
| `REQUEST_TIMEOUT_SECONDS` | `45` | Backend model request timeout. |
| `SECRET_KEY` | Random in dev | JWT signing key. Required when `ENVIRONMENT=production`. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | JWT lifetime in minutes. |
| `DATABASE_URL` | `sqlite:///data/users.db` | SQLAlchemy user database URL. |
| `CORS_ORIGINS` | `*` in dev | Comma-separated allowed frontend origins. Wildcard is blocked in production. |
| `CLOUDSEC_API_URL` | Render backend URL in frontend | Backend URL used by Streamlit. |
| `HOST` | `0.0.0.0` | Backend bind host. |
| `PORT` | `8000` | Backend bind port. |
| `ENVIRONMENT` | `development` | Runtime environment label and guard mode. |
| `DATA_DIR` | `data` | Directory containing RAG source documents. |
| `VECTORSTORE_DIR` | `vectorstore` | Directory for generated vectorstore files. |
| `MAX_QUERY_CHARS` | `4000` | Maximum `/ask` query length. |
| `MAX_ATTACHMENT_CHARS` | `12000` | Maximum text content per attachment. |
| `MAX_ATTACHMENT_COUNT` | `5` | Maximum attachments per request. |
| `MAX_CONCURRENT_ASK_REQUESTS` | `4` | In-process concurrency guard for `/ask`. |
| `ENABLE_SENTENCE_TRANSFORMER` | Disabled | Enables local SentenceTransformer loading when explicitly set. |
| `SENTENCE_TRANSFORMER_MODEL_PATH` | Empty | Optional local path for SentenceTransformer model files. |

Hash embeddings are the default because they work without downloads. For better retrieval, set `ENABLE_SENTENCE_TRANSFORMER=true` only when `all-MiniLM-L6-v2` or your configured local model path is already available on disk. The app loads SentenceTransformer with `local_files_only=True`, so production startup does not require internet access.

## RAG Knowledge Base

The local knowledge base lives under `data/`. The `data/aws_docs/` folder contains focused cloud security notes such as IAM security, S3 security, VPC networking, CloudTrail logging, KMS encryption, secrets management, incident response, and common misconfigurations.

To add knowledge:

1. Create or update a text-like file under `data/`, preferably a focused file under `data/aws_docs/`.
2. Keep each document focused on one topic so retrieval can select useful chunks.
3. Rebuild the vectorstore:

```bash
python -m app.ingest
```

4. Restart the backend if it is already running.

The model provider, Gemini by default, writes the final answer. The RAG grounding comes from retrieved local documents, not from Gemini alone. This lets the app answer general questions directly while keeping cloud-security answers tied to your curated knowledge base.

## API Overview

### Health

```http
GET /health
```

### Signup

```http
POST /signup
Content-Type: application/json

{
  "email": "you@example.com",
  "password": "at-least-8-characters"
}
```

### Login

```http
POST /login
Content-Type: application/json

{
  "email": "you@example.com",
  "password": "at-least-8-characters"
}
```

### Ask The Agent

```http
POST /ask
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "query": "Analyze this IAM policy for least-privilege issues.",
  "attachments": [
    {
      "name": "policy.json",
      "mime_type": "application/json",
      "size_bytes": 1234,
      "kind": "json",
      "text_content": "{\"Version\":\"2012-10-17\",\"Statement\":[]}"
    }
  ]
}
```

`/ask` requires a valid JWT and either a non-empty query or at least one attachment.

## Example Usage

### Example Query

```text
Summarize AWS IAM best practices for least privilege and risky wildcard permissions.
```

### Example Response Shape

```text
- Use narrowly scoped IAM actions and resources instead of wildcard permissions.
- Review policies for broad access such as "*" on Action or Resource.
- Confidence: Medium. The answer is based on retrieved local cloud-security context.
```

Actual responses depend on the contents of `data/`, the vectorstore state, and whether the selected provider API key is configured.

## Deployment

### Backend On Render

This repository includes `render.yaml`, `Procfile`, and `Dockerfile`.

Default backend start command:

```bash
python app.py
```

Recommended production environment variables:

```text
ENVIRONMENT=production
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.5-flash
SECRET_KEY=replace-with-a-long-random-secret
CORS_ORIGINS=https://your-streamlit-app-url.streamlit.app
CLOUDSEC_API_URL=https://your-backend-url.onrender.com
```

After adding or changing files under `data/`, push the commit, deploy the latest commit on Render, then rebuild the vectorstore from the Render shell:

```bash
python -m app.ingest
```

If the Render instance is rebuilt or the generated `vectorstore/` directory is not persisted, run ingestion again after deployment.

For durable production accounts, configure `DATABASE_URL` to a managed database. The default SQLite database is suitable for local development, but may not persist on ephemeral hosting.

### Frontend On Streamlit Community Cloud

Use this entrypoint:

```text
frontend/streamlit_app.py
```

The frontend has a lightweight dependency file:

```text
frontend/requirements.txt
```

Set:

```text
CLOUDSEC_API_URL=https://your-backend-url.onrender.com
```

### Frontend On Render

If deploying the Streamlit frontend to Render:

```bash
streamlit run frontend/streamlit_app.py --server.address 0.0.0.0 --server.port $PORT
```

## Security Considerations

- `SECRET_KEY` must be stable and private in production.
- `ENVIRONMENT=production` enforces a configured `SECRET_KEY`.
- JWTs are required for protected `/ask` access.
- Passwords are hashed with bcrypt before storage.
- Signup and login include lightweight rate limiting.
- Production CORS should use explicit frontend origins, not `*`.
- API keys and secrets should be configured through environment variables, never committed.
- Local SQLite is intended for development. Use a managed database for durable production users.
- Uploaded media files can be previewed in the frontend, but image/audio/video content is not directly inspected by the backend in this version.

## Improvements Made

Recent production-hardening and AI-quality work includes:

- Stable production JWT secret enforcement.
- Docker ignore rule to avoid packaging local SQLite databases.
- Auth rate limiting for signup and login.
- Clear model/API failure messages instead of silent fallbacks.
- Safer integer environment parsing.
- Production CORS wildcard protection.
- `/ask` concurrency guard to reduce overload risk.
- RAG chunking with overlap and metadata.
- Vectorstore schema detection and safe rebuild path.
- Retrieval reranking using lightweight keyword overlap.
- Structured prompts with separate instructions, context, sources, and user query.
- Logging for retrieval results, model calls, and fallback triggers.
- Frontend attachment-count validation aligned with backend limits.
- Cold-start optimization by using hash embeddings by default unless SentenceTransformer is explicitly enabled.

## Future Improvements

- Add automated tests for auth, RAG retrieval, and frontend/backend contracts.
- Add richer policy checks for IAM and cloud misconfiguration analysis.
- Add managed database deployment examples.
- Add source citations in the frontend response UI.
- Add support for extracting text from PDFs and office documents.
- Add optional evaluation examples for retrieval quality.

## Limitations

- Built-in security analyzers are heuristic helpers, not a replacement for a full cloud security scanner.
- Media uploads are accepted by the UI, but image/audio/video content is not directly analyzed by the backend.
- RAG quality depends on the local documents available under `data/`.
- Model-generated responses require a valid API key for the selected `LLM_PROVIDER`.
