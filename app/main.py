from contextlib import asynccontextmanager
from collections import defaultdict, deque
from threading import BoundedSemaphore
from time import monotonic
from typing import Annotated, List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy.orm import Session

from app.agent import run_agent
from app.auth import create_access_token, hash_password, verify_password, verify_token
from app.config import get_settings
from app.database import User, get_db, init_db


settings = get_settings()
bearer_scheme = HTTPBearer(auto_error=False)
AUTH_RATE_LIMIT_WINDOW_SECONDS = 60
AUTH_RATE_LIMIT_MAX_ATTEMPTS = 10
auth_rate_limits = defaultdict(deque)
ask_semaphore = BoundedSemaphore(int(settings["max_concurrent_ask_requests"]))


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title=str(settings["app_name"]), lifespan=lifespan)
init_db()
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings["cors_origins"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AttachmentRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., min_length=1, max_length=255)
    mime_type: Optional[str] = Field(default=None, max_length=255)
    size_bytes: int = Field(default=0, ge=0, le=25_000_000)
    kind: Optional[str] = Field(default=None, max_length=50)
    text_content: Optional[str] = Field(
        default=None,
        max_length=int(settings["max_attachment_chars"]),
    )


class ChatHistoryMessage(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=4000)


class QueryRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    query: str = Field(default="", max_length=int(settings["max_query_chars"]))
    attachments: Optional[List[AttachmentRequest]] = Field(
        default=None,
        max_length=int(settings["max_attachment_count"]),
    )
    history: Optional[List[ChatHistoryMessage]] = Field(default=None, max_length=12)


class SignupRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_email: str


def _extract_bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authorization header.")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header.")
    return token.strip()


def _rate_limit_auth(endpoint: str, identifier: str) -> None:
    now = monotonic()
    key = (endpoint, identifier)
    attempts = auth_rate_limits[key]
    while attempts and now - attempts[0] > AUTH_RATE_LIMIT_WINDOW_SECONDS:
        attempts.popleft()
    if len(attempts) >= AUTH_RATE_LIMIT_MAX_ATTEMPTS:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many attempts. Try again later.")
    attempts.append(now)


def _client_identifier(http_request: Request, email: str) -> str:
    forwarded_for = http_request.headers.get("x-forwarded-for", "")
    client_ip = forwarded_for.split(",", 1)[0].strip()
    if not client_ip and http_request.client:
        client_ip = http_request.client.host
    return f"{client_ip or 'unknown'}:{email.lower()}"


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    authorization = None if credentials is None else f"{credentials.scheme} {credentials.credentials}"
    token = _extract_bearer_token(authorization)
    payload = verify_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token.")

    user = db.query(User).filter(User.email == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")
    return user


@app.get("/")
@app.head("/")
def read_root():
    return {
        "message": "CloudSec AI Agent is running",
        "environment": settings["environment"],
    }


@app.get("/health")
def healthcheck():
    return {"status": "ok"}


@app.post("/signup", response_model=dict)
def signup(request: SignupRequest, http_request: Request, db: Session = Depends(get_db)):
    _rate_limit_auth("signup", _client_identifier(http_request, request.email))
    existing_user = db.query(User).filter(User.email == request.email.lower()).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    hashed_pwd = hash_password(request.password)
    new_user = User(email=request.email.lower(), hashed_password=hashed_pwd)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully", "user_id": new_user.id, "email": new_user.email}


@app.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, http_request: Request, db: Session = Depends(get_db)):
    _rate_limit_auth("login", _client_identifier(http_request, request.email))
    user = db.query(User).filter(User.email == request.email.lower()).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    access_token = create_access_token(data={"sub": user.email})
    return TokenResponse(access_token=access_token, user_email=user.email)


@app.post("/ask")
def ask_agent(request: QueryRequest, _: User = Depends(get_current_user)):
    if not request.query and not request.attachments:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide a query or at least one attachment.")

    if not ask_semaphore.acquire(blocking=False):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="The agent is busy. Try again shortly.")

    try:
        response = run_agent(
            request.query,
            [attachment.model_dump() for attachment in (request.attachments or [])],
            history=[message.model_dump() for message in (request.history or [])],
        )
        return {"answer": response}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The agent could not process the request.",
        )
    finally:
        ask_semaphore.release()
